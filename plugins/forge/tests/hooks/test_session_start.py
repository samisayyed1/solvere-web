"""Tests for hooks/session_start.py (CONTRACTS.md §13, ADR-001 §4-5)."""

from __future__ import annotations

import json
from pathlib import Path

from .hookutil import forge_project, make_forge_project, non_forge_project, run_hook


def test_outside_forge_project_prints_one_line_hint(non_forge_project):
    """SessionStart is the one hook allowed to say something outside a Forge
    product repo (brief §3.4)."""
    result = run_hook("session_start.py", {"cwd": str(non_forge_project), "source": "startup"})
    assert result.returncode == 0
    assert "additionalContext" in result.output
    assert "forge.toml" in result.output["additionalContext"]


def test_prints_the_current_gate(forge_project):
    result = run_hook("session_start.py", {"cwd": str(forge_project), "source": "startup"})
    assert result.returncode == 0
    assert "gate G1" in result.output["additionalContext"]


def test_reports_failing_checks(forge_project):
    out_dir = forge_project / "out" / "verify"
    out_dir.mkdir(parents=True)
    (out_dir / "geometry.min_wall.json").write_text(json.dumps({
        "schema": "forge.check/1", "check_id": "geometry.min_wall", "target": "cad/enclosure.py",
        "status": "fail", "level": "L1", "measurements": [], "tool_versions": {}, "git_sha": "x",
        "started": "2026-01-01T00:00:00Z", "duration_s": 0.1,
    }))
    result = run_hook("session_start.py", {"cwd": str(forge_project), "source": "startup"})
    assert "geometry.min_wall" in result.output["additionalContext"]


def test_reports_open_review_findings(forge_project):
    verdict = {
        "schema": "forge.verdict/1", "reviewer": "red-team", "gate": "G1", "subject": "smoke",
        "criteria": [{"id": "REQ-MECH-001", "verdict": "FAIL", "evidence": [], "finding": "bad",
                      "severity": "major", "affects": ["function"]}],
        "overall": "FAIL", "summary": "1 defect", "not_checked": [],
    }
    (forge_project / "reviews" / "G1.md").write_text(f"# G1\n\n```json\n{json.dumps(verdict)}\n```\n")
    result = run_hook("session_start.py", {"cwd": str(forge_project), "source": "startup"})
    assert "Open review findings: 1" in result.output["additionalContext"]


def test_reports_open_assumptions_and_risks(forge_project):
    (forge_project / "ASSUMPTIONS.md").write_text(
        "# Assumptions\n\n## Open\n\n| ID | Assumption |\n|---|---|\n| A-001 | wall is thick enough |\n"
        "| A-002 | height is fine |\n\n## Retired\n\n| ID | Assumption | Retired by | Date |\n|---|---|---|---|\n"
    )
    (forge_project / "RISKS.md").write_text(
        "# Risks\n\n| ID | Risk | Severity | Likelihood | Mitigation | Status | Owner |\n"
        "|---|---|---|---|---|---|---|\n"
        "| R-001 | snap fit untested | Medium | Medium | measure | open | mech |\n"
        "| R-002 | already handled | Low | Low | done | closed | mech |\n"
    )
    result = run_hook("session_start.py", {"cwd": str(forge_project), "source": "startup"})
    text = result.output["additionalContext"]
    assert "2 in ASSUMPTIONS.md" in text
    assert "1 in RISKS.md" in text


def test_compact_source_reinjects_precompact_summary(forge_project):
    run_hook("pre_compact.py", {"cwd": str(forge_project), "trigger": "auto"})
    result = run_hook("session_start.py", {"cwd": str(forge_project), "source": "compact"})
    text = result.output["additionalContext"]
    assert "restored after compaction" in text


def test_non_compact_source_does_not_include_compaction_summary(forge_project):
    result = run_hook("session_start.py", {"cwd": str(forge_project), "source": "startup"})
    assert "restored after compaction" not in result.output["additionalContext"]


def test_additional_context_stays_under_2000_chars(forge_project):
    out_dir = forge_project / "out" / "verify"
    out_dir.mkdir(parents=True)
    for i in range(40):
        (out_dir / f"check_{i}.json").write_text(json.dumps({
            "schema": "forge.check/1", "check_id": f"domain.check_{i}", "target": "x",
            "status": "fail", "level": "L1", "measurements": [], "tool_versions": {}, "git_sha": "x",
            "started": "2026-01-01T00:00:00Z", "duration_s": 0.1,
        }))
    result = run_hook("session_start.py", {"cwd": str(forge_project), "source": "startup"})
    assert len(result.output["additionalContext"]) <= 2000


def test_missing_forge_toml_gate_shows_unset(tmp_path):
    project = make_forge_project(tmp_path / "proj2")
    (project / "forge.toml").write_text("[project]\nname = \"x\"\n")
    result = run_hook("session_start.py", {"cwd": str(project), "source": "startup"})
    assert "(unset)" in result.output["additionalContext"]
