"""Select CAD faces by geometric predicates (runs inside an open gmsh session).

A selector is a TOML inline table (or a list of them, meaning the union). Every predicate
given in one table must hold (logical AND). Documented in references/face-selectors.md.

    { plane = "x", at = "min" }               planar face normal to x, at the part's min x
    { plane = "z", at = 12.5 }                planar face normal to z at z = 12.5 mm
    { normal = [0, 0, 1] }                    planar face whose OUTWARD normal is +z (angle_tol_deg)
    { cylinder_radius_mm = 5.0, axis = "z" }  cylindrical face of radius 5 mm, axis parallel to z
    { within_box_mm = [x0,y0,z0,x1,y1,z1] }   face bounding box inside this box
    { contains_point_mm = [x,y,z] }           face passes within tol_mm of this point
    { type = "plane" }                        gmsh/OCC surface type (plane, cylinder, cone, ...)
    tol_mm (default 0.01), angle_tol_deg (default 1.0), expect_count (int, optional guard)

An empty match is always an error (never a silently unloaded / unconstrained model).
"""
from __future__ import annotations

import math

import gmsh
import numpy as np

_KEYS = {"plane", "at", "normal", "cylinder_radius_mm", "axis", "within_box_mm", "contains_point_mm",
         "type", "tol_mm", "angle_tol_deg", "expect_count"}
_AXES = {"x": 0, "y": 1, "z": 2}


class SelectorError(ValueError):
    """The selector is malformed or matched no face."""


def _unit(v) -> np.ndarray:
    a = np.asarray(v, dtype=float)
    n = np.linalg.norm(a)
    if a.shape != (3,) or n == 0:
        raise SelectorError(f"direction {v!r} must be a non-zero 3-vector")
    return a / n


def _axis_vec(axis) -> np.ndarray:
    if isinstance(axis, str):
        if axis not in _AXES:
            raise SelectorError(f"axis {axis!r} must be x, y, z or a 3-vector")
        v = np.zeros(3)
        v[_AXES[axis]] = 1.0
        return v
    return _unit(axis)


def _interior_param(tag: int) -> tuple[list[float], np.ndarray] | None:
    """A (u, v) parameter and point that lie on the trimmed face (not in a hole)."""
    lo, hi = gmsh.model.getParametrizationBounds(2, tag)
    for n in (1, 3, 7, 15):
        for i in range(1, n + 1):
            for j in range(1, n + 1):
                uv = [lo[0] + (hi[0] - lo[0]) * i / (n + 1), lo[1] + (hi[1] - lo[1]) * j / (n + 1)]
                if gmsh.model.isInside(2, tag, uv, parametric=True):
                    return uv, np.array(gmsh.model.getValue(2, tag, uv))
    return None


def face_info(tag: int, vtag: int) -> dict:
    """Geometric facts about one surface of volume ``vtag``."""
    typ = gmsh.model.getType(2, tag).lower()
    bb = gmsh.model.getBoundingBox(2, tag)
    info = {"tag": tag, "type": typ, "bbox": list(bb),
            "area_mm2": gmsh.model.occ.getMass(2, tag), "normal": None, "radius": None, "axis": None}
    hit = _interior_param(tag)
    if hit is None:
        return info
    uv, p = hit
    n = np.array(gmsh.model.getNormal(tag, uv), dtype=float)
    # make the normal outward: step off the face and ask the solid
    size = max(bb[3] - bb[0], bb[4] - bb[1], bb[5] - bb[2], 1e-6)
    eps = 1e-4 * size + 1e-6
    if gmsh.model.isInside(3, vtag, list(p + eps * n)) and not gmsh.model.isInside(3, vtag, list(p - eps * n)):
        n = -n
    info["normal"] = n / np.linalg.norm(n)
    if typ == "cylinder":
        kmax, kmin, dmax, dmin = gmsh.model.getPrincipalCurvatures(tag, uv)
        k = [abs(kmax[0]), abs(kmin[0])]
        dirs = [np.array(dmax[:3]), np.array(dmin[:3])]
        i_curved = int(np.argmax(k))
        if k[i_curved] > 0:
            info["radius"] = 1.0 / k[i_curved]
            info["axis"] = dirs[1 - i_curved] / np.linalg.norm(dirs[1 - i_curved])
    return info


def _matches(spec: dict, info: dict, part_bb: list[float]) -> bool:
    tol = float(spec.get("tol_mm", 0.01))
    ang = math.radians(float(spec.get("angle_tol_deg", 1.0)))
    bb = info["bbox"]
    if "type" in spec and info["type"] != str(spec["type"]).lower():
        return False
    if "plane" in spec:
        ax = _AXES.get(spec["plane"])
        if ax is None:
            raise SelectorError(f"plane {spec['plane']!r} must be x, y or z")
        if info["type"] != "plane" or (bb[ax + 3] - bb[ax]) > tol:
            return False
        at = spec.get("at")
        if at is None:
            raise SelectorError("a plane selector needs at = \"min\" | \"max\" | <coordinate mm>")
        target = part_bb[ax] if at == "min" else part_bb[ax + 3] if at == "max" else float(at)
        if abs(0.5 * (bb[ax] + bb[ax + 3]) - target) > tol:
            return False
    elif "at" in spec:
        raise SelectorError("'at' is only meaningful together with 'plane'")
    if "normal" in spec:
        if info["type"] != "plane" or info["normal"] is None:
            return False
        if math.acos(max(-1.0, min(1.0, float(np.dot(info["normal"], _unit(spec["normal"])))))) > ang:
            return False
    if "cylinder_radius_mm" in spec:
        if info["type"] != "cylinder" or info["radius"] is None:
            return False
        if abs(info["radius"] - float(spec["cylinder_radius_mm"])) > tol:
            return False
        if "axis" in spec and abs(float(np.dot(info["axis"], _axis_vec(spec["axis"])))) < math.cos(ang):
            return False
    elif "axis" in spec:
        raise SelectorError("'axis' is only meaningful together with 'cylinder_radius_mm'")
    if "within_box_mm" in spec:
        b = [float(v) for v in spec["within_box_mm"]]
        if len(b) != 6:
            raise SelectorError("within_box_mm needs [xmin, ymin, zmin, xmax, ymax, zmax]")
        if any(bb[i] < b[i] - tol for i in range(3)) or any(bb[i + 3] > b[i + 3] + tol for i in range(3)):
            return False
    if "contains_point_mm" in spec:
        p = [float(v) for v in spec["contains_point_mm"]]
        q = gmsh.model.getClosestPoint(2, info["tag"], p)[0]
        if np.linalg.norm(np.array(q) - np.array(p)) > tol or not gmsh.model.isInside(2, info["tag"], list(q)):
            return False
    return True


def select_faces(spec, vtag: int, part_bb: list[float], infos: dict[int, dict], label: str) -> list[int]:
    """Surface tags of volume ``vtag`` matching ``spec`` (a table or a list of tables = union)."""
    specs = spec if isinstance(spec, list) else [spec]
    if not specs:
        raise SelectorError(f"{label}: empty face selector")
    out: list[int] = []
    for s in specs:
        if not isinstance(s, dict) or not s:
            raise SelectorError(f"{label}: each face selector must be a non-empty table, got {s!r}")
        unknown = set(s) - _KEYS
        if unknown:
            raise SelectorError(f"{label}: unknown selector key(s) {sorted(unknown)}; allowed {sorted(_KEYS)}")
        hits = [t for t, info in infos.items() if _matches(s, info, part_bb)]
        if not hits:
            raise SelectorError(
                f"{label}: selector {s} matched no face. Faces present: "
                + "; ".join(describe(i) for i in infos.values())
            )
        if "expect_count" in s and len(hits) != int(s["expect_count"]):
            raise SelectorError(f"{label}: selector {s} matched {len(hits)} faces, expected {s['expect_count']}")
        out.extend(t for t in hits if t not in out)
    return sorted(out)


def describe(info: dict) -> str:
    bb = info["bbox"]
    extra = ""
    if info["normal"] is not None and info["type"] == "plane":
        extra = f" n=({info['normal'][0]:+.2f},{info['normal'][1]:+.2f},{info['normal'][2]:+.2f})"
    if info["radius"] is not None:
        extra = f" r={info['radius']:.3f}mm"
    return (f"#{info['tag']} {info['type']}{extra} bbox=[{bb[0]:.2f},{bb[1]:.2f},{bb[2]:.2f} .. "
            f"{bb[3]:.2f},{bb[4]:.2f},{bb[5]:.2f}] A={info['area_mm2']:.2f}mm2")
