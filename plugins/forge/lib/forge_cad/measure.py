"""Geometry measurement algorithms (CONTRACTS.md §9, FORGE-BRIEF §3.3).

Every function here takes a loaded build123d ``Shape`` (see ``forge_cad.load``)
and returns a plain, JSON-serialisable ``dict`` (or a list of them) of raw
measurements in millimetres/degrees/grams -- **no pass/fail judgement**. The
calling skill script (``verifying-geometry`` / ``checking-dfm``) compares
these numbers against a limit and records the result through
``forge.checkresult`` (CONTRACTS §3), so remediation text always lives next
to the requirement it fixes, not next to the measuring code.

Algorithms, per FORGE-BRIEF §3.3 "Mechanical":

- ``validity``            -- OCP ``BRepCheck_Analyzer`` (the exact check
  ``build123d.Shape.is_valid`` itself wraps; called directly here so a
  measurement, not just a bool, is returned).
- ``watertight_export``   -- STL export + trimesh ``is_watertight``/manifold
  checks.
- ``bounding_box`` / ``volume`` / ``area`` / ``mass_properties``.
- ``min_wall_thickness``  -- ray casting from sampled surface points along
  inward normals to the opposite wall (trimesh's ray intersector when
  available, else a documented vectorised Moeller-Trumbore fallback -- see
  ``_ray_mesh_hits``).
- ``clearance`` / ``interference`` -- OCP ``BRepExtrema_DistShapeShape`` for
  clearance (via build123d's wrapper, which calls it directly) and boolean
  common volume for interference.
- ``draft_angles``        -- face normal vs. pull direction, signed so a
  releasing face reads positive (see the docstring for the sign convention).
- ``min_radius``          -- curvature of cylindrical faces, filtered by
  ``Face.is_circular_concave`` for fillets.
- ``hole_edge_distance``  -- cylindrical hole axis (via OCP
  ``BRepAdaptor_Surface``) to the outer boundary wire.
- ``boss_rib_thickness``  -- ``min_wall_thickness`` restricted to the given
  faces, expressed as a ratio to the nominal wall.

Known resolution limits are documented on each function and repeated in
``plugins/forge/skills/verifying-geometry/references/algorithms.md``.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Sequence

import build123d as bd
import numpy as np
import trimesh
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Cylinder

__all__ = [
    "validity",
    "watertight_export",
    "bounding_box",
    "volume",
    "area",
    "mass_properties",
    "min_wall_thickness",
    "clearance",
    "interference",
    "draft_angles",
    "select_side_faces",
    "min_radius",
    "hole_edge_distance",
    "boss_rib_thickness",
]

Vec3 = tuple[float, float, float]


def _v3(v: bd.Vector) -> Vec3:
    return (round(v.X, 6), round(v.Y, 6), round(v.Z, 6))


def _unit(v: Sequence[float]) -> np.ndarray:
    a = np.asarray(v, dtype=float)
    n = np.linalg.norm(a)
    if n < 1e-12:
        raise ValueError(f"cannot normalize a near-zero vector {v!r}")
    return a / n


# --------------------------------------------------------------------------
# Validity
# --------------------------------------------------------------------------

def validity(shape: bd.Shape) -> dict[str, Any]:
    """Solid validity via OCP's ``BRepCheck_Analyzer`` and manifoldness.

    ``BRepCheck_Analyzer`` runs OCCT's full topological/geometric sanity
    check (self-intersections, tolerance violations, wire closure, orientation
    consistency, ...). This calls it directly on ``shape.wrapped`` rather than
    trusting a cached result, so it always reflects the shape as measured.
    """
    if shape.is_null:
        return {"is_valid": False, "is_manifold": False, "solid_count": 0, "error": "empty shape"}
    checker = BRepCheck_Analyzer(shape.wrapped)
    checker.SetParallel(True)
    is_valid = bool(checker.IsValid())
    solids = shape.solids()
    return {
        "is_valid": is_valid,
        "is_manifold": bool(shape.is_manifold),
        "solid_count": len(solids),
    }


# --------------------------------------------------------------------------
# Watertight export
# --------------------------------------------------------------------------

def watertight_export(shape: bd.Shape, out_path: str | Path, *, tolerance: float = 0.1,
                       angular_tolerance: float = 0.2) -> dict[str, Any]:
    """Export ``shape`` to STL and check the mesh with trimesh.

    ``tolerance``/``angular_tolerance`` are the STL tessellation deflections
    (mm / rad) build123d passes to OCCT's mesher -- tighter values catch more
    thin-wall or small-fillet failures at the cost of triangle count and
    export time. A part with a valid, closed BREP (see :func:`validity`) can
    still tessellate to a non-watertight mesh at a coarse tolerance; a
    non-watertight *STL* result with a valid BREP is a tessellation-resolution
    finding, not necessarily a real gap -- tighten ``tolerance`` and re-check
    before treating it as a design defect.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    ok = bd.export_stl(shape, str(out_path), tolerance=tolerance, angular_tolerance=angular_tolerance)
    if not ok:
        return {"export_ok": False, "watertight": False, "error": "build123d export_stl reported failure"}
    # STL on disk is a triangle soup (no shared-vertex indexing); loading with
    # the default `process=True` welds coincident vertices within trimesh's
    # merge tolerance before the watertight/manifold check, which is required
    # -- an un-welded soup always reads as thousands of disconnected bodies.
    mesh = trimesh.load_mesh(str(out_path), file_type="stl")
    return {
        "export_ok": True,
        "watertight": bool(mesh.is_watertight),
        "is_winding_consistent": bool(mesh.is_winding_consistent),
        "euler_number": int(mesh.euler_number),
        "body_count": int(len(mesh.split(only_watertight=False))),
        "vertex_count": int(len(mesh.vertices)),
        "triangle_count": int(len(mesh.faces)),
        "path": str(out_path),
    }


# --------------------------------------------------------------------------
# Bounding box / volume / area / mass
# --------------------------------------------------------------------------

def bounding_box(shape: bd.Shape) -> dict[str, Any]:
    bb = shape.bounding_box()
    return {
        "min_mm": _v3(bb.min),
        "max_mm": _v3(bb.max),
        "size_mm": _v3(bb.size),
    }


def volume(shape: bd.Shape) -> float:
    """Volume in mm^3 (build123d/OCCT mass properties, exact BREP integration)."""
    return float(shape.volume)


def area(shape: bd.Shape) -> float:
    """Surface area in mm^2."""
    return float(shape.area)


def mass_properties(shape: bd.Shape, *, density_kg_m3: float) -> dict[str, Any]:
    """Mass and centre of mass from exact BREP volume and a supplied density.

    ``density_kg_m3`` must come from ``params/params.toml`` (CONTRACTS §2),
    never hard-coded -- material density is a parameter like any dimension.
    volume [mm^3] * density [kg/m^3] * 1e-9 [m^3/mm^3] * 1000 [g/kg] = mass [g].
    """
    vol_mm3 = float(shape.volume)
    mass_g = vol_mm3 * density_kg_m3 * 1e-6
    com = shape.center(bd.CenterOf.MASS)
    return {"volume_mm3": vol_mm3, "density_kg_m3": density_kg_m3, "mass_g": mass_g,
            "center_of_mass_mm": _v3(com)}


# --------------------------------------------------------------------------
# Min wall thickness (ray casting)
# --------------------------------------------------------------------------

def _tessellate_to_trimesh(shape: bd.Shape, *, tolerance: float, angular_tolerance: float,
                            faces: Sequence[bd.Face] | None = None) -> trimesh.Trimesh:
    if faces is not None and len(faces) == 0:
        return trimesh.Trimesh(vertices=np.zeros((0, 3)), faces=np.zeros((0, 3), dtype=np.int64), process=False)
    target = shape if faces is None else bd.Compound(children=list(faces))
    verts, tris = target.tessellate(tolerance, angular_tolerance)
    vertices = np.array([[v.X, v.Y, v.Z] for v in verts], dtype=float)
    faces_arr = np.array(tris, dtype=np.int64)
    return trimesh.Trimesh(vertices=vertices, faces=faces_arr, process=False)


def _ray_mesh_hits(mesh: trimesh.Trimesh, origins: np.ndarray, directions: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """First-hit distance per ray, using trimesh's intersector when it works.

    trimesh's default (non-pyembree) ``RayMeshIntersector`` builds an
    ``rtree`` bounding-volume tree; that package is not part of the pinned
    CAD env (ADR-001 §8 T1/T5 pins trimesh/PyVista/VTK only). This falls back
    to a vectorised Moeller-Trumbore ray/triangle test against every triangle
    -- O(rays x triangles), fine at the sample counts (hundreds-low
    thousands) and triangle counts (parts, not full assemblies) this is used
    for, but not a scalable general-purpose ray tracer.

    Returns ``(hit, distance)`` arrays, one row per ray; ``hit`` is False and
    ``distance`` is ``nan`` where nothing was struck.
    """
    n = len(origins)
    try:
        locations, index_ray, _ = mesh.ray.intersects_location(
            ray_origins=origins, ray_directions=directions, multiple_hits=False
        )
        dist = np.full(n, np.nan)
        hit = np.zeros(n, dtype=bool)
        if len(index_ray):
            d = np.linalg.norm(locations - origins[index_ray], axis=1)
            for i, r in enumerate(index_ray):
                if not hit[r] or d[i] < dist[r]:
                    dist[r] = d[i]
                    hit[r] = True
        return hit, dist
    except (ImportError, ModuleNotFoundError):
        pass  # rtree (or pyembree) unavailable -- fall back below.

    tri = mesh.triangles  # (T, 3, 3)
    v0, v1, v2 = tri[:, 0, :], tri[:, 1, :], tri[:, 2, :]
    e1 = v1 - v0
    e2 = v2 - v0
    eps = 1e-9
    dist = np.full(n, np.nan)
    hit = np.zeros(n, dtype=bool)
    for i in range(n):
        o, d = origins[i], directions[i]
        pvec = np.cross(d, e2)
        det = np.einsum("ij,ij->i", e1, pvec)
        valid = np.abs(det) > eps
        inv_det = np.zeros_like(det)
        inv_det[valid] = 1.0 / det[valid]
        tvec = o - v0
        u = np.einsum("ij,ij->i", tvec, pvec) * inv_det
        valid &= (u >= -1e-6) & (u <= 1 + 1e-6)
        qvec_full = np.cross(tvec, e1)
        v = np.einsum("ij,ij->i", d[None, :].repeat(len(tri), axis=0), qvec_full) * inv_det
        valid &= (v >= -1e-6) & (u + v <= 1 + 1e-6)
        t = np.einsum("ij,ij->i", e2, qvec_full) * inv_det
        valid &= t > 1e-6
        if valid.any():
            t_min = t[valid].min()
            dist[i] = t_min
            hit[i] = True
    return hit, dist


def min_wall_thickness(shape: bd.Shape, *, sample_count: int = 1500, tessellate_tolerance: float = 0.05,
                        angular_tolerance: float = 0.2, faces: Sequence[bd.Face] | None = None,
                        seed: int = 0, offset: float = 1e-4) -> dict[str, Any]:
    """Minimum wall thickness by ray casting from sampled surface points.

    Samples ``sample_count`` points on the (optionally face-restricted)
    tessellated surface, casts a ray from each point along its **inward**
    normal -- nudged ``offset`` mm inward first, so the ray never re-crosses
    the plane of the triangle it started on (a self-hit at distance
    ~``offset``, not the true opposite wall) -- and records the distance to
    the first further surface hit as the local wall thickness. The minimum
    over all hit samples is reported with its location. ``faces`` restricts
    only *where samples are taken from*; rays are always cast against the
    full ``shape`` so the true opposite wall is found even when it belongs
    to a different face than the one sampled (e.g. the inner cavity face
    under a sampled outer face).

    **Resolution limits** (state honestly, per FORGE-BRIEF §3.7):
    - This is a Monte Carlo estimate, not an exact minimum: a thinner spot
      smaller than the sampling density can be missed. Increase
      ``sample_count`` for small/thin features, and treat a passing result
      near the limit with suspicion.
    - Samples with no opposite-surface hit (rays exiting to infinity, e.g.
      near a convex silhouette edge) are excluded from ``hit_count`` and
      recorded separately; if ``hit_count`` is a small fraction of
      ``sample_count`` the shape may be mostly convex/open and this check is
      not meaningful for it.
    - Coarser ``tessellate_tolerance`` under-resolves curved walls and can
      both over- and under-estimate thickness; the default (0.05 mm) favours
      accuracy over speed.
    - Does not distinguish "thin wall" from "near-zero-thickness
      self-intersection" -- a shape that fails :func:`validity` or
      :func:`watertight_export` should be fixed before trusting this number.
    """
    rng = np.random.default_rng(seed)
    sample_mesh = _tessellate_to_trimesh(shape, tolerance=tessellate_tolerance,
                                          angular_tolerance=angular_tolerance, faces=faces)
    if len(sample_mesh.faces) == 0:
        return {"min_thickness_mm": None, "location_mm": None, "sample_count": 0, "hit_count": 0,
                "resolution_note": "no triangles to sample (empty face selection?)"}
    ray_mesh = sample_mesh if faces is None else _tessellate_to_trimesh(
        shape, tolerance=tessellate_tolerance, angular_tolerance=angular_tolerance, faces=None)

    points, face_idx = trimesh.sample.sample_surface(sample_mesh, sample_count, seed=int(rng.integers(0, 2**31 - 1)))
    normals = sample_mesh.face_normals[face_idx]
    origins = points - normals * offset  # nudge inward, continue inward -- see docstring
    directions = -normals

    hit, dist = _ray_mesh_hits(ray_mesh, origins, directions)
    hit_count = int(hit.sum())
    if hit_count == 0:
        return {"min_thickness_mm": None, "location_mm": None, "sample_count": sample_count, "hit_count": 0,
                "resolution_note": "no ray found an opposite wall; shape may be open/convex here"}

    # Correct for the inward starting nudge so the reported thickness is the
    # distance from the true (unnudged) surface point, not from `offset` in.
    valid_dist = dist[hit] + offset
    valid_points = points[hit]
    i_min = int(np.argmin(valid_dist))
    return {
        "min_thickness_mm": float(valid_dist[i_min]),
        "location_mm": tuple(round(float(x), 6) for x in valid_points[i_min]),
        "sample_count": int(sample_count),
        "hit_count": hit_count,
        "mean_thickness_mm": float(valid_dist.mean()),
        "resolution_note": (
            f"Monte Carlo ray cast, {sample_count} samples, tessellate_tolerance={tessellate_tolerance} mm; "
            "a thinner spot smaller than the sample density can be missed."
        ),
    }


# --------------------------------------------------------------------------
# Clearance / interference
# --------------------------------------------------------------------------

def clearance(shape_a: bd.Shape, shape_b: bd.Shape) -> dict[str, Any]:
    """Minimum distance between two solids.

    Backed by OCP ``BRepExtrema_DistShapeShape`` (build123d's
    ``distance_to_with_closest_points`` calls it directly): an exact
    BREP-to-BREP distance, not a sampled approximation. Zero means the
    shapes touch or overlap -- pair with :func:`interference` to tell
    "touching" from "penetrating".
    """
    dist, p_a, p_b = shape_a.distance_to_with_closest_points(shape_b)
    return {"distance_mm": float(dist), "point_a_mm": _v3(p_a), "point_b_mm": _v3(p_b)}


def interference(shape_a: bd.Shape, shape_b: bd.Shape) -> dict[str, Any]:
    """Whether two solids overlap, and by how much, via boolean intersection.

    ``shape_a.intersect(shape_b)`` returns the common solid(s) (or ``None``
    for no overlap); summing their volumes gives an exact overlap volume from
    OCCT's boolean kernel, not a sampled estimate.
    """
    common = shape_a.intersect(shape_b)
    if not common:
        return {"interferes": False, "overlap_volume_mm3": 0.0, "solid_count": 0}
    solids = common.solids() if hasattr(common, "solids") else [common]
    overlap = sum(float(s.volume) for s in solids)
    return {"interferes": overlap > 1e-9, "overlap_volume_mm3": overlap, "solid_count": len(solids)}


# --------------------------------------------------------------------------
# Draft angle
# --------------------------------------------------------------------------

def draft_angles(shape: bd.Shape, faces: Sequence[bd.Face], *, pull_direction: Vec3 = (0.0, 0.0, 1.0)) -> list[dict[str, Any]]:
    """Draft angle of each given face against ``pull_direction``.

    **Sign convention** (standard in mold-draft analysis): for a unit pull
    direction ``d`` and a face's outward unit normal ``n`` (outward is
    guaranteed for the faces of a valid, correctly-oriented build123d
    ``Solid``), the draft angle is ``asin(n . d)`` in degrees.
    - 0 deg: the face is parallel to the pull direction (a straight vertical
      wall -- zero draft, sticks in the mold).
    - positive: the face leans away from the cavity in the direction of
      pull -- a properly releasing face.
    - negative: an undercut in the pull direction -- the face will not
      release.
    Only pass faces that are actually moldable side walls (see
    :func:`select_side_faces` for a default selector); top/bottom faces
    nearly perpendicular to the pull axis do not have a meaningful draft
    angle and will read near +-90 deg here.
    """
    d = _unit(pull_direction)
    out: list[dict[str, Any]] = []
    all_faces = shape.faces()
    for face in faces:
        n = face.normal_at(face.center())
        n_arr = _unit((n.X, n.Y, n.Z))
        draft_deg = math.degrees(math.asin(max(-1.0, min(1.0, float(np.dot(n_arr, d))))))
        try:
            idx = all_faces.index(face)
        except ValueError:
            idx = -1
        out.append({
            "face_index": idx,
            "draft_deg": draft_deg,
            "area_mm2": float(face.area),
            "normal": tuple(round(float(x), 6) for x in n_arr),
        })
    return out


def select_side_faces(shape: bd.Shape, *, pull_direction: Vec3 = (0.0, 0.0, 1.0),
                       flat_tol_deg: float = 5.0) -> list[bd.Face]:
    """Default face selection for draft checks: planar walls roughly parallel
    to the pull axis (i.e. everything that is *not* a top/bottom/parting
    face). ``flat_tol_deg`` excludes faces within that many degrees of
    perpendicular-to-pull (those are the flat top/bottom/parting faces where
    "draft" is not a meaningful concept). This is a convenience default --
    a real part should tag its actual moldable faces explicitly (e.g. in the
    part module) rather than relying on this heuristic alone.
    """
    d = _unit(pull_direction)
    tol_dot = math.sin(math.radians(90.0 - flat_tol_deg))
    selected = []
    for face in shape.faces():
        if not face.is_planar:
            continue
        n = face.normal_at(face.center())
        n_arr = _unit((n.X, n.Y, n.Z))
        if abs(float(np.dot(n_arr, d))) < tol_dot:
            selected.append(face)
    return selected


# --------------------------------------------------------------------------
# Min radius (fillets)
# --------------------------------------------------------------------------

def min_radius(shape: bd.Shape, *, concave_only: bool = True) -> list[dict[str, Any]]:
    """Radius of every cylindrical face, e.g. to find the smallest internal
    fillet.

    Uses ``Face.radius`` (cylindrical faces only) and ``Face.is_circular_concave``
    to tell an internal fillet/round (concave -- material curves away from
    the fillet into the part) from an external round-over or boss/pin
    (convex). ``concave_only=True`` (the default) matches "minimum
    concave/fillet radius" in the brief; pass ``False`` to also see convex
    rounds.

    **Limitation:** toroidal (compound-curvature, e.g. a swept corner
    blend) and spherical fillet faces are not measured -- only single-radius
    cylindrical faces. A part with toroidal corner blends needs a visual
    inspection (``inspecting-renders``) in addition to this check.
    """
    out: list[dict[str, Any]] = []
    for i, face in enumerate(shape.faces()):
        if face.geom_type != bd.GeomType.CYLINDER:
            continue
        try:
            concave = bool(face.is_circular_concave)
        except Exception:
            concave = None
        if concave_only and concave is not True:
            continue
        out.append({
            "face_index": i,
            "radius_mm": float(face.radius),
            "is_concave": concave,
            "area_mm2": float(face.area),
        })
    return out


# --------------------------------------------------------------------------
# Hole-to-edge distance
# --------------------------------------------------------------------------

def _cylinder_axis(face: bd.Face) -> tuple[Vec3, Vec3, float]:
    """Axis point, axis direction and radius of a cylindrical face, via OCP
    ``BRepAdaptor_Surface`` (not the face's parametric centroid, which is
    only on-axis for a full 360 deg patch)."""
    adaptor = BRepAdaptor_Surface(face.wrapped, True)
    if adaptor.GetType() != GeomAbs_Cylinder:
        raise ValueError("face is not cylindrical")
    cyl = adaptor.Cylinder()
    ax = cyl.Axis()
    loc = ax.Location()
    dirv = ax.Direction()
    return (loc.X(), loc.Y(), loc.Z()), (dirv.X(), dirv.Y(), dirv.Z()), float(cyl.Radius())


def find_holes(shape: bd.Shape, *, max_boundary_edges: int = 3) -> list[dict[str, Any]]:
    """Cylindrical faces that look like a full-round hole rather than a
    fillet: concave, and bounded by at most ``max_boundary_edges`` edges (a
    full-revolution cylindrical face has 2 circular rims plus at most one
    seam edge; a partial cylindrical fillet patch is bounded by 4+ edges).
    This is a documented heuristic, not a feature-recognition guarantee --
    verify against the part's known hole count.
    """
    out: list[dict[str, Any]] = []
    for i, face in enumerate(shape.faces()):
        if face.geom_type != bd.GeomType.CYLINDER:
            continue
        if getattr(face, "is_circular_concave", False) is not True:
            continue
        if len(face.edges()) > max_boundary_edges:
            continue
        point, axis, radius = _cylinder_axis(face)
        out.append({"face_index": i, "axis_point_mm": tuple(round(x, 6) for x in point),
                     "axis_direction": tuple(round(x, 6) for x in axis), "radius_mm": radius})
    return out


def hole_edge_distance(shape: bd.Shape, hole_face: bd.Face, boundary_face: bd.Face) -> dict[str, Any]:
    """Distance from a hole's axis (and from its wall) to a boundary face's
    outer edge.

    Finds the hole's axis (point + direction) via OCP ``BRepAdaptor_Surface``
    (see :func:`_cylinder_axis`), intersects that axis line with
    ``boundary_face``'s plane to get the point where the hole actually pierces
    that face (a raw axis point can sit anywhere along the cylinder, including
    beyond the face -- using it directly would mix an out-of-plane offset into
    the distance), then measures the in-plane distance from that pierce point
    to the face's outer wire via ``distance_to_with_closest_points`` (OCP
    ``BRepExtrema_DistShapeShape``, the same primitive :func:`clearance` uses).
    ``wall_to_edge_mm`` (axis distance minus hole radius) is the number DFM
    hole-to-edge rules are usually stated against. Assumes ``boundary_face``
    is planar.
    """
    axis_point, axis_dir, radius = _cylinder_axis(hole_face)
    if not boundary_face.is_planar:
        raise ValueError("hole_edge_distance requires a planar boundary_face")
    plane_point = boundary_face.center()
    plane_normal = _unit(tuple(boundary_face.normal_at(plane_point)))
    ap = np.asarray(axis_point, dtype=float)
    ad = _unit(axis_dir)
    denom = float(np.dot(ad, plane_normal))
    if abs(denom) < 1e-9:
        raise ValueError("hole axis is parallel to boundary_face's plane; cannot find a pierce point")
    pp = np.array([plane_point.X, plane_point.Y, plane_point.Z])
    t = float(np.dot(pp - ap, plane_normal)) / denom
    pierce = ap + t * ad

    vertex = bd.Vertex(*[float(x) for x in pierce])
    outer = boundary_face.outer_wire()
    dist, p_axis, p_edge = vertex.distance_to_with_closest_points(outer)
    return {
        "axis_point_mm": tuple(round(x, 6) for x in axis_point),
        "pierce_point_mm": tuple(round(float(x), 6) for x in pierce),
        "hole_radius_mm": radius,
        "axis_to_edge_mm": float(dist),
        "wall_to_edge_mm": float(dist) - radius,
        "nearest_edge_point_mm": _v3(p_edge),
    }


# --------------------------------------------------------------------------
# Boss / rib thickness
# --------------------------------------------------------------------------

def boss_rib_thickness(shape: bd.Shape, faces: Sequence[bd.Face], *, nominal_wall_mm: float,
                        sample_count: int = 400, tessellate_tolerance: float = 0.05,
                        seed: int = 0) -> dict[str, Any]:
    """Measured thickness of a boss/rib feature (via :func:`min_wall_thickness`
    restricted to ``faces``) expressed as a ratio to the surrounding nominal
    wall. DFM rules (checking-dfm) cap this ratio (e.g. injection-molded ribs
    at most ~0.6x the nominal wall, R5c) to control sink marks.
    """
    result = min_wall_thickness(shape, sample_count=sample_count,
                                 tessellate_tolerance=tessellate_tolerance, faces=faces, seed=seed)
    thickness = result.get("min_thickness_mm")
    ratio = (thickness / nominal_wall_mm) if thickness is not None and nominal_wall_mm else None
    return {**result, "nominal_wall_mm": nominal_wall_mm, "ratio": ratio}
