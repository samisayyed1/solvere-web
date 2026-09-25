"""Generate a multi-view, multi-sheet drawing from a forge.drawing/2 spec
(runs under ``forge-python``; drives ``freecadcmd`` for the TechDraw part).

    model (build123d module or STEP) --measure (build123d)--> values + reference points
        --layout (this file)--> job.json --freecadcmd techdraw_sheets.py--> sheetN.techdraw.dxf + layout.json
        --compose_sheet (ezdxf)--> sheetN.dxf --dxf_to_pdf--> sheetN.pdf

The drawing is derived from the model and params, never the other way: no
number on the sheet is typed in by hand. ``generate`` is pure with respect to
its inputs (fixed date, no clock, no randomness), which is what the
reproducibility check relies on.
"""
from __future__ import annotations

import json
import math
import os
import subprocess
from pathlib import Path
from typing import Any, Mapping

import build123d as bd

import compose_sheet as cs
import model_measure as mm
from drawspec import SHEET_SIZES_MM, SpecError, format_dim_text

SCRIPTS = Path(__file__).resolve().parent
TECHDRAW_PY = SCRIPTS / "techdraw_sheets.py"
VIEW_GAP_MM = 6.0

_TEMPLATES = {"A4": "ISO/A4_Landscape_blank.svg", "A3": "ISO/A3_Landscape_blank.svg", "A2": "ISO/A2_Landscape_blank.svg",
              "A1": "ISO/A1_Landscape_blank.svg", "A0": "ISO/A0_Landscape_blank.svg", "ANSI-A": "ASME/ANSIA_Landscape_blank.svg",
              "ANSI-B": "ASME/ANSIB_Landscape_blank.svg", "ANSI-C": "ASME/ANSIC_Landscape.svg"}
# logical grid cell of each principal view relative to the front view, (col, row), row up
_CELLS = {
    "third": {"front": (0, 0), "top": (0, 1), "bottom": (0, -1), "right": (1, 0), "left": (-1, 0), "rear": (2, 0)},
    "first": {"front": (0, 0), "top": (0, -1), "bottom": (0, 1), "right": (-1, 0), "left": (1, 0), "rear": (-2, 0)},
}
# free cells: pictorial views prefer the corners, sections/details the front view's row/column
_FREE_ISO = [(1, 1), (-1, 1), (1, -1), (-1, -1), (2, 1), (2, -1), (-2, 1), (-2, -1), (2, 0), (-2, 0), (3, 0), (3, 1)]
_FREE_AUX = [(1, 0), (-1, 0), (0, -1), (0, 1), (2, 0), (-2, 0), (1, 1), (-1, 1), (1, -1), (-1, -1), (3, 0), (2, 1), (2, -1)]


class GenerationError(RuntimeError):
    """freecadcmd / composition failed (exit 2)."""


def _paper_axes(view: Mapping[str, Any]):
    return mm.paper_axes(view["direction"], view["x_direction"])


def plan_dimensions(spec: Mapping[str, Any], measures: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """Decide, per dimension, the paper axis it runs along, its side and its stacking index."""
    plans: dict[str, dict[str, Any]] = {}
    for dim in spec["dimensions"]:
        m = measures[dim["id"]]
        view = spec["views"][dim["view"]]
        xa, ya = _paper_axes(view)
        if dim["type"] == "linear":
            cx, cy = abs(mm.dot(dim["axis"], xa)), abs(mm.dot(dim["axis"], ya))
            if cx > 1 - 1e-9:
                along = "x"
            elif cy > 1 - 1e-9:
                along = "y"
            else:
                raise SpecError(f"[[dimension]] {dim['id']!r}: axis {dim['axis']} is not in the plane of view {view['id']!r} ({view['kind']})")
        elif "error" in m:
            along = "circle"
        else:
            ad = m["axis_dir"]
            if abs(mm.dot(ad, view["direction"])) > 1 - 1e-9:
                along = "circle"
            elif abs(mm.dot(ad, view["direction"])) < 1e-9:
                t = (mm.dot(ad, xa), mm.dot(ad, ya))
                along = "x" if abs(t[1]) > 1 - 1e-9 else "y" if abs(t[0]) > 1 - 1e-9 else "oblique"
            else:
                along = "oblique"
        side = dim["side"]
        if along == "x":
            side = side or "below"
            if side not in ("below", "above"):
                raise SpecError(f"[[dimension]] {dim['id']!r}: side {side!r} is not valid for a horizontal dimension (below/above)")
        elif along == "y":
            side = side or "right"
            if side not in ("left", "right"):
                raise SpecError(f"[[dimension]] {dim['id']!r}: side {side!r} is not valid for a vertical dimension (left/right)")
        else:
            side = "circle"
        plans[dim["id"]] = {"along": along, "side": side, "value": m.get("value", 0.0)}
    groups: dict[tuple[str, str], list[str]] = {}
    for dim in spec["dimensions"]:
        groups.setdefault((dim["view"], plans[dim["id"]]["side"]), []).append(dim["id"])
    for ids in groups.values():
        for k, did in enumerate(sorted(ids, key=lambda i: (plans[i]["value"], i))):
            plans[did]["stack"] = k
    return plans


def _footprint(shape, view, spec, plans) -> dict[str, float]:
    s = view["scale"]
    if view["kind"] == "detail":
        w = h = 2 * view["radius"] * s
    else:
        x0, x1, y0, y1 = mm.projected_extent(shape, view["direction"], view["x_direction"])
        w, h = (x1 - x0) * s, (y1 - y0) * s
    margin = {"below": 4.0, "above": 4.0, "left": 4.0, "right": 4.0}
    for dim in spec["dimensions"]:
        if dim["view"] != view["id"]:
            continue
        p = plans[dim["id"]]
        has_fcf = any(g["dimension"] == dim["id"] for g in spec["gdt"])
        if p["side"] == "circle":
            margin["right"] = max(margin["right"], 30.0 + 6 * p["stack"] + (10.0 if has_fcf else 0.0))
            margin["above"] = max(margin["above"], 22.0 + 6 * p["stack"] + (8.0 if has_fcf else 0.0))
        else:
            extra = 8.0 if has_fcf else 0.0
            margin[p["side"]] = max(margin[p["side"]], 10.0 + 8.0 * p["stack"] + 6.0 + extra)
            if has_fcf and p["side"] in ("left", "right"):
                margin[p["side"]] += 20.0
    if view["kind"] in ("section", "detail"):
        margin["below"] += 12.0
    for d in spec["datums"].values():
        if d["view"] == view["id"]:
            for k in margin:
                margin[k] = max(margin[k], 20.0)
    return {"w": w, "h": h, "left": w / 2 + margin["left"], "right": w / 2 + margin["right"],
            "below": h / 2 + margin["below"], "above": h / 2 + margin["above"]}


def layout_sheet(shape, spec, sheet, plans) -> dict[str, Any]:
    """Place the sheet's views on a projection-consistent grid. Returns positions and a fit report."""
    W, H = SHEET_SIZES_MM[spec["drawing"]["sheet_size"]]
    views = [spec["views"][v] for v in sheet["views"]]
    cellmap = _CELLS[spec["drawing"]["projection"]]
    cells: dict[str, tuple[int, int]] = {}
    has_front = any(v["kind"] == "front" for v in views)
    taken: set[tuple[int, int]] = set()
    for v in views:
        if "cell" in v:
            cells[v["id"]] = v["cell"]
        elif has_front and v["kind"] in cellmap:
            cells[v["id"]] = cellmap[v["kind"]]
        else:
            continue
        if cells[v["id"]] in taken:
            raise SpecError(f"view {v['id']!r}: grid cell {cells[v['id']]} is already used on sheet {sheet['index']}")
        taken.add(cells[v["id"]])
    for v in views:
        if v["id"] in cells:
            continue
        # without a front view there is no projection grid: views go in a row
        free = (_FREE_ISO if v["kind"] == "iso" else _FREE_AUX) if has_front else [(i, 0) for i in range(len(views) + 1)]
        rows_used, cols_used = {c[1] for c in taken}, {c[0] for c in taken}
        # prefer cells that do not add a new grid row/column (keeps the sheet compact)
        free = sorted(free, key=lambda c: (c[1] not in rows_used) + (c[0] not in cols_used))
        cell = next(c for c in free if c not in taken)
        cells[v["id"]] = cell
        taken.add(cell)
    fp = {v["id"]: _footprint(shape, v, spec, plans) for v in views}
    cols = sorted({c[0] for c in cells.values()})
    rows = sorted({c[1] for c in cells.values()})
    # Views sharing a column (row) share its centre line, so projected views stay aligned;
    # the column is as wide as the widest left part plus the widest right part.
    cl = {c: max(fp[v]["left"] for v, cc in cells.items() if cc[0] == c) + VIEW_GAP_MM / 2 for c in cols}
    cr = {c: max(fp[v]["right"] for v, cc in cells.items() if cc[0] == c) + VIEW_GAP_MM / 2 for c in cols}
    rb = {r: max(fp[v]["below"] for v, cc in cells.items() if cc[1] == r) + VIEW_GAP_MM / 2 for r in rows}
    ra = {r: max(fp[v]["above"] for v, cc in cells.items() if cc[1] == r) + VIEW_GAP_MM / 2 for r in rows}
    need_w, need_h = sum(cl[c] + cr[c] for c in cols), sum(rb[r] + ra[r] for r in rows)
    rx0, rx1 = cs.BORDER + 2.0, W - cs.BORDER - 2.0
    bottom = cs.BORDER + cs.TB_H + 3.0
    if sheet["index"] == 1:
        nl = len(cs.note_lines(spec, W - 2 * cs.BORDER - cs.TB_W - 8.0))
        bottom = max(bottom, cs.BORDER + 3.0 + nl * 4.2 + 3.0)
    ry0, ry1 = bottom, H - cs.BORDER - 2.0
    x = (rx0 + rx1) / 2 - need_w / 2
    colx = {}
    for c in cols:
        colx[c] = x + cl[c]
        x += cl[c] + cr[c]
    y = (ry0 + ry1) / 2 - need_h / 2
    rowy = {}
    for r in rows:
        rowy[r] = y + rb[r]
        y += rb[r] + ra[r]
    pos = {vid: (round(colx[c[0]], 3), round(rowy[c[1]], 3)) for vid, c in cells.items()}
    return {"positions": pos, "cells": cells, "need": (need_w, need_h), "region": (rx1 - rx0, ry1 - ry0),
            "fits": need_w <= rx1 - rx0 + 1e-6 and need_h <= ry1 - ry0 + 1e-6}


def _view_order(spec) -> list[str]:
    order, done = [], set()
    pending = list(spec["views"])
    while pending:
        for vid in list(pending):
            base = spec["views"][vid].get("base")
            if base is None or base in done:
                order.append(vid)
                done.add(vid)
                pending.remove(vid)
    return order


def generate(project: Path, spec: Mapping[str, Any], shape: bd.Shape, measures: Mapping[str, Any],
             datum_anchors: Mapping[str, Any], out_dir: Path, freecadcmd: str) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    plans = plan_dimensions(spec, measures)
    layouts = {s["index"]: layout_sheet(shape, spec, s, plans) for s in spec["sheets"]}
    step_path = out_dir / "model.step"
    bd.export_step(shape, str(step_path))

    jviews = []
    for vid in _view_order(spec):
        v = spec["views"][vid]
        X, Y = layouts[v["sheet"]]["positions"][vid]
        jv = {"id": vid, "obj": v["obj"], "kind": v["kind"], "page": v["sheet"], "direction": list(v["direction"]),
              "x_direction": list(v["x_direction"]), "scale": v["scale"], "X": X, "Y": Y}
        if v["kind"] == "section":
            jv.update({"base": v["base"], "origin": list(v["origin"]), "label": v["label"]})
        if v["kind"] == "detail":
            jv.update({"base": v["base"], "center": list(v["center"]), "radius": v["radius"], "label": v["label"]})
        jviews.append(jv)
    jdims = []
    for dim in spec["dimensions"]:
        m = measures[dim["id"]]
        if "error" in m:
            continue
        fmt, arbitrary = format_dim_text(dim, m["value"])
        jd = {"id": dim["id"], "obj": dim["obj"], "view": dim["view"], "type": dim["type"], "format": fmt,
              "arbitrary": arbitrary, "side": plans[dim["id"]]["side"], "stack": plans[dim["id"]]["stack"],
              "along": plans[dim["id"]]["along"], "angle": float(dim.get("angle", 45.0)),
              "has_fcf": any(g["dimension"] == dim["id"] for g in spec["gdt"]),
              "offset": [float(x) for x in dim["offset"]]}
        if dim["type"] == "linear":
            jd.update({"p1": m["p1"], "p2": m["p2"]})
        else:
            jd.update({"center": m["center"], "axis_dir": m["axis_dir"], "radius": m["radius"]})
        jdims.append(jd)
    sheets_out = []
    pages = []
    for s in spec["sheets"]:
        pages.append({"index": s["index"], "out_dxf": str((out_dir / f"sheet{s['index']}.techdraw.dxf").resolve())})
    job = {"step": str(step_path.resolve()), "template": _TEMPLATES[spec["drawing"]["sheet_size"]], "pages": pages,
           "views": jviews, "dims": jdims, "out_layout": str((out_dir / "layout.json").resolve())}
    job_path = out_dir / "job.json"
    job_path.write_text(json.dumps(job, indent=1, sort_keys=True))
    env = dict(os.environ, FORGE_DRAWING_JOB=str(job_path.resolve()))
    r = subprocess.run([freecadcmd, str(TECHDRAW_PY)], env=env, capture_output=True, text=True, timeout=600)
    (out_dir / "freecadcmd.log").write_text(r.stdout + "\n--- stderr ---\n" + r.stderr)
    if r.returncode != 0 or "OK " not in r.stdout:
        raise GenerationError(f"freecadcmd techdraw_sheets.py failed (exit {r.returncode}); see {out_dir / 'freecadcmd.log'}: "
                              f"{(r.stderr or r.stdout)[-600:]}")
    layout = json.loads((out_dir / "layout.json").read_text())

    loops = {vid: mm.section_loops(shape, v["origin"], v["direction"])
             for vid, v in spec["views"].items() if v["kind"] == "section"}
    issues = []
    size = SHEET_SIZES_MM[spec["drawing"]["sheet_size"]]
    for s in spec["sheets"]:
        raw = out_dir / f"sheet{s['index']}.techdraw.dxf"
        final = out_dir / f"sheet{s['index']}.dxf"
        issues += cs.compose(str(raw), str(final), spec=spec, sheet=s, sheet_size=size, layout=layout, measures=measures,
                             datum_anchors=datum_anchors, section_loops=loops, n_sheets=len(spec["sheets"]), plans=plans)
        from dxf_to_pdf import dxf_to_pdf
        pdf = out_dir / f"sheet{s['index']}.pdf"
        dxf_to_pdf(final, pdf, paper=size, text_layer=True)
        sheets_out.append({"index": s["index"], "dxf": final, "pdf": pdf, "fits": layouts[s["index"]]["fits"],
                           "need": layouts[s["index"]]["need"], "region": layouts[s["index"]]["region"]})
    return {"sheets": sheets_out, "layout": layout, "plans": plans, "issues": issues, "log": r.stdout.strip().splitlines()[-1:]}
