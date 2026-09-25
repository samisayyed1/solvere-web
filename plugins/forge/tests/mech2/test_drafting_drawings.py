"""S14: the legacy single-view [part] drawing spec (no `schema` key) must be
refused with a migration message, not run through its own weaker path -- it
predates [model] (a real part to measure against), the tolerance >= 0
check, and the scale validation the v2 (`schema = "forge.drawing/2"`) path
has. See tests/mech2/test_drafting_drawings_general.py for the v2 path's
end-to-end and seeded-wrong tests.
"""
from __future__ import annotations

import subprocess
import sys
import tomllib
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[2] / "skills" / "drafting-drawings"
SCRIPTS_DIR = SKILL_DIR / "scripts"
VERIFY_PY = SCRIPTS_DIR / "verify.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "bracket_rev_a.toml"
FORGE_PYTHON = Path.home() / ".forge" / "bin" / "forge-python"
PY = str(FORGE_PYTHON) if FORGE_PYTHON.exists() else sys.executable


def _run_verify(project: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PY, str(VERIFY_PY), "--project", str(project)],
        capture_output=True, text=True, timeout=60,
    )


def _write_legacy_spec(project: Path) -> Path:
    specs_dir = project / "cad" / "drawings"
    specs_dir.mkdir(parents=True, exist_ok=True)
    path = specs_dir / "bracket_rev_a.toml"
    path.write_text(FIXTURE.read_text())
    return path


def test_verify_py_refuses_the_legacy_part_spec_with_a_migration_message(tmp_path):
    """The fixture is a genuine pre-v2 spec (a bare [drawing]/[part]/[[dimension]]
    table with value_mm/tol_plus_mm, no `schema` key) -- it must ERROR, never
    silently pass or run through the old weaker checks."""
    _write_legacy_spec(tmp_path)
    r = _run_verify(tmp_path)
    assert r.returncode == 2, r.stdout + r.stderr
    out = r.stdout + r.stderr
    assert "legacy" in out.lower()
    assert "forge.drawing/2" in out
    assert "[model]" in out


def test_verify_py_migration_message_names_the_spec_file(tmp_path):
    """The refusal must be specific to the offending file, not a generic error."""
    _write_legacy_spec(tmp_path)
    r = _run_verify(tmp_path)
    assert "bracket_rev_a.toml" in (r.stdout + r.stderr)


def test_legacy_fixture_really_has_no_schema_key():
    """Guards the test fixture itself: if someone migrates bracket_rev_a.toml
    to v2 without updating this file, the refusal test above would start
    failing for the wrong reason (spec no longer legacy) rather than silently
    passing on a stale assumption."""
    data = tomllib.loads(FIXTURE.read_text())
    assert "schema" not in data
    assert "part" in data and "model" not in data


def test_verify_py_skips_cleanly_with_no_specs(tmp_path):
    r = _run_verify(tmp_path)
    assert r.returncode == 0
    assert "[SKIP]" in r.stdout
