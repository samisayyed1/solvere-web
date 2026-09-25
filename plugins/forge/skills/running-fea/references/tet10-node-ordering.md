# gmsh tet10 → CalculiX C3D10 node ordering

This file records the permutation the general path uses and the evidence for it. It was established by experiment on gmsh 4.15.2 and ccx 2.23. It was not copied from a secondary source: the previous builder trusted such a source and got `*ERROR in e_c3d: nonpositive jacobian`.

## The two conventions (0-based local node numbers)

| local node | gmsh "Tetrahedron 10" (type 11) | CalculiX / Abaqus C3D10 |
|---|---|---|
| 0–3 | corners | corners (same order) |
| 4 | mid-edge 0–1 | mid-edge 0–1 |
| 5 | mid-edge 1–2 | mid-edge 1–2 |
| 6 | mid-edge 2–0 | mid-edge 2–0 |
| 7 | mid-edge 3–0 | mid-edge 0–3 |
| **8** | **mid-edge 3–2** | **mid-edge 1–3** |
| **9** | **mid-edge 3–1** | **mid-edge 2–3** |

So `ccx_conn = gmsh_conn[[0, 1, 2, 3, 4, 5, 6, 7, 9, 8]]`: the last two mid-edge nodes swap. The constant is `tet10.GMSH_TO_CCX_TET10`.

gmsh's 6-node triangle (type 9), used for the surface loads, is ordered as corners 0–2, then mid-edges 3 = 0–1, 4 = 1–2 and 5 = 2–0.

## Evidence (tests in `plugins/forge/tests/mech2/test_running_fea_general_units.py`)

1. **Mid-edge geometry.** The test meshes a straight-sided box through the real STEP → gmsh path.
   - Read with gmsh's own table, every mid-edge node lies at its edge midpoint (max deviation < 1e-9, relative to edge length).
   - Read with CalculiX's table, the raw gmsh order puts nodes 8 and 9 on the wrong edge in *every* element (min deviation > 0.2).
   - After the permutation, the deviation is < 1e-9 and every corner volume is positive.
   - Test: `test_gmsh_tet10_matches_its_documented_edge_table_and_ccx_table_after_permutation`.
2. **CalculiX negative control.** The same mesh written without the swap makes ccx abort with `nonpositive jacobian`, which is the original failure. With the swap it solves. Test: `test_ccx_rejects_unpermuted_tet10_negative_control`.
3. **Constant-stress patch test.** A 40 × 10 × 8 mm block has symmetry supports on its three min faces and a 50 MPa uniform traction on the x-max face. It must reproduce σxx = 50 MPa at every node and u_x = σx/E.
   - Measured on 783 nodes: max |σxx − σ|/σ = 1.0e-5 (the 6-significant-digit `.frd` print precision), max |other components|/σ = 2.7e-10.
   - A displacement-controlled version passes the same way.
   - Tests: `test_constant_stress_patch_test_is_exact`, `test_prescribed_displacement_patch_test`.
4. **Consistent loads matter.** The same patch loaded with *equal* shares on every face node gives > 5 % stress error. A uniform traction on a tri6 puts zero force on the corner nodes and A·t/3 on each mid-edge node. Tests: `test_lumped_equal_nodal_loads_fail_the_patch_test` and `test_consistent_tri6_loads_zero_on_corners_third_on_midsides`.
5. **Every production solve re-checks it.** `verify.py` records `tet10_ordering_max_midside_deviation` (limit 0.25) for every level, and refuses to solve a mesh with a non-positive corner volume.
   - On curved faces the mid-edge nodes lie on the true geometry, not on the chord. That gives small non-zero values: 0.009 on the plate hole and 0.05 on the Ø20 tube at h = 3 mm.
   - A wrong ordering gives ≥ ~0.5.

## If gmsh or CalculiX is upgraded

Run `test_running_fea_general_units.py`. If the geometry or patch test fails, re-derive the permutation from the mid-edge test before changing anything else. Never "fix" the problem by switching to the unverified ordering tables in forum posts.
