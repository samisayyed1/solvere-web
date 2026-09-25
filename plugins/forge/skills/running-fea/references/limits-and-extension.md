# Limits of validity and how to extend this skill

## What the general (tet10) path has proven

Scripts: `general_fea.py`, `face_select.py`, `tet10.py`, `handcalc.py`, `general_report.py`.

- **Geometry:** any single closed solid from a STEP file or a build123d script (`object = <Part or zero-arg function>`), in mm. The known-answer tests cover a box, a plate with a hole (1/8 symmetric model), a thin-walled tube (STEP input) and a quarter thick cylinder.
- **Element:** C3D10, the 10-node quadratic tetrahedron with curved mid-edge nodes on the geometry. The gmsh → CalculiX permutation is proven in `tet10-node-ordering.md`.
- **Supports:**
  - `fixed`: all 3 translations;
  - `symmetry`: the normal translation on an axis-aligned plane;
  - `displacement`: chosen global DOFs, optionally non-zero.
  - A rigid-body rank check runs before every solve.
- **Loads:**
  - `force`: uniform traction with a given resultant;
  - `pressure`: along the outward normal, positive into the surface;
  - `torque`: Saint-Venant τ ∝ r about an axis through the face centroid or `center_mm`;
  - `point_force`: singular by construction and always tracked.
  - All surface loads are consistent tri6 nodal forces.
- **Material:** linear elastic, isotropic, from `params/params.toml` (E, ν, yield, density, each with a source) or inline with `source`.
- **Analysis:** `*STATIC`, one step, linear geometry.

## Known limits (stated in every report)

- **Linear elastic, small deflection, small strain.**
  - `small_deflection_ratio` = max |u| / smallest bounding-box dimension must be ≤ 0.1 (`[validity].max_displacement_ratio`).
  - That is a coarse proxy. For thin plates and shells, deflection comparable to the thickness already needs a nonlinear (membrane) analysis.
- **No plasticity.** A safety factor below 1 means first yield somewhere, not collapse. The linear stress above yield is not a real stress.
- **No contact, bolts, preload, friction, assemblies** (exactly one solid) **or thermal loads.**
- **No gravity or inertial loads.** Density is used only to report mass.
- **Stress reporting.**
  - Stresses are CalculiX nodal values: extrapolated from integration points and averaged over the elements sharing a node.
  - Peaks on coarse meshes are therefore smoothed, which is why convergence is checked on the peak itself.
  - The `.frd` file carries 6 significant digits.
- **Static strength only.** Fatigue, buckling, modal and dynamic analyses are out of scope. A converged linear static stress is an *input* to a fatigue assessment, not the assessment.
- **Symmetry** is only on axis-aligned planes.
- **Solver checks.**
  - ccx 2.23 with SPOOLES does **not** reliably detect a singular stiffness matrix. It printed "Job finished" for an unconstrained model (|u| ≈ 1e10 mm) and for a partly constrained one (plausible-looking numbers).
  - The rigid-body rank check before solving is therefore the guard, not the solver.
  - As a backstop, a displacement larger than 10 × the part size is an error.
- **Evidence level L2 at most.** Physical test data gives L4; certification or sign-off gives L5.

## Extending

**A new load or support type:**
1. Add it to `build_loads` / `build_constraints` with a matching schema key.
2. Add a known-answer case with a closed form that exercises it, as the Lamé case does for `pressure` and the tube does for `torque`.
3. Add a seeded-wrong case to `tests/mech2/test_running_fea_general.py`.

**A new hand-calc formula:** add a function to `handcalc.py` with a docstring citation and a pure-number unit test in `test_running_fea_general_units.py`. Mark any reference you did not personally read as not re-verified.

**Gravity:** use CalculiX `*DLOAD, EALL, GRAV` with `*DENSITY` in t/mm³. The reaction balance needs the FE volume, which calls for a degree-3 tet10 quadrature (the Jacobian of a curved tet10 is cubic). Do not reuse the OCC volume.

**Shells or beams for thin parts:** a different element family, a different node ordering, and new proofs. Do not reuse C3D10 for walls with fewer than 2 elements through the thickness without a convergence study that shows it works.

## The structured-hex BOX path (legacy)

`mesh_and_solve.py` handles a rectangular prismatic cantilever with a structured C3D8I hex mesh. It is still used for cases with `[geometry] length_mm/width_mm/height_mm` and keeps its original tests (`tests/mech2/test_running_fea.py`).

The general path covers the same case (−0.02 % vs Euler–Bernoulli) and more. New cases should use the general schema. The box path stays only so that existing case files keep working.
