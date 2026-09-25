"""M8 (review #1) seeded-wrong tests for checking-dfm/scripts/verify.py:

1. Rib/boss ratio-vs-ratio: a rule capping rib/boss thickness at 0.5x the
   nominal wall must compare the measured *ratio* against 0.5, never convert
   0.5 into an absolute millimetre limit and compare the ratio against that
   (that let an 0.8-ratio rib pass a 0.5 cap on a 2 mm wall).
2. Overhang vs. draft: an overhang rule (FDM/SLA "max overhang without
   support") must be evaluated only on downward-facing faces, as angle from
   *horizontal*, not reuse mold-draft's angle-from-*vertical* semantics
   (which failed every vertical wall).

Fixture parts/specs: plugins/forge/tests/fixtures/dfm_ratio_overhang/.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
FIXTURE_SRC = Path(__file__).resolve().parents[1] / "fixtures" / "dfm_ratio_overhang"
VERIFY_SCRIPT = REPO_ROOT / "plugins" / "forge" / "skills" / "checking-dfm" / "scripts" / "verify.py"
FORGE_PYTHON = Path.home() / ".forge" / "bin" / "forge-python"
PY = str(FORGE_PYTHON) if FORGE_PYTHON.exists() else sys.executable


@pytest.fixture
def project(tmp_path) -> Path:
    dest = tmp_path / "dfm_ratio_overhang"
    shutil.copytree(FIXTURE_SRC, dest)
    return dest


def _run(project: Path, spec_name: str) -> subprocess.CompletedProcess:
    """Run checking-dfm on exactly one requirements/dfm/<spec_name>.toml so
    each test is isolated from the other fixture specs in this project."""
    for f in (project / "requirements" / "dfm").glob("*.toml"):
        if f.name != f"{spec_name}.toml":
            f.unlink()
    return subprocess.run([PY, str(VERIFY_SCRIPT), "--project", str(project)],
                           capture_output=True, text=True, timeout=120)


def _result(project: Path, check_id: str) -> dict:
    return json.loads((project / "out" / "verify" / f"{check_id}.json").read_text())


# --- rib/boss ratio-vs-ratio -------------------------------------------

def test_rib_over_ratio_cap_fails(project):
    """0.8 ratio (1.6 mm rib / 2.0 mm wall) on a 0.5x cap: must FAIL, and the
    measurement itself must be the ratio (~0.8), never a millimetre value."""
    proc = _run(project, "rib_bad")
    assert proc.returncode == 1, proc.stdout + proc.stderr
    result = _result(project, "dfm.rib_max_ratio_of_wall.rib_bad")
    assert result["status"] == "fail"
    m = result["measurements"][0]
    assert m["name"] == "boss_rib_ratio"
    assert m["unit"] == "1"
    assert m["value"] == pytest.approx(0.8, abs=1e-3)
    assert m["limit"]["max"] == pytest.approx(0.5, abs=1e-6), (
        "the limit compared against the ratio must itself be a bare ratio (0.5), "
        "not 0.5 * nominal_wall_mm converted to millimetres"
    )
    assert not m["pass"]
    assert len(m["remediation"]) >= 10


def test_rib_under_ratio_cap_passes(project):
    """0.4 ratio (0.8 mm rib / 2.0 mm wall) on the same 0.5x cap: must PASS."""
    proc = _run(project, "rib_good")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    result = _result(project, "dfm.rib_max_ratio_of_wall.rib_good")
    assert result["status"] == "pass"
    m = result["measurements"][0]
    assert m["value"] == pytest.approx(0.4, abs=1e-3)
    assert m["limit"]["max"] == pytest.approx(0.5, abs=1e-6)


# --- overhang vs. draft --------------------------------------------------

def test_30deg_downward_overhang_fails_45deg_limit(project):
    """A genuine downward-facing overhang at 30 deg from horizontal must FAIL
    a 45 deg 'max overhang without support' limit."""
    proc = _run(project, "ramp")
    assert proc.returncode == 1, proc.stdout + proc.stderr
    result = _result(project, "dfm.overhang_max_deg.ramp_overhang")
    assert result["status"] == "fail"
    measurements = result["measurements"]
    assert len(measurements) == 1, "exactly one downward-facing face on this wedge"
    m = measurements[0]
    assert m["name"].startswith("overhang_face_")
    assert m["unit"] == "deg"
    assert m["value"] == pytest.approx(30.0, abs=0.5)
    assert m["limit"]["min"] == pytest.approx(45.0, abs=1e-6)
    assert not m["pass"]
    assert len(m["remediation"]) >= 10


def test_vertical_wall_passes_the_overhang_check(project):
    """A vertical side wall (explicitly selected, not the flat bottom) is not
    an overhang at all and must PASS -- before the fix, geometry.draft's
    angle-from-vertical was reused here and every vertical wall failed."""
    proc = _run(project, "vertical")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    result = _result(project, "dfm.overhang_max_deg.vertical_wall")
    assert result["status"] == "pass"
    m = result["measurements"][0]
    assert m["name"] == "overhang_none_found", (
        "a vertical face is not downward-facing at all and must be filtered "
        "out before the angle-vs-limit comparison, not measured and happen "
        "to pass"
    )
    assert m["pass"]


def test_skip_on_a_project_with_no_dfm_specs(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    proc = subprocess.run([PY, str(VERIFY_SCRIPT), "--project", str(empty)],
                           capture_output=True, text=True, timeout=60)
    assert proc.returncode == 0
    assert "[SKIP]" in proc.stdout
