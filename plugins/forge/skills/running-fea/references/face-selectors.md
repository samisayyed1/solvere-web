# Face selectors (`scripts/face_select.py`)

Supports, loads, refinement zones, stress-exclusion zones and hand-calc probes all name **CAD faces** by geometry. They never name mesh node numbers: those change at every refinement level, and nobody can review them.

- **Evaluation.** Selectors are evaluated inside gmsh on the imported STEP solid, once per level. The same selector must pick the same faces at every level.
- **Mesh sets.** A face's node set includes its boundary edges and vertices. Its surface elements are the 6-node triangles gmsh put on it.

## Syntax

`faces = { ... }` is one selector, and every key in it must hold (AND). `faces = [ {...}, {...} ]` is the union (OR).

| key | meaning |
|---|---|
| `plane = "x"\|"y"\|"z"` + `at = "min"\|"max"\|<mm>` | a planar face normal to that axis, lying at the part's bounding-box min/max or at the given coordinate |
| `normal = [nx, ny, nz]` | a planar face whose **outward** normal is within `angle_tol_deg` of this direction. Outward is decided by asking the solid which side of the face is material. |
| `cylinder_radius_mm = r` (+ optional `axis = "x"\|"y"\|"z"\|[ax, ay, az]`) | a cylindrical face of radius r ± `tol_mm` (from the principal curvatures), optionally with its axis parallel to the given direction. Matches holes and bosses alike. |
| `within_box_mm = [x0, y0, z0, x1, y1, z1]` | the face's bounding box lies inside this box |
| `contains_point_mm = [x, y, z]` | the face passes within `tol_mm` of this point (trimmed face, not the untrimmed surface) |
| `type = "plane"\|"cylinder"\|"cone"\|"sphere"\|"torus"\|"bspline surface"\|...` | the OCC surface type as gmsh reports it |
| `tol_mm` (default 0.01) | position / radius tolerance |
| `angle_tol_deg` (default 1.0) | normal / axis tolerance |
| `expect_count = n` | guard: fail unless exactly n faces match (recommended on real parts) |

## Rules

- A selector that matches **no face** is an error (exit 2). The error lists every face with its type, normal or radius, bounding box and area, so the selector can be corrected from the message.
- Unknown keys are errors, so a typo cannot silently widen or narrow a selection.
- `at` without `plane`, and `axis` without `cylinder_radius_mm`, are errors.
- `symmetry` supports need a single `plane = ...` selector, because the constrained degree of freedom comes from that axis. Symmetry on an inclined plane is out of scope; it would need `*TRANSFORM`.
- A CAD face that is both loaded and supported is refused.
  - A loaded face that only *shares an edge* with a support is allowed; this happens on every symmetry model.
  - Load components on constrained DOFs are removed, because the support takes them directly. The removed amount is reported in `level.json` as "(absorbed by supports)".

## Build123d tip

build123d centres primitives on the origin unless you pass `align=`. `at = "min" | "max"` makes selections independent of that choice. Use numeric `at` only when the coordinate is itself a parameter.
