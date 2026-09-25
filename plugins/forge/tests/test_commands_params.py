"""Tests for `forge params get|set|lint` (lib/forge/commands/params.py, CONTRACTS.md §2)."""

from __future__ import annotations

import json
from pathlib import Path

from forge.cli import main

PARAMS_TOML = """\
[enclosure.wall_thickness]
value = 2.0
unit = "mm"
status = "assumed"
source = "R5d FDM min wall 0.8-1.2mm; chosen 2.0 for stiffness"

[enclosure.height]
value = 40.0
unit = "mm"
status = "verified"
source = "measured on rev A prototype"
verified_by = "Alice Chen"
evidence = ["EV-0001"]
"""


def _run(capsys, argv, repo_root):
    code = main(argv, repo_root=repo_root)
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def _make_project(tmp_path: Path) -> Path:
    (tmp_path / "params").mkdir(parents=True)
    (tmp_path / "params" / "params.toml").write_text(PARAMS_TOML)
    return tmp_path


def test_get_prints_a_leaf(tmp_path, capsys, repo_root):
    project = _make_project(tmp_path)
    code, out, _err = _run(capsys, ["params", "--project", str(project), "get", "enclosure.wall_thickness"], repo_root)
    assert code == 0
    assert "value: 2.0" in out
    assert "status: assumed" in out


def test_get_json(tmp_path, capsys, repo_root):
    project = _make_project(tmp_path)
    code, out, _err = _run(capsys, ["params", "--project", str(project), "get", "enclosure.wall_thickness", "--json"], repo_root)
    assert code == 0
    assert json.loads(out)["unit"] == "mm"


def test_get_missing_key_fails(tmp_path, capsys, repo_root):
    project = _make_project(tmp_path)
    code, _out, err = _run(capsys, ["params", "--project", str(project), "get", "nope.nope"], repo_root)
    assert code == 1
    assert "no such param" in err


def test_set_unverified_param_no_justification_needed(tmp_path, capsys, repo_root):
    project = _make_project(tmp_path)
    code, out, _err = _run(capsys, [
        "params", "--project", str(project), "set", "enclosure.wall_thickness", "--value", "2.5",
    ], repo_root)
    assert code == 0
    assert "wrote" in out
    text = (project / "params" / "params.toml").read_text()
    assert "value = 2.5" in text


def test_set_verified_param_without_justification_is_rejected(tmp_path, capsys, repo_root):
    """Sabotage case: changing a verified value with no --justification must fail."""
    project = _make_project(tmp_path)
    code, _out, err = _run(capsys, [
        "params", "--project", str(project), "set", "enclosure.height", "--value", "41",
    ], repo_root)
    assert code == 1
    assert "justification" in err
    # and the file on disk must be untouched
    assert "value = 40.0" in (project / "params" / "params.toml").read_text()


def test_set_verified_param_with_justification_succeeds_and_logs_changelog(tmp_path, capsys, repo_root):
    project = _make_project(tmp_path)
    code, out, _err = _run(capsys, [
        "params", "--project", str(project), "set", "enclosure.height", "--value", "42",
        "--justification", "measured on rev B prototype with calipers",
    ], repo_root)
    assert code == 0
    assert "wrote" in out
    text = (project / "params" / "params.toml").read_text()
    assert "value = 42" in text
    changelog = (project / "params" / "CHANGELOG.md").read_text()
    assert "enclosure.height" in changelog
    assert "measured on rev B prototype with calipers" in changelog
    assert "40.0" in changelog  # old value recorded


def test_set_too_short_justification_is_rejected(tmp_path, capsys, repo_root):
    project = _make_project(tmp_path)
    code, _out, err = _run(capsys, [
        "params", "--project", str(project), "set", "enclosure.height", "--value", "42", "--justification", "x",
    ], repo_root)
    assert code == 1
    assert "justification" in err


def test_set_new_param_requires_all_core_fields(tmp_path, capsys, repo_root):
    project = _make_project(tmp_path)
    code, _out, err = _run(capsys, [
        "params", "--project", str(project), "set", "enclosure.lid_radius", "--value", "3.0",
    ], repo_root)
    assert code == 1
    assert "does not exist yet" in err


def test_set_new_param_with_all_fields_creates_it(tmp_path, capsys, repo_root):
    project = _make_project(tmp_path)
    code, _out, _err = _run(capsys, [
        "params", "--project", str(project), "set", "enclosure.lid_radius",
        "--value", "3.0", "--unit", "mm", "--status", "assumed", "--source", "chosen for aesthetics",
    ], repo_root)
    assert code == 0
    code2, out2, _err2 = _run(capsys, ["params", "--project", str(project), "get", "enclosure.lid_radius", "--json"], repo_root)
    assert code2 == 0
    assert json.loads(out2)["value"] == 3.0


def test_set_schema_invalid_leaf_rejected(tmp_path, capsys, repo_root):
    project = _make_project(tmp_path)
    code, _out, err = _run(capsys, [
        "params", "--project", str(project), "set", "enclosure.wall_thickness", "--unit", "",
    ], repo_root)
    assert code == 1
    assert "schemas/params.schema.json" in err


def test_set_boolean_and_string_value_coercion(tmp_path, capsys, repo_root):
    project = _make_project(tmp_path)
    _run(capsys, [
        "params", "--project", str(project), "set", "flags.uses_heatset_inserts",
        "--value", "true", "--unit", "1", "--status", "assumed", "--source", "design choice",
    ], repo_root)
    code, out, _err = _run(capsys, ["params", "--project", str(project), "get", "flags.uses_heatset_inserts", "--json"], repo_root)
    assert code == 0
    assert json.loads(out)["value"] is True


def test_lint_reports_zero_errors_on_valid_file(tmp_path, capsys, repo_root):
    project = _make_project(tmp_path)
    code, out, _err = _run(capsys, ["params", "--project", str(project), "lint"], repo_root)
    assert code == 0
    assert "2 param(s), 0 error(s)" in out


def test_lint_catches_missing_source_field(tmp_path, capsys, repo_root):
    """Sabotage case: a param leaf with a required field stripped must fail lint."""
    project = _make_project(tmp_path)
    (project / "params" / "params.toml").write_text(
        '[enclosure.wall_thickness]\nvalue = 2.0\nunit = "mm"\nstatus = "assumed"\n'
    )
    code, out, _err = _run(capsys, ["params", "--project", str(project), "lint"], repo_root)
    assert code == 1
    assert "source" in out


def test_lint_missing_file(tmp_path, capsys, repo_root):
    code, _out, err = _run(capsys, ["params", "--project", str(tmp_path), "lint"], repo_root)
    assert code == 1
    assert "not found" in err


def test_lint_json_output(tmp_path, capsys, repo_root):
    project = _make_project(tmp_path)
    code, out, _err = _run(capsys, ["params", "--project", str(project), "lint", "--json"], repo_root)
    assert code == 0
    data = json.loads(out)
    assert data["count"] == 2
    assert data["errors"] == []
