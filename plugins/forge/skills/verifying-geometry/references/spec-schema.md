# `requirements/geometry/<part>.toml` schema

One file per part (or per assembly pair). `scripts/verify.py` reads every
file in `requirements/geometry/`, builds each part's geometry from its
build123d module, and runs the listed check families through
`forge_cad.measure`. Every numeric limit must trace to a `REQ-<AREA>-<NNN>`
in `requirements/requirements.md` (CONTRACTS §6) via `requirement = "..."`.

```toml
[part]
name = "enclosure_base"        # slug; used in check_id and out/verify/ filenames
module = "cad/enclosure_base.py"  # relative to the project root; exposes build()/PART
pull_direction = [0, 0, 1]     # optional, default [0,0,1]; used by geometry.draft

[[check]]
family = "geometry.validity"     # OCP BRepCheck_Analyzer + manifoldness
requirement = "REQ-MECH-001"

[[check]]
family = "geometry.watertight"   # STL export + trimesh is_watertight
requirement = "REQ-MECH-001"
tolerance_mm = 0.05              # optional, default 0.05

[[check]]
family = "geometry.bbox"
requirement = "REQ-MECH-002"
axis = "x"                       # x | y | z
min_mm = 39.9
max_mm = 40.1
# or: min_mm_param = "enclosure.length"   (params/params.toml key; CONTRACTS §2)

[[check]]
family = "geometry.volume"
requirement = "REQ-MECH-003"
min_mm3 = 7000
max_mm3 = 9000

[[check]]
family = "geometry.mass"
requirement = "REQ-MECH-003"
density_kg_m3 = 1200             # or density_kg_m3_param = "material.density"
max_g = 12.0

[[check]]
family = "geometry.min_wall"
requirement = "REQ-MECH-004"
min_mm = 2.0                     # or min_mm_param = "enclosure.wall_thickness"
sample_count = 1500              # optional, default 1500 (--fast caps at 300)
faces = [3, 4, 5]                # optional face-index list; default: whole shape

[[check]]
family = "geometry.clearance"
requirement = "REQ-MECH-005"
other_module = "cad/lid.py"      # the mating part
min_mm = 0.2

[[check]]
family = "geometry.interference"
requirement = "REQ-MECH-005"
other_module = "cad/lid.py"      # always checked for exactly 0 overlap

[[check]]
family = "geometry.draft"
requirement = "REQ-MECH-006"
min_deg = 1.0
faces = "auto"                   # "auto" (select_side_faces) or an index list

[[check]]
family = "geometry.min_radius"
requirement = "REQ-MECH-007"
min_mm = 0.5
concave_only = true              # optional, default true (internal fillets only)

[[check]]
family = "geometry.hole_edge"
requirement = "REQ-MECH-008"
min_mm = 3.0
boundary_face = "top"            # "top" | "bottom" (by Z); checks every hole found

[[check]]
family = "geometry.boss_rib"
requirement = "REQ-MECH-009"
nominal_wall_mm = 2.0
max_ratio = 0.6
faces = [12, 13]                 # required: the boss/rib's own faces
```

**`_param` alternative.** Any numeric field (`min_mm`, `max_mm`, `density_kg_m3`,
`nominal_wall_mm`, ...) can instead be given as `<field>_param = "dotted.key"`,
resolved against `params/params.toml`'s `.value` (CONTRACTS §2) -- so a limit
tracks the same single source of truth the part was built from, instead of a
second hard-coded copy.

**Face indices** are the position of a face in `shape.faces()` for that
loaded part -- stable within one `load_part()` call, not a persistent ID.
Get them once (e.g. with `inspect-part`/build123d-mcp `inspect_part`, or a
short forge-python snippet) and pin them in the spec; if the part is
restructured, re-derive them.

**check_id.** Each check family writes `out/verify/<family>.<part-name>.json`,
e.g. `geometry.min_wall.enclosure_base.json` -- the part-name suffix is what
keeps two parts' checks from overwriting each other's result file.
