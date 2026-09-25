# Measurement algorithms and their resolution limits

Full docstrings live on each function in `plugins/forge/lib/forge_cad/measure.py`
(import it and `help()` any name for the authoritative text). This is the
short version, with what to do when a number is close to a limit.

| Check family | Function | Method | Known limit |
|---|---|---|---|
| `geometry.validity` | `validity` | OCP `BRepCheck_Analyzer` on the live shape, plus `is_manifold` | Exact -- a topological/geometric checker, not sampled. |
| `geometry.watertight` | `watertight_export` | STL export, trimesh `is_watertight`/`is_winding_consistent`/`euler_number` after vertex welding | A valid BREP can still tessellate non-watertight at a coarse `tolerance_mm`; tighten it and re-check before treating a fail as a real gap. |
| `geometry.bbox` / `volume` / `mass` | `bounding_box` / `volume` / `mass_properties` | Exact BREP integration (OCCT mass properties) | Exact to solver tolerance (~1e-6 relative); `mass` needs a density from `params/params.toml`, never hard-coded. |
| `geometry.min_wall` / `geometry.boss_rib` | `min_wall_thickness` / `boss_rib_thickness` | Monte Carlo: sample points on the tessellated surface, ray-cast along the inward normal to the opposite wall | Statistical, not exhaustive -- a thinner spot smaller than the sample density can be missed. Raise `sample_count` for small/thin features and treat a pass close to the limit with suspicion. A sample with no opposite-wall hit is excluded from `hit_count`; if most samples miss, the shape is mostly open/convex there and the check isn't meaningful. |
| `geometry.clearance` / `geometry.interference` | `clearance` / `interference` | OCP `BRepExtrema_DistShapeShape` (clearance) / boolean common volume (interference) | Exact BREP-to-BREP; zero clearance means touching *or* overlapping -- always pair the two checks. |
| `geometry.draft` | `draft_angles` | `asin(face_normal . pull_direction)`, degrees | Assumes outward face normals (true for a valid, correctly oriented `Solid`). Only meaningful on faces roughly parallel to the pull axis; `select_side_faces` excludes near-perpendicular (top/bottom) faces by default, but a part should tag its real moldable faces explicitly where the heuristic could be wrong. |
| `geometry.min_radius` | `min_radius` | `Face.radius` (cylindrical faces only) filtered by `Face.is_circular_concave` | Toroidal/spherical (compound-curvature) fillets are not measured -- only single-radius cylindrical faces. Cross-check those with `inspecting-renders`. |
| `geometry.hole_edge` | `hole_edge_distance` / `find_holes` | Hole axis via OCP `BRepAdaptor_Surface`, axis-plane intersection to find the pierce point on the boundary face, then `BRepExtrema_DistShapeShape` to its outer wire | `find_holes` is a heuristic (concave cylindrical face, <=3 boundary edges) that can miss unusual hole shapes or misclassify a very short, wide fillet as a hole -- verify the count against the part's known hole list. |

**Ray-cast fallback note.** trimesh's built-in ray intersector needs the
`rtree` package, which is not in the pinned CAD env (ADR-001 §8). When it is
unavailable, `min_wall_thickness`/`boss_rib_thickness` fall back to a
vectorised Moeller-Trumbore ray/triangle test against every mesh triangle --
correct, but O(rays x triangles); keep `sample_count` and part complexity
reasonable (hundreds-to-low-thousands of samples against a single part's
mesh, not a full assembly).
