"""Drawing spec (``schema = "forge.drawing/2"``) loader and validator.

Standard library only (runs under ``forge-python``; imported by the pipeline,
the checks and the tests). The schema is documented in
``references/spec-schema.md``; this module is the executable form of it.

A spec error (missing table, bad type, unknown view kind, a datum reference
that resolves to nothing, ...) raises :class:`SpecError`; ``verify.py``
reports that as exit 2 -- a malformed spec is never a pass. Whether the
*model* matches the spec (selectors, values) is decided later, as failing
measurements, not here.
"""
from __future__ import annotations

import ast
import math
import operator
import re
from pathlib import Path
from typing import Any, Mapping

SCHEMA = "forge.drawing/2"

SHEET_SIZES_MM = {  # landscape (width, height)
    "A4": (297.0, 210.0), "A3": (420.0, 297.0), "A2": (594.0, 420.0),
    "A1": (841.0, 594.0), "A0": (1189.0, 841.0),
    "ANSI-A": (279.4, 215.9), "ANSI-B": (431.8, 279.4), "ANSI-C": (558.8, 431.8),
}
ORTHO_KINDS = ("front", "rear", "top", "bottom", "right", "left")
VIEW_KINDS = ORTHO_KINDS + ("iso", "section", "detail")
# (direction toward the viewer, x direction on paper); paper-up = direction x xdir.
ORTHO_BASIS = {
    "front": ((0, -1, 0), (1, 0, 0)),
    "rear": ((0, 1, 0), (-1, 0, 0)),
    "top": ((0, 0, 1), (1, 0, 0)),
    "bottom": ((0, 0, -1), (1, 0, 0)),
    "right": ((1, 0, 0), (0, 1, 0)),
    "left": ((-1, 0, 0), (0, -1, 0)),
    "iso": ((1, -1, 1), (1, 1, 0)),
}
DIM_TYPES = ("linear", "diameter", "radius")
TITLE_FIELDS = ("title", "number", "rev", "material", "units", "general_tolerance", "author", "date")
SIGNOFF_DEFAULT = "NOT FOR MANUFACTURE UNTIL SIGNED"
# GD&T characteristics supported as feature-control-frame text. Datum rules are the
# general ones common to ASME Y14.5 and ISO 1101 (form: no datums; orientation and
# runout: at least one) -- see references/spec-schema.md. No standard text reproduced.
GDT_FORM = ("straightness", "flatness", "circularity", "cylindricity")
GDT_NEEDS_DATUM = ("perpendicularity", "parallelism", "angularity", "circular_runout", "total_runout")
GDT_DATUM_OPTIONAL = ("position", "profile_line", "profile_surface")
GDT_CHARACTERISTICS = GDT_FORM + GDT_NEEDS_DATUM + GDT_DATUM_OPTIONAL
DATUM_LETTER = re.compile(r"^[A-HJ-NPR-Z]$")  # I, O, Q excluded (read as 1, 0, O)
_ID = re.compile(r"^[a-z][a-z0-9_]{0,40}$")
_REQ = re.compile(r"^REQ-[A-Z]+-[0-9]{3,}$")
_GENTOL = re.compile(r"^ISO 2768-([fmcv])([HKL]?)$")
MIN_DECIMALS = 2  # 0.005 mm worst-case display rounding < the 0.01 mm verification tolerance


class SpecError(ValueError):
    """The drawing spec is malformed (exit 2), not a design failure."""


# ---------------------------------------------------------------- expressions
_BINOPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}
_PARAM_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)+")


def param_value(params: Mapping[str, Any], key: str) -> float:
    node: Any = params
    for part in key.split("."):
        if not isinstance(node, Mapping) or part not in node:
            raise SpecError(f"params/params.toml has no key {key!r}")
        node = node[part]
    if isinstance(node, Mapping):
        if "value" not in node:
            raise SpecError(f"params key {key!r} has no 'value'")
        unit = node.get("unit", "mm")
        if unit not in ("mm", "1"):
            raise SpecError(f"params key {key!r} has unit {unit!r}; drawings use mm")
        node = node["value"]
    if not isinstance(node, (int, float)) or isinstance(node, bool):
        raise SpecError(f"params key {key!r} is not numeric: {node!r}")
    return float(node)


def param_tol(params: Mapping[str, Any], key: str) -> tuple[float, float] | None:
    node: Any = params
    for part in key.split("."):
        node = node[part]
    if isinstance(node, Mapping) and isinstance(node.get("tol"), Mapping):
        t = node["tol"]
        return float(t.get("plus", 0.0)), float(t.get("minus", 0.0))
    return None


def eval_expr(value: Any, params: Mapping[str, Any], where: str) -> float:
    """A number, or a string of params keys / numbers combined with + - * / ( )."""
    if isinstance(value, bool):
        raise SpecError(f"{where}: boolean is not a length")
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        raise SpecError(f"{where}: expected a number or params expression, got {value!r}")
    names: dict[str, float] = {}

    def _sub(m: re.Match) -> str:
        var = f"_p{len(names)}"
        names[var] = param_value(params, m.group(0))
        return var

    src = _PARAM_NAME.sub(_sub, value)
    try:
        tree = ast.parse(src, mode="eval")
    except SyntaxError as exc:
        raise SpecError(f"{where}: cannot parse expression {value!r}: {exc}") from exc

    def _ev(node: ast.AST) -> float:
        if isinstance(node, ast.Expression):
            return _ev(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return float(node.value)
        if isinstance(node, ast.Name) and node.id in names:
            return names[node.id]
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            v = _ev(node.operand)
            return -v if isinstance(node.op, ast.USub) else v
        if isinstance(node, ast.BinOp) and type(node.op) in _BINOPS:
            return _BINOPS[type(node.op)](_ev(node.left), _ev(node.right))
        raise SpecError(f"{where}: unsupported element in expression {value!r} (only numbers, params keys, + - * / and parentheses)")

    out = _ev(tree)
    if not math.isfinite(out):
        raise SpecError(f"{where}: expression {value!r} is not finite")
    return out


def eval_point(value: Any, params: Mapping[str, Any], where: str) -> tuple[float, float, float]:
    if not isinstance(value, list) or len(value) != 3:
        raise SpecError(f"{where}: expected a 3-element [x, y, z] list (mm), got {value!r}")
    x, y, z = (eval_expr(v, params, f"{where}[{i}]") for i, v in enumerate(value))
    return (x, y, z)


_AXES = {"X": (1.0, 0.0, 0.0), "Y": (0.0, 1.0, 0.0), "Z": (0.0, 0.0, 1.0)}


def parse_axis(value: Any, where: str, *, signed: bool) -> tuple[tuple[float, float, float], int]:
    """'X' / '+X' / '-X' (or a 3-list) -> (unit vector, sign) where sign 0 means 'either'."""
    if isinstance(value, list):
        if len(value) != 3 or not all(isinstance(v, (int, float)) for v in value):
            raise SpecError(f"{where}: vector must be 3 numbers, got {value!r}")
        n = math.sqrt(sum(float(v) ** 2 for v in value))
        if n < 1e-12:
            raise SpecError(f"{where}: zero vector")
        return (float(value[0]) / n, float(value[1]) / n, float(value[2]) / n), 1
    if not isinstance(value, str):
        raise SpecError(f"{where}: expected an axis like 'X', '+Y', '-Z', got {value!r}")
    m = re.fullmatch(r"([+-]?)([XYZ])", value.strip().upper())
    if not m:
        raise SpecError(f"{where}: expected an axis like 'X', '+Y', '-Z', got {value!r}")
    sign = {"": 0, "+": 1, "-": -1}[m.group(1)]
    if signed and sign == 0:
        sign = 1
    base = _AXES[m.group(2)]
    s = -1.0 if sign == -1 else 1.0
    return (base[0] * s, base[1] * s, base[2] * s), sign


def parse_scale(value: Any, where: str) -> float:
    if not isinstance(value, str) or not re.fullmatch(r"\d+(\.\d+)?:\d+(\.\d+)?", value.strip()):
        raise SpecError(f"{where}: scale must look like '1:1', '2:1' or '1:2', got {value!r}")
    a, b = value.strip().split(":")
    if float(b) == 0 or float(a) == 0:
        raise SpecError(f"{where}: zero in scale {value!r}")
    return float(a) / float(b)


# ------------------------------------------------------------------ selectors
def parse_ref(raw: Any, params: Mapping[str, Any], where: str) -> dict[str, Any]:
    """Normalise a feature selector (see references/spec-schema.md#selectors)."""
    if not isinstance(raw, Mapping):
        raise SpecError(f"{where}: selector must be an inline table, got {raw!r}")
    kinds = [k for k in ("plane", "cylinder", "vertex") if k in raw]
    if len(kinds) != 1:
        raise SpecError(f"{where}: selector needs exactly one of plane / cylinder / vertex, got keys {sorted(raw)}")
    kind = kinds[0]
    snap = eval_expr(raw.get("snap", 0.5), params, f"{where}.snap")
    if kind == "plane":
        axis, sign = parse_axis(raw["plane"], f"{where}.plane", signed=False)
        if sign == -1:  # keep the axis positive; the sign only filters the outward normal
            axis = (-axis[0], -axis[1], -axis[2])
        if isinstance(raw["plane"], list):
            raise SpecError(f"{where}: plane takes an axis name ('X', '+Y', '-Z'), not a vector")
        at = raw.get("at")
        if at is None:
            raise SpecError(f"{where}: plane selector needs at = 'min' | 'max' | <coordinate>")
        at_v: Any = at if at in ("min", "max") else eval_expr(at, params, f"{where}.at")
        return {"kind": "plane", "axis": axis, "sign": sign, "at": at_v, "snap": snap}
    if kind == "cylinder":
        axis, _ = parse_axis(raw["cylinder"], f"{where}.cylinder", signed=True)
        if "near" not in raw:
            raise SpecError(f"{where}: cylinder selector needs near = [x, y, z] (a point on or next to the cylindrical face)")
        return {"kind": "cylinder", "axis": axis, "near": eval_point(raw["near"], params, f"{where}.near"), "snap": snap}
    return {"kind": "vertex", "near": eval_point(raw["vertex"], params, f"{where}.vertex"), "snap": snap}


# ---------------------------------------------------------------- tolerances
def parse_tol(raw: Any, where: str) -> dict[str, Any]:
    style = "plusminus"
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        plus = minus = float(raw)
    elif isinstance(raw, Mapping):
        if "plus" not in raw or "minus" not in raw:
            raise SpecError(f"{where}: tol table needs plus and minus (mm)")
        plus, minus = float(raw["plus"]), float(raw["minus"])
        style = raw.get("style", "plusminus")
        if style not in ("plusminus", "limits"):
            raise SpecError(f"{where}: tol.style must be 'plusminus' or 'limits'")
    else:
        raise SpecError(f"{where}: every critical dimension needs an explicit tol (number for +/-, or {{plus, minus[, style]}})")
    # S14: plus/minus are magnitudes (the sign convention -- upper = nominal+plus,
    # lower = nominal-minus -- is applied in format_dim_text/the checker, not here),
    # so a negative value is never valid on its own, even when plus+minus still
    # nets positive (e.g. plus=0.20, minus=-0.10 used to slip through here).
    if plus < 0 or minus < 0:
        raise SpecError(f"{where}: tol.plus and tol.minus must each be >= 0 (magnitudes; got +{plus}/-{minus})")
    if plus + minus <= 0:
        raise SpecError(f"{where}: tolerance zone plus + minus must be > 0 (got +{plus}/-{minus})")
    return {"plus": plus, "minus": minus, "style": style}


def _decimals_for(x: float) -> int:
    s = f"{abs(x):.6f}".rstrip("0")
    return max(0, len(s.split(".")[1]) if "." in s else 0)


def format_dim_text(dim: Mapping[str, Any], nominal: float | None) -> tuple[str, bool]:
    """Return (TechDraw FormatSpec or literal text, is_arbitrary).

    Uses DXF control codes (%%c diameter, %%p plus/minus) -- FreeCAD writes
    DXF R2000 whose code page mangles raw UTF-8, and these codes survive.
    ``nominal`` is only needed for the literal 'limits' style.
    """
    d = dim["decimals"]
    tol = dim["tol"]
    td = max(d, _decimals_for(tol["plus"]), _decimals_for(tol["minus"]))
    prefix = (f"{dim['count']}X " if dim.get("count", 1) > 1 else "") + {"diameter": "%%c", "radius": "R"}.get(dim["type"], "")
    if tol["style"] == "limits":
        if nominal is None:
            raise ValueError("limits style needs the nominal")
        up, lo = nominal + tol["plus"], nominal - tol["minus"]
        return f"{prefix}{up:.{td}f}/{lo:.{td}f}", True
    if abs(tol["plus"] - tol["minus"]) < 1e-12:
        return f"{prefix}%.{d}f %%p{tol['plus']:.{td}f}", False
    return f"{prefix}%.{d}f {_dev(tol['plus'], td)}/{_dev(-tol['minus'], td)}", False


def _dev(x: float, td: int) -> str:
    """A deviation: signed, except zero which is written as a bare 0."""
    return "0" if abs(x) < 1e-12 else f"{x:+.{td}f}"


# ---------------------------------------------------------------------- spec
def _req(table: Mapping[str, Any], key: str, where: str) -> Any:
    if key not in table:
        raise SpecError(f"{where}: missing required key {key!r}")
    return table[key]


def _str(table: Mapping[str, Any], key: str, where: str) -> str:
    v = _req(table, key, where)
    if not isinstance(v, str) or not v.strip():
        raise SpecError(f"{where}.{key}: must be a non-empty string")
    if any(ord(c) > 126 for c in v):
        raise SpecError(f"{where}.{key}: use ASCII text ({v!r}); DXF R2000 output cannot carry it reliably")
    return v.strip()


def is_v2(raw: Mapping[str, Any]) -> bool:
    return raw.get("schema") == SCHEMA


def load_spec(raw: Mapping[str, Any], params: Mapping[str, Any], *, stem: str) -> dict[str, Any]:
    """Validate a parsed TOML spec and return the normalised form."""
    if raw.get("schema") != SCHEMA:
        raise SpecError(f"schema must be {SCHEMA!r}")
    drawing = raw.get("drawing")
    if not isinstance(drawing, Mapping):
        raise SpecError("missing [drawing] table")
    dw: dict[str, Any] = {f: _str(drawing, f, "[drawing]") for f in TITLE_FIELDS}
    if dw["units"] != "mm":
        raise SpecError("[drawing].units must be 'mm' (CONTRACTS.md §10: SI with mm for geometry)")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", dw["date"]):
        raise SpecError("[drawing].date must be ISO 8601 YYYY-MM-DD (fixed in the spec, so output is reproducible)")
    m = _GENTOL.match(dw["general_tolerance"])
    if not m:
        raise SpecError("[drawing].general_tolerance must look like 'ISO 2768-m' (classes f/m/c/v, R5a §1)")
    dw["general_tolerance_geometric_class"] = m.group(2)
    dw["name"] = str(drawing.get("name", stem))
    if not _ID.match(dw["name"]):
        raise SpecError(f"[drawing].name {dw['name']!r} must match {_ID.pattern}")
    proj = _str(drawing, "projection", "[drawing]").lower()
    if proj not in ("first", "third"):
        raise SpecError("[drawing].projection must be 'first' or 'third' (declared, then drawn as the symbol)")
    dw["projection"] = proj
    size = _str(drawing, "sheet_size", "[drawing]").upper()
    if size not in SHEET_SIZES_MM:
        raise SpecError(f"[drawing].sheet_size must be one of {sorted(SHEET_SIZES_MM)}")
    dw["sheet_size"] = size
    dw["signoff"] = str(drawing.get("signoff", SIGNOFF_DEFAULT))
    if "NOT FOR MANUFACTURE" not in dw["signoff"].upper():
        raise SpecError("[drawing].signoff must keep the words 'NOT FOR MANUFACTURE' (human sign-off before release)")
    dw["tolerancing_standard"] = str(drawing.get("tolerancing_standard", "")).strip()

    model = raw.get("model")
    if not isinstance(model, Mapping):
        raise SpecError("missing [model] table (module = 'cad/<part>.py' or step = '<file>.step')")
    if ("module" in model) == ("step" in model):
        raise SpecError("[model] needs exactly one of module / step")
    mdl = {"module": model.get("module"), "step": model.get("step"),
           "params": str(model.get("params", "params/params.toml"))}

    # -- views
    views_raw = raw.get("view", [])
    if not isinstance(views_raw, list) or not views_raw:
        raise SpecError("at least one [[view]] is required")
    views: dict[str, dict[str, Any]] = {}
    for i, v in enumerate(views_raw):
        where = f"[[view]] #{i + 1}"
        vid = _str(v, "id", where)
        if not _ID.match(vid) or vid in views:
            raise SpecError(f"{where}: id {vid!r} must be unique and match {_ID.pattern}")
        kind = _str(v, "kind", where).lower()
        if kind not in VIEW_KINDS:
            raise SpecError(f"{where}: kind must be one of {VIEW_KINDS}")
        view: dict[str, Any] = {"id": vid, "kind": kind, "obj": f"View_{vid}"}
        if "cell" in v:
            c = v["cell"]
            if not (isinstance(c, list) and len(c) == 2 and all(isinstance(x, int) for x in c)):
                raise SpecError(f"{where}: cell must be [column, row] integers on the view grid (front view = [0, 0], row up)")
            if kind in ORTHO_KINDS:
                raise SpecError(f"{where}: principal views are placed by the projection method; 'cell' is for iso/section/detail views")
            view["cell"] = (c[0], c[1])
        if "scale" in v:
            view["scale_str"] = v["scale"]
            view["scale"] = parse_scale(v["scale"], f"{where}.scale")
        if kind in ORTHO_BASIS:
            d, x = ORTHO_BASIS[kind]
            if kind == "iso" and "direction" in v:
                d = parse_axis(v["direction"], f"{where}.direction", signed=True)[0]
                x = parse_axis(_req(v, "x_direction", where), f"{where}.x_direction", signed=True)[0]
            view["direction"], view["x_direction"] = _unit(d), _unit(x)
        if kind == "section":
            view["base"] = _str(v, "base", where)
            view["label"] = _str(v, "label", where).upper()
            view["origin"] = eval_point(_req(v, "origin", where), params, f"{where}.origin")
            n = parse_axis(_req(v, "normal", where), f"{where}.normal", signed=True)[0]
            view["direction"] = n
            view["x_direction"] = _section_xdir(n)
        if kind == "detail":
            view["base"] = _str(v, "base", where)
            view["label"] = _str(v, "label", where).upper()
            view["center"] = eval_point(_req(v, "center", where), params, f"{where}.center")
            view["radius"] = eval_expr(_req(v, "radius", where), params, f"{where}.radius")
            if view["radius"] <= 0:
                raise SpecError(f"{where}: radius must be > 0")
            if "scale" not in view:
                raise SpecError(f"{where}: a detail view needs its own scale (e.g. '4:1')")
        if kind in ("section", "detail") and not DATUM_LETTER.match(view["label"]):
            raise SpecError(f"{where}: label must be one capital letter (not I, O, Q)")
        views[vid] = view
    for vid, view in views.items():
        if view["kind"] in ("section", "detail"):
            base = views.get(view["base"])
            if base is None:
                raise SpecError(f"view {vid!r}: base view {view['base']!r} is not declared")
            if base["kind"] in ("iso",) or (view["kind"] == "section" and base["kind"] == "detail"):
                raise SpecError(f"view {vid!r}: base view {view['base']!r} ({base['kind']}) cannot carry a {view['kind']} marker")
            if view["kind"] == "section" and abs(_dot(view["direction"], base["direction"])) > 1e-9:
                raise SpecError(f"view {vid!r}: the section plane must be seen edge-on in its base view (normal perpendicular to the base view direction)")
            if view["kind"] == "detail":
                view["direction"], view["x_direction"] = base["direction"], base["x_direction"]
    labels = [v["label"] for v in views.values() if "label" in v]
    if len(labels) != len(set(labels)):
        raise SpecError(f"section/detail labels must be unique, got {labels}")

    # -- sheets
    sheets_raw = raw.get("sheet", [])
    if not isinstance(sheets_raw, list) or not sheets_raw:
        raise SpecError("at least one [[sheet]] (scale, views) is required")
    sheets = []
    placed: set[str] = set()
    for i, s in enumerate(sheets_raw):
        where = f"[[sheet]] #{i + 1}"
        scale_str = _str(s, "scale", where)
        scale = parse_scale(scale_str, f"{where}.scale")
        ids = _req(s, "views", where)
        if not isinstance(ids, list) or not ids:
            raise SpecError(f"{where}: views must be a non-empty list of view ids")
        for vid in ids:
            if vid not in views:
                raise SpecError(f"{where}: view {vid!r} is not declared in [[view]]")
            if vid in placed:
                raise SpecError(f"{where}: view {vid!r} is already on another sheet")
            placed.add(vid)
            views[vid]["sheet"] = i + 1
            views[vid].setdefault("scale", scale)
            views[vid].setdefault("scale_str", scale_str)
        sheets.append({"index": i + 1, "scale": scale, "scale_str": scale_str, "views": list(ids)})
    missing = sorted(set(views) - placed)
    if missing:
        raise SpecError(f"views {missing} are declared but not placed on any [[sheet]]")

    # -- datums
    datums: dict[str, dict[str, Any]] = {}
    for i, d in enumerate(raw.get("datum", []) or []):
        where = f"[[datum]] #{i + 1}"
        did = _str(d, "id", where).upper()
        if not DATUM_LETTER.match(did) or did in datums:
            raise SpecError(f"{where}: id {did!r} must be a unique capital letter (not I, O, Q)")
        vid = _str(d, "view", where)
        if vid not in views or views[vid]["kind"] == "iso":
            raise SpecError(f"{where}: view {vid!r} must be a declared non-pictorial view")
        along = float(d.get("along", 0.1))
        if not 0.0 <= along <= 1.0:
            raise SpecError(f"{where}: along must be a fraction 0..1 of the face's visible length")
        datums[did] = {"id": did, "view": vid, "along": along, "on": parse_ref(_req(d, "on", where), params, f"{where}.on")}

    # -- dimensions
    dims_raw = raw.get("dimension", [])
    if not isinstance(dims_raw, list) or not dims_raw:
        raise SpecError("no [[dimension]] entries -- a drawing with no critical dimensions cannot be checked")
    dims: list[dict[str, Any]] = []
    seen: set[str] = set()
    for i, d in enumerate(dims_raw):
        where = f"[[dimension]] #{i + 1}"
        did = _str(d, "id", where)
        if not _ID.match(did) or did in seen:
            raise SpecError(f"{where}: id {did!r} must be unique and match {_ID.pattern}")
        seen.add(did)
        where = f"[[dimension]] {did!r}"
        param = _str(d, "param", where)
        nominal = param_value(params, param)
        req = _str(d, "requirement", where)
        if not _REQ.match(req):
            raise SpecError(f"{where}: requirement {req!r} must look like REQ-MECH-001")
        vid = _str(d, "view", where)
        if vid not in views:
            raise SpecError(f"{where}: view {vid!r} is not declared")
        if views[vid]["kind"] == "iso":
            raise SpecError(f"{where}: critical dimensions go on orthographic, section or detail views, not the pictorial (iso) view")
        typ = _str(d, "type", where).lower()
        if typ not in DIM_TYPES:
            raise SpecError(f"{where}: type must be one of {DIM_TYPES}")
        dim: dict[str, Any] = {"id": did, "obj": f"Dim_{did}", "param": param, "param_nominal": nominal,
                               "param_tol": param_tol(params, param), "requirement": req, "view": vid, "type": typ,
                               "tol": parse_tol(d.get("tol"), f"{where}.tol"),
                               "decimals": int(d.get("decimals", 2)), "count": int(d.get("count", 1)),
                               "side": d.get("side"), "offset": d.get("offset", [0.0, 0.0]),
                               "angle": float(d.get("angle", 45.0)),
                               "allow_annotation": bool(d.get("allow_annotation", False))}
        if dim["decimals"] < MIN_DECIMALS or dim["decimals"] > 4:
            raise SpecError(f"{where}: decimals must be {MIN_DECIMALS}..4 (display rounding must stay below the 0.01 mm check)")
        if dim["count"] < 1:
            raise SpecError(f"{where}: count must be >= 1")
        if typ == "linear":
            dim["axis"] = parse_axis(_req(d, "axis", where), f"{where}.axis", signed=True)[0]
            dim["from"] = parse_ref(_req(d, "from", where), params, f"{where}.from")
            dim["to"] = parse_ref(_req(d, "to", where), params, f"{where}.to")
            if dim["count"] != 1:
                raise SpecError(f"{where}: count applies to diameter/radius callouts only")
        else:
            dim["of"] = parse_ref(_req(d, "of", where), params, f"{where}.of")
            if dim["of"]["kind"] != "cylinder":
                raise SpecError(f"{where}: {typ} needs of = {{ cylinder = ..., near = [...] }}")
        if not (isinstance(dim["offset"], list) and len(dim["offset"]) == 2):
            raise SpecError(f"{where}: offset must be [dx, dy] in sheet mm")
        dims.append(dim)

    # -- feature control frames
    gdts = []
    for i, g in enumerate(raw.get("gdt", []) or []):
        where = f"[[gdt]] #{i + 1}"
        gid = _str(g, "id", where)
        if not _ID.match(gid):
            raise SpecError(f"{where}: id {gid!r} must match {_ID.pattern}")
        ch = _str(g, "characteristic", where).lower()
        if ch not in GDT_CHARACTERISTICS:
            raise SpecError(f"{where}: characteristic must be one of {GDT_CHARACTERISTICS}")
        tolv = eval_expr(_req(g, "tolerance", where), params, f"{where}.tolerance")
        if tolv <= 0:
            raise SpecError(f"{where}: tolerance must be > 0 mm")
        drefs = [str(x).upper() for x in g.get("datums", [])]
        for dref in drefs:
            if dref not in datums:
                raise SpecError(f"{where}: datum reference {dref!r} is not declared in [[datum]] -- a feature control frame must reference declared datum features")
        if len(set(drefs)) != len(drefs) or len(drefs) > 3:
            raise SpecError(f"{where}: datums must be up to 3 distinct letters (primary, secondary, tertiary)")
        if ch in GDT_FORM and drefs:
            raise SpecError(f"{where}: a form tolerance ({ch}) takes no datum reference")
        if ch in GDT_NEEDS_DATUM and not drefs:
            raise SpecError(f"{where}: {ch} needs at least one datum reference")
        mod = str(g.get("modifier", "")).upper()
        if mod not in ("", "M", "L"):
            raise SpecError(f"{where}: modifier must be 'M' (MMC), 'L' (LMC) or omitted")
        dim_ref = g.get("dimension")
        if dim_ref is None or dim_ref not in seen:
            raise SpecError(f"{where}: dimension = <id of the [[dimension]] whose feature this frame controls> is required")
        req = g.get("requirement")
        if req is not None and not _REQ.match(str(req)):
            raise SpecError(f"{where}: requirement {req!r} must look like REQ-MECH-001")
        gdts.append({"id": gid, "characteristic": ch, "tolerance": tolv, "diameter_zone": bool(g.get("diameter_zone", False)),
                     "modifier": mod, "datums": drefs, "dimension": dim_ref, "requirement": req})
    if (gdts or datums) and not dw["tolerancing_standard"]:
        raise SpecError("[drawing].tolerancing_standard is required when [[gdt]]/[[datum]] are used (e.g. 'ASME Y14.5-2018' or 'ISO 1101:2017'; R5a §1) -- a frame's meaning depends on it")

    notes = []
    for i, n in enumerate(raw.get("note", []) or []):
        notes.append(_str(n, "text", f"[[note]] #{i + 1}"))

    return {"schema": SCHEMA, "name": dw["name"], "drawing": dw, "model": mdl, "views": views, "sheets": sheets,
            "datums": datums, "dimensions": dims, "gdt": gdts, "notes": notes}


def _dot(a, b) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _unit(v) -> tuple[float, float, float]:
    n = math.sqrt(_dot(v, v))
    return (v[0] / n, v[1] / n, v[2] / n)


def _section_xdir(n) -> tuple[float, float, float]:
    """Paper x for a section seen along its normal: Z x N (keeps Z up), X if N is vertical."""
    if abs(n[2]) > 1 - 1e-9:
        return (1.0, 0.0, 0.0)
    c = (-n[1], n[0], 0.0)  # (0,0,1) x n
    return _unit(c)


def spec_path_stem(path: Path) -> str:
    return re.sub(r"[^a-z0-9_]+", "_", path.stem.lower()).strip("_") or "drawing"
