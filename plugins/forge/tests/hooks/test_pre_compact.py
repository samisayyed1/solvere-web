"""Tests for hooks/pre_compact.py (CONTRACTS.md §13)."""

from __future__ import annotations

import json
from pathlib import Path

from .hookutil import LIB_DIR, forge_project, non_forge_project, run_hook
import sys

sys.path.insert(0, str(LIB_DIR))
from forge import state as state_lib  # noqa: E402


def test_noop_outside_forge_project(non_forge_project):
    result = run_hook("pre_compact.py", {"cwd": str(non_forge_project)})
    assert result.returncode == 0
    assert result.output is None
    assert not (non_forge_project / ".forge").exists()


def test_never_blocks_compaction(forge_project):
    result = run_hook("pre_compact.py", {"cwd": str(forge_project), "trigger": "auto"})
    assert result.returncode == 0


def test_writes_state_snapshot_with_gate_and_modified_files(forge_project):
    (forge_project / "cad" / "enclosure.py").write_text("print('changed')\n")
    run_hook("pre_compact.py", {"cwd": str(forge_project), "trigger": "manual"})

    data = state_lib.load(forge_project)
    assert data["gate"] == "G1"
    assert "cad/enclosure.py" in data["modified_files"]


def test_captures_open_review_findings(forge_project):
    verdict = {
        "schema": "forge.verdict/1", "reviewer": "red-team", "gate": "G1", "subject": "smoke",
        "criteria": [
            {"id": "REQ-MECH-001", "verdict": "FAIL", "evidence": [], "finding": "bad", "severity": "major",
             "affects": ["function"]},
            {"id": "REQ-MECH-002", "verdict": "PASS", "evidence": ["x"], "finding": "ok"},
        ],
        "overall": "FAIL", "summary": "1 defect", "not_checked": [],
    }
    review_text = f"# G1 review\n\n```json\n{json.dumps(verdict)}\n```\n\nHuman sign-off: ____________  Name: ____  Date: ____  Decision: PASS / FAIL\n"
    (forge_project / "reviews" / "G1.md").write_text(review_text)

    run_hook("pre_compact.py", {"cwd": str(forge_project)})

    data = state_lib.load(forge_project)
    assert len(data["open_findings"]) == 1
    assert data["open_findings"][0]["id"] == "REQ-MECH-001"


def test_captures_failing_checks(forge_project):
    out_dir = forge_project / "out" / "verify"
    out_dir.mkdir(parents=True)
    (out_dir / "geometry.min_wall.json").write_text(json.dumps({
        "schema": "forge.check/1", "check_id": "geometry.min_wall", "target": "cad/enclosure.py",
        "status": "fail", "level": "L1", "measurements": [], "tool_versions": {}, "git_sha": "x",
        "started": "2026-01-01T00:00:00Z", "duration_s": 0.1,
    }))
    run_hook("pre_compact.py", {"cwd": str(forge_project)})
    data = state_lib.load(forge_project)
    assert "geometry.min_wall" in data["failing_checks"]
