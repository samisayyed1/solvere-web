"""Tests for hooks/subagent_stop.py -- reviewer verdict-schema enforcement (CONTRACTS.md §5, §13)."""

from __future__ import annotations

import json

from .hookutil import forge_project, non_forge_project, run_hook

VALID_VERDICT = {
    "schema": "forge.verdict/1", "reviewer": "verification-evaluator", "gate": "G2", "subject": "enclosure rev B",
    "criteria": [{
        "id": "REQ-MECH-004", "verdict": "FAIL", "evidence": ["out/verify/geometry.min_wall.json"],
        "finding": "Lid lip wall 1.62 mm below 2.0 mm minimum.", "severity": "major",
        "affects": ["manufacturability", "function"],
    }],
    "overall": "FAIL", "summary": "1 major defect; 11 criteria PASS.", "not_checked": [],
}


def _msg_with_block(payload: dict) -> str:
    return f"Reviewed the design.\n\n```json\n{json.dumps(payload)}\n```\n"


def test_noop_outside_forge_project(non_forge_project):
    result = run_hook("subagent_stop.py", {
        "cwd": str(non_forge_project), "agent_type": "forge:red-team", "last_assistant_message": "no json",
    })
    assert result.returncode == 0
    assert result.output is None


def test_non_judge_agent_is_ignored(forge_project):
    result = run_hook("subagent_stop.py", {
        "cwd": str(forge_project), "agent_type": "forge:mechanical-engineer",
        "last_assistant_message": "no verdict here at all",
    })
    assert result.returncode == 0
    assert result.output is None


def test_empty_agent_type_is_ignored(forge_project):
    result = run_hook("subagent_stop.py", {
        "cwd": str(forge_project), "agent_type": "", "last_assistant_message": "no verdict here",
    })
    assert result.returncode == 0
    assert result.output is None


def test_valid_verdict_from_verification_evaluator_passes(forge_project):
    result = run_hook("subagent_stop.py", {
        "cwd": str(forge_project), "agent_type": "forge:verification-evaluator",
        "last_assistant_message": _msg_with_block(VALID_VERDICT),
    })
    assert result.returncode == 0
    assert result.output is None


def test_valid_verdict_from_red_team_passes(forge_project):
    payload = dict(VALID_VERDICT, reviewer="red-team")
    result = run_hook("subagent_stop.py", {
        "cwd": str(forge_project), "agent_type": "forge:red-team",
        "last_assistant_message": _msg_with_block(payload),
    })
    assert result.returncode == 0
    assert result.output is None


def test_missing_verdict_block_blocks(forge_project):
    """Sabotage case: a judge that free-forms its answer with no ```json block must be rejected."""
    result = run_hook("subagent_stop.py", {
        "cwd": str(forge_project), "agent_type": "forge:red-team",
        "last_assistant_message": "Looks fine to me, no issues found.",
    })
    assert result.returncode == 2
    assert result.output["decision"] == "block"
    assert "```json" in result.output["reason"] or "fenced" in result.output["reason"]


def test_malformed_json_block_blocks(forge_project):
    result = run_hook("subagent_stop.py", {
        "cwd": str(forge_project), "agent_type": "forge:red-team",
        "last_assistant_message": "```json\n{not: valid json,,,}\n```",
    })
    assert result.returncode == 2
    assert result.output["decision"] == "block"


def test_schema_invalid_verdict_blocks_with_precise_errors(forge_project):
    """Sabotage case: a FAIL criterion missing severity/affects must be rejected
    with the actual schema errors, not a generic message."""
    bad = json.loads(json.dumps(VALID_VERDICT))
    del bad["criteria"][0]["severity"]
    del bad["criteria"][0]["affects"]
    result = run_hook("subagent_stop.py", {
        "cwd": str(forge_project), "agent_type": "forge:verification-evaluator",
        "last_assistant_message": _msg_with_block(bad),
    })
    assert result.returncode == 2
    assert "severity" in result.output["reason"]
    assert "affects" in result.output["reason"]


def test_uses_the_last_json_block_when_several_present(forge_project):
    """The reviewer may think out loud in earlier ```json blocks; only the LAST one counts."""
    bad_block = "```json\n{\"scratch\": \"notes\"}\n```"
    good_block = f"```json\n{json.dumps(VALID_VERDICT)}\n```"
    message = f"Some notes first.\n\n{bad_block}\n\nFinal verdict:\n\n{good_block}"
    result = run_hook("subagent_stop.py", {
        "cwd": str(forge_project), "agent_type": "forge:red-team", "last_assistant_message": message,
    })
    assert result.returncode == 0
    assert result.output is None


def test_wrong_schema_const_blocks(forge_project):
    bad = json.loads(json.dumps(VALID_VERDICT))
    bad["schema"] = "forge.verdict/2"
    result = run_hook("subagent_stop.py", {
        "cwd": str(forge_project), "agent_type": "forge:verification-evaluator",
        "last_assistant_message": _msg_with_block(bad),
    })
    assert result.returncode == 2


# ---------------------------------------------------------------------------
# review #1, M5: overall PASS only if every criterion is PASS
# ---------------------------------------------------------------------------

def _pass_criterion(cid: str) -> dict:
    return {"id": cid, "verdict": "PASS", "evidence": ["out/verify/geometry.min_wall.json"], "finding": "ok"}


def test_overall_pass_with_a_failing_criterion_is_blocked(forge_project):
    """Seeded wrong: overall PASS over a critical FAIL used to exit 0."""
    payload = dict(VALID_VERDICT, overall="PASS",
                   criteria=[_pass_criterion("REQ-MECH-001"),
                             dict(VALID_VERDICT["criteria"][0], severity="critical")])
    result = run_hook("subagent_stop.py", {
        "cwd": str(forge_project), "agent_type": "forge:verification-evaluator",
        "last_assistant_message": _msg_with_block(payload),
    })
    assert result.returncode == 2
    assert result.output["decision"] == "block"
    assert "overall is PASS but these criteria are not PASS: REQ-MECH-004=FAIL" in result.output["reason"]


def test_overall_pass_with_a_blocked_criterion_is_blocked(forge_project):
    payload = dict(VALID_VERDICT, overall="PASS",
                   criteria=[{"id": "REQ-MECH-002", "verdict": "BLOCKED", "evidence": [], "finding": "no data"}])
    result = run_hook("subagent_stop.py", {
        "cwd": str(forge_project), "agent_type": "forge:red-team",
        "last_assistant_message": _msg_with_block(payload),
    })
    assert result.returncode == 2
    assert "REQ-MECH-002=BLOCKED" in result.output["reason"]


def test_overall_pass_with_every_criterion_pass_is_accepted(forge_project):
    payload = dict(VALID_VERDICT, overall="PASS",
                   criteria=[_pass_criterion("REQ-MECH-001"), _pass_criterion("REQ-MECH-004")])
    result = run_hook("subagent_stop.py", {
        "cwd": str(forge_project), "agent_type": "forge:verification-evaluator",
        "last_assistant_message": _msg_with_block(payload),
    })
    assert (result.returncode, result.output) == (0, None)


def test_verdict_schema_itself_encodes_the_overall_rule():
    import sys
    from pathlib import Path
    from .hookutil import LIB_DIR, PLUGIN_ROOT
    sys.path.insert(0, str(LIB_DIR))
    from forge import minischema
    schema = json.loads((PLUGIN_ROOT / "schemas" / "verdict.schema.json").read_text())
    bad = dict(VALID_VERDICT, overall="PASS")
    assert any("criteria[0].verdict" in e for e in minischema.validate(bad, schema))
    assert minischema.validate(VALID_VERDICT, schema) == []
    assert Path(PLUGIN_ROOT).is_dir()
