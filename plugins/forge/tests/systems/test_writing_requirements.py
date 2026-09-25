"""writing-requirements/scripts/verify.py: EARS lint (CONTRACTS.md §6, §9).

A good fixture must pass; each seeded-wrong fixture must fail with the
specific finding it was designed to trigger, proving the lint can fail.
"""
from __future__ import annotations

import json

from .conftest import load_skill_module

verify = load_skill_module("writing-requirements")

GOOD_REQUIREMENTS = """\
## REQ-SYS-001

The HydroSense sensor shall store each moisture reading with a UTC timestamp.

Rationale: field agronomists need a defensible time series.
Verify: test

## REQ-SYS-002

When the user presses the Measure button, the HydroSense sensor shall
display a moisture reading within 2.0 s.

Rationale: previous generation was too slow per stakeholder interviews.
Verify: test
"""


def _write_requirements(tmp_path, text: str):
    reqs_dir = tmp_path / "requirements"
    reqs_dir.mkdir(parents=True, exist_ok=True)
    (reqs_dir / "requirements.md").write_text(text)
    return tmp_path


def _measurement(result: dict, suffix: str) -> dict | None:
    """Find a measurement whose name ends with ``suffix`` (measurement names
    are ``REQ-ID@Lnn.rule`` -- match on the rule suffix, not the exact key,
    so tests don't need to know the fixture's line numbers)."""
    return next((m for m in result["measurements"] if m["name"].endswith(suffix)), None)


def test_good_fixture_passes(tmp_path):
    project = _write_requirements(tmp_path, GOOD_REQUIREMENTS)
    assert verify.run(project, None) == 0
    out = json.loads((project / "out/verify/requirements.ears_lint.json").read_text())
    assert out["status"] == "pass"
    assert all(m["pass"] for m in out["measurements"])


def test_bad_ears_pattern_fails(tmp_path):
    bad = """\
## REQ-SYS-001

Moisture readings get stored somewhere eventually.

Rationale: because.
Verify: test
"""
    project = _write_requirements(tmp_path, bad)
    assert verify.run(project, None) == 1
    out = json.loads((project / "out/verify/requirements.ears_lint.json").read_text())
    m = _measurement(out, ".ears_pattern")
    assert m is not None and m["pass"] is False
    assert len(m["remediation"]) >= 10


def test_missing_verify_line_fails(tmp_path):
    bad = """\
## REQ-SYS-001

The HydroSense sensor shall store each moisture reading with a UTC timestamp.

Rationale: field agronomists need a defensible time series.
"""
    project = _write_requirements(tmp_path, bad)
    assert verify.run(project, None) == 1
    out = json.loads((project / "out/verify/requirements.ears_lint.json").read_text())
    m = _measurement(out, ".has_verify_line")
    assert m is not None and m["pass"] is False


def test_invalid_verify_method_fails(tmp_path):
    bad = """\
## REQ-SYS-001

The HydroSense sensor shall store each moisture reading with a UTC timestamp.

Rationale: field agronomists need a defensible time series.
Verify: manual
"""
    project = _write_requirements(tmp_path, bad)
    assert verify.run(project, None) == 1
    out = json.loads((project / "out/verify/requirements.ears_lint.json").read_text())
    m = _measurement(out, ".verify_method")
    assert m is not None and m["pass"] is False


def test_number_without_unit_fails(tmp_path):
    bad = """\
## REQ-MECH-004

The enclosure shall have a wall thickness of at least 2.

Rationale: FDM min wall.
Verify: analysis
"""
    project = _write_requirements(tmp_path, bad)
    assert verify.run(project, None) == 1
    out = json.loads((project / "out/verify/requirements.ears_lint.json").read_text())
    m = _measurement(out, ".numbers_have_units")
    assert m is not None and m["pass"] is False


def test_vague_word_fails(tmp_path):
    bad = """\
## REQ-SYS-001

The HydroSense app shall have a fast and user-friendly interface.

Rationale: usability matters.
Verify: demo
"""
    project = _write_requirements(tmp_path, bad)
    assert verify.run(project, None) == 1
    out = json.loads((project / "out/verify/requirements.ears_lint.json").read_text())
    m = _measurement(out, ".no_vague_words")
    assert m is not None and m["pass"] is False


def test_duplicate_id_fails(tmp_path):
    bad = GOOD_REQUIREMENTS.replace("REQ-SYS-002", "REQ-SYS-001")
    project = _write_requirements(tmp_path, bad)
    assert verify.run(project, None) == 1
    out = json.loads((project / "out/verify/requirements.ears_lint.json").read_text())
    unique_id_measurements = [m for m in out["measurements"] if m["name"].endswith(".unique_id")]
    # one block (the first) passes, the reused second block fails
    assert len(unique_id_measurements) == 2
    assert any(m["pass"] is False for m in unique_id_measurements)


def test_two_shall_clauses_fails(tmp_path):
    bad = """\
## REQ-SYS-001

The HydroSense sensor shall log readings and shall alert on failure.

Rationale: two behaviours bundled.
Verify: test
"""
    project = _write_requirements(tmp_path, bad)
    assert verify.run(project, None) == 1
    out = json.loads((project / "out/verify/requirements.ears_lint.json").read_text())
    m = _measurement(out, ".one_shall")
    assert m is not None and m["pass"] is False


def test_no_requirements_file_is_skip_not_pass_or_fail(tmp_path):
    assert verify.run(tmp_path, None) == 0
    assert not (tmp_path / "out/verify/requirements.ears_lint.json").exists()


def test_changed_filter_skips_unrelated_change(tmp_path):
    project = _write_requirements(tmp_path, GOOD_REQUIREMENTS)
    other = tmp_path / "cad" / "part.py"
    other.parent.mkdir(parents=True, exist_ok=True)
    other.write_text("# irrelevant")
    assert verify.run(project, [str(other)]) == 0
    assert not (project / "out/verify/requirements.ears_lint.json").exists()
