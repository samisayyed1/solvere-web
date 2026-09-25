---
name: running-fea
description: Run a linear-static FEA of a solid part (STEP or build123d → gmsh 2nd-order tets → CalculiX C3D10). Supports and loads are declared on named CAD faces; the run includes a mandatory closed-form hand-calc cross-check, a ≥3-level mesh convergence study, stress-singularity detection, a reaction-balance check, and a safety factor with the location of the peak. Use when the user asks to "run FEA", "check the stress", "will this break", "safety factor", "deflection under load", "mesh convergence", "stress concentration", or when analysis/fea/*.toml changes. Also fires from the simulation.md path rule on analysis/**. Do NOT use for tolerance stacks (stacking-tolerances), contact/assemblies, plasticity, buckling, fatigue, modal/dynamic or thermal analysis -- this skill refuses those (see "What this skill refuses").
paths:
  - "analysis/fea/**"
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(${CLAUDE_SKILL_DIR}/scripts/verify.py:*), Bash(forge-python ${CLAUDE_SKILL_DIR}/scripts/verify.py:*)
---

# Running FEA

**Non-negotiable rules, read first:**

1. **Every case is a file:** `analysis/fea/<case>.toml`. It declares:
   - geometry (STEP or a build123d script);
   - material (from `params/params.toml`, every value with a `source`; no invented properties);
   - supports and loads on **named CAD faces**;
   - ≥ 3 mesh sizes;
   - ≥ 1 hand calc;
   - the requirement.

   `verify.py` refuses a case with a missing, unknown or misspelled key: exit 2, never a silent pass.
2. **The hand-calc cross-check is mandatory.**
   - Every case compares its finest-mesh result with a closed form (`references/hand-calcs.md`) within a stated tolerance.
   - If no closed form bounds the problem, it is out of scope. Either split it into sub-problems that do have one, or say so. Do not run it "just to see".
3. **The mesh convergence study is mandatory.** At least 3 levels, each finer by a ratio of at least 1.2. The % change between the two finest levels must be within tolerance for every hand-calc quantity and for the peak stress that sets the safety factor.
4. **Singular stresses are detected, not trusted.**
   - A peak that keeps growing with refinement (re-entrant corner, point load, clamped-face edge) sets `stress_singularity_suspected` and fails the check.
   - Fix the idealisation (fillet, load patch), or exclude the zone with a written `reason` that a reviewer can challenge.
5. **Reactions must balance the applied loads within 0.5 %** (force and moment), on every level. **Under-constrained models are errors.**
   - ccx 2.23 does not always detect a singular stiffness matrix: it printed "Job finished" with garbage results.
   - So a rigid-body rank check runs before every solve and names the free modes.
6. **Evidence level:**
   - **L2 only** when every hand calc, every convergence check, the singularity check, the reaction balance, the small-deflection check and the tet10 ordering check pass.
   - Otherwise **L1**.
   - A failing safety factor does not lower the level: it is a design failure, not bad evidence.
   - FEA is never "validated". That needs L4, physical test data.
7. **State the limits in every report:** linear elastic, small deflection and strain, static, one solid, no contact, preload or thermal load. The script writes them into `notes`; repeat them when summarising for the user.
8. **Report margins and locations, not verdicts.** Examples: "SF 1.34 vs 1.5 (−10.7 %) at x=…, y=…, z=… mm, 0.0 mm from 'load:torque'". Specific margins at a named location steer redesign better than pass/fail (R3, physics in the loop).

## General case file

Example: a plate with a hole, modelled as 1/8 with symmetry. This is the known-answer test case.

```toml
[case]
name = "plate_hole"
description = "200 x 50 x 2 mm plate, central 10 mm hole, 5 kN axial"

[geometry]
build123d = "cad/plate.py"     # or: step = "cad/out/plate.step"
object = "part"                # module-level Part, or a zero-argument function returning one (default "part")

[material]
params = "materials.steel"     # reads params.toml leaves E, nu, yield, density (value/unit/source/status)
# inline alternative: E_MPa, nu, yield_MPa, density_kg_m3, source  (source is mandatory)

[[bc]]
name = "sym_x"
type = "symmetry"              # fixed (all 3) | symmetry (normal dof of an axis plane) | displacement (dofs=[1,2,3], value_mm)
faces = { plane = "x", at = "min" }
[[bc]]
name = "sym_y"
type = "symmetry"
faces = { plane = "y", at = "min" }
[[bc]]
name = "sym_z"
type = "symmetry"
faces = { plane = "z", at = "min" }

[[load]]
name = "tension"
type = "force"                 # force (vector_n, uniform traction) | pressure (pressure_mpa, +ve into surface)
faces = { plane = "x", at = "max" }   # | torque (torque_nmm, axis, center_mm?) | point_force (vector_n, at_mm) -- singular
vector_n = [1250.0, 0.0, 0.0]

[[refine]]                     # optional; local size = size_factor * h near the faces, grows to h at dist_max_mm
name = "hole"
faces = { cylinder_radius_mm = 5.0, axis = "z" }
size_factor = 0.08
dist_min_mm = 0.5
dist_max_mm = 10.0

# [stress]                     # optional; nodes within distance_mm of these faces don't set the safety factor
# exclude = [{ faces = { plane = "x", at = "min" }, distance_mm = 10.0, reason = "clamped-root edge singularity, Saint-Venant zone" }]

[mesh]
sizes_mm = [4.0, 2.8, 2.0]     # >= 3 global sizes, each step ratio >= 1.2
convergence_tol_pct = 2.0      # % change between the two finest levels, every hand-calc quantity
# stress_convergence_tol_pct = 2.0   # for the peak von Mises (defaults to convergence_tol_pct)
# max_nodes = 400000

[[hand_calc]]
name = "hole_peak_stress"
formula = "plate_hole_tension_peak_stress"      # see references/hand-calcs.md, or "custom"
inputs = { gross_stress_mpa = 50.0, width_mm = 50.0, hole_diameter_mm = 10.0 }
fea = { quantity = "peak_principal" }           # peak_von_mises | peak_principal | max_displacement |
tolerance_pct = 10.0                            # face_mean_displacement (faces, component x|y|z|-x|..|magnitude) |
                                                # face_rotation (faces, axis, center_mm?)
[requirement]
min_safety_factor = 1.5
# max_reaction_imbalance_pct = 0.5   # may tighten, never loosen

# [validity]
# max_displacement_ratio = 0.1       # max |u| / smallest bbox dimension (small-deflection proxy)
```

**Face selectors** are written `faces = { ... }`. They accept `plane` + `at`, outward `normal`, `cylinder_radius_mm` (+ `axis`), `within_box_mm`, `contains_point_mm`, `type`, `tol_mm`, `angle_tol_deg` and `expect_count`. A list of selectors means their union. A selector that matches no face is an error that lists every face of the part. See `references/face-selectors.md`.

**Named hand-calc formulas:**
- `cantilever_end_load_deflection`
- `cantilever_bending_stress`
- `simply_supported_center_load_deflection`
- `plate_hole_tension_peak_stress` (Peterson / Heywood / Roark finite-width Kt)
- `tube_torsion_twist`
- `tube_torsion_peak_von_mises`
- `thick_cylinder_internal_pressure_hoop_stress` (Lamé)
- `custom`: needs `value`, `unit`, `expression`, `reference`, and is flagged "re-derive before trusting".

The hand calc's unit must match the FEA quantity's unit. Formulas, derivations, validity limits and citations are in `references/hand-calcs.md`.

## Running

```
forge-python ${CLAUDE_SKILL_DIR}/scripts/verify.py --project <root> [--changed analysis/fea/<case>.toml]
```

- **It is slow.** Every level is a real gmsh mesh and CalculiX solve: 2–12 s per case for the reference cases (≤ 42 k nodes), minutes for fine meshes of real parts. `--fast` is accepted but does not skip physics.
- **No cases** means `[SKIP]`, exit 0.
- **Exit codes:** 0 pass, 1 fail, 2 error. Errors include a malformed case, an unmatched selector, an under-constrained model, a CalculiX `*ERROR`, a missing ccx, or a non-finite or absurd result.

**Outputs:**
- `out/verify/sim.fea_<case>.json` (`forge.check/1`), with these measurements (location given where applicable):
  - `hand_calc_<name>_diff_pct` and `convergence_<name>_pct_change` for each hand calc;
  - `stress_convergence_pct_change`;
  - `stress_singularity_suspected`;
  - `safety_factor` (location of the peak);
  - `reaction_balance_pct`;
  - `small_deflection_ratio` (location of max |u|);
  - `tet10_ordering_max_midside_deviation`.
- `notes` in the same file carry: material provenance, the geometry sha256, mass, each hand calc with its formula and reference, a per-level table, the peak von Mises / max principal / max displacement with locations, the unexcluded peak and its trend, any diverging hot spots, the supports and loads, and the validity limits.
- `out/fea/<case>/summary.json` holds all of the above plus Richardson estimates and observed orders.
- `out/fea/<case>/level<i>_h<h>mm/` holds `mesh.msh`, `model.inp`, `model.frd`, `model.dat`, `model.ccx.log` and `level.json`: face descriptions, load resultants, the load absorbed by supports, and the ordering proof.

## Pipeline (`scripts/general_fea.py`)

1. **Geometry.**
   - A STEP file is used as-is.
   - A build123d script is executed and its `object` exported to `out/fea/<case>/geometry.step`. It runs the project's own code; only point at scripts you trust.
   - Exactly one solid.
2. **Faces.** Every selector is resolved on the OCC model inside gmsh at every level. The outward normal is decided by asking the solid; cylinder radius and axis come from the principal curvatures.
3. **Mesh.**
   - gmsh Delaunay 3-D, 2nd order: curved mid-edge nodes on the geometry, `HighOrderOptimize = 2`.
   - `MeshSizeMax = h`, with a `Distance` + `Threshold` field per `[[refine]]` zone, scaled with h.
   - Refused if any element's scaled Jacobian is ≤ 0, or the mesh exceeds `max_nodes`.
4. **Node order.**
   - gmsh tet10 → C3D10 is `[0,1,2,3,4,5,6,7,9,8]`: the last two mid-edge nodes swap.
   - Proven by mid-edge geometry, a CalculiX negative control (`nonpositive jacobian` without the swap), and an exact constant-stress patch test (see `references/tet10-node-ordering.md`).
   - Re-checked on every mesh.
5. **Loads.**
   - Consistent nodal forces from 7-point tri6 quadrature over the curved faces. (Equal nodal shares fail the patch test by > 5 %.)
   - Pressure uses outward normals oriented against the owning tetrahedron.
   - Torque uses τ ∝ r, so the resultant torque is exact and the net force is zero.
   - Load on DOFs that a support also constrains, e.g. a pressure face meeting a symmetry plane, is removed and reported.
   - A face that is both loaded and supported is refused.
6. **Pre-solve checks.** The rigid-body mode rank of the constrained DOFs must be 6, otherwise error, naming the free modes.
7. **Solve.**
   - CalculiX `*STATIC`, output `*NODE FILE U, RF` and `*EL FILE S`, multi-threaded.
   - Any `*ERROR`, "singular" or "zero pivot" line, a missing "Job finished", or non-finite output is an error.
8. **Post-processing.**
   - Nodal von Mises and principal stresses.
   - The assessed peak (outside declared exclusions) and the global peak, both with location and nearest named face.
   - Max |u| with location.
   - Area-weighted face mean displacement, and least-squares face rotation.
   - Reactions summed over the constrained DOFs only, as force and moment balance about the centroid.
9. **Study.**
   - Hand-calc difference at the finest level.
   - % change, observed order and Richardson estimate for each quantity.
   - Hot-spot divergence test in a fixed ball of radius ½ h₁ around each tracked point (see `references/convergence-and-singularities.md`).
   - Safety factor = yield / assessed peak von Mises.

## Verified accuracy (known-answer tests, `tests/mech2/test_running_fea_general.py`)

| case | quantity | hand calc | FEA (finest) | diff | converged |
|---|---|---|---|---|---|
| 100×10×10 steel cantilever, 100 N tip | tip deflection | 0.190476 mm (EB; Timoshenko shear +0.77 % noted) | 0.190442 mm | −0.02 % | 0.07 % |
| same, 10 mm from root (exclusion edge) | bending stress | 54.00 MPa | 54.10 MPa | +0.19 % | 0.25 % |
| plate W=50, d=10 (d/W = 0.20), σ_gross 50 MPa | peak σ₁ at hole edge | 157.44 MPa (Peterson Kt_n 2.519 × 62.5) | 158.89 MPa at (0.05, 5.00, 0.12) | +0.92 % | 0.03 % |
| Ø20/Ø16×100 tube, 100 N·m | twist | 0.013350 rad | 0.013350 rad | −0.0001 % | 0.0002 % |
| same | peak von Mises | 186.76 MPa | 187.06 MPa | +0.16 % | 0.22 % |
| Lamé a=10, b=15, p=50 MPa | hoop stress | 130.0 MPa | 131.14 MPa | +0.87 % | 0.93 % |

Reaction imbalance was ≤ 0.0012 % in every case. Seeded-wrong cases fail as they must: under-refined mesh, under-constrained model, wrong hand calc, singular point load, and malformed cases.

## What this skill refuses

- A case without a hand calc, with fewer than 3 mesh levels, with refinement steps below a ratio of 1.2, with unknown keys, or with a material value that has no `source`: exit 2.
- A selector that matches nothing, or a face that is both loaded and supported: exit 2.
- An under-constrained model: exit 2, before solving, naming the free rigid-body modes.
- Assemblies or multiple solids (no contact), plasticity, large deflection, buckling, modal/dynamic, fatigue, thermal and gravity loads. See `references/limits-and-extension.md`.
- Reporting L2 when any evidence check failed, or calling any result "validated".

## Legacy box path

A case whose `[geometry]` has `length_mm`, `width_mm` and `height_mm`, instead of `step` or `build123d`, runs the original structured-hex C3D8I cantilever (`scripts/mesh_and_solve.py`). That schema uses `[load] force_n`, `[mesh] levels = [[nx, ny, nz], …]` and `[hand_calc] deflection_tolerance_pct / stress_tolerance_pct`.

It is kept so existing cases keep working, and its tests still pass. The general path supersedes it: the same beam gives −0.02 % against Euler–Bernoulli. Write new cases in the general schema.
