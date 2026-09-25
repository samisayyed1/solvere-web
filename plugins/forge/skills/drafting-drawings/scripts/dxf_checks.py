"""Read a finished drawing back and check it against the spec and the model
(runs under ``forge-python``). Every function here reads the *output* files --
the sheet DXFs (and PDFs) -- never the generator's intentions, so a tampered
or hand-edited DXF is judged on what it actually contains.

``check_drawing`` records measurements through ``forge.checkresult.Check``;
the tests call it on deliberately broken DXFs (seeded-wrong cases).
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

import ezdxf
from ezdxf import bbox as ezbbox

from dxf_to_pdf import decode_codes, pdf_strings

VALUE_TOL_MM = 0.01   # drawing / TechDraw / params vs the build123d measurement
EXTENT_TOL_MM = 0.05  # a principal view's outline vs the model's projected extents x scale
ALIGN_TOL_MM = 0.5    # projected views sharing a row/column
GEOMETRY_TYPES = ("LINE", "CIRCLE", "ARC", "ELLIPSE", "SPLINE", "LWPOLYLINE", "POLYLINE")
_NUM = r"\d+(?:\.\d+)?"
_DEV = r"(?:[+-]\d+(?:\.\d+)?|0)"
_DIM_RE = re.compile(rf"^(?:(?P<count>\d+)X )?(?P<sym>%%[cC]|R)?(?P<nom>{_NUM})"
                     rf"(?:(?P<sym_tol> %%[pP](?P<pm>{_NUM}))|(?: (?P<up>{_DEV})/(?P<lo>{_DEV}))|(?:/(?P<lim_lo>{_NUM})))?$")


# ------------------------------------------------------------------- reading
def read_dxf(path: Path):
    return ezdxf.readfile(str(path))


def layer_entities(doc, layer: str) -> list:
    return [e for e in doc.modelspace() if e.dxf.layer == layer]


def texts_on(doc, layer: str) -> list[str]:
    out = []
    for e in layer_entities(doc, layer):
        if e.dxftype() == "TEXT":
            out.append(e.dxf.text.strip())
        elif e.dxftype() == "MTEXT":
            out.append(e.plain_text().strip())
    return out


def dimension_texts(doc, layer: str) -> list[str]:
    out = []
    for e in layer_entities(doc, layer):
        if e.dxftype() != "DIMENSION":
            continue
        blk = doc.blocks.get(e.dxf.geometry) if e.dxf.hasattr("geometry") else None
        ts = [t.dxf.text for t in blk.query("TEXT")] if blk is not None else []
        out.append((ts[0] if ts else e.dxf.get("text", "")).strip())
    return out


def extents(entities) -> tuple[float, float, float, float] | None:
    b = ezbbox.extents(entities, fast=False)
    if not b.has_data:
        return None
    return b.extmin[0], b.extmin[1], b.extmax[0], b.extmax[1]


def parse_dim_text(text: str) -> dict[str, Any] | None:
    m = _DIM_RE.match(text.strip())
    if not m:
        return None
    out: dict[str, Any] = {"count": int(m.group("count") or 1),
                           "symbol": {"%%c": "diameter", "%%C": "diameter", "R": "radius"}.get(m.group("sym") or "", "linear"),
                           "nominal": float(m.group("nom"))}
    if m.group("pm"):
        out.update(style="plusminus", plus=float(m.group("pm")), minus=float(m.group("pm")))
    elif m.group("up"):
        out.update(style="plusminus", plus=float(m.group("up")), minus=-float(m.group("lo")))
    elif m.group("lim_lo"):
        out.update(style="limits", upper=float(m.group("nom")), lower=float(m.group("lim_lo")))
    else:
        out["style"] = None
    return out


# ---------------------------------------------------------- reproducibility
def _r(x: float) -> float:
    v = round(float(x), 4)
    return 0.0 if v == 0 else v


def _canon_value(v: Any) -> Any:
    if isinstance(v, float):
        return _r(v)
    if hasattr(v, "__iter__") and not isinstance(v, (str, bytes)):
        return [_canon_value(x) for x in v]
    return v


def _canon_entity(doc, e) -> str:
    attrs = {k: _canon_value(v) for k, v in e.dxfattribs().items() if k not in ("handle", "owner", "geometry")}
    extra: Any = None
    t = e.dxftype()
    if t == "LWPOLYLINE":
        extra = [_canon_value(p) for p in e.get_points("xy")]
    elif t == "SPLINE":
        extra = [_canon_value(list(p)) for p in e.control_points] + [_canon_value(list(p)) for p in e.fit_points]
    elif t == "HATCH":
        paths = []
        for p in e.paths:
            if hasattr(p, "vertices"):
                paths.append([_canon_value(list(v)[:2]) for v in p.vertices])
        extra = [e.dxf.pattern_name, paths]
    elif t == "DIMENSION":
        blk = doc.blocks.get(e.dxf.geometry) if e.dxf.hasattr("geometry") else None
        extra = sorted(_canon_entity(doc, x) for x in blk) if blk is not None else []
    xd = e.get_xdata("FORGE") if e.has_xdata("FORGE") else None
    return json.dumps([t, attrs, extra, [list(x) for x in xd] if xd else None], sort_keys=True, default=str)


def canonical_entities(path: Path) -> list[str]:
    """Order-independent description of every modelspace entity (handles excluded)."""
    doc = read_dxf(path)
    ents = [_canon_entity(doc, e) for e in doc.modelspace()]
    # layer state is part of what prints: a frozen/off/recoloured layer hides or changes a view
    for layer in doc.layers:
        ents.append(json.dumps(["LAYER", {"layer": layer.dxf.name, "color": layer.dxf.get("color"), "linetype": layer.dxf.get("linetype"),
                                          "on": layer.is_on(), "frozen": layer.is_frozen(), "plot": layer.dxf.get("plot", 1)}],
                               sort_keys=True))
    return sorted(ents)


def entity_set_diff(a: Path, b: Path) -> tuple[int, str]:
    ca, cb = Counter(canonical_entities(a)), Counter(canonical_entities(b))
    only_a, only_b = ca - cb, cb - ca
    n = sum(only_a.values()) + sum(only_b.values())
    layers = Counter(json.loads(x)[1].get("layer", "?") for x in list(only_a.elements()) + list(only_b.elements()))
    return n, ", ".join(f"{k}: {v}" for k, v in sorted(layers.items())) or "none"


def entity_set_sha(path: Path) -> str:
    return hashlib.sha256("\n".join(canonical_entities(path)).encode()).hexdigest()


# ------------------------------------------------------- projection symbol
def projection_method_drawn(doc) -> tuple[str | None, str]:
    """Infer the projection method from the symbol's geometry (not its label)."""
    ents = layer_entities(doc, "PROJECTION_SYMBOL")
    circles = [e for e in ents if e.dxftype() == "CIRCLE"]
    lines = [e for e in ents if e.dxftype() == "LINE" and e.dxf.get("linetype", "BYLAYER") in ("BYLAYER", "CONTINUOUS")]
    if len(circles) != 2:
        return None, f"expected 2 concentric circles, found {len(circles)}"
    c1, c2 = sorted(circles, key=lambda c: c.dxf.radius)
    if math.dist((c1.dxf.center[0], c1.dxf.center[1]), (c2.dxf.center[0], c2.dxf.center[1])) > 0.01:
        return None, "circles are not concentric"
    verticals = [ln for ln in lines if abs(ln.dxf.start[0] - ln.dxf.end[0]) < 1e-6]
    slanted = [ln for ln in lines if ln not in verticals]
    if len(verticals) != 2 or len(slanted) != 2:
        return None, f"expected a trapezoid (2 parallel ends + 2 sides), found {len(verticals)} ends / {len(slanted)} sides"
    big, small = sorted(verticals, key=lambda ln: -abs(ln.dxf.end[1] - ln.dxf.start[1]))
    lb, ls = abs(big.dxf.end[1] - big.dxf.start[1]), abs(small.dxf.end[1] - small.dxf.start[1])
    if abs(lb - 2 * c2.dxf.radius) > 0.01 or abs(ls - 2 * c1.dxf.radius) > 0.01:
        return None, "trapezoid ends do not match the circle diameters (not the same truncated cone)"
    ends = {(round(p[0], 3), round(p[1], 3)) for ln in (big, small) for p in (ln.dxf.start, ln.dxf.end)}
    side_pts = {(round(p[0], 3), round(p[1], 3)) for ln in slanted for p in (ln.dxf.start, ln.dxf.end)}
    if ends != side_pts:
        return None, "the trapezoid's sides do not join its ends"
    axis_y = (big.dxf.start[1] + big.dxf.end[1]) / 2
    if abs((small.dxf.start[1] + small.dxf.end[1]) / 2 - axis_y) > 0.01 or abs(c1.dxf.center[1] - axis_y) > 0.01:
        return None, "the circles and the trapezoid are not on one axis"
    xb, xs, xc = big.dxf.start[0], small.dxf.start[0], c1.dxf.center[0]
    toward = (xs - xb) * (xc - xs) > 0  # small end points at the circles
    beyond = abs(xc - xb) > abs(xs - xb)
    if toward and beyond:
        return "third", "small end of the cone faces the end view"
    if not toward and not (min(xb, xs) < xc < max(xb, xs)):
        return "first", "small end of the cone faces away from the end view"
    return None, "circles overlap the trapezoid"


# -------------------------------------------------------------------- check
_CELLS = {
    "third": {"top": (0, 1), "bottom": (0, -1), "right": (1, 0), "left": (-1, 0), "rear": (2, 0)},
    "first": {"top": (0, -1), "bottom": (0, 1), "right": (-1, 0), "left": (1, 0), "rear": (-2, 0)},
}


EDGE_TOL_MM = 0.05


def _unmatched_points(pts, center, scale, proj) -> int:
    """How many sheet points (mapped back to model mm about the view centre) are off every projected model edge."""
    import numpy as np
    segs, pcenter = proj
    if not pts:
        return 0
    a = np.asarray([s[0] for s in segs]); b = np.asarray([s[1] for s in segs])
    ab = b - a
    L2 = np.maximum((ab ** 2).sum(axis=1), 1e-18)
    bad = 0
    for x, y in pts:
        q = np.array([(x - center[0]) / scale + pcenter[0], (y - center[1]) / scale + pcenter[1]])
        t = np.clip(((q - a) * ab).sum(axis=1) / L2, 0.0, 1.0)
        d = np.sqrt((((a + ab * t[:, None]) - q) ** 2).sum(axis=1)).min()
        if d > EDGE_TOL_MM:
            bad += 1
    return bad


def title_fields_expected(spec: Mapping[str, Any], sheet: Mapping[str, Any], n_sheets: int) -> list[str]:
    dw = spec["drawing"]
    out = [dw["title"], dw["number"], dw["rev"], dw["material"], dw["units"], dw["general_tolerance"], dw["author"],
           dw["date"], sheet["scale_str"], f"SHEET {sheet['index']} OF {n_sheets}", dw["signoff"],
           f"{dw['projection'].upper()} ANGLE PROJECTION"]
    if dw["tolerancing_standard"]:
        out.append(dw["tolerancing_standard"])
    return out


def displayed_text(dim: Mapping[str, Any], parsed: Mapping[str, Any] | None, raw: str) -> str:
    return decode_codes(raw)


def check_drawing(chk, *, spec: Mapping[str, Any], sheet_files: Mapping[int, Mapping[str, Path]],
                  layout: Mapping[str, Any], measures: Mapping[str, Any], model_extents: Mapping[str, Any],
                  gen: Mapping[str, Any] | None, repro: Mapping[int, tuple[int, str]] | None,
                  model_edges: Mapping[str, Any] | None = None) -> None:
    """Record every drawing measurement on ``chk`` (a forge.checkresult.Check)."""
    dw = spec["drawing"]
    n = len(spec["sheets"])
    docs = {i: read_dxf(f["dxf"]) for i, f in sheet_files.items()}
    pdf_text = {i: set(pdf_strings(f["pdf"])) if f["pdf"].exists() else set() for i, f in sheet_files.items()}

    m = re.match(r"^ISO 2768-[fmcv]([HKL]?)$", dw["general_tolerance"])
    chk.measure("general_tolerance_class_current", 0 if m and m.group(1) else 1, "1", equals=1,
                remediation=f"General tolerance {dw['general_tolerance']!r} carries an ISO 2768-2 geometric class; ISO 2768-2 was "
                            "withdrawn (2021) and replaced by ISO 22081 (R5a §1-2). State ISO 2768-<f|m|c|v> for sizes and "
                            "specify general geometrical tolerances per ISO 22081 in a note.")

    for s in spec["sheets"]:
        i = s["index"]
        doc = docs[i]
        # -- title block
        from compose_sheet import TITLE_LABELS
        tb_all = texts_on(doc, "TITLE_BLOCK")
        tb = Counter(tb_all)
        exp = title_fields_expected(spec, s, n)
        missing = [x for x in exp if tb[x] < 1]
        allowed = Counter(exp) + Counter(TITLE_LABELS) + Counter(["-"] if not dw["tolerancing_standard"] else [])
        extra = list((tb - allowed).elements())
        if extra:
            missing.append(f"unexpected/duplicate text {extra}")
        chk.measure(f"sheet{i}_title_block_fields", len(exp) - len(missing), "1", equals=len(exp),
                    remediation=f"Sheet {i}: title-block text missing from layer TITLE_BLOCK: {missing}. Every field "
                                "(part, number, rev, material, units, general tolerance, author, date, scale, sheet, "
                                "sign-off line, projection) must be present as its own TEXT; regenerate, do not hand-edit.")
        # -- projection symbol
        drawn, why = projection_method_drawn(doc)
        chk.measure(f"sheet{i}_projection_symbol", 1 if drawn == dw["projection"] else 0, "1", equals=1,
                    remediation=f"Sheet {i}: projection symbol on layer PROJECTION_SYMBOL reads as {drawn!r} ({why}); the spec "
                                f"declares {dw['projection']!r} angle. The symbol must be present and match the declared method.")
        # -- layout fit
        if gen is not None:
            g = next(x for x in gen["sheets"] if x["index"] == i)
            over = max(0.0, g["need"][0] - g["region"][0], g["need"][1] - g["region"][1])
            chk.measure(f"sheet{i}_layout_overflow", round(over, 2), "mm", max=0.0,
                        remediation=f"Sheet {i}: the views and their dimensions need {g['need'][0]:.0f} x {g['need'][1]:.0f} mm "
                                    f"but the drawing area is {g['region'][0]:.0f} x {g['region'][1]:.0f} mm at "
                                    f"{s['scale_str']}. Use a larger sheet_size, a smaller scale, or move views to another [[sheet]].")
        # -- pdf
        pdf = sheet_files[i]["pdf"]
        size = pdf.stat().st_size if pdf.exists() else 0
        chk.measure(f"sheet{i}_pdf_size", size, "bytes", min=1000,
                    remediation=f"{pdf} is missing or implausibly small ({size} bytes); rerun dxf_to_pdf.py on the sheet DXF.")
        want = [decode_codes(x) for x in exp]
        got = sum(1 for x in want if x in pdf_text[i])
        chk.measure(f"sheet{i}_pdf_text_layer", got, "1", min=len(want),
                    remediation=f"Sheet {i} PDF text layer lacks {[x for x in want if x not in pdf_text[i]]}; "
                                "the PDF must carry the same title-block and dimension text as the DXF.")
        # -- reproducibility
        if repro is not None:
            nd, where = repro[i]
            chk.measure(f"sheet{i}_reproducible", nd, "entities", max=0,
                        remediation=f"Sheet {i}: regenerating from the same spec, params and model gave {nd} different DXF "
                                    f"entities (by layer: {where}). A drawing must be a pure function of its inputs: remove "
                                    "clock/random inputs, or do not hand-edit generated DXFs.")
        # -- arrangement of principal views
        cells = _CELLS[dw["projection"]]
        on = {spec["views"][v]["kind"]: v for v in s["views"] if spec["views"][v]["kind"] in ("front",) + tuple(cells)}
        if "front" in on:
            fb = extents(layer_entities(doc, spec["views"][on["front"]]["obj"]))
            bad = []
            for kind, vid in on.items():
                if kind == "front" or fb is None:
                    continue
                vb = extents(layer_entities(doc, spec["views"][vid]["obj"]))
                if vb is None:
                    continue
                col, row = cells[kind]
                fcx, fcy = (fb[0] + fb[2]) / 2, (fb[1] + fb[3]) / 2
                vcx, vcy = (vb[0] + vb[2]) / 2, (vb[1] + vb[3]) / 2
                if col and (vcx - fcx) * col <= 0 or row and (vcy - fcy) * row <= 0:
                    bad.append(f"{vid} ({kind}) is on the wrong side of the front view for {dw['projection']}-angle")
                if col == 0 and abs(vcx - fcx) > ALIGN_TOL_MM or row == 0 and abs(vcy - fcy) > ALIGN_TOL_MM:
                    bad.append(f"{vid} ({kind}) is not aligned with the front view")
            chk.measure(f"sheet{i}_view_arrangement", len(bad), "violations", max=0,
                        remediation=f"Sheet {i}: {bad}. Principal views must sit where the declared projection method puts "
                                    "them and stay aligned with the front view.")

    # -- views
    for vid, v in spec["views"].items():
        doc = docs[v["sheet"]]
        geo = [e for e in layer_entities(doc, v["obj"]) if e.dxftype() in GEOMETRY_TYPES]
        chk.measure(f"view_{vid}_present", len(geo), "entities", min=3,
                    remediation=f"View {vid!r} ({v['kind']}) has {len(geo)} geometry entities on layer {v['obj']} of sheet "
                                f"{v['sheet']}; a declared view must be drawn. Check freecadcmd.log for a view that failed.")
        proj = (model_edges or {}).get(vid)
        if proj is not None and geo:
            b = extents(geo)
            c = ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
            pts = [(p[0], p[1]) for e in geo if e.dxftype() == "LINE" for p in (e.dxf.start, e.dxf.end)]
            bad = _unmatched_points(pts, c, v["scale"], proj)
            chk.measure(f"view_{vid}_orientation", bad, "points", max=0,
                        remediation=f"View {vid!r}: {bad} line end points on layer {v['obj']} do not lie on the model's edges "
                                    f"projected as a {v['kind']} view (tolerance {EDGE_TOL_MM} mm) -- the view is mirrored, "
                                    "rotated or of another direction than declared.")
        exp_ext = model_extents.get(vid)
        if exp_ext is not None and geo:
            b = extents(geo)
            err = max(abs((b[2] - b[0]) - exp_ext[0]), abs((b[3] - b[1]) - exp_ext[1]))
            chk.measure(f"view_{vid}_extent_error", round(err, 4), "mm", max=EXTENT_TOL_MM,
                        remediation=f"View {vid!r} outline is {b[2] - b[0]:.3f} x {b[3] - b[1]:.3f} mm on the sheet; the model "
                                    f"projected at {v['scale_str']} is {exp_ext[0]:.3f} x {exp_ext[1]:.3f} mm. The view is at "
                                    "the wrong scale/orientation, or (section) shows the wrong side of the cutting plane.")
        if v["kind"] in ("section", "detail"):
            base_doc = docs[spec["views"][v["base"]]["sheet"]]
            marker_layer = f"{'SECTION_LINE' if v['kind'] == 'section' else 'DETAIL_CIRCLE'}_{vid}"
            marker_ok = v["label"] in texts_on(base_doc, marker_layer) and any(
                e.dxftype() in ("LINE", "CIRCLE") for e in layer_entities(base_doc, marker_layer))
            label = texts_on(doc, f"VIEW_LABEL_{vid}")
            label_ok = any(t.startswith(("SECTION ", "DETAIL ")) and v["label"] in t for t in label)
            hatch_ok = v["kind"] != "section" or any(e.dxftype() == "HATCH" for e in layer_entities(doc, f"HATCH_{vid}"))
            ok = marker_ok and label_ok and hatch_ok
            chk.measure(f"view_{vid}_markers", 1 if ok else 0, "1", equals=1,
                        remediation=f"{v['kind'].title()} view {vid!r}: cutting-plane/detail marker with letter {v['label']} on "
                                    f"the base view: {marker_ok}; view label: {label_ok}; hatching: {hatch_ok}. All three "
                                    "must be present.")

    # -- dimensions
    for dim in spec["dimensions"]:
        did = dim["id"]
        req = dim["requirement"]
        doc = docs[spec["views"][dim["view"]]["sheet"]]
        m = measures[did]
        if "error" in m:
            chk.measure(f"dim_{did}_resolved", 0, "1", equals=1, requirement=req,
                        remediation=f"Dimension {did!r}: its selector does not resolve on the model ({m['error']}). The model "
                                    "no longer has the feature the drawing calls out; fix the model or the selector.")
            continue
        model_v = m["value"]
        rec = layout.get("dims", {}).get(did, {})
        texts = dimension_texts(doc, dim["obj"]) + texts_on(doc, f"DIMTXT_{did}")
        callouts = [t for t in texts if parse_dim_text(t)]
        parsed = parse_dim_text(callouts[0]) if len(callouts) == 1 else None
        raw_text = callouts[0] if callouts else (texts[0] if texts else "")
        want_sym = {"diameter": "diameter", "radius": "radius"}.get(dim["type"], "linear")
        present = parsed is not None and parsed["symbol"] == want_sym and parsed["count"] == dim["count"]
        chk.measure(f"dim_{did}_present", 1 if present else 0, "1", equals=1, requirement=req,
                    remediation=f"Critical dimension {did!r} ({dim['type']}, view {dim['view']!r}) is not on the drawing as a "
                                f"parseable callout with the right symbol/count (found {texts!r} on layers {dim['obj']} / "
                                f"DIMTXT_{did}). Regenerate the drawing; see layout.json for why TechDraw could not attach it: "
                                f"{rec.get('reason', 'n/a')}. Exactly one callout per dimension is allowed (found {len(callouts)}).")
        if rec.get("method") == "annotation":
            lay_v = layout.get("views", {}).get(dim["view"])
            ok_leader = lay_v is not None and _leader_on_feature(doc, did, lay_v, m.get("center") or m.get("p2"))
            chk.measure(f"dim_{did}_annotation_fallback", 1 if (dim["allow_annotation"] and ok_leader) else 0, "1", equals=1,
                        requirement=req,
                        remediation=f"Dimension {did!r} could not be attached as a TechDraw dimension ({rec.get('reason')}), so "
                                    "its value is annotation text with no independent TechDraw measurement. Put it on a view where "
                                    "the feature is visible edge-on or as a circle; only if that is impossible set "
                                    f"allow_annotation = true (allowed: {dim['allow_annotation']}; leader on the feature: {ok_leader}).")
        if parsed is None:
            continue
        tol = dim["tol"]
        if parsed["style"] == "limits":
            # each limit on its own: upper = model + plus, lower = model - minus
            nominal_drawn = parsed["upper"] - tol["plus"]
            err = max(abs(parsed["upper"] - (model_v + tol["plus"])), abs(parsed["lower"] - (model_v - tol["minus"])))
            tol_ok = tol["style"] == "limits" and abs((parsed["upper"] - parsed["lower"]) - (tol["plus"] + tol["minus"])) <= 1e-6
        else:
            nominal_drawn = parsed["nominal"]
            err = abs(nominal_drawn - model_v)
            tol_ok = parsed["style"] == "plusminus" and tol["style"] == "plusminus" and \
                abs(parsed["plus"] - tol["plus"]) < 1e-9 and abs(parsed["minus"] - tol["minus"]) < 1e-9
        chk.measure(f"dim_{did}_drawing_vs_model", round(err, 5), "mm", max=VALUE_TOL_MM, requirement=req,
                    remediation=f"Dimension {did!r}: the drawing says {nominal_drawn:.4f} mm but the model measures "
                                f"{model_v:.4f} mm (build123d, independent of TechDraw); |diff| {err:.4f} > {VALUE_TOL_MM} mm. "
                                "Regenerate the drawing from the current model; never edit the number by hand.")
        chk.measure(f"dim_{did}_tolerance", 1 if tol_ok else 0, "1", equals=1, requirement=req,
                    remediation=f"Dimension {did!r}: callout {raw_text!r} does not carry the spec tolerance "
                                f"(+{tol['plus']}/-{tol['minus']} mm, style {tol['style']}). Every critical dimension needs its "
                                "explicit tolerance on the sheet.")
        if rec.get("method") not in ("techdraw", "annotation") or (rec.get("method") == "techdraw" and "raw_value" not in rec):
            chk.measure(f"dim_{did}_attachment_recorded", 0, "1", equals=1, requirement=req,
                        remediation=f"Dimension {did!r} has no attachment record in layout.json, so TechDraw's own value "
                                    "cannot be compared with the model. Regenerate the drawing (verify.py without --recheck).")
        geo_v = _dxf_linear_value(doc, dim["obj"], rec.get("type"), spec["views"][dim["view"]]["scale"])
        if rec.get("method") == "techdraw" and rec.get("type") in ("DistanceX", "DistanceY"):
            e4 = abs(geo_v - model_v) if geo_v is not None else math.inf
            chk.measure(f"dim_{did}_dxf_geometry_vs_model", round(e4, 5) if geo_v is not None else -1.0, "mm",
                        min=0.0, max=VALUE_TOL_MM, requirement=req,
                        remediation=f"Dimension {did!r}: the DIMENSION's extension-line origins in the DXF span "
                                    f"{geo_v} mm (sheet distance / view scale) but the model measures {model_v:.4f} mm; the "
                                    "dimension is attached to the wrong geometry or the DXF was edited.")
        if rec.get("method") == "techdraw" and "raw_value" in rec:
            e2 = abs(rec["raw_value"] - model_v)
            chk.measure(f"dim_{did}_techdraw_vs_model", round(e2, 5), "mm", max=VALUE_TOL_MM, requirement=req,
                        remediation=f"Dimension {did!r}: TechDraw measured {rec['raw_value']:.4f} mm on the projected view "
                                    f"(refs {rec.get('refs')}) but the model measures {model_v:.4f} mm -- the dimension is "
                                    "attached to the wrong geometry. Tighten the selector or pick a view where the feature is "
                                    "seen edge-on.")
        e3 = abs(dim["param_nominal"] - model_v)
        chk.measure(f"dim_{did}_params_vs_model", round(e3, 5), "mm", max=VALUE_TOL_MM, requirement=req,
                    remediation=f"Dimension {did!r}: params {dim['param']} = {dim['param_nominal']} mm but the model measures "
                                f"{model_v:.4f} mm. The model is not built from params (CONTRACTS §2), or the dimension is "
                                "bound to the wrong params key.")
        if dim["param_tol"] is not None:
            pp, pm = dim["param_tol"]
            same = abs(pp - tol["plus"]) < 1e-9 and abs(pm - tol["minus"]) < 1e-9
            chk.measure(f"dim_{did}_tolerance_vs_params", 1 if same else 0, "1", equals=1, requirement=req,
                        remediation=f"Dimension {did!r}: drawing tolerance +{tol['plus']}/-{tol['minus']} mm differs from params "
                                    f"{dim['param']} tol +{pp}/-{pm} mm. params/params.toml is the single source of truth; "
                                    "change it there (forge params set) or fix the spec.")
        if dim["count"] > 1:
            chk.measure(f"dim_{did}_feature_count", m.get("count_found", 0), "1", equals=dim["count"], requirement=req,
                        remediation=f"Dimension {did!r} is called out as {dim['count']}X but the model has "
                                    f"{m.get('count_found', 0)} coaxial-distinct cylinders of that radius and direction.")
        shown = decode_codes(raw_text)
        in_pdf = shown in pdf_text[spec["views"][dim["view"]]["sheet"]]
        chk.measure(f"dim_{did}_in_pdf", 1 if in_pdf else 0, "1", equals=1, requirement=req,
                    remediation=f"Dimension {did!r}: {shown!r} is in the DXF but not in the PDF text layer; regenerate the PDF.")

    # -- datums and feature control frames
    for did, d in spec["datums"].items():
        doc = docs[spec["views"][d["view"]]["sheet"]]
        ents = layer_entities(doc, f"DATUM_{did}")
        ok = did in texts_on(doc, f"DATUM_{did}") and any(e.dxftype() == "SOLID" for e in ents)
        chk.measure(f"datum_{did}_symbol", 1 if ok else 0, "1", equals=1,
                    remediation=f"Datum feature symbol {did} (filled triangle + boxed letter) is missing from layer DATUM_{did}.")
    for g in spec["gdt"]:
        vid = next(x["view"] for x in spec["dimensions"] if x["id"] == g["dimension"])
        doc = docs[spec["views"][vid]["sheet"]]
        ents = layer_entities(doc, f"FCF_{g['id']}")
        chars = [dict(e.get_xdata("FORGE")).get(1000) for e in ents if e.has_xdata("FORGE")]
        from compose_sheet import fcf_text_cells
        want_cells = fcf_text_cells(g)
        have = texts_on(doc, f"FCF_{g['id']}")
        ok = f"gdt:{g['characteristic']}" in [x for e in ents if e.has_xdata("FORGE") for _, x in e.get_xdata("FORGE")] \
            and all(c in have for c in want_cells) and len(have) == len(want_cells)
        chk.measure(f"gdt_{g['id']}_frame", 1 if ok else 0, "1", equals=1, requirement=g["requirement"],
                    remediation=f"Feature control frame {g['id']!r} should read {g['characteristic']} | {' | '.join(want_cells)} "
                                f"on layer FCF_{g['id']}; found {chars} / {have}.")

    # -- notes
    if spec["notes"]:
        doc = docs[1]
        lines = sorted((e for e in layer_entities(doc, "NOTES") if e.dxftype() == "TEXT"), key=lambda e: -e.dxf.insert[1])
        blob = re.sub(r"\s+", " ", " ".join(e.dxf.text.strip() for e in lines))
        found = sum(1 for nt in spec["notes"] if re.sub(r"\s+", " ", nt) in blob)
        chk.measure("notes_present", found, "1", min=len(spec["notes"]),
                    remediation="Spec [[note]] text is missing from the NOTES layer on sheet 1.")

    for issue in (gen or {}).get("issues", []):
        chk.measure(issue["name"], 0, "1", equals=1, remediation=issue["remediation"])


def _dxf_linear_value(doc, layer: str, dtype: str | None, scale: float) -> float | None:
    """TechDraw's measured length recovered from the DXF itself: the extension-line origins."""
    for e in layer_entities(doc, layer):
        if e.dxftype() != "DIMENSION":
            continue
        p2, p3 = e.dxf.get("defpoint2"), e.dxf.get("defpoint3")
        if p2 is None or p3 is None:
            return None
        d = abs(p2[0] - p3[0]) if dtype == "DistanceX" else abs(p2[1] - p3[1])
        return d / scale
    return None


def _leader_on_feature(doc, did: str, lay: Mapping[str, Any], p3) -> bool:
    """The annotation's arrowhead tip must sit on the feature's projection (within 0.1 sheet mm)."""
    if p3 is None:
        return False
    from compose_sheet import page_xy
    fx, fy = page_xy(lay, p3)
    for e in layer_entities(doc, f"DIMTXT_{did}"):
        if e.dxftype() == "SOLID" and math.hypot(e.dxf.vtx0[0] - fx, e.dxf.vtx0[1] - fy) <= 0.1:
            return True
    return False
