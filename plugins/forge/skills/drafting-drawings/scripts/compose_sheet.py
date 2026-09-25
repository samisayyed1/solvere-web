"""Finish a TechDraw page DXF into a drawing sheet (runs under ``forge-python``).

``TechDraw.writeDXFPage`` exports the page's views and dimensions but not the
template graphic, view captions, section/detail markers or hatching (those
are GUI-side in FreeCAD 1.1.3). This module adds them with ezdxf, on named
layers the checks read back:

    FRAME, TITLE_BLOCK, PROJECTION_SYMBOL, NOTES,
    SECTION_LINE_<view>, HATCH_<view>, DETAIL_CIRCLE_<view>, VIEW_LABEL_<view>,
    DATUM_<letter>, FCF_<gdt id>, DIMTXT_<dimension id> (annotation fallback)

Every 3-D point is mapped to the sheet with the projection TechDraw itself
reported for that view (layout.json: view2d = A.p + b; sheet = (X, Y) + s *
view2d), so markers sit on the TechDraw geometry, not on a re-derivation of it.
Text uses DXF control codes (%%c, %%p) only -- see drawspec.format_dim_text.
"""
from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

import ezdxf

TB_W, TB_ROW, TB_SYM_ROW = 180.0, 8.0, 14.0
TITLE_LABELS = ("TITLE", "NUMBER", "MATERIAL", "REV", "SHEET", "GENERAL TOLERANCES", "UNITS", "SCALE", "DRAWN", "DATE",
                "APPROVED (SIGN + DATE)", "TOLERANCING STANDARD")
TB_H = 5 * TB_ROW + TB_SYM_ROW
BORDER = 10.0
APPID = "FORGE"

# Projection symbol (truncated cone, ISO 5456-2 / ASME Y14.3 convention -- edition not
# researched in R5a): trapezoid (side view, axis horizontal) + two concentric circles
# (end view seen from the small end). Third angle: the small end of the trapezoid faces
# the circles; first angle: it faces away. Geometry is checked by dxf_checks.
SYM_D_LARGE, SYM_D_SMALL, SYM_LEN, SYM_GAP = 10.0, 5.0, 10.0, 4.0


def _layer(doc, name: str, color: int = 7, linetype: str = "CONTINUOUS") -> str:
    if name not in doc.layers:
        doc.layers.add(name, color=color, linetype=linetype)
    return name


def _setup(doc) -> None:
    for name, pattern, desc in (("FORGE_CENTER", [20.0, 12.0, -3.0, 2.0, -3.0], "Center ____ _ ____"),
                                ("FORGE_CUTTING", [26.0, 18.0, -3.0, 2.0, -3.0], "Cutting plane ______ _ ______")):
        if name not in doc.linetypes:
            doc.linetypes.add(name, pattern=pattern, description=desc)
    if APPID not in doc.appids:
        doc.appids.new(APPID)


def page_xy(view: Mapping[str, Any], p: Sequence[float]) -> tuple[float, float]:
    A, b, s = view["A"], view["b"], view["scale"]
    x = A[0][0] * p[0] + A[0][1] * p[1] + A[0][2] * p[2] + b[0]
    y = A[1][0] * p[0] + A[1][1] * p[1] + A[1][2] * p[2] + b[1]
    return view["X"] + s * x, view["Y"] + s * y


def page_dir(view: Mapping[str, Any], d: Sequence[float]) -> tuple[float, float]:
    A = view["A"]
    return (A[0][0] * d[0] + A[0][1] * d[1] + A[0][2] * d[2], A[1][0] * d[0] + A[1][1] * d[1] + A[1][2] * d[2])


def page_bbox(view: Mapping[str, Any]) -> tuple[float, float, float, float]:
    bb, s = view["bbox"], view["scale"]
    return view["X"] + s * bb[0], view["Y"] + s * bb[1], view["X"] + s * bb[2], view["Y"] + s * bb[3]


def _text(msp, text: str, x: float, y: float, h: float, layer: str, align: str = "LEFT", rot: float = 0.0):
    from ezdxf.enums import TextEntityAlignment
    al = {"LEFT": TextEntityAlignment.BOTTOM_LEFT, "CENTER": TextEntityAlignment.BOTTOM_CENTER,
          "MIDDLE": TextEntityAlignment.MIDDLE_CENTER, "RIGHT": TextEntityAlignment.BOTTOM_RIGHT,
          "MIDLEFT": TextEntityAlignment.MIDDLE_LEFT}[align]
    t = msp.add_text(text, height=h, rotation=rot, dxfattribs={"layer": layer, "style": "Standard"})
    t.set_placement((x, y), align=al)
    return t


def _norm(v):
    n = math.hypot(v[0], v[1])
    return (v[0] / n, v[1] / n) if n > 1e-12 else (0.0, 0.0)


def _arrow(msp, tail, tip, layer, size=3.0):
    msp.add_line(tail, tip, dxfattribs={"layer": layer})
    d = _norm((tip[0] - tail[0], tip[1] - tail[1]))
    n = (-d[1], d[0])
    b = (tip[0] - d[0] * size, tip[1] - d[1] * size)
    msp.add_solid([tip, (b[0] + n[0] * size / 3, b[1] + n[1] * size / 3), (b[0] - n[0] * size / 3, b[1] - n[1] * size / 3)],
                  dxfattribs={"layer": layer})


# ---------------------------------------------------------------- title block
def title_block(msp, W: float, spec: Mapping[str, Any], sheet: Mapping[str, Any], n_sheets: int) -> None:
    dw = spec["drawing"]
    L = "TITLE_BLOCK"
    x0, y0 = W - BORDER - TB_W, BORDER
    msp.add_lwpolyline([(x0, y0), (x0 + TB_W, y0), (x0 + TB_W, y0 + TB_H), (x0, y0 + TB_H)], close=True, dxfattribs={"layer": L})
    ys = [y0 + TB_SYM_ROW + i * TB_ROW for i in range(5)] + [y0 + TB_H]
    for y in ys[:-1]:
        msp.add_line((x0, y), (x0 + TB_W, y), dxfattribs={"layer": L})
    # rows from the top: (label, value, width) cells
    rows = [
        [("", dw["signoff"], TB_W)],
        [("TITLE", dw["title"], 120.0), ("NUMBER", dw["number"], 60.0)],
        [("MATERIAL", dw["material"], 90.0), ("REV", dw["rev"], 30.0), ("SHEET", f"SHEET {sheet['index']} OF {n_sheets}", 60.0)],
        [("GENERAL TOLERANCES", dw["general_tolerance"], 90.0), ("UNITS", dw["units"], 30.0), ("SCALE", sheet["scale_str"], 60.0)],
        [("DRAWN", dw["author"], 60.0), ("DATE", dw["date"], 60.0), ("APPROVED (SIGN + DATE)", "", 60.0)],
    ]
    for r, cells in enumerate(rows):
        ytop = ys[-1 - r]
        x = x0
        for label, value, w in cells:
            if x > x0:
                msp.add_line((x, ytop - TB_ROW), (x, ytop), dxfattribs={"layer": L})
            if label:
                _text(msp, label, x + 1.2, ytop - 2.6, 1.8, L)
                if value:
                    _text(msp, value, x + 1.2, ytop - TB_ROW + 1.2, 3.2 if label != "TITLE" else 3.5, L)
            else:
                t = _text(msp, value, x + w / 2, ytop - TB_ROW / 2, 3.5, L, align="MIDDLE")
                t.dxf.color = 1
            x += w
    # symbol row: tolerancing standard + projection symbol
    ytop = y0 + TB_SYM_ROW
    msp.add_line((x0 + 120, y0), (x0 + 120, ytop), dxfattribs={"layer": L})
    _text(msp, "TOLERANCING STANDARD", x0 + 1.2, ytop - 2.6, 1.8, L)
    _text(msp, dw["tolerancing_standard"] or "-", x0 + 1.2, y0 + 2.0, 3.2, L)
    _text(msp, f"{dw['projection'].upper()} ANGLE PROJECTION", x0 + 121.2, ytop - 2.6, 1.8, L)
    projection_symbol(msp, x0 + 150, y0 + 6.0, dw["projection"])


def projection_symbol(msp, cx: float, cy: float, method: str) -> None:
    L = "PROJECTION_SYMBOL"
    total = SYM_LEN + SYM_GAP + SYM_D_LARGE
    left = cx - total / 2
    if method == "third":
        tx0, circ_x = left, left + SYM_LEN + SYM_GAP + SYM_D_LARGE / 2
        big_end_x, small_end_x = tx0, tx0 + SYM_LEN      # small end faces the circles (to the right)
    else:
        circ_x, tx0 = left + SYM_D_LARGE / 2, left + SYM_D_LARGE + SYM_GAP
        big_end_x, small_end_x = tx0, tx0 + SYM_LEN      # small end faces away from the circles
    hb, hs = SYM_D_LARGE / 2, SYM_D_SMALL / 2
    for a, b in (((big_end_x, cy - hb), (big_end_x, cy + hb)), ((small_end_x, cy - hs), (small_end_x, cy + hs)),
                 ((big_end_x, cy + hb), (small_end_x, cy + hs)), ((big_end_x, cy - hb), (small_end_x, cy - hs))):
        msp.add_line(a, b, dxfattribs={"layer": L})
    msp.add_circle((circ_x, cy), hb, dxfattribs={"layer": L})
    msp.add_circle((circ_x, cy), hs, dxfattribs={"layer": L})
    ln = msp.add_line((left - 1.5, cy), (left + total + 1.5, cy), dxfattribs={"layer": L, "linetype": "FORGE_CENTER"})
    ln.dxf.ltscale = 0.25


# --------------------------------------------------------------------- notes
def wrap(text: str, width_mm: float, h: float) -> list[str]:
    per = max(10, int(width_mm / (0.62 * h)))
    words, lines, cur = text.split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > per:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return lines


def note_lines(spec: Mapping[str, Any], width_mm: float, h: float = 2.5) -> list[str]:
    dw = spec["drawing"]
    auto = [f"DIMENSIONS IN {dw['units']}. UNTOLERANCED DIMENSIONS: {dw['general_tolerance']}.",
            "CRITICAL DIMENSIONS CARRY EXPLICIT TOLERANCES AND ARE VERIFIED AGAINST THE 3-D MODEL."]
    out = ["NOTES:"]
    for i, n in enumerate(auto + list(spec["notes"]), 1):
        ls = wrap(n, width_mm - 5, h)
        out.append(f"{i}. {ls[0]}")
        out += [f"   {x}" for x in ls[1:]]
    return out


def notes(msp, spec, x0: float, y0: float, width_mm: float) -> None:
    lines = note_lines(spec, width_mm)
    for i, ln in enumerate(reversed(lines)):
        _text(msp, ln, x0, y0 + i * 4.2, 2.5, "NOTES")


# ------------------------------------------------------------ views markings
def section_marks(msp, sec: Mapping[str, Any], base: Mapping[str, Any], base_lay: Mapping[str, Any],
                  elsewhere: int | None = None) -> None:
    L = f"SECTION_LINE_{sec['id']}"
    o = page_xy(base_lay, sec["origin"])
    n = sec["direction"]
    bd_ = base["direction"]
    t3 = (n[1] * bd_[2] - n[2] * bd_[1], n[2] * bd_[0] - n[0] * bd_[2], n[0] * bd_[1] - n[1] * bd_[0])
    t = _norm(page_dir(base_lay, t3))
    v = _norm(page_dir(base_lay, (-n[0], -n[1], -n[2])))  # direction of sight
    x0, y0, x1, y1 = page_bbox(base_lay)
    corners = [(x0, y0), (x0, y1), (x1, y0), (x1, y1)]
    ts = [(c[0] - o[0]) * t[0] + (c[1] - o[1]) * t[1] for c in corners]
    a, b = min(ts) - 5.0, max(ts) + 5.0
    p0 = (o[0] + a * t[0], o[1] + a * t[1])
    p1 = (o[0] + b * t[0], o[1] + b * t[1])
    ln = msp.add_line(p0, p1, dxfattribs={"layer": L, "linetype": "FORGE_CUTTING"})
    ln.dxf.ltscale = 0.3
    for end, sgn in ((p0, 1), (p1, -1)):
        inner = (end[0] + sgn * t[0] * 6, end[1] + sgn * t[1] * 6)
        msp.add_lwpolyline([end, inner], dxfattribs={"layer": L, "const_width": 0.7})
        tip = (end[0] + v[0] * 9, end[1] + v[1] * 9)
        _arrow(msp, end, tip, L)
        lab = (end[0] + v[0] * 9 - sgn * t[0] * 4, end[1] + v[1] * 9 - sgn * t[1] * 4)
        _text(msp, sec["label"], lab[0], lab[1], 5.0, L, align="MIDDLE")
        if elsewhere:
            _text(msp, f"(SHEET {elsewhere})", lab[0], lab[1] - 5.0, 2.5, L, align="MIDDLE")


def detail_marks(msp, det: Mapping[str, Any], base_lay: Mapping[str, Any], elsewhere: int | None = None) -> None:
    L = f"DETAIL_CIRCLE_{det['id']}"
    c = page_xy(base_lay, det["center"])
    r = det["radius"] * base_lay["scale"]
    circ = msp.add_circle(c, r, dxfattribs={"layer": L, "linetype": "FORGE_CUTTING"})
    circ.dxf.ltscale = 0.2
    _text(msp, det["label"], c[0] + (r + 4) * 0.7071, c[1] + (r + 4) * 0.7071, 5.0, L, align="MIDDLE")
    if elsewhere:
        _text(msp, f"(SHEET {elsewhere})", c[0] + (r + 4) * 0.7071, c[1] + (r + 4) * 0.7071 - 5.0, 2.5, L, align="MIDDLE")


def _lowest_annotation(doc, spec, vid: str) -> float | None:
    """Lowest y of the dimensions / frames that belong to a view (labels go under them)."""
    from ezdxf import bbox as _bbox
    layers = {d["obj"] for d in spec["dimensions"] if d["view"] == vid}
    layers |= {f"DIMTXT_{d['id']}" for d in spec["dimensions"] if d["view"] == vid}
    dims = {d["id"] for d in spec["dimensions"] if d["view"] == vid}
    layers |= {f"FCF_{g['id']}" for g in spec["gdt"] if g["dimension"] in dims}
    layers |= {f"DATUM_{k}" for k, d in spec["datums"].items() if d["view"] == vid}
    ents = [e for e in doc.modelspace() if e.dxf.layer in layers]
    if not ents:
        return None
    b = _bbox.extents(ents, fast=True)
    return b.extmin[1] if b.has_data else None


def view_label(msp, view: Mapping[str, Any], lay: Mapping[str, Any], sheet_scale_str: str, below: float | None = None) -> None:
    L = f"VIEW_LABEL_{view['id']}"
    x0, y0, x1, _ = page_bbox(lay)
    if below is not None and below < y0 - 2.0:
        y0 = below + 3.0
    kind = "SECTION" if view["kind"] == "section" else "DETAIL"
    name = f"{view['label']}-{view['label']}" if kind == "SECTION" else view["label"]
    text = f"{kind} {name}"
    if view["scale_str"] != sheet_scale_str or kind == "DETAIL":
        text += f" ({view['scale_str']})"
    _text(msp, text, (x0 + x1) / 2, y0 - 9.0, 3.5, L, align="CENTER")


def hatch(msp, view_id: str, lay: Mapping[str, Any], loops_3d, clip_circle=None) -> int:
    """Hatch the cut faces (loops in model mm) in a view; optionally clipped to a detail circle."""
    from ezdxf.math import Vec2
    from ezdxf.math.clipping import ConvexClippingPolygon2d
    L = f"HATCH_{view_id}"
    clipper = None
    if clip_circle is not None:
        (cx, cy), r = clip_circle
        clipper = ConvexClippingPolygon2d([Vec2(cx + r * math.cos(2 * math.pi * i / 96), cy + r * math.sin(2 * math.pi * i / 96))
                                           for i in range(96)])
    n = 0
    for face in loops_3d:
        paths = []
        for loop in face:
            pts = [page_xy(lay, p) for p in loop]
            if clipper is None:
                paths.append(pts)
            else:
                paths += [[(v.x, v.y) for v in poly] for poly in clipper.clip_polygon([Vec2(p) for p in pts])]
        paths = [p for p in paths if len(p) >= 3]
        if not paths:
            continue
        h = msp.add_hatch(color=8, dxfattribs={"layer": L})
        h.set_pattern_fill("ANSI31", scale=0.8)
        for pts in paths:
            h.paths.add_polyline_path(pts, is_closed=True)
        n += 1
    return n


def datum_symbol(msp, datum: Mapping[str, Any], anchor: Mapping[str, Any], lay: Mapping[str, Any]) -> str | None:
    """Filled triangle on the feature, leader, boxed letter. Returns an issue string or None."""
    L = f"DATUM_{datum['id']}"
    issue = None
    if anchor["kind"] == "plane":
        d = page_dir(lay, anchor["normal"])
        if math.hypot(*d) < 0.99:
            issue = f"datum {datum['id']} face is not seen edge-on in view {datum['view']!r}; attach it in a view where the face projects to a line"
        u = _norm(d) if math.hypot(*d) > 1e-6 else (0.0, -1.0)
        # sit the triangle 10 % (datum.along) along the face's edge-on line, clear of the mid-span dimension text
        w0 = (-u[1], u[0])
        pts = [page_xy(lay, v) for v in anchor.get("vertices") or [anchor["point"]]]
        ts = [q[0] * w0[0] + q[1] * w0[1] for q in pts]
        c = page_xy(lay, anchor["point"])
        tc = c[0] * w0[0] + c[1] * w0[1]
        t = min(ts) + datum.get("along", 0.1) * (max(ts) - min(ts))
        p = (c[0] + (t - tc) * w0[0], c[1] + (t - tc) * w0[1])
    else:
        c = page_xy(lay, anchor["point"])
        ax = page_dir(lay, anchor["axis_dir"])
        u = (-_norm(ax)[1], _norm(ax)[0]) if math.hypot(*ax) > 0.5 else (0.0, -1.0)
        if u[1] > 0 or (abs(u[1]) < 1e-9 and u[0] < 0):
            u = (-u[0], -u[1])
        r = anchor["radius"] * lay["scale"]
        p = (c[0] + u[0] * r, c[1] + u[1] * r)
    w = (-u[1], u[0])
    base1 = (p[0] + w[0] * 1.8, p[1] + w[1] * 1.8)
    base2 = (p[0] - w[0] * 1.8, p[1] - w[1] * 1.8)
    apex = (p[0] + u[0] * 3.0, p[1] + u[1] * 3.0)
    msp.add_solid([base1, base2, apex], dxfattribs={"layer": L})
    box_c = (p[0] + u[0] * 14.0, p[1] + u[1] * 14.0)
    edge = (p[0] + u[0] * 11.0, p[1] + u[1] * 11.0)
    msp.add_line(apex, edge, dxfattribs={"layer": L})
    msp.add_lwpolyline([(box_c[0] - 3, box_c[1] - 3), (box_c[0] + 3, box_c[1] - 3), (box_c[0] + 3, box_c[1] + 3),
                        (box_c[0] - 3, box_c[1] + 3)], close=True, dxfattribs={"layer": L})
    _text(msp, datum["id"], box_c[0], box_c[1], 3.5, L, align="MIDDLE")
    return issue


def fcf_text_cells(g: Mapping[str, Any]) -> list[str]:
    tol = f"{g['tolerance']:.3f}".rstrip("0")
    if len(tol.split(".")[1]) < 2:
        tol = f"{g['tolerance']:.2f}"
    t = ("%%c" if g["diameter_zone"] else "") + tol + (f" ({g['modifier']})" if g["modifier"] else "")
    return [t] + list(g["datums"])


def _gdt_symbol(msp, ch: str, cx: float, cy: float, L: str) -> None:
    a = dict(dxfattribs={"layer": L})
    if ch == "straightness":
        msp.add_line((cx - 2.2, cy), (cx + 2.2, cy), **a)
    elif ch == "flatness":
        msp.add_lwpolyline([(cx - 2.4, cy - 1.2), (cx + 1.2, cy - 1.2), (cx + 2.4, cy + 1.2), (cx - 1.2, cy + 1.2)], close=True, **a)
    elif ch == "circularity":
        msp.add_circle((cx, cy), 1.8, **a)
    elif ch == "cylindricity":
        msp.add_circle((cx, cy), 1.4, **a)
        msp.add_line((cx - 2.4, cy - 1.8), (cx - 0.4, cy + 1.8), **a)
        msp.add_line((cx + 0.4, cy - 1.8), (cx + 2.4, cy + 1.8), **a)
    elif ch in ("profile_line", "profile_surface"):
        msp.add_arc((cx, cy - 1.0), 2.0, 0, 180, **a)
        if ch == "profile_surface":
            msp.add_line((cx - 2.0, cy - 1.0), (cx + 2.0, cy - 1.0), **a)
    elif ch == "perpendicularity":
        msp.add_line((cx - 2.2, cy - 1.8), (cx + 2.2, cy - 1.8), **a)
        msp.add_line((cx, cy - 1.8), (cx, cy + 2.0), **a)
    elif ch == "parallelism":
        msp.add_line((cx - 2.0, cy - 1.8), (cx - 0.4, cy + 1.8), **a)
        msp.add_line((cx + 0.4, cy - 1.8), (cx + 2.0, cy + 1.8), **a)
    elif ch == "angularity":
        msp.add_line((cx - 2.2, cy - 1.8), (cx + 2.2, cy - 1.8), **a)
        msp.add_line((cx - 2.2, cy - 1.8), (cx + 1.8, cy + 1.8), **a)
    elif ch == "position":
        msp.add_circle((cx, cy), 1.4, **a)
        msp.add_line((cx - 2.4, cy), (cx + 2.4, cy), **a)
        msp.add_line((cx, cy - 2.4), (cx, cy + 2.4), **a)
    elif ch in ("circular_runout", "total_runout"):
        _arrow(msp, (cx - 1.5, cy - 2.0), (cx + 1.0, cy + 2.2), L, size=1.4)
        if ch == "total_runout":
            _arrow(msp, (cx + 0.5, cy - 2.0), (cx + 3.0, cy + 2.2), L, size=1.4)
            msp.add_line((cx - 1.5, cy - 2.0), (cx + 0.5, cy - 2.0), **a)


def feature_control_frame(msp, g: Mapping[str, Any], text_box, side: str) -> None:
    """Frame beside its dimension's text, on the side away from the view."""
    L = f"FCF_{g['id']}"
    h = 6.0
    cells = fcf_text_cells(g)
    widths = [8.0, max(12.0, 2.3 * len(cells[0].replace("%%c", "X")) + 3.0)] + [6.0] * (len(cells) - 1)
    total = sum(widths)
    bx0, by0, bx1, by1 = text_box
    if side == "above":
        x, y0 = (bx0 + bx1) / 2 - total / 2, by1 + 1.5
    elif side == "left":
        x, y0 = bx0 - 1.5 - total, (by0 + by1) / 2 - h / 2
    elif side == "right":
        x, y0 = bx1 + 1.5, (by0 + by1) / 2 - h / 2
    else:  # below, circle callouts
        x, y0 = (bx0 + bx1) / 2 - total / 2, by0 - 1.5 - h
    y_top = y0 + h
    frame = msp.add_lwpolyline([(x, y0), (x + total, y0), (x + total, y_top), (x, y_top)], close=True, dxfattribs={"layer": L})
    frame.set_xdata(APPID, [(1000, f"gdt:{g['characteristic']}"), (1000, f"id:{g['id']}")])
    xc = x
    for i, w in enumerate(widths):
        if i:
            msp.add_line((xc, y0), (xc, y_top), dxfattribs={"layer": L})
        if i == 0:
            _gdt_symbol(msp, g["characteristic"], xc + w / 2, y0 + h / 2, L)
        else:
            _text(msp, cells[i - 1], xc + w / 2, y0 + h / 2, 3.0, L, align="MIDDLE")
        xc += w


def annotation_dimension(msp, dim, text: str, feature_xy, lay) -> tuple[float, float]:
    """Fallback when TechDraw could not attach the dimension headlessly: text + leader."""
    L = f"DIMTXT_{dim['id']}"
    x0, y0, x1, y1 = page_bbox(lay)
    tx, ty = x1 + 12.0 + dim["offset"][0], min(y1, max(y0, feature_xy[1] + 8.0)) + dim["offset"][1]
    t = _text(msp, text, tx, ty, 3.5, L, align="MIDLEFT")
    _arrow(msp, (tx - 1.0, ty), feature_xy, L, size=2.5)
    return t


def fix_vertical_dimension_text(doc) -> None:
    """Turn TechDraw's horizontal text on vertical (DistanceY) dimensions to read from the right.

    writeDXFPage writes every dimension text unrotated and centred on the
    dimension line; for a vertical dimension that straddles the line and runs
    into the view. The text string and every line of the dimension are kept;
    only the text is rotated 90 degrees and moved beside its dimension line.
    """
    from ezdxf.enums import TextEntityAlignment
    for e in doc.modelspace().query("DIMENSION"):
        blk = doc.blocks.get(e.dxf.geometry) if e.dxf.hasattr("geometry") else None
        if blk is None:
            continue
        p2, p3 = e.dxf.get("defpoint2"), e.dxf.get("defpoint3")
        if p2 is None or p3 is None or abs(p2[1] - p3[1]) < 1e-6:
            continue
        span = abs(p2[1] - p3[1])
        lines = [ln for ln in blk.query("LINE") if abs(ln.dxf.start[0] - ln.dxf.end[0]) < 1e-6
                 and abs(abs(ln.dxf.end[1] - ln.dxf.start[1]) - span) < 0.01]
        if not lines:
            continue  # not a vertical linear dimension (no vertical dimension line of the full span)
        dim_line = lines[0]
        x = dim_line.dxf.start[0]
        ymid = (dim_line.dxf.start[1] + dim_line.dxf.end[1]) / 2
        for t in blk.query("TEXT"):
            t.dxf.rotation = 90.0
            t.set_placement((x - 1.0, ymid), align=TextEntityAlignment.BOTTOM_CENTER)


def center_marks(msp, doc, view_layers: list[str]) -> None:
    """Centre marks (thin chain lines) on every full circle of the orthographic views."""
    for e in list(doc.modelspace().query("CIRCLE")):
        if e.dxf.layer not in view_layers:
            continue
        c, r = e.dxf.center, e.dxf.radius
        ext = r + 2.5
        for a, b in (((c[0] - ext, c[1]), (c[0] + ext, c[1])), ((c[0], c[1] - ext), (c[0], c[1] + ext))):
            ln = msp.add_line(a, b, dxfattribs={"layer": "CENTERLINES", "linetype": "FORGE_CENTER"})
            ln.dxf.ltscale = max(0.15, min(0.5, r / 20.0))


def frame(msp, W: float, H: float) -> None:
    msp.add_lwpolyline([(BORDER, BORDER), (W - BORDER, BORDER), (W - BORDER, H - BORDER), (BORDER, H - BORDER)],
                       close=True, dxfattribs={"layer": "FRAME", "const_width": 0.5})


def _text_box(entity) -> tuple[float, float, float, float]:
    from ezdxf import bbox as _bbox
    b = _bbox.extents([entity], fast=True)
    return b.extmin[0], b.extmin[1], b.extmax[0], b.extmax[1]


def dimension_text(doc, layer: str):
    for e in doc.modelspace().query("DIMENSION"):
        if e.dxf.layer != layer:
            continue
        blk = doc.blocks.get(e.dxf.geometry) if e.dxf.hasattr("geometry") else None
        for t in (blk.query("TEXT") if blk is not None else []):
            return e, t
    return None, None


def radial_leader(doc, msp, layer: str, radius_page: float) -> bool:
    """Leader + arrowhead for a Diameter/Radius dimension.

    Headless writeDXFPage exports the DIMENSION of a circle with its lines and
    arrowheads collapsed onto the centre (only the text is placed); the text
    and the centre (defpoint) are right, so the leader is rebuilt from them:
    arrowhead on the circle pointing at the centre, line to the text.
    """
    e, t = dimension_text(doc, layer)
    if e is None or e.dxf.dimtype & 0x0F not in (3, 4):
        return False
    c = e.dxf.defpoint
    x0, y0, x1, y1 = _text_box(t)
    right = (x0 + x1) / 2 >= c[0]
    end = (x0 - 1.0, (y0 + y1) / 2) if right else (x1 + 1.0, (y0 + y1) / 2)
    u = _norm((end[0] - c[0], end[1] - c[1]))
    on_circle = (c[0] + u[0] * radius_page, c[1] + u[1] * radius_page)
    _arrow(msp, end, on_circle, layer, size=3.0)
    return True


def compose(raw_dxf: str, out_dxf: str, *, spec, sheet, sheet_size, layout, measures, datum_anchors,
            section_loops, n_sheets: int, plans) -> list[dict[str, str]]:
    """Write the finished sheet DXF. Returns issues found while composing (each becomes a failing check)."""
    doc = ezdxf.readfile(raw_dxf)
    _setup(doc)
    for name, color in (("FRAME", 7), ("TITLE_BLOCK", 7), ("PROJECTION_SYMBOL", 7), ("NOTES", 7)):
        _layer(doc, name, color)
    msp = doc.modelspace()
    W, H = sheet_size
    issues: list[dict[str, str]] = []
    frame(msp, W, H)
    title_block(msp, W, spec, sheet, n_sheets)
    if sheet["index"] == 1:
        notes(msp, spec, BORDER + 4.0, BORDER + 3.0, W - 2 * BORDER - TB_W - 8.0)
    views = spec["views"]
    lv = layout["views"]
    on_sheet = set(sheet["views"])
    fix_vertical_dimension_text(doc)
    _layer(doc, "CENTERLINES", color=8)
    center_marks(msp, doc, [views[v]["obj"] for v in sheet["views"] if views[v]["kind"] not in ("iso",)])
    for vid in sheet["views"]:
        v = views[vid]
        if v["kind"] == "detail" and views[v["base"]]["kind"] == "section":
            _layer(doc, f"HATCH_{vid}", color=8)
            circle = (page_xy(lv[vid], v["center"]), v["radius"] * lv[vid]["scale"])
            hatch(msp, vid, lv[vid], section_loops.get(v["base"], []), clip_circle=circle)
        if v["kind"] == "section":
            _layer(doc, f"HATCH_{vid}", color=8)
            if not hatch(msp, vid, lv[vid], section_loops.get(vid, [])):
                issues.append({"name": f"section_{vid}_cut_faces", "remediation":
                               f"The section plane of view {vid!r} does not cut the solid (no cut faces to hatch); move its origin into the material."})
    for vid, v in views.items():
        if v["kind"] in ("section", "detail") and views[v["base"]]["sheet"] == sheet["index"]:
            base_lay = lv[v["base"]]
            elsewhere = v["sheet"] if v["sheet"] != sheet["index"] else None
            if v["kind"] == "section":
                _layer(doc, f"SECTION_LINE_{vid}", color=1)
                section_marks(msp, v, views[v["base"]], base_lay, elsewhere)
            else:
                _layer(doc, f"DETAIL_CIRCLE_{vid}", color=1)
                detail_marks(msp, v, base_lay, elsewhere)
    for did, datum in spec["datums"].items():
        if datum["view"] in on_sheet:
            _layer(doc, f"DATUM_{did}")
            anchor = datum_anchors[did]
            if "error" in anchor:
                issues.append({"name": f"datum_{did}_resolved", "remediation": f"Datum {did} selector: {anchor['error']}"})
                continue
            issue = datum_symbol(msp, datum, anchor, lv[datum["view"]])
            if issue:
                issues.append({"name": f"datum_{did}_edge_on", "remediation": issue})
    text_anchor: dict[str, tuple[float, float]] = {}
    from drawspec import format_dim_text
    for dim in spec["dimensions"]:
        if dim["view"] not in on_sheet:
            continue
        m = measures[dim["id"]]
        rec = layout["dims"].get(dim["id"])
        if "error" in m or rec is None:
            continue
        if rec["method"] == "techdraw":
            if rec["type"] in ("Diameter", "Radius"):
                radial_leader(doc, msp, dim["obj"], m["radius"] * lv[dim["view"]]["scale"])
            _, t = dimension_text(doc, dim["obj"])
            if t is not None:
                text_anchor[dim["id"]] = _text_box(t)
            continue
        _layer(doc, f"DIMTXT_{dim['id']}")
        fmt, arbitrary = format_dim_text(dim, m["value"])
        text = fmt if arbitrary else fmt.replace(f"%.{dim['decimals']}f", f"{m['value']:.{dim['decimals']}f}")
        lay = lv[dim["view"]]
        feat = page_xy(lay, m.get("center") or m.get("p2"))
        text_anchor[dim["id"]] = _text_box(annotation_dimension(msp, dim, text, feat, lay))
    for g in spec["gdt"]:
        dim_view = next(d["view"] for d in spec["dimensions"] if d["id"] == g["dimension"])
        if dim_view not in on_sheet:
            continue
        _layer(doc, f"FCF_{g['id']}")
        a = text_anchor.get(g["dimension"])
        if a is None:
            issues.append({"name": f"gdt_{g['id']}_placed", "remediation":
                           f"Feature control frame {g['id']!r} could not be placed: its dimension {g['dimension']!r} is not on the sheet."})
            continue
        side = plans[g["dimension"]]["side"]
        feature_control_frame(msp, g, a, side)
    for vid in sheet["views"]:
        v = views[vid]
        if v["kind"] in ("section", "detail"):
            _layer(doc, f"VIEW_LABEL_{vid}")
            below = _lowest_annotation(doc, spec, vid)
            view_label(msp, v, lv[vid], sheet["scale_str"], below)
    doc.header["$INSUNITS"] = 4  # mm
    doc.header["$MEASUREMENT"] = 1
    doc.header["$EXTMIN"] = (0, 0, 0)
    doc.header["$EXTMAX"] = (W, H, 0)
    doc.saveas(out_dxf)
    return issues
