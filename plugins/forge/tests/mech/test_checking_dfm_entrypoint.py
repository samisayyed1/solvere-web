"""End-to-end checking-dfm/scripts/verify.py against the fixture project:
box.py passes the FDM wall/hole rules but deliberately fails the FDM
clearance rule against its lid (a real DFM limit, not a geometry-spec one);
box_thin.py fails the FDM wall rule and its seeded-overstressed snap-fit
latch fails the PC allowable-strain check."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
FIXTURE_SRC = Path(__file__).resolve().parents[1] / "fixtures" / "mech_project"
VERIFY_SCRIPT = REPO_ROOT / "plugins" / "forge" / "skills" / "checking-dfm" / "scripts" / "verify.py"
# verify.py needs the CAD env (build123d et al, CONTRACTS.md SS10) regardless of which
# interpreter is running pytest itself (forge-python or a plain stdlib venv) -- prefer the
# real CAD python for the subprocess, matching tests/mech2's convention, and fall back to
# sys.executable only when it isn't installed (CI without the toolchain: this end-to-end
# test then can't run and should skip, never silently pass).
FORGE_PYTHON = Path.home() / ".forge" / "bin" / "forge-python"
PY = str(FORGE_PYTHON) if FORGE_PYTHON.exists() else sys.executable


@pytest.fixture
def project(tmp_path) -> Path:
    dest = tmp_path / "mech_project"
    shutil.copytree(FIXTURE_SRC, dest)
    return dest


def _run(project: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run([PY, str(VERIFY_SCRIPT), "--project", str(project), *extra],
                           capture_output=True, text=True, timeout=120)


def _result(project: Path, check_id: str) -> dict:
    return json.loads((project / "out" / "verify" / f"{check_id}.json").read_text())


def test_suite_fails_overall(project):
    proc = _run(project)
    assert proc.returncode == 1, proc.stdout + proc.stderr


def test_box_wall_and_hole_pass_fdm_rules(project):
    _run(project)
    assert _result(project, "dfm.wall_min_unsupported_mm.box")["status"] == "pass"
    assert _result(project, "dfm.hole_min_diameter_mm.box")["status"] == "pass"


def test_box_clearance_to_lid_fails_the_fdm_rule_even_though_geometry_spec_allows_it(project):
    """The same 0.3 mm clearance passes verifying-geometry's own 0.2 mm
    project requirement (see requirements/geometry/box.toml) but fails
    checking-dfm's stricter, process-sourced 1.0 mm FDM rule -- these are
    two different requirement sources and can legitimately disagree."""
    _run(project)
    result = _result(project, "dfm.clearance_moving_mm.box")
    assert result["status"] == "fail"
    assert result["measurements"][0]["value"] == pytest.approx(0.3, abs=1e-3)


def test_box_snap_fit_passes(project):
    _run(project)
    assert _result(project, "dfm.snap_fit.lid_latch.box")["status"] == "pass"


def test_snap_fit_strain_unit_is_percent(project):
    """M3 (review #1): root_strain_pct's value is already a percentage
    (0-100), so its unit must be '%', not the dimensionless '1' that used to
    mislabel it."""
    _run(project)
    result = _result(project, "dfm.snap_fit.lid_latch.box")
    m = next(x for x in result["measurements"] if x["name"] == "root_strain_pct")
    assert m["unit"] == "%"


def test_short_arm_warning_surfaces_in_the_check_result(project):
    """M3 (review #1): the short-arm warning used to be computed and then
    discarded -- it must actually reach out/verify/*.json's `notes`."""
    spec = project / "requirements" / "dfm" / "box.toml"
    spec.write_text(spec.read_text() + """
[[snap_fit]]
name = "short_latch"
requirement = "REQ-MECH-010"
material = "pc_makrolon"
deflection_mm = 0.3
length_mm = 5.0
thickness_mm = 1.2
taper = "constant"
frequent = false
""")
    _run(project)
    result = _result(project, "dfm.snap_fit.short_latch.box")
    assert result.get("notes"), "the short-arm warning must be recorded as the check's notes"
    assert "short-arm" in result["notes"] or "short arm" in result["notes"].lower()
    assert "BASF" in result["notes"]


def test_normal_length_arm_has_no_short_arm_warning(project):
    """The positive case for the above: an arm well above the L/h=10
    threshold must not carry a spurious warning."""
    _run(project)
    result = _result(project, "dfm.snap_fit.lid_latch.box")
    assert not result.get("notes")


def test_box_thin_wall_fails(project):
    _run(project)
    result = _result(project, "dfm.wall_min_unsupported_mm.box_thin")
    assert result["status"] == "fail"
    assert result["measurements"][0]["remediation"]


def test_box_thin_snap_fit_overstressed_latch_fails(project):
    _run(project)
    result = _result(project, "dfm.snap_fit.overstressed_latch.box_thin")
    assert result["status"] == "fail"
    assert result["measurements"][0]["value"] > 4.0  # PC allowable strain, percent


def test_unsupported_rule_family_is_a_hard_error_not_a_skip(project):
    spec = project / "requirements" / "dfm" / "box.toml"
    spec.write_text(spec.read_text() + '\n[[check]]\nrule = "bridge_max_structural_mm"\nrequirement = "REQ-MFG-001"\n')
    # bridge_max_structural_mm's check_family is "unsupported" in fdm.toml -- must hard-error, not silently skip.
    proc = _run(project, "--changed", "cad/box.py")
    assert proc.returncode == 2
    assert "no forge_cad measurement" in proc.stderr


def test_unknown_material_is_a_hard_error(project):
    spec = project / "requirements" / "dfm" / "box.toml"
    text = spec.read_text().replace('material = "pc_makrolon"', 'material = "unobtainium"')
    spec.write_text(text)
    proc = _run(project, "--changed", "cad/box.py")
    assert proc.returncode == 2
    assert "unknown material" in proc.stderr


def test_changed_params_toml_reruns_every_spec_and_catches_a_wall_violation(project):
    """Eval defect: --changed params/params.toml matched no spec file or
    [part].module, so `_iter_specs` returned [] and the entrypoint printed
    [SKIP] even though the new value could push a wall below the DFM
    minimum. Without the fix this fails: rc == 0, "[SKIP]" in stdout, and
    out/verify/dfm.wall_min_unsupported_mm.box.json is never written."""
    params_path = project / "params" / "params.toml"
    text = params_path.read_text()
    assert "value = 2.0" in text
    # fdm.toml's wall_min_unsupported_mm rule requires >= 1.2 mm; 1.0 mm
    # (box.py's actual built wall, driven by this param) fails it. (A wall
    # much thinner than this makes box.py's own 2.0 mm outer fillet
    # geometrically invalid -- an unrelated build error, not the DFM
    # violation this test is targeting.)
    params_path.write_text(text.replace(
        "[enclosure.wall_thickness]\nvalue = 2.0", "[enclosure.wall_thickness]\nvalue = 1.0", 1))

    proc = _run(project, "--changed", "params/params.toml")

    assert "[SKIP]" not in proc.stdout, proc.stdout + proc.stderr
    result = _result(project, "dfm.wall_min_unsupported_mm.box")
    assert result["status"] == "fail"
    m = next(x for x in result["measurements"] if x["name"] == "min_wall")
    assert m["value"] < 1.2
    assert "wall_min_unsupported_mm" in m["remediation"]


def test_changed_params_toml_still_passes_the_wall_rule_when_in_bounds(project):


def test_changed_params_toml_still_passes_when_the_value_stays_in_bounds(project):
    """Positive case: a params.toml edit that keeps the wall above the DFM
    minimum must still run (not [SKIP]) and pass."""
    params_path = project / "params" / "params.toml"
    text = params_path.read_text()
    params_path.write_text(text.replace(
        "[enclosure.wall_thickness]\nvalue = 2.0", "[enclosure.wall_thickness]\nvalue = 2.1", 1))

    proc = _run(project, "--changed", "params/params.toml")

    assert "[SKIP]" not in proc.stdout
    assert _result(project, "dfm.wall_min_unsupported_mm.box")["status"] == "pass"


def test_repeated_rule_for_one_part_does_not_overwrite_its_result_file(project):
    """A spec can legally list the same rule twice for one part (e.g. two
    [[check]] entries against different face subsets). Without
    disambiguation the second entry's result silently overwrote the
    first's out/verify/dfm.wall_min_unsupported_mm.box.json."""
    spec = project / "requirements" / "dfm" / "box.toml"
    spec.write_text(spec.read_text() + """
[[check]]
rule = "wall_min_unsupported_mm"
requirement = "REQ-MFG-001"
sample_count = 500
""")
    proc = _run(project, "--changed", "requirements/dfm/box.toml")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    first = _result(project, "dfm.wall_min_unsupported_mm.box")
    second = _result(project, "dfm.wall_min_unsupported_mm.box_2")
    assert first["status"] == "pass"
    assert second["status"] == "pass"


def test_repeated_snap_fit_name_for_one_part_does_not_overwrite_its_result_file(project):
    """Same collision, for [[snap_fit]] entries: two snap fits with the same
    name on the same part must not clobber each other's result file."""
    spec = project / "requirements" / "dfm" / "box.toml"
    spec.write_text(spec.read_text() + """
[[snap_fit]]
name = "lid_latch"
requirement = "REQ-MECH-010"
material = "pc_makrolon"
deflection_mm = 1.5
length_mm = 15.0
thickness_mm = 1.2
taper = "constant"
frequent = false
""")
    proc = _run(project, "--changed", "requirements/dfm/box.toml")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    first = _result(project, "dfm.snap_fit.lid_latch.box")
    second = _result(project, "dfm.snap_fit.lid_latch.box_2")
    assert first["status"] == "pass"
    assert second["status"] == "pass"


def test_skip_on_a_project_with_no_dfm_specs(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    proc = _run(empty)
    assert proc.returncode == 0
    assert "[SKIP]" in proc.stdout
