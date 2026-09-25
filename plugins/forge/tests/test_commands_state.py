"""Tests for `forge state show` (lib/forge/commands/state.py, CONTRACTS.md §11)."""

from __future__ import annotations

import json
from pathlib import Path

from forge import state as state_lib
from forge.cli import main


def _run(capsys, argv, repo_root):
    code = main(argv, repo_root=repo_root)
    out = capsys.readouterr().out
    return code, out


def test_state_show_on_fresh_project(tmp_path, capsys, repo_root):
    code, out = _run(capsys, ["state", "--project", str(tmp_path), "show"], repo_root)
    assert code == 0
    assert "gate: (unset)" in out
    assert "consecutive Stop blocks: 0" in out


def test_state_show_json(tmp_path, capsys, repo_root):
    state_lib.save(tmp_path, {"gate": "G2", "stop_block_count": 3})
    code, out = _run(capsys, ["state", "--project", str(tmp_path), "show", "--json"], repo_root)
    assert code == 0
    data = json.loads(out)
    assert data["gate"] == "G2"
    assert data["stop_block_count"] == 3


def test_state_show_renders_findings_and_failing_checks(tmp_path, capsys, repo_root):
    state_lib.write_precompact_snapshot(
        tmp_path, modified_files=["cad/a.py"], gate="G1",
        open_findings=[{"id": "REQ-MECH-001", "verdict": "FAIL", "finding": "bad"}],
        failing_checks=["geometry.min_wall"],
    )
    code, out = _run(capsys, ["state", "--project", str(tmp_path), "show"], repo_root)
    assert code == 0
    assert "REQ-MECH-001" in out
    assert "geometry.min_wall" in out
    assert "cad/a.py" in out
