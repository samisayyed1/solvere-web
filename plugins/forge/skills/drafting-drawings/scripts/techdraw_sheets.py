"""Multi-view TechDraw sheets from a job file -- runs under ``freecadcmd``.

freecadcmd's bundled Python 3.11 is a separate interpreter from forge-python:
no build123d/ezdxf here, standard library + FreeCAD only. The job JSON is
written by ``drawing_pipeline.py`` (forge-python), which has already
checked the spec, measured the model and laid the views out.

    FORGE_DRAWING_JOB=<abs job.json> freecadcmd techdraw_sheets.py

For every page: imports the STEP, adds DrawViewPart / DrawViewSection /
DrawViewDetail views, projects each dimension's model reference points into
its view, snaps them to the view's own projected (HLR) vertices or circle
edges, adds TechDraw::DrawViewDimension objects, and exports the page with
``TechDraw.writeDXFPage`` (full-page DXF is the headless export that works;
PDF/SVG page export needs the GUI -- ADR-001 §15.3). Writes a layout JSON
with, per view, the page placement and the exact 3-D -> 2-D projection map
(so the ezdxf composer can place hatching, datum and section markers), and,
per dimension, how it was attached and TechDraw's own measured value.

Exit 0 and ``OK`` on success; exit 2 and ``ERROR`` otherwise.
"""
from __future__ import annotations

import json
import math
import os
import sys
import traceback

SNAP_MM = 0.05          # model mm: projected reference point -> real view vertex
CIRCLE_MATCH_MM = 0.05  # centre and radius match for a circle edge
GAP0_MM = 9.0           # sheet mm from the view outline to the first dimension line
STEP_MM = 8.0           # sheet mm between stacked dimension lines
# FreeCAD 1.1.3 draws a linear dimension's line 5 mm below (DistanceX) / left of
# (DistanceY) the text position it is given (measured on the exported DXF), so the
# text position is offset by this much to put the line where it is wanted.
TD_LINE_OFFSET_MM = 5.0


def _vec(FreeCAD, v):
    return FreeCAD.Vector(float(v[0]), float(v[1]), float(v[2]))


def _vertices(view):
    out = []
    i = 0
    while True:
        try:
            p = view.getVertexByIndex(i).Point
        except Exception:
            break
        out.append((i, p.x, p.y))
        i += 1
    return out


def _edges(view):
    out = []
    i = 0
    while True:
        try:
            e = view.getEdgeByIndex(i)
        except Exception:
            break
        out.append((i, e))
        i += 1
    return out


def _bbox(view):
    xs, ys = [], []
    for _, e in _edges(view):
        b = e.BoundBox
        xs += [b.XMin, b.XMax]
        ys += [b.YMin, b.YMax]
    if not xs:
        return None
    return [min(xs), min(ys), max(xs), max(ys)]


def _affine(FreeCAD, doc, view):
    """view2d(p) = A @ p + b, measured through TechDraw's own projection of 4 points.

    A cosmetic vertex stores its point with Y inverted (Qt convention), which
    is undone here; the vertices are removed again before any dimension is made.
    """
    pts = [(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)]
    q = []
    for p in pts:
        tag = view.makeCosmeticVertex3d(_vec(FreeCAD, p))
        cv = view.getCosmeticVertex(tag).Point
        q.append((cv.x, -cv.y))
        view.removeCosmeticVertex(tag)
    doc.recompute()
    b = q[0]
    A = [[q[i + 1][0] - b[0] for i in range(3)], [q[i + 1][1] - b[1] for i in range(3)]]
    return A, [b[0], b[1]]


def _apply(A, b, p):
    return (A[0][0] * p[0] + A[0][1] * p[1] + A[0][2] * p[2] + b[0],
            A[1][0] * p[0] + A[1][1] * p[1] + A[1][2] * p[2] + b[1])


def _snap(verts, q, along):
    """Nearest real vertex whose coordinate along `along` (0=x, 1=y) matches q within SNAP_MM."""
    other = 1 - along
    best = None
    for i, x, y in verts:
        c = (x, y)
        if abs(c[along] - q[along]) <= SNAP_MM:
            key = (abs(c[other] - q[other]), abs(c[along] - q[along]))
            if best is None or key < best[0]:
                best = (key, i)
    return None if best is None else best[1]


def main() -> int:
    try:
        sys.stdout.reconfigure(line_buffering=True, encoding="utf-8")
        sys.stderr.reconfigure(line_buffering=True, encoding="utf-8")
    except Exception:
        pass
    job_path = os.environ.get("FORGE_DRAWING_JOB")
    if not job_path:
        print("ERROR: FORGE_DRAWING_JOB must be set", file=sys.stderr)
        return 2
    with open(job_path, encoding="utf-8") as fh:
        job = json.load(fh)

    import FreeCAD
    import Part
    import TechDraw

    doc = FreeCAD.newDocument("forge_sheets")
    shape = Part.read(job["step"])
    model = doc.addObject("Part::Feature", "Model")
    model.Shape = shape
    doc.recompute()

    pages = {}
    for pg in job["pages"]:
        page = doc.addObject("TechDraw::DrawPage", f"Page{pg['index']}")
        tmpl = doc.addObject("TechDraw::DrawSVGTemplate", f"Template{pg['index']}")
        tmpl.Template = os.path.join(FreeCAD.getResourceDir(), "Mod", "TechDraw", "Templates", job["template"])
        page.Template = tmpl
        pages[pg["index"]] = page
    doc.recompute()

    views = {}
    layout = {"views": {}, "dims": {}, "freecad": ".".join(FreeCAD.Version()[:3])}
    for v in job["views"]:
        typ = {"section": "TechDraw::DrawViewSection", "detail": "TechDraw::DrawViewDetail"}.get(v["kind"], "TechDraw::DrawViewPart")
        obj = doc.addObject(typ, v["obj"])
        pages[v["page"]].addView(obj)
        obj.Source = [model]
        obj.Direction = _vec(FreeCAD, v["direction"])
        obj.XDirection = _vec(FreeCAD, v["x_direction"])
        obj.ScaleType = "Custom"
        obj.Scale = float(v["scale"])
        obj.X = float(v["X"])
        obj.Y = float(v["Y"])
        if v["kind"] == "section":
            obj.BaseView = views[v["base"]]
            obj.SectionNormal = _vec(FreeCAD, v["direction"])
            obj.SectionOrigin = _vec(FreeCAD, v["origin"])
            obj.SectionSymbol = v["label"]
        if v["kind"] == "detail":
            base = views[v["base"]]
            bl = layout["views"][v["base"]]
            ax, ay = _apply(bl["A"], bl["b"], v["center"])
            obj.BaseView = base
            obj.AnchorPoint = FreeCAD.Vector(ax, ay, 0)
            obj.Radius = float(v["radius"])
            obj.Reference = v["label"]
        doc.recompute()
        views[v["id"]] = obj
        if v["kind"] == "detail":
            bl = layout["views"][v["base"]]
            A, b = bl["A"], [bl["b"][0] - ax, bl["b"][1] - ay]
            extra = {"anchor2d_base": [ax, ay]}
        else:
            A, b = _affine(FreeCAD, doc, obj)
            extra = {}
        bb = _bbox(obj)
        if bb is None:
            print(f"ERROR: view {v['id']} produced no projected geometry", file=sys.stderr)
            return 2
        layout["views"][v["id"]] = {"obj": v["obj"], "page": v["page"], "X": float(v["X"]), "Y": float(v["Y"]),
                                    "scale": float(v["scale"]), "A": A, "b": b, "bbox": bb, **extra}

    for d in job["dims"]:
        view = views[d["view"]]
        vl = layout["views"][d["view"]]
        A, b, s, bb = vl["A"], vl["b"], vl["scale"], vl["bbox"]
        rec = {"method": None}
        layout["dims"][d["id"]] = rec
        try:
            refs, dtype, text_xy = None, None, None
            verts = _vertices(view)
            if d["type"] in ("diameter", "radius"):
                c2 = _apply(A, b, d["center"])
                ta = (A[0][0] * d["axis_dir"][0] + A[0][1] * d["axis_dir"][1] + A[0][2] * d["axis_dir"][2],
                      A[1][0] * d["axis_dir"][0] + A[1][1] * d["axis_dir"][1] + A[1][2] * d["axis_dir"][2])
                tn = math.hypot(*ta)
                if tn < 1e-6:  # looking along the axis: the feature is a circle in this view
                    for i, e in _edges(view):
                        crv = e.Curve
                        if "Circle" not in type(crv).__name__:
                            continue
                        if abs(crv.Radius - d["radius"]) <= CIRCLE_MATCH_MM and \
                                math.hypot(crv.Center.x - c2[0], crv.Center.y - c2[1]) <= CIRCLE_MATCH_MM:
                            refs = [(view, f"Edge{i}")]
                            dtype = "Diameter" if d["type"] == "diameter" else "Radius"
                            ang = math.radians(d.get("angle", 45.0))
                            ux, uy = math.cos(ang), math.sin(ang)
                            # reach far enough along the leader to clear the view outline
                            exits = [t for t in ((bb[2] * s - c2[0] * s) / ux if ux > 1e-9 else math.inf,
                                                 (bb[0] * s - c2[0] * s) / ux if ux < -1e-9 else math.inf,
                                                 (bb[3] * s - c2[1] * s) / uy if uy > 1e-9 else math.inf,
                                                 (bb[1] * s - c2[1] * s) / uy if uy < -1e-9 else math.inf)]
                            reach = max(d["radius"] * s + 6.0, min(exits) + 7.0 + (9.0 if d.get("has_fcf") else 0.0)) + 6.0 * d["stack"]
                            text_xy = (c2[0] * s + reach * ux, c2[1] * s + reach * uy)
                            rec["snap"] = ["circle"]
                            break
                    if refs is None:
                        rec["reason"] = "no projected circle edge matches the feature (hidden, or clipped out of the view)"
                elif abs(tn - 1) < 1e-6 and d["type"] == "diameter":
                    # side-on: dimension across the two silhouette lines
                    n2 = (-ta[1] / tn, ta[0] / tn)
                    q1 = (c2[0] - d["radius"] * n2[0], c2[1] - d["radius"] * n2[1])
                    q2 = (c2[0] + d["radius"] * n2[0], c2[1] + d["radius"] * n2[1])
                    along = 0 if abs(n2[0]) > abs(n2[1]) else 1
                    refs, dtype, text_xy = _linear(FreeCAD, doc, view, verts, q1, q2, d, bb, s, rec, along)
                else:
                    rec["reason"] = "the feature axis is oblique to this view"
            else:
                q1, q2 = _apply(A, b, d["p1"]), _apply(A, b, d["p2"])
                refs, dtype, text_xy = _linear(FreeCAD, doc, view, verts, q1, q2, d, bb, s, rec)
            if refs is None:
                rec["method"] = "annotation"
                continue
            dim = doc.addObject("TechDraw::DrawViewDimension", d["obj"])
            pages[vl["page"]].addView(dim)
            dim.Type = dtype
            dim.References2D = refs
            dim.Arbitrary = bool(d["arbitrary"])
            dim.FormatSpec = d["format"]
            dim.X = float(text_xy[0] + d["offset"][0])
            dim.Y = float(text_xy[1] + d["offset"][1])
            doc.recompute()
            raw = float(dim.getRawValue())
            expected = rec.pop("expected", None)
            if expected is not None and abs(raw - expected) > 1e-3:
                # placement self-check (not the verification -- verify.py compares with build123d)
                pages[vl["page"]].removeView(dim)
                doc.removeObject(dim.Name)
                rec.update({"method": "annotation", "reason": f"TechDraw measured {raw:.4f} mm between the attached points, expected {expected:.4f} mm; attachment rejected"})
                continue
            rec.update({"method": "techdraw", "type": dtype, "raw_value": raw, "refs": [r[1] for r in refs]})
        except Exception as exc:  # noqa: BLE001 -- recorded; the check decides
            rec.update({"method": "annotation", "reason": f"{type(exc).__name__}: {exc}"})

    doc.recompute()
    for pg in job["pages"]:
        out = pg["out_dxf"]
        os.makedirs(os.path.dirname(out), exist_ok=True)
        TechDraw.writeDXFPage(pages[pg["index"]], out)
        if not os.path.exists(out) or os.path.getsize(out) == 0:
            print(f"ERROR: writeDXFPage produced nothing for page {pg['index']}", file=sys.stderr)
            return 2
    with open(job["out_layout"], "w", encoding="utf-8") as fh:
        json.dump(layout, fh, indent=1, sort_keys=True)
    n_td = sum(1 for r in layout["dims"].values() if r["method"] == "techdraw")
    print(f"OK {len(job['pages'])} page(s), {n_td}/{len(job['dims'])} dimensions as TechDraw dimensions")
    return 0


def _linear(FreeCAD, doc, view, verts, q1, q2, d, bb, s, rec, along=None):
    """Dimension between two projected reference points along paper x (0) or y (1).

    Only the coordinate along the dimension is significant; the other one is
    the reference point's own projection and only breaks ties when snapping.
    """
    if along is None:
        along = {"x": 0, "y": 1}[d["along"]]
    dtype = ("DistanceX", "DistanceY")[along]
    if abs(q2[along] - q1[along]) < 1e-6:
        rec["reason"] = "the two reference points coincide along the dimension direction in this view"
        return None, None, None
    if q2[along] < q1[along]:
        # TechDraw puts the dimension line on one side of the text depending on the
        # direction from the first to the second reference; ascending order makes it
        # always TD_LINE_OFFSET_MM below / left of the text position (verified).
        q1, q2 = q2, q1
    names, snaps = [], []
    rec["q"] = [[round(q1[0], 4), round(q1[1], 4)], [round(q2[0], 4), round(q2[1], 4)]]
    for q in (q1, q2):
        idx = _snap(verts, q, along)
        if idx is None:
            # No real vertex there (TechDraw's vertex list omits some edge ends, e.g. in
            # detail views): add a cosmetic vertex at the projected point. The 2-D
            # makeCosmeticVertex takes vertex-frame coordinates as they are (verified:
            # a DistanceY to it measures as given); the 3-D variant stores Y mirrored.
            view.makeCosmeticVertex(FreeCAD.Vector(q[0], q[1], 0))
            doc.recompute()
            verts[:] = _vertices(view)
            hits = [t[0] for t in verts if abs(t[1] - q[0]) < 1e-6 and abs(t[2] - q[1]) < 1e-6]
            if not hits:
                rec["reason"] = "cosmetic vertex did not appear in the view's vertex list"
                return None, None, None
            idx = hits[-1]
            snaps.append("cosmetic")
        else:
            snaps.append("vertex")
        names.append(f"Vertex{idx}")
    if names[0] == names[1]:
        rec["reason"] = "both ends snapped to the same vertex"
        return None, None, None
    rec["snap"] = snaps
    rec["expected"] = abs(q2[along] - q1[along])
    side = d["side"]
    g = GAP0_MM + STEP_MM * d["stack"]
    if along == 0:
        mid = (q1[0] + q2[0]) / 2 * s
        line = bb[1] * s - g if side == "below" else bb[3] * s + g
        return [(view, names[0]), (view, names[1])], dtype, (mid, line + TD_LINE_OFFSET_MM)
    mid = (q1[1] + q2[1]) / 2 * s
    line = bb[2] * s + g if side == "right" else bb[0] * s - g
    return [(view, names[0]), (view, names[1])], dtype, (line + TD_LINE_OFFSET_MM, mid)


# freecadcmd runs a script with __name__ set to the file stem, not "__main__"
# (verified empirically), so main() is called unconditionally. The process is
# ended with os._exit: with a DrawViewDetail on the page, freecadcmd 1.1.3 was
# observed to finish all work (DXFs and layout written) and then never exit,
# presumably waiting on a TechDraw worker thread at shutdown.
try:
    _rc = main()
except Exception:  # noqa: BLE001 -- fail closed with a traceback
    traceback.print_exc()
    _rc = 2
sys.stdout.flush()
sys.stderr.flush()
os._exit(_rc)
