"""End-to-end verifying-geometry/scripts/verify.py against the fixture
project (plugins/forge/tests/fixtures/mech_project): a PASS case (box.py)
and a seeded-FAIL case (box_thin.py) in one spec directory, plus the
--changed/--fast/[SKIP] contract (CONTRACTS.md §9)."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")  # CAD env only (~/.forge/bin/forge-python)

REPO_ROOT = Path(__file__).resolve().parents[4]
FIXTURE_SRC = Path(__file__).resolve().parents[1] / "fixtures" / "mech_project"
VERIFY_SCRIPT = REPO_ROOT / "plugins" / "forge" / "skills" / "verifying-geometry" / "scripts" / "verify.py"
SCHEMA = json.loads((REPO_ROOT / "plugins" / "forge" / "schemas" / "check-result.schema.json").read_text())
# verify.py needs the CAD env (build123d et al, CONTRACTS.md SS10) regardless of which
# interpreter is running pytest itself -- prefer the real CAD python for the subprocess
# (matches tests/mech2's convention), falling back to sys.executable only when it isn't
# installed.
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


def test_full_suite_fails_overall_because_box_thin_is_seeded_wrong(project):
    proc = _run(project)
    assert proc.returncode == 1, proc.stdout + proc.stderr


def test_box_passes_every_check(project):
    _run(project)
    for check_id in ("geometry.validity.box", "geometry.watertight.box", "geometry.bbox.box",
                      "geometry.volume.box", "geometry.mass.box", "geometry.min_wall.box",
                      "geometry.min_radius.box", "geometry.hole_edge.box", "geometry.clearance.box",
                      "geometry.interference.box"):
        result = _result(project, check_id)
        assert result["status"] == "pass", f"{check_id}: {result}"


def test_box_thin_min_wall_and_volume_fail_with_remediation(project):
    _run(project)
    for check_id in ("geometry.min_wall.box_thin", "geometry.volume.box_thin"):
        result = _result(project, check_id)
        assert result["status"] == "fail"
        failing = [m for m in result["measurements"] if not m["pass"]]
        assert failing and all(len(m["remediation"]) >= 10 for m in failing)


def test_box_thin_bbox_still_passes_envelope_is_unaffected_by_wall(project):
    _run(project)
    result = _result(project, "geometry.bbox.box_thin")
    assert result["status"] == "pass"


def test_every_written_result_matches_the_check_result_schema(project):
    _run(project)
    validator = jsonschema.Draft202012Validator(SCHEMA)
    files = list((project / "out" / "verify").glob("*.json"))
    assert len(files) == 14  # 10 [[check]] entries in box.toml + 4 in box_thin.toml
    for f in files:
        doc = json.loads(f.read_text())
        errors = list(validator.iter_errors(doc))
        assert not errors, f"{f.name}: {[e.message for e in errors]}"


def test_changed_filters_to_only_the_matching_part(project):
    proc = _run(project, "--changed", "cad/box_thin.py")
    assert proc.returncode == 1
    written = {f.stem for f in (project / "out" / "verify").glob("*.json")}
    assert all(name.endswith("box_thin") for name in written)
    assert "geometry.validity.box" not in written


def test_fast_mode_still_runs_and_still_fails(project):
    proc = _run(project, "--fast")
    assert proc.returncode == 1


def test_skip_on_a_project_with_no_specs(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    proc = _run(empty)
    assert proc.returncode == 0
    assert "[SKIP]" in proc.stdout


def test_never_fakes_a_pass_on_a_module_that_fails_to_build(project):
    bad = project / "cad" / "box.py"
    bad.write_text("import build123d as bd\ndef build(params=None):\n    raise RuntimeError('boom')\n")
    proc = _run(project, "--changed", "cad/box.py")
    assert proc.returncode == 2
    assert "boom" in proc.stderr or "boom" in proc.stdout
