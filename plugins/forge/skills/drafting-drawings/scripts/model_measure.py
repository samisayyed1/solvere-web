"""Independent model measurement for drafting-drawings (runs under ``forge-python``).

Every critical dimension on a drawing is re-measured here, on the exact
B-rep in build123d/OCP, from the spec's geometric selectors -- never read
back from TechDraw. ``verify.py`` then compares three numbers per dimension:
the params nominal, this measurement, and what the drawing (DXF) says.

Selectors (see references/spec-schema.md#selectors):

- ``plane``    planar faces whose outward normal is parallel to an axis
               ('X' either sense, '+X'/'-X' one sense); pick ``at`` =
               'min' | 'max' | a coordinate (nearest, within ``snap``).
- ``cylinder`` cylindrical faces whose axis is parallel to an axis; pick the
               face nearest to ``near`` (a point on/next to the face, within
               ``snap``). A second, different cylinder within 1e-3 mm of the
               best distance is an ambiguous selector, reported as such.
- ``vertex``   the model vertex nearest to a point (within ``snap``).
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import build123d as bd

Vec = tuple[float, float, float]
AMBIGUITY_MM = 1e-3
PARALLEL = 1 - 1e-9


class Unresolved(Exception):
    """A selector matched no (or more than one) model feature."""


def _t(v: bd.Vector) -> Vec:
    return (float(v.X), float(v.Y), float(v.Z))


def dot(a: Sequence[float], b: Sequence[float]) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a: Sequence[float], b: Sequence[float]) -> Vec:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def unit(a: Sequence[float]) -> Vec:
    n = math.sqrt(dot(a, a))
    return (a[0] / n, a[1] / n, a[2] / n)


def load_model(project: Path, model: Mapping[str, Any], params: Mapping[str, Any]) -> bd.Shape:
    from forge_cad.load import load_part, load_step
    if model.get("module"):
        return load_part(project / model["module"], params=params)
    return load_step(project / model["step"])


# ------------------------------------------------------------------ selectors
def _cyl_axis(face: bd.Face) -> tuple[Vec, Vec]:
    ax = face.axis_of_rotation
    return _t(ax.position), unit(_t(ax.direction))


def _axis_key(point: Vec, direction: Vec, radius: float) -> tuple:
    # canonical axis line: the point on the line closest to the origin
    t = dot(point, direction)
    p0 = (point[0] - t * direction[0], point[1] - t * direction[1], point[2] - t * direction[2])
    return (round(p0[0], 3), round(p0[1], 3), round(p0[2], 3), round(radius, 3))


def resolve(shape: bd.Shape, ref: Mapping[str, Any], hint: Sequence[float] | None = None) -> dict[str, Any]:
    """Resolve a selector. ``hint`` (e.g. a detail view's centre) moves the returned
    reference point to the part of the feature nearest to it; it never changes
    which feature is selected or the measured value."""
    kind = ref["kind"]
    if kind == "plane":
        axis = ref["axis"]
        cands = []
        for f in shape.faces():
            if f.geom_type != bd.GeomType.PLANE:
                continue
            n = _t(f.normal_at())
            c = dot(n, axis)
            if abs(c) < PARALLEL:
                continue
            if ref["sign"] == 1 and c < 0 or ref["sign"] == -1 and c > 0:
                continue
            cands.append((dot(_t(f.center()), axis), f.area, f, n))
        if not cands:
            raise Unresolved(f"no planar face with normal {'+-'[ref['sign'] < 0] if ref['sign'] else ''}{axis}")
        if ref["at"] == "min":
            pos = min(c[0] for c in cands)
        elif ref["at"] == "max":
            pos = max(c[0] for c in cands)
        else:
            pos = min((c[0] for c in cands), key=lambda p: abs(p - ref["at"]))
            if abs(pos - ref["at"]) > ref["snap"]:
                raise Unresolved(f"nearest planar face (normal {axis}) is at {pos:.3f} mm, not within {ref['snap']} mm of {ref['at']:.3f} mm")
        at_pos = sorted((c for c in cands if abs(c[0] - pos) < 1e-6), key=lambda c: -c[1])
        best = at_pos[0]
        point = _t(best[2].center())
        if hint is not None:
            near_faces = sorted(at_pos, key=lambda c: c[2].distance_to(bd.Vector(*hint)))
            best = near_faces[0]
            point = _t(best[2].closest_points(bd.Vector(*hint))[0])
        return {"kind": "plane", "axis": axis, "position": pos, "point": point, "normal": best[3],
                "vertices": [_t(bd.Vector(v.X, v.Y, v.Z)) for v in best[2].vertices()]}
    if kind == "cylinder":
        axis = ref["axis"]
        near = bd.Vector(*ref["near"])
        cands = []
        for f in shape.faces():
            if f.geom_type != bd.GeomType.CYLINDER:
                continue
            p, d = _cyl_axis(f)
            if abs(dot(d, axis)) < PARALLEL:
                continue
            cands.append((f.distance_to(near), f, p, d, float(f.radius)))
        if not cands:
            raise Unresolved(f"no cylindrical face with axis parallel to {axis}")
        cands.sort(key=lambda c: c[0])
        best = cands[0]
        if best[0] > ref["snap"]:
            raise Unresolved(f"nearest cylindrical face is {best[0]:.3f} mm from {tuple(ref['near'])}, more than snap {ref['snap']} mm")
        bkey = _axis_key(best[2], best[3], best[4])
        for c in cands[1:]:
            if c[0] - best[0] > AMBIGUITY_MM:
                break
            if _axis_key(c[2], c[3], c[4]) != bkey:
                raise Unresolved(f"ambiguous cylinder selector near {tuple(ref['near'])}: faces of radius {best[4]:.3f} and {c[4]:.3f} mm are equally near; move 'near' onto one face")
        p, d, r = best[2], best[3], best[4]
        fc = _t(best[1].center()) if hint is None else tuple(hint)
        t = dot((fc[0] - p[0], fc[1] - p[1], fc[2] - p[2]), d)
        center = (p[0] + t * d[0], p[1] + t * d[1], p[2] + t * d[2])
        # count coaxial-distinct cylinders of this radius that close all the way round
        # (a fillet or partial arc of the same radius is not a hole/boss "N X" feature)
        span: dict[tuple, float] = {}
        for c in cands:
            if abs(c[4] - r) < 1e-3:
                span[_axis_key(c[2], c[3], c[4])] = span.get(_axis_key(c[2], c[3], c[4]), 0.0) + _angular_span(c[1])
        same = {k for k, v in span.items() if v >= 2 * math.pi - 1e-6}
        return {"kind": "cylinder", "axis_dir": d, "center": center, "radius": r, "point": center,
                "count_same": len(same)}
    near = ref["near"]
    best_v, best_d = None, math.inf
    for v in shape.vertices():
        p = (v.X, v.Y, v.Z)
        dd = math.dist(p, near)
        if dd < best_d:
            best_v, best_d = p, dd
    if best_v is None or best_d > ref["snap"]:
        raise Unresolved(f"no vertex within {ref['snap']} mm of {tuple(near)}")
    return {"kind": "vertex", "point": best_v}


def _angular_span(face: bd.Face) -> float:
    from OCP.BRepTools import BRepTools
    u0, u1, _, _ = BRepTools.UVBounds_s(face.wrapped)
    return abs(u1 - u0)


def edge_polylines(shape: bd.Shape, samples: int = 256) -> list[list[Vec]]:
    """Every model edge as a dense 3-D polyline (lines: 2 points)."""
    out = []
    for e in shape.edges():
        n = 2 if e.geom_type == bd.GeomType.LINE else samples
        out.append([_t(e.position_at(i / (n - 1))) for i in range(n)])
    return out


def _pos_along(r: Mapping[str, Any], axis: Vec) -> float:
    if r["kind"] == "plane":
        if abs(dot(r["axis"], axis)) < PARALLEL:
            raise Unresolved("plane selector's normal is not parallel to the dimension axis")
        return dot(r["point"], axis)
    if r["kind"] == "cylinder":
        if abs(dot(r["axis_dir"], axis)) > 1e-9:
            raise Unresolved("cylinder axis is not perpendicular to the dimension axis, so its axis has no single position along it")
        return dot(r["center"], axis)
    return dot(r["point"], axis)


def measure_dimension(shape: bd.Shape, dim: Mapping[str, Any], hint: Sequence[float] | None = None) -> dict[str, Any]:
    """Return {'value': mm, geometry for placement} or {'error': reason}."""
    try:
        if dim["type"] == "linear":
            axis = dim["axis"]
            a, b = resolve(shape, dim["from"], hint), resolve(shape, dim["to"], hint)
            pa, pb = _pos_along(a, axis), _pos_along(b, axis)
            value = abs(pb - pa)
            if value < 1e-6:
                raise Unresolved("from and to resolve to the same position (zero-length dimension)")
            return {"value": value, "p1": list(a["point"]), "p2": list(b["point"]), "axis": list(axis),
                    "pos1": pa, "pos2": pb}
        c = resolve(shape, dim["of"], hint)
        value = 2 * c["radius"] if dim["type"] == "diameter" else c["radius"]
        return {"value": value, "center": list(c["center"]), "axis_dir": list(c["axis_dir"]),
                "radius": c["radius"], "count_found": c["count_same"]}
    except Unresolved as exc:
        return {"error": str(exc)}


def datum_anchor(shape: bd.Shape, datum: Mapping[str, Any]) -> dict[str, Any]:
    try:
        r = resolve(shape, datum["on"])
    except Unresolved as exc:
        return {"error": str(exc)}
    if r["kind"] == "plane":
        return {"point": list(r["point"]), "normal": list(r["normal"]), "kind": "plane",
                "vertices": [list(v) for v in r["vertices"]]}
    if r["kind"] == "cylinder":
        return {"point": list(r["center"]), "axis_dir": list(r["axis_dir"]), "radius": r["radius"], "kind": "cylinder"}
    return {"error": "a datum feature must be a plane or cylinder selector"}


def point_on_surface_distance(shape: bd.Shape, p: Sequence[float]) -> float:
    return float(shape.distance_to(bd.Vector(*p)))


# --------------------------------------------------------------- view geometry
def paper_axes(direction: Vec, x_dir: Vec) -> tuple[Vec, Vec]:
    return x_dir, unit(cross(direction, x_dir))


def projected_extent(shape: bd.Shape, direction: Vec, x_dir: Vec) -> tuple[float, float, float, float]:
    """Exact extents of the solid on the paper axes (mm, model scale): xmin, xmax, ymin, ymax.

    Uses an oriented bounding box aligned to the view (bd.Location of the view
    basis), which is exact for the B-rep (optimal=True), not a mesh estimate.
    """
    xa, ya = paper_axes(direction, x_dir)
    plane = bd.Plane(origin=(0, 0, 0), x_dir=xa, z_dir=direction)
    local = plane.to_local_coords(shape)
    bb = local.bounding_box(optimal=True)
    return bb.min.X, bb.max.X, bb.min.Y, bb.max.Y


def section_loops(shape: bd.Shape, origin: Vec, normal: Vec, samples: int = 72) -> list[list[list[Vec]]]:
    """Cut faces of the solid by the plane, as [face][loop][points] in model mm."""
    big = 10 * max(shape.bounding_box().size.X, shape.bounding_box().size.Y, shape.bounding_box().size.Z, 1.0)
    plane = bd.Plane(origin=origin, z_dir=normal)
    cutter = bd.Face.make_rect(big, big, plane)
    out = []
    for face in shape.intersect(cutter).faces():
        loops = []
        for wire in [face.outer_wire()] + list(face.inner_wires()):
            segs = []
            for edge in wire.edges():
                n = 2 if edge.geom_type == bd.GeomType.LINE else samples
                segs.append([_t(edge.position_at(i / (n - 1))) for i in range(n)])
            loops.append(_chain(segs))
        out.append(loops)
    return out


def _chain(segs: list[list[Vec]], tol: float = 1e-4) -> list[Vec]:
    """Join edge polylines end to end into one closed loop (edges come unordered)."""
    if not segs:
        return []
    pts = list(segs[0])
    rest = segs[1:]
    while rest:
        for i, s in enumerate(rest):
            if math.dist(pts[-1], s[0]) < tol:
                pts.extend(s[1:])
            elif math.dist(pts[-1], s[-1]) < tol:
                pts.extend(list(reversed(s))[1:])
            elif math.dist(pts[0], s[-1]) < tol:
                pts[:0] = s[:-1]
            elif math.dist(pts[0], s[0]) < tol:
                pts[:0] = list(reversed(s))[:-1]
            else:
                continue
            rest.pop(i)
            break
        else:  # disconnected remainder: append as-is (still a boundary, hatch tolerates it)
            pts.extend(rest.pop(0))
    return pts


def measure_all(shape: bd.Shape, spec: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """Measure every critical dimension; dimensions on a detail view anchor near its centre."""
    out = {}
    for dim in spec["dimensions"]:
        view = spec["views"][dim["view"]]
        hint = view["center"] if view["kind"] == "detail" else None
        out[dim["id"]] = measure_dimension(shape, dim, hint)
    return out
