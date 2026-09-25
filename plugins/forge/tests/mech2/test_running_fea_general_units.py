"""Unit + proof tests for running-fea's general (tet10) path.

Proves the gmsh -> CalculiX C3D10 node permutation three independent ways (mid-edge geometry,
a CalculiX negative control, and a constant-stress patch test), plus face selectors, the
rigid-body pre-check and the closed-form hand calcs. Real gmsh / CalculiX runs, a few seconds each.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "skills" / "running-fea" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import general_fea as g  # noqa: E402
import handcalc  # noqa: E402
import tet10  # noqa: E402

CCX = Path.home() / ".forge" / "bin" / "ccx"
STEEL = {"name": "test steel", "E": 210000.0, "nu": 0.3, "yield": 250.0, "density": 7850.0, "source": "test"}


def _box_step(tmp_path: Path, lx=40.0, ly=10.0, lz=8.0) -> Path:
    from build123d import Align, Box, export_step
    p = tmp_path / "box.step"
    export_step(Box(lx, ly, lz, align=(Align.MIN, Align.MIN, Align.MIN)), str(p))
    return p


def _plate_hole_step(tmp_path: Path) -> Path:
    from build123d import Align, Box, BuildPart, Cylinder, Mode, export_step
    with BuildPart() as bp:
        Box(100, 25, 1, align=(Align.MIN, Align.MIN, Align.MIN))
        Cylinder(5, 1, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    p = tmp_path / "plate.step"
    export_step(bp.part, str(p))
    return p


def _mesh(step: Path, h: float, selections=None, permutation=tet10.GMSH_TO_CCX_TET10):
    return g.mesh_part(step, h=h, selections=selections or {}, refine=[], max_nodes=200_000,
                       high_order_optimize=2, permutation=permutation)


# ----------------------------------------------------------------- node ordering proofs

def test_gmsh_tet10_matches_its_documented_edge_table_and_ccx_table_after_permutation(tmp_path):
    """Straight-sided box mesh: every mid-edge node sits exactly at its edge midpoint."""
    identity = tuple(range(10))
    raw = _mesh(_box_step(tmp_path), 3.0, permutation=identity)
    assert raw.tets.shape[0] > 200
    dev_gmsh = tet10.midside_deviation(raw.xyz, raw.tets, tet10.GMSH_TET10_EDGES)
    assert dev_gmsh.max() < 1e-9, "gmsh's own tet10 order is not the documented one"
    # the raw gmsh order read with CalculiX's edge table is WRONG on nodes 8/9
    dev_wrong = tet10.midside_deviation(raw.xyz, raw.tets, tet10.CCX_TET10_EDGES)
    assert dev_wrong.min() > 0.2, "identity order must put nodes 8/9 on the wrong edges in every element"
    perm = raw.tets[:, list(tet10.GMSH_TO_CCX_TET10)]
    rep = tet10.ordering_report(raw.xyz, perm)
    assert rep["max_midside_deviation"] < 1e-9
    assert rep["n_nonpositive_volume"] == 0 and rep["min_corner_volume_mm3"] > 0


def test_ccx_rejects_unpermuted_tet10_negative_control(tmp_path):
    """Without the 8<->9 swap CalculiX aborts with a nonpositive Jacobian -- the builder's original failure."""
    step = _box_step(tmp_path)
    sel = {"bc:root": {"plane": "x", "at": "min"}, "load:tip": {"plane": "x", "at": "max"}}
    case = {"bc": [{"name": "root", "type": "fixed", "faces": sel["bc:root"]}],
            "load": [{"name": "tip", "type": "force", "faces": sel["load:tip"], "vector_n": [0, 0, -10.0]}]}
    for perm, should_fail in ((tuple(range(10)), True), (tet10.GMSH_TO_CCX_TET10, False)):
        mesh = _mesh(step, 4.0, sel, permutation=perm)
        forces, _ = g.build_loads(case, mesh)
        cons = g.build_constraints(case, mesh)
        work = tmp_path / ("identity" if should_fail else "swapped")
        inp = g.write_inp(work / "model.inp", mesh, STEEL, cons, forces)
        if should_fail:
            with pytest.raises(g.FeaError, match="nonpositive jacobian"):
                g.run_ccx(inp, str(CCX))
        else:
            g.run_ccx(inp, str(CCX))


def test_constant_stress_patch_test_is_exact(tmp_path):
    """Uniaxial tension of a symmetric-supported block: sigma_xx = F/A at EVERY node, u_x = sigma L / E.

    A tet10 mesh with correct ordering and consistent surface loads reproduces the linear
    displacement field exactly, so errors here are only CalculiX's 6-digit .frd print precision.
    """
    step = _box_step(tmp_path, 40.0, 10.0, 8.0)
    sigma = 50.0
    case = {
        "case": {"name": "patch"}, "_material": STEEL, "mesh": {"sizes_mm": [4.0]},
        "bc": [{"name": "sx", "type": "symmetry", "faces": {"plane": "x", "at": "min"}},
               {"name": "sy", "type": "symmetry", "faces": {"plane": "y", "at": "min"}},
               {"name": "sz", "type": "symmetry", "faces": {"plane": "z", "at": "min"}}],
        "load": [{"name": "pull", "type": "force", "faces": {"plane": "x", "at": "max"},
                  "vector_n": [sigma * 10.0 * 8.0, 0.0, 0.0]}],
        "hand_calc": [],
    }
    lv = g.solve_level(case, step, 4.0, tmp_path / "patch", str(CCX))
    res = g.read_frd(tmp_path / "patch" / "model.frd", lv.n_nodes)
    s, u = res["STRESS"], res["DISP"]
    err_xx = np.max(np.abs(s[:, 0] - sigma)) / sigma
    err_other = np.max(np.abs(s[:, 1:])) / sigma
    print(f"patch test: {lv.n_nodes} nodes, max |sxx - sigma|/sigma = {err_xx:.2e}, max |other|/sigma = {err_other:.2e}")
    assert err_xx < 2e-5
    assert err_other < 2e-5
    xyz = lv.post["_xyz"]
    assert np.max(np.abs(u[:, 0] - sigma / STEEL["E"] * xyz[:, 0])) < 1e-6 * 40.0
    assert lv.post["reaction_imbalance_pct"] < 1e-3


def test_prescribed_displacement_patch_test(tmp_path):
    """Displacement-controlled patch: u_x = 0.01 mm on x = 40 face -> sigma_xx = E * 0.01 / 40 everywhere."""
    step = _box_step(tmp_path, 40.0, 10.0, 8.0)
    case = {
        "case": {"name": "patch_u"}, "_material": STEEL, "mesh": {"sizes_mm": [4.0]},
        "bc": [{"name": "sx", "type": "symmetry", "faces": {"plane": "x", "at": "min"}},
               {"name": "sy", "type": "symmetry", "faces": {"plane": "y", "at": "min"}},
               {"name": "sz", "type": "symmetry", "faces": {"plane": "z", "at": "min"}},
               {"name": "pull", "type": "displacement", "dofs": [1], "value_mm": 0.01,
                "faces": {"plane": "x", "at": "max"}}],
        "load": [], "hand_calc": [],
    }
    lv = g.solve_level(case, step, 4.0, tmp_path / "patch_u", str(CCX))
    s = g.read_frd(tmp_path / "patch_u" / "model.frd", lv.n_nodes)["STRESS"]
    expected = STEEL["E"] * 0.01 / 40.0
    assert np.max(np.abs(s[:, 0] - expected)) / expected < 2e-5
    assert lv.post["reaction_imbalance_pct"] < 1e-3          # reactions balance each other
    assert lv.post["reaction_by_bc_n"]["pull"][0] == pytest.approx(expected * 80.0, rel=1e-4)


def test_refine_zone_shrinks_elements_near_the_hole(tmp_path):
    step = _plate_hole_step(tmp_path)
    sel = {"hole": {"cylinder_radius_mm": 5.0}, "refine:hole": {"cylinder_radius_mm": 5.0}}
    plain = g.mesh_part(step, h=4.0, selections=sel, refine=[], max_nodes=200_000, high_order_optimize=2)
    fine = g.mesh_part(step, h=4.0, selections=sel, max_nodes=200_000, high_order_optimize=2,
                       refine=[{"name": "hole", "faces": sel["refine:hole"], "size_factor": 0.1, "dist_min_mm": 0.5, "dist_max_mm": 8.0}])
    assert fine.faces["hole"].nodes.size > 5 * plain.faces["hole"].nodes.size


def test_consistent_tri6_loads_zero_on_corners_third_on_midsides():
    """Uniform traction on a flat tri6: 0 to corners, A*t/3 to each mid-edge node (not A*t/6 each)."""
    xyz = np.array([[0, 0, 0], [2, 0, 0], [0, 3, 0], [1, 0, 0], [1, 1.5, 0], [0, 1.5, 0]], dtype=float)
    f = tet10.consistent_nodal_forces(xyz, np.array([[0, 1, 2, 3, 4, 5]]),
                                      lambda p, n: np.broadcast_to(np.array([0, 0, 1.0]), p.shape))
    area = 3.0
    assert np.allclose(f[:3, 2], 0.0, atol=1e-12)
    assert np.allclose(f[3:, 2], area / 3.0, rtol=1e-12)


def test_lumped_equal_nodal_loads_fail_the_patch_test(tmp_path):
    """Negative control: the same patch loaded by equal shares on every face node is NOT uniform."""
    step = _box_step(tmp_path, 40.0, 10.0, 8.0)
    sigma = 50.0
    sel = {"bc:sx": {"plane": "x", "at": "min"}, "bc:sy": {"plane": "y", "at": "min"},
           "bc:sz": {"plane": "z", "at": "min"}, "load:pull": {"plane": "x", "at": "max"}}
    case = {"bc": [{"name": n[3:], "type": "symmetry", "faces": sel[n]} for n in ("bc:sx", "bc:sy", "bc:sz")]}
    mesh = _mesh(step, 4.0, sel)
    nodes = mesh.faces["load:pull"].nodes
    forces = np.zeros_like(mesh.xyz)
    forces[nodes, 0] = sigma * 80.0 / nodes.size
    inp = g.write_inp(tmp_path / "lumped" / "model.inp", mesh, STEEL, g.build_constraints(case, mesh), forces)
    g.run_ccx(inp, str(CCX))
    s = g.read_frd(inp.with_suffix(".frd"), mesh.xyz.shape[0])["STRESS"]
    assert np.max(np.abs(s[:, 0] - sigma)) / sigma > 0.05


def test_tri6_quadrature_integrates_curved_quarter_cylinder_area():
    """Curved tri6 geometry: area of a quarter-cylinder patch within the quadratic-geometry error."""
    r, length, n = 5.0, 4.0, 16
    th = np.linspace(0, math.pi / 2, 2 * n + 1)
    zs = np.linspace(0, length, 3)
    pts = np.array([[r * math.cos(t), r * math.sin(t), z] for z in zs for t in th])
    idx = lambda i, j: j * (2 * n + 1) + i  # noqa: E731
    tris = []
    for i in range(0, 2 * n, 2):
        a, b, c, d = idx(i, 0), idx(i + 2, 0), idx(i, 2), idx(i + 2, 2)
        tris.append([a, b, d, idx(i + 1, 0), idx(i + 2, 1), idx(i + 1, 1)])
        tris.append([a, d, c, idx(i + 1, 1), idx(i + 1, 2), idx(i, 1)])
    area, cen, *_ = tet10.face_integrals(pts, np.array(tris))
    assert area == pytest.approx(math.pi / 2 * r * length, rel=1e-4)


# ----------------------------------------------------------------- selectors & constraints

def test_face_selectors_on_plate_with_hole(tmp_path):
    step = _plate_hole_step(tmp_path)
    sel = {"hole": {"cylinder_radius_mm": 5.0, "axis": "z"}, "top": {"normal": [0, 0, 1]},
           "bottom": {"normal": [0, 0, -1]}, "xmin": {"plane": "x", "at": "min"},
           "xmax_by_value": {"plane": "x", "at": 100.0},
           "near_point": {"contains_point_mm": [50.0, 25.0, 0.5]},
           "both_x": [{"plane": "x", "at": "min"}, {"plane": "x", "at": "max"}],
           "boxed": {"within_box_mm": [-1, -1, -1, 6, 6, 2], "type": "cylinder"}}
    mesh = _mesh(step, 5.0, sel)
    hole_r = np.linalg.norm(mesh.xyz[mesh.faces["hole"].nodes][:, :2], axis=1)
    assert np.allclose(hole_r, 5.0, atol=1e-6)
    assert np.allclose(mesh.xyz[mesh.faces["top"].nodes][:, 2], 1.0)
    assert np.allclose(mesh.xyz[mesh.faces["bottom"].nodes][:, 2], 0.0)
    assert np.allclose(mesh.xyz[mesh.faces["xmin"].nodes][:, 0], 0.0)
    assert np.allclose(mesh.xyz[mesh.faces["xmax_by_value"].nodes][:, 0], 100.0)
    assert np.allclose(mesh.xyz[mesh.faces["near_point"].nodes][:, 1], 25.0)
    assert len(mesh.faces["both_x"].tags) == 2
    assert mesh.faces["boxed"].tags == mesh.faces["hole"].tags


@pytest.mark.parametrize("spec,match", [
    ({"cylinder_radius_mm": 7.0}, "matched no face"),
    ({"plane": "x", "at": "min", "expect_count": 2}, "expected 2"),
    ({"plane": "x", "at": "min", "colour": "red"}, "unknown selector key"),
    ({"plane": "x"}, "needs at"),
])
def test_face_selector_errors_are_loud(tmp_path, spec, match):
    with pytest.raises(g.CaseError, match=match):
        _mesh(_plate_hole_step(tmp_path), 6.0, {"s": spec})


def test_rigid_body_check_names_free_modes(tmp_path):
    step = _box_step(tmp_path)
    sel = {"bc:a": {"plane": "x", "at": "min"}}
    mesh = _mesh(step, 5.0, sel)
    fixed = g.build_constraints({"bc": [{"name": "a", "type": "fixed", "faces": sel["bc:a"]}]}, mesh)
    assert g.rigid_body_check(mesh, fixed) == []
    sym = g.build_constraints({"bc": [{"name": "a", "type": "symmetry", "faces": sel["bc:a"]}]}, mesh)
    free = g.rigid_body_check(mesh, sym)
    assert len(free) == 3
    text = " ".join(free)
    assert "translation y" in text and "translation z" in text and "rotation about x" in text


# ----------------------------------------------------------------- hand calcs

def test_plate_hole_kt_fits_agree_and_reach_kirsch_limit():
    for m in ("peterson", "heywood", "roark"):
        assert handcalc.plate_hole_kt_net(0.0, m) == pytest.approx(3.0, abs=0.01)   # Kirsch, infinite plate
    k = [handcalc.plate_hole_kt_net(0.2, m) for m in ("peterson", "heywood", "roark")]
    assert max(k) / min(k) - 1 < 0.005
    hc = handcalc.plate_hole_tension_peak_stress({"gross_stress_mpa": 50.0, "width_mm": 50.0,
                                                  "hole_diameter_mm": 10.0}, 210000.0, 0.3)
    assert hc.value == pytest.approx(handcalc.plate_hole_kt_net(0.2) * 62.5, rel=1e-12)
    assert hc.value == pytest.approx(157.44, abs=0.01)


def test_torsion_and_cantilever_formulas_match_textbook_numbers():
    tw = handcalc.tube_torsion_twist({"torque_nmm": 1e5, "length_mm": 100.0, "outer_diameter_mm": 20.0,
                                      "inner_diameter_mm": 16.0}, 210000.0, 0.3)
    j = math.pi * (20 ** 4 - 16 ** 4) / 32
    assert tw.value == pytest.approx(1e5 * 100 / (210000 / 2.6 * j), rel=1e-12)
    vm = handcalc.tube_torsion_peak_von_mises({"torque_nmm": 1e5, "outer_diameter_mm": 20.0,
                                               "inner_diameter_mm": 16.0}, 210000.0, 0.3)
    assert vm.value == pytest.approx(math.sqrt(3) * 1e5 * 10 / j, rel=1e-12)
    cb = handcalc.cantilever_end_load_deflection({"force_n": 100.0, "length_mm": 100.0, "width_mm": 10.0,
                                                  "height_mm": 10.0}, 210000.0, 0.3)
    assert cb.value == pytest.approx(0.19047619, rel=1e-7)
    assert "0.77 %" in cb.notes          # Timoshenko shear correction stated, not silently applied
    lame = handcalc.thick_cylinder_internal_pressure_hoop_stress(
        {"pressure_mpa": 50.0, "inner_radius_mm": 10.0, "outer_radius_mm": 15.0}, 210000.0, 0.3)
    assert lame.value == pytest.approx(130.0, rel=1e-12)
    with pytest.raises(handcalc.HandCalcError):
        handcalc.evaluate("no_such_formula", {}, 1.0, 0.3)
    with pytest.raises(handcalc.HandCalcError):
        handcalc.evaluate("custom", {"value": 1.0}, 1.0, 0.3)


def test_convergence_classifier():
    ok = g.convergence([100.0, 101.0, 101.2], [4.0, 2.0, 1.0], 1.0)
    assert ok["state"] == "converged" and ok["observed_order"] == pytest.approx(math.log(5) / math.log(2))
    slow = g.convergence([100.0, 110.0, 115.0], [4.0, 2.0, 1.0], 1.0)
    assert slow["state"] == "not_converged" and not slow["diverging"]
    sing = g.convergence([100.0, 141.0, 200.0], [4.0, 2.0, 1.0], 1.0)   # ~ h^-0.5 growth
    assert sing["state"] == "diverging"
