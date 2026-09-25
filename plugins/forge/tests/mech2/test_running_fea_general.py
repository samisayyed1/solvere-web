"""Known-answer + seeded-wrong tests for running-fea's GENERAL path through verify.py.

Known answers (closed forms, see skills/running-fea/references/hand-calcs.md):
  (a) cantilever box via tet10, tip deflection vs Euler-Bernoulli (<= 3 %)
  (b) plate with a central hole (d/W = 0.2) in tension, peak stress vs Peterson Kt_n * sigma_nom (<= 10 %)
  (c) thin-walled tube in torsion, twist angle and peak von Mises vs Saint-Venant (STEP input)
  (e) thick cylinder under internal pressure, hoop stress vs Lame (pressure load + outward normals)
  (d) reaction balance <= 0.5 % on every level of every case
Seeded wrong (must NOT pass): under-refined mesh, under-constrained supports, wrong hand calc,
singular point load, malformed cases.

Real gmsh + CalculiX solves: roughly 60-90 s for the whole module.
"""
from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parents[2] / "skills" / "running-fea"
VERIFY_PY = SKILL_DIR / "scripts" / "verify.py"
FORGE_PYTHON = Path.home() / ".forge" / "bin" / "forge-python"
PY = str(FORGE_PYTHON) if FORGE_PYTHON.exists() else sys.executable

PARAMS = """
[materials.steel.E]
value = 210.0
unit = "GPa"
status = "assumed"
source = "generic structural steel handbook value (test fixture, not a datasheet)"

[materials.steel.nu]
value = 0.3
unit = "1"
status = "assumed"
source = "generic structural steel handbook value (test fixture, not a datasheet)"

[materials.steel.yield]
value = 250.0
unit = "MPa"
status = "assumed"
source = "ASTM A36 minimum yield (test fixture, not a mill cert)"

[materials.steel.density]
value = 7850.0
unit = "kg/m3"
status = "assumed"
source = "generic structural steel handbook value (test fixture, not a datasheet)"
"""

BEAM_PY = """
from build123d import Box, Align
part = Box(100, 10, 10, align=(Align.MIN, Align.CENTER, Align.CENTER))
"""

# 1/8 model of a 200 x 50 x 2 mm plate with a central 10 mm hole: symmetry at x=0, y=0, z=0.
PLATE_PY = """
from build123d import Box, Cylinder, Align, Mode, BuildPart
with BuildPart() as bp:
    Box(100, 25, 1, align=(Align.MIN, Align.MIN, Align.MIN))
    Cylinder(5, 1, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
part = bp.part
"""

CANTILEVER = """
[case]
name = "{name}"
[geometry]
build123d = "cad/beam.py"
[material]
params = "materials.steel"
[[bc]]
name = "root"
type = "fixed"
faces = {{ plane = "x", at = "min" }}
{load}
[stress]
exclude = [
  {{ faces = {{ plane = "x", at = "min" }}, distance_mm = 10.0, reason = "clamped-root edge of the idealised fully fixed face (Saint-Venant zone, one beam depth)" }},
  {{ faces = {{ plane = "x", at = "max" }}, distance_mm = 5.0, reason = "load-introduction zone of the idealised uniform tip traction" }},
]
[mesh]
sizes_mm = {sizes}
convergence_tol_pct = 1.0
stress_convergence_tol_pct = 3.0
[[hand_calc]]
name = "tip_deflection"
formula = "cantilever_end_load_deflection"
inputs = {{ force_n = 100.0, length_mm = 100.0, width_mm = 10.0, height_mm = {hc_height} }}
fea = {{ quantity = "face_mean_displacement", faces = {{ plane = "x", at = "max" }}, component = "-z" }}
tolerance_pct = 3.0
[[hand_calc]]
name = "bending_stress_10mm_from_root"
formula = "cantilever_bending_stress"
inputs = {{ force_n = 100.0, lever_arm_mm = 90.0, width_mm = 10.0, height_mm = 10.0 }}
fea = {{ quantity = "peak_von_mises" }}
tolerance_pct = 5.0
[requirement]
min_safety_factor = 1.5
"""
TIP_TRACTION = """[[load]]
name = "tip"
type = "force"
faces = { plane = "x", at = "max" }
vector_n = [0.0, 0.0, -100.0]"""

PLATE = """
[case]
name = "{name}"
[geometry]
build123d = "cad/plate.py"
[material]
params = "materials.steel"
{bcs}
[[load]]
name = "tension"
type = "force"
faces = {{ plane = "x", at = "max" }}
vector_n = [1250.0, 0.0, 0.0]
{refine}
[mesh]
sizes_mm = {sizes}
convergence_tol_pct = 2.0
[[hand_calc]]
name = "hole_peak_stress"
formula = "plate_hole_tension_peak_stress"
inputs = {{ gross_stress_mpa = 50.0, width_mm = 50.0, hole_diameter_mm = 10.0 }}
fea = {{ quantity = "peak_principal" }}
tolerance_pct = 10.0
[requirement]
min_safety_factor = 1.5
"""
PLATE_SYM = """[[bc]]
name = "sym_x"
type = "symmetry"
faces = { plane = "x", at = "min" }
[[bc]]
name = "sym_y"
type = "symmetry"
faces = { plane = "y", at = "min" }
[[bc]]
name = "sym_z"
type = "symmetry"
faces = { plane = "z", at = "min" }"""
HOLE_REFINE = """[[refine]]
name = "hole"
faces = { cylinder_radius_mm = 5.0, axis = "z" }
size_factor = 0.08
dist_min_mm = 0.5
dist_max_mm = 10.0"""

TUBE = """
[case]
name = "tube_torsion"
[geometry]
step = "cad/tube.step"
[material]
params = "materials.steel"
[[bc]]
name = "root"
type = "fixed"
faces = { plane = "z", at = "min" }
[[load]]
name = "torque"
type = "torque"
faces = { plane = "z", at = "max" }
torque_nmm = 100000.0
axis = [0.0, 0.0, 1.0]
[mesh]
sizes_mm = [3.0, 2.0, 1.4]
convergence_tol_pct = 1.0
stress_convergence_tol_pct = 2.0
[[hand_calc]]
name = "twist"
formula = "tube_torsion_twist"
inputs = { torque_nmm = 100000.0, length_mm = 100.0, outer_diameter_mm = 20.0, inner_diameter_mm = 16.0 }
fea = { quantity = "face_rotation", faces = { plane = "z", at = "max" }, axis = [0.0, 0.0, 1.0] }
tolerance_pct = 2.0
[[hand_calc]]
name = "peak_von_mises"
formula = "tube_torsion_peak_von_mises"
inputs = { torque_nmm = 100000.0, outer_diameter_mm = 20.0, inner_diameter_mm = 16.0 }
fea = { quantity = "peak_von_mises" }
tolerance_pct = 5.0
[requirement]
min_safety_factor = 1.2
"""


LAME_PY = """
from build123d import Box, Cylinder, Align, Mode, BuildPart
with BuildPart() as bp:
    Cylinder(15, 20, align=(Align.CENTER, Align.CENTER, Align.MIN))
    Cylinder(10, 20, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    Box(20, 20, 20, align=(Align.MIN, Align.MIN, Align.MIN), mode=Mode.INTERSECT)
part = bp.part
"""

LAME = """
[case]
name = "lame_cylinder"
[geometry]
build123d = "cad/lame.py"
[material]
params = "materials.steel"
""" + PLATE_SYM + """
[[load]]
name = "internal"
type = "pressure"
faces = { cylinder_radius_mm = 10.0, axis = "z" }
pressure_mpa = 50.0
[mesh]
sizes_mm = [3.0, 2.0, 1.4]
convergence_tol_pct = 2.0
[[hand_calc]]
name = "hoop"
formula = "thick_cylinder_internal_pressure_hoop_stress"
inputs = { pressure_mpa = 50.0, inner_radius_mm = 10.0, outer_radius_mm = 15.0 }
fea = { quantity = "peak_principal" }
tolerance_pct = 3.0
[requirement]
min_safety_factor = 1.2
"""


def _project(root: Path, cases: dict[str, str]) -> Path:
    (root / "params").mkdir(parents=True, exist_ok=True)
    (root / "params" / "params.toml").write_text(PARAMS)
    (root / "cad").mkdir(exist_ok=True)
    (root / "cad" / "beam.py").write_text(BEAM_PY)
    (root / "cad" / "plate.py").write_text(PLATE_PY)
    (root / "cad" / "lame.py").write_text(LAME_PY)
    (root / "analysis" / "fea").mkdir(parents=True, exist_ok=True)
    for name, text in cases.items():
        (root / "analysis" / "fea" / f"{name}.toml").write_text(textwrap.dedent(text))
    return root


def _verify(project: Path, case: str | None = None) -> subprocess.CompletedProcess:
    cmd = [PY, str(VERIFY_PY), "--project", str(project)]
    if case:
        cmd += ["--changed", f"analysis/fea/{case}.toml"]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=900)


def _result(project: Path, check: str) -> dict:
    return json.loads((project / "out" / "verify" / f"sim.fea_{check}.json").read_text())


def _m(out: dict) -> dict:
    return {m["name"]: m for m in out["measurements"]}


# ---------------------------------------------------------------- known answers

@pytest.fixture(scope="module")
def known(tmp_path_factory):
    root = tmp_path_factory.mktemp("fea_general_known")
    cases = {
        "cantilever": CANTILEVER.format(name="cantilever_tet", load=TIP_TRACTION, sizes="[5.0, 3.5, 2.5]",
                                        hc_height="10.0"),
        "plate": PLATE.format(name="plate_hole", bcs=PLATE_SYM, refine=HOLE_REFINE, sizes="[4.0, 2.8, 2.0]"),
        "tube": TUBE,
        "lame": LAME,
    }
    _project(root, cases)
    from build123d import Align, BuildPart, Cylinder, Mode, export_step
    with BuildPart() as bp:
        Cylinder(10, 100, align=(Align.CENTER, Align.CENTER, Align.MIN))
        Cylinder(8, 100, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    export_step(bp.part, str(root / "cad" / "tube.step"))
    r = _verify(root)
    return root, r


@pytest.mark.slow
def test_known_answer_run_passes(known):
    root, r = known
    assert r.returncode == 0, r.stdout + r.stderr
    for check in ("cantilever_tet", "plate_hole", "tube_torsion", "lame_cylinder"):
        out = _result(root, check)
        assert out["status"] == "pass", (check, out)
        assert out["level"] == "L2", check


@pytest.mark.slow
def test_a_cantilever_tet10_within_3pct_of_euler_bernoulli(known):
    root, _ = known
    out = _result(root, "cantilever_tet")
    m = _m(out)
    assert abs(m["hand_calc_tip_deflection_diff_pct"]["value"]) < 3.0
    assert abs(m["hand_calc_tip_deflection_diff_pct"]["value"]) < 1.0, "reference case lands at about -0.02 %"
    assert m["convergence_tip_deflection_pct_change"]["pass"]
    assert abs(m["hand_calc_bending_stress_10mm_from_root_diff_pct"]["value"]) < 5.0
    assert "Timoshenko shear correction" in out["notes"] and "0.77 %" in out["notes"]
    assert m["stress_singularity_suspected"]["value"] is False


@pytest.mark.slow
def test_b_plate_hole_peak_within_10pct_of_peterson_at_hole_edge(known):
    root, _ = known
    out = _result(root, "plate_hole")
    m = _m(out)
    assert abs(m["hand_calc_hole_peak_stress_diff_pct"]["value"]) < 10.0
    assert abs(m["hand_calc_hole_peak_stress_diff_pct"]["value"]) < 3.0, "reference case lands at about +0.9 %"
    assert "d/W = 0.200" in out["notes"]
    # the peak must be where theory puts it: hole edge, on the net section (x ~ 0, y ~ r = 5 mm)
    loc = m["hand_calc_hole_peak_stress_diff_pct"]["location"]
    xyz = [float(v.split("=")[1]) for v in loc.split(" mm")[0].split(", ")]
    assert abs(xyz[0]) < 0.5 and abs(xyz[1] - 5.0) < 0.1, loc
    assert "refine:hole" in loc
    assert m["convergence_hole_peak_stress_pct_change"]["value"] < 2.0


@pytest.mark.slow
def test_c_tube_torsion_twist_and_peak_stress_from_step_input(known):
    root, _ = known
    out = _result(root, "tube_torsion")
    m = _m(out)
    assert abs(m["hand_calc_twist_diff_pct"]["value"]) < 2.0
    assert abs(m["hand_calc_peak_von_mises_diff_pct"]["value"]) < 5.0
    assert "tube.step" in out["notes"]


@pytest.mark.slow
def test_e_lame_cylinder_hoop_stress_within_3pct(known):
    root, _ = known
    out = _result(root, "lame_cylinder")
    m = _m(out)
    assert abs(m["hand_calc_hoop_diff_pct"]["value"]) < 3.0
    # a wrong (inward) normal would pull the bore inward: hoop stress compressive, peak principal wrong
    summary = json.loads((root / "out" / "fea" / "lame_cylinder" / "summary.json").read_text())
    assert summary["hand_calcs"][0]["fea"] > 0
    # pressure resultant on the quarter bore = p * r_i * L = 50 * 10 * 20 = 10 000 N in x and in y
    level = json.loads(next((root / "out" / "fea" / "lame_cylinder").glob("level2_*/level.json")).read_text())
    rx, ry, _ = level["post"]["reaction_force_n"]
    assert rx == pytest.approx(-10000.0, rel=1e-3) and ry == pytest.approx(-10000.0, rel=1e-3)


@pytest.mark.slow
def test_d_reaction_balance_within_half_percent_everywhere(known):
    root, _ = known
    for check in ("cantilever_tet", "plate_hole", "tube_torsion", "lame_cylinder"):
        m = _m(_result(root, check))
        assert m["reaction_balance_pct"]["value"] <= 0.5, check
        assert m["reaction_balance_pct"]["limit"] == {"max": 0.5}
        assert m["tet10_ordering_max_midside_deviation"]["pass"]
    summary = json.loads((root / "out" / "fea" / "tube_torsion" / "summary.json").read_text())
    assert all(lv["reaction_imbalance_pct"] < 0.5 for lv in summary["levels"])  # pure torque: moment balance


@pytest.mark.slow
def test_results_report_locations_of_peaks(known):
    root, _ = known
    out = _result(root, "plate_hole")
    m = _m(out)
    assert "x=" in m["safety_factor"]["location"] and "node" in m["safety_factor"]["location"]
    assert "max displacement" in out["notes"] and "peak von Mises" in out["notes"]
    assert "Validity limits" in out["notes"] and "no contact" in out["notes"]


# ---------------------------------------------------------------- seeded wrong

@pytest.mark.slow
def test_seeded_under_refined_mesh_fails_convergence(tmp_path):
    root = _project(tmp_path, {"coarse": PLATE.format(name="plate_coarse", bcs=PLATE_SYM, refine="",
                                                      sizes="[8.0, 5.0, 3.0]")})
    r = _verify(root)
    assert r.returncode == 1, r.stdout + r.stderr
    out = _result(root, "plate_coarse")
    assert out["status"] == "fail" and out["level"] == "L1"
    m = _m(out)
    assert m["convergence_hole_peak_stress_pct_change"]["pass"] is False
    assert m["convergence_hole_peak_stress_pct_change"]["value"] > 2.0
    assert "finer level" in m["convergence_hole_peak_stress_pct_change"]["remediation"]


@pytest.mark.slow
def test_seeded_under_constrained_model_is_an_error_not_a_pass(tmp_path):
    only_x = PLATE_SYM.split("[[bc]]\nname = \"sym_y\"")[0]
    root = _project(tmp_path, {"free": PLATE.format(name="plate_free", bcs=only_x, refine="", sizes="[8.0, 5.0, 3.0]")})
    r = _verify(root)
    assert r.returncode == 2, r.stdout + r.stderr
    out = _result(root, "plate_free")
    assert out["status"] == "error"
    assert "under-constrained" in out["error"] and "singular" in out["error"]
    assert "translation y" in out["error"] and "rotation about x" in out["error"]
    assert "pass" not in r.stdout.lower()


@pytest.mark.slow
def test_calculix_itself_does_not_catch_the_under_constrained_model(tmp_path):
    """Characterisation: why the pre-check exists. ccx 2.23/SPOOLES solves the singular system silently."""
    sys.path.insert(0, str(SKILL_DIR / "scripts"))
    import general_fea as g
    only_x = PLATE_SYM.split("[[bc]]\nname = \"sym_y\"")[0]
    root = _project(tmp_path, {"free": PLATE.format(name="plate_free", bcs=only_x, refine="", sizes="[8.0, 5.0, 3.0]")})
    case = g.load_case(root / "analysis" / "fea" / "free.toml", root)
    study = g.run_study(case, root, root / "out" / "nocheck", str(Path.home() / ".forge" / "bin" / "ccx"),
                        precheck=False)
    log = (study["levels"][0].work_dir / "model.ccx.log").read_text()
    assert "Job finished" in log and "*ERROR" not in log


@pytest.mark.slow
def test_seeded_wrong_hand_calc_fails_and_demotes_to_L1(tmp_path):
    root = _project(tmp_path, {"cant": CANTILEVER.format(name="cantilever_wrong_hc", load=TIP_TRACTION,
                                                         sizes="[5.0, 3.5, 2.5]", hc_height="11.0")})
    r = _verify(root)
    assert r.returncode == 1, r.stdout + r.stderr
    out = _result(root, "cantilever_wrong_hc")
    assert out["level"] == "L1"
    m = _m(out)
    assert m["hand_calc_tip_deflection_diff_pct"]["pass"] is False
    assert m["hand_calc_tip_deflection_diff_pct"]["value"] > 25.0      # (11/10)^3 - 1 = +33 %


@pytest.mark.slow
def test_seeded_point_load_singularity_is_flagged(tmp_path):
    point = """[[load]]
name = "poke"
type = "point_force"
at_mm = [50.0, 0.0, 5.0]
vector_n = [0.0, 0.0, -100.0]"""
    text = CANTILEVER.format(name="cantilever_point", load=point, sizes="[5.0, 3.5, 2.5]", hc_height="10.0")
    # the deflection hand calc for a load at mid-span (tip deflection F a^2 (3L - a) / (6 E I)) so the
    # ONLY thing wrong with this model is the singular point load
    text = text.replace('formula = "cantilever_end_load_deflection"\ninputs = { force_n = 100.0, length_mm = 100.0, '
                        'width_mm = 10.0, height_mm = 10.0 }',
                        'formula = "custom"\ninputs = { value = 0.0595238, unit = "mm", expression = "F a^2 (3L - a)/'
                        '(6 E I), F=100 N, a=50 mm, L=100 mm, I=833.33 mm4", reference = "Gere & Goodno, cantilever, '
                        'intermediate point load" }')
    text = text.replace('fea = { quantity = "face_mean_displacement", faces = { plane = "x", at = "max" }, '
                        'component = "-z" }', 'fea = { quantity = "max_displacement" }')
    i = text.index('[[hand_calc]]\nname = "bending_stress_10mm_from_root"')
    text = text[:i] + text[text.index("[requirement]"):]
    root = _project(tmp_path, {"point": text})
    r = _verify(root)
    assert r.returncode == 1, r.stdout + r.stderr
    out = _result(root, "cantilever_point")
    assert out["level"] == "L1"
    m = _m(out)
    assert m["hand_calc_tip_deflection_diff_pct"]["pass"] is True
    assert m["stress_singularity_suspected"]["value"] is True
    assert "load:poke" in m["stress_singularity_suspected"]["location"]
    assert "singular" in m["stress_singularity_suspected"]["remediation"]


# ---------------------------------------------------------------- malformed cases (exit 2)

@pytest.mark.parametrize("mutate,match", [
    (lambda t: t[:t.index("[[hand_calc]]")] + "[requirement]\nmin_safety_factor = 1.5\n", "hand_calc"),
    (lambda t: t.replace("sizes_mm = [5.0, 3.5, 2.5]", "sizes_mm = [5.0, 4.9, 4.8]"), "ratio"),
    (lambda t: t.replace("sizes_mm = [5.0, 3.5, 2.5]", "sizes_mm = [5.0, 3.5]"), ">= 3"),
    (lambda t: t.replace("convergence_tol_pct = 1.0", "convergence_tol_pct = 1.0\nconvergance = 2"), "unknown key"),
    (lambda t: t.replace('params = "materials.steel"', 'params = "materials.unobtainium"'), "not found"),
    (lambda t: t.replace("min_safety_factor = 1.5", "min_safety_factor = 1.5\nmax_reaction_imbalance_pct = 5.0"),
     "0.5"),
])
def test_malformed_general_cases_error_out(tmp_path, mutate, match):
    text = mutate(CANTILEVER.format(name="cantilever_bad", load=TIP_TRACTION, sizes="[5.0, 3.5, 2.5]",
                                    hc_height="10.0"))
    root = _project(tmp_path, {"bad": text})
    r = _verify(root)
    assert r.returncode == 2, r.stdout + r.stderr
    out = json.loads(next((root / "out" / "verify").glob("*.json")).read_text())
    assert out["status"] == "error" and match in out["error"], out["error"]


def test_material_param_without_source_is_refused(tmp_path):
    root = _project(tmp_path, {"cant": CANTILEVER.format(name="cantilever_nosrc", load=TIP_TRACTION,
                                                         sizes="[5.0, 3.5, 2.5]", hc_height="10.0")})
    p = root / "params" / "params.toml"
    p.write_text(p.read_text().replace('source = "ASTM A36 minimum yield (test fixture, not a mill cert)"', ""))
    r = _verify(root)
    assert r.returncode == 2
    out =json.loads(next((root / "out" / "verify").glob("*.json")).read_text())
    assert "no source" in out["error"]
