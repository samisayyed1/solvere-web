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


def test_skip_on_a_project_with_no_dfm_specs(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    proc = _run(empty)
    assert proc.returncode == 0
    assert "[SKIP]" in proc.stdout
