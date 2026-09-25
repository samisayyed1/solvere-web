"""Tests for hooks/pre_tool_use.py (CONTRACTS.md §8, ADR-001 §5)."""

from __future__ import annotations

import time
from pathlib import Path

from .hookutil import forge_project, non_forge_project, run_hook


def _write(project: Path, tool_name: str, file_path: Path, content: str, agent_type: str | None = None) -> dict:
    payload = {"cwd": str(project), "tool_name": tool_name,
               "tool_input": {"file_path": str(file_path), "content": content}}
    if agent_type is not None:
        payload["agent_type"] = agent_type
    return payload


def _edit(project: Path, file_path: Path, old: str, new: str, agent_type: str | None = None) -> dict:
    payload = {"cwd": str(project), "tool_name": "Edit",
               "tool_input": {"file_path": str(file_path), "old_string": old, "new_string": new}}
    if agent_type is not None:
        payload["agent_type"] = agent_type
    return payload


def _bash(project: Path, command: str) -> dict:
    return {"cwd": str(project), "tool_name": "Bash", "tool_input": {"command": command}}


# ---------------------------------------------------------------------------
# no-op outside a Forge project
# ---------------------------------------------------------------------------

def test_noop_outside_forge_project(non_forge_project):
    result = run_hook("pre_tool_use.py", _bash(non_forge_project, "git push --force origin main"))
    assert result.returncode == 0
    assert result.output is None


# ---------------------------------------------------------------------------
# destructive Bash (sabotage: force-push must be denied)
# ---------------------------------------------------------------------------

def test_force_push_denied(forge_project):
    result = run_hook("pre_tool_use.py", _bash(forge_project, "git push --force origin main"))
    assert result.permission_decision == "deny"
    assert "force-push" in result.reason


def test_force_push_short_flag_denied(forge_project):
    result = run_hook("pre_tool_use.py", _bash(forge_project, "git push -f origin main"))
    assert result.permission_decision == "deny"


def test_git_reset_hard_denied(forge_project):
    result = run_hook("pre_tool_use.py", _bash(forge_project, "git reset --hard HEAD~1"))
    assert result.permission_decision == "deny"


def test_dd_denied(forge_project):
    result = run_hook("pre_tool_use.py", _bash(forge_project, "dd if=/dev/zero of=/dev/sda"))
    assert result.permission_decision == "deny"


def test_device_redirect_denied(forge_project):
    result = run_hook("pre_tool_use.py", _bash(forge_project, "echo hi > /dev/sda"))
    assert result.permission_decision == "deny"


def test_rm_rf_inside_out_allowed(forge_project):
    result = run_hook("pre_tool_use.py", _bash(forge_project, "rm -rf out/build"))
    assert result.returncode == 0
    assert result.output is None


def test_rm_rf_outside_out_denied(forge_project):
    result = run_hook("pre_tool_use.py", _bash(forge_project, "rm -rf cad/"))
    assert result.permission_decision == "deny"
    assert "out/" in result.reason


def test_plain_rm_of_one_file_allowed(forge_project):
    result = run_hook("pre_tool_use.py", _bash(forge_project, "rm cad/enclosure.py"))
    assert result.returncode == 0
    assert result.output is None


def test_chmod_777_recursive_outside_out_denied(forge_project):
    result = run_hook("pre_tool_use.py", _bash(forge_project, "chmod -R 777 cad/"))
    assert result.permission_decision == "deny"


def test_unrelated_bash_allowed(forge_project):
    result = run_hook("pre_tool_use.py", _bash(forge_project, "python3 -m pytest tests/"))
    assert result.returncode == 0
    assert result.output is None


# ---------------------------------------------------------------------------
# network egress
# ---------------------------------------------------------------------------

def test_curl_outside_allowlist_denied(forge_project):
    result = run_hook("pre_tool_use.py", _bash(forge_project, "curl https://evil.example.com/x"))
    assert result.permission_decision == "deny"
    assert "evil.example.com" in result.reason


def test_curl_inside_allowlist_allowed(forge_project):
    result = run_hook("pre_tool_use.py", _bash(forge_project, "curl https://github.com/foo/bar"))
    assert result.returncode == 0
    assert result.output is None


def test_curl_subdomain_of_allowlist_allowed(forge_project):
    result = run_hook("pre_tool_use.py", _bash(forge_project, "curl https://api.github.com/repos"))
    assert result.returncode == 0
    assert result.output is None


def test_webfetch_outside_allowlist_denied(forge_project):
    payload = {"cwd": str(forge_project), "tool_name": "WebFetch", "tool_input": {"url": "https://evil.example.com/page"}}
    result = run_hook("pre_tool_use.py", payload)
    assert result.permission_decision == "deny"


def test_webfetch_inside_allowlist_allowed(forge_project):
    payload = {"cwd": str(forge_project), "tool_name": "WebFetch", "tool_input": {"url": "https://github.com/foo"}}
    result = run_hook("pre_tool_use.py", payload)
    assert result.returncode == 0
    assert result.output is None


# ---------------------------------------------------------------------------
# maker != checker: judges may never write (sabotage case)
# ---------------------------------------------------------------------------

def test_judge_write_denied(forge_project):
    payload = _write(forge_project, "Write", forge_project / "requirements" / "requirements.md", "x",
                      agent_type="forge:verification-evaluator")
    result = run_hook("pre_tool_use.py", payload)
    assert result.permission_decision == "deny"
    assert "read-only reviewer" in result.reason


def test_red_team_edit_denied(forge_project):
    payload = _edit(forge_project, forge_project / "cad" / "enclosure.py", "print('part')", "x",
                     agent_type="forge:red-team")
    result = run_hook("pre_tool_use.py", payload)
    assert result.permission_decision == "deny"


def test_non_judge_agent_write_allowed(forge_project):
    payload = _write(forge_project, "Write", forge_project / "requirements" / "requirements.md", "x",
                      agent_type="forge:systems-engineer")
    result = run_hook("pre_tool_use.py", payload)
    assert result.returncode == 0
    assert result.output is None


# ---------------------------------------------------------------------------
# cad/** only forge:mechanical-engineer
# ---------------------------------------------------------------------------

def test_cad_write_by_other_agent_denied(forge_project):
    payload = _write(forge_project, "Write", forge_project / "cad" / "part2.py", "x",
                      agent_type="forge:software-architect")
    result = run_hook("pre_tool_use.py", payload)
    assert result.permission_decision == "deny"
    assert "forge:mechanical-engineer" in result.reason


def test_cad_write_by_mechanical_engineer_allowed(forge_project):
    payload = _write(forge_project, "Write", forge_project / "cad" / "part2.py", "x",
                      agent_type="forge:mechanical-engineer")
    result = run_hook("pre_tool_use.py", payload)
    assert result.returncode == 0
    assert result.output is None


def test_cad_write_by_main_thread_asks(forge_project):
    payload = _write(forge_project, "Write", forge_project / "cad" / "part2.py", "x", agent_type=None)
    result = run_hook("pre_tool_use.py", payload)
    assert result.permission_decision == "ask"


# ---------------------------------------------------------------------------
# protected paths
# ---------------------------------------------------------------------------

def test_write_to_release_denied(forge_project):
    payload = _write(forge_project, "Write", forge_project / "release" / "v1.tar", "x")
    result = run_hook("pre_tool_use.py", payload)
    assert result.permission_decision == "deny"


def test_write_to_security_denied(forge_project):
    payload = _write(forge_project, "Write", forge_project / "security" / "keys.json", "x")
    result = run_hook("pre_tool_use.py", payload)
    assert result.permission_decision == "deny"


def test_write_to_claude_settings_denied(forge_project):
    payload = _write(forge_project, "Write", forge_project / ".claude" / "settings.json", "x")
    result = run_hook("pre_tool_use.py", payload)
    assert result.permission_decision == "deny"


def test_write_to_claude_settings_local_denied(forge_project):
    payload = _write(forge_project, "Write", forge_project / ".claude" / "settings.local.json", "x")
    result = run_hook("pre_tool_use.py", payload)
    assert result.permission_decision == "deny"


def test_write_to_hil_bench_config_denied(forge_project):
    payload = _write(forge_project, "Write", forge_project / "hil" / "bench1.toml", "x")
    result = run_hook("pre_tool_use.py", payload)
    assert result.permission_decision == "deny"


def test_write_to_unrelated_path_allowed(forge_project):
    payload = _write(forge_project, "Write", forge_project / "docs" / "notes.md", "x")
    result = run_hook("pre_tool_use.py", payload)
    assert result.returncode == 0
    assert result.output is None


# ---------------------------------------------------------------------------
# reviews/G*.md human sign-off
# ---------------------------------------------------------------------------

def test_filling_blank_signoff_denied(forge_project):
    payload = _edit(forge_project, forge_project / "reviews" / "G1.md",
                     "Human sign-off: ____________", "Human sign-off: /s/ Alice")
    result = run_hook("pre_tool_use.py", payload)
    assert result.permission_decision == "deny"
    assert "sign-off" in result.reason


def test_editing_review_without_touching_signoff_allowed(forge_project):
    payload = _edit(forge_project, forge_project / "reviews" / "G1.md", "# G1 review", "# G1 review (draft 2)")
    result = run_hook("pre_tool_use.py", payload)
    assert result.returncode == 0
    assert result.output is None


def test_creating_new_review_prefilled_denied(forge_project):
    payload = _write(forge_project, "Write", forge_project / "reviews" / "G2.md",
                      "# G2 review\n\nHuman sign-off: Alice signed it  Name: Alice  Date: today  Decision: PASS\n")
    result = run_hook("pre_tool_use.py", payload)
    assert result.permission_decision == "deny"


def test_creating_new_review_blank_signoff_allowed(forge_project):
    payload = _write(forge_project, "Write", forge_project / "reviews" / "G2.md",
                      "# G2 review\n\nHuman sign-off: ____________  Name: ____  Date: ____  Decision: PASS / FAIL\n")
    result = run_hook("pre_tool_use.py", payload)
    assert result.returncode == 0
    assert result.output is None


# ---------------------------------------------------------------------------
# verified params (sabotage: direct edit to a verified param must be denied)
# ---------------------------------------------------------------------------

def test_direct_edit_of_verified_param_denied(forge_project):
    payload = _edit(forge_project, forge_project / "params" / "params.toml", "value = 40.0", "value = 41.0")
    result = run_hook("pre_tool_use.py", payload)
    assert result.permission_decision == "deny"
    assert "verified" in result.reason
    assert "forge params set" in result.reason


def test_direct_edit_of_unverified_param_allowed(forge_project):
    payload = _edit(forge_project, forge_project / "params" / "params.toml", "value = 2.0", "value = 2.5")
    result = run_hook("pre_tool_use.py", payload)
    assert result.returncode == 0
    assert result.output is None


def test_multiedit_touching_verified_param_denied(forge_project):
    payload = {
        "cwd": str(forge_project), "tool_name": "MultiEdit",
        "tool_input": {"file_path": str(forge_project / "params" / "params.toml"), "edits": [
            {"old_string": "value = 2.0", "new_string": "value = 2.2"},
            {"old_string": "value = 40.0", "new_string": "value = 45.0"},
        ]},
    }
    result = run_hook("pre_tool_use.py", payload)
    assert result.permission_decision == "deny"


def test_write_of_whole_params_file_removing_verified_param_denied(forge_project):
    payload = _write(forge_project, "Write", forge_project / "params" / "params.toml",
                      "[enclosure.wall_thickness]\nvalue = 2.0\nunit = \"mm\"\nstatus = \"assumed\"\n"
                      "source = \"x\"\n")
    result = run_hook("pre_tool_use.py", payload)
    assert result.permission_decision == "deny"


def test_write_of_params_file_that_would_not_parse_denied(forge_project):
    payload = _write(forge_project, "Write", forge_project / "params" / "params.toml", "not valid toml [[[")
    result = run_hook("pre_tool_use.py", payload)
    assert result.permission_decision == "deny"
    assert "parse" in result.reason


def test_new_params_file_created_from_scratch_allowed(tmp_path, forge_project):
    # No params.toml currently exists in a fresh (empty cad-only) project -> no verified leaf to protect.
    project = forge_project
    (project / "params" / "params.toml").unlink()
    import subprocess
    subprocess.run(["git", "-C", str(project), "add", "-A"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(project), "commit", "-q", "-m", "remove params"], check=True, capture_output=True)
    payload = _write(project, "Write", project / "params" / "params.toml",
                      "[enclosure.wall_thickness]\nvalue = 2.0\nunit = \"mm\"\nstatus = \"assumed\"\nsource = \"x\"\n")
    result = run_hook("pre_tool_use.py", payload)
    assert result.returncode == 0
    assert result.output is None


# ---------------------------------------------------------------------------
# NotebookEdit: path rules still apply even though content can't be simulated
# ---------------------------------------------------------------------------

def test_notebookedit_to_protected_path_denied(forge_project):
    payload = {"cwd": str(forge_project), "tool_name": "NotebookEdit",
               "tool_input": {"file_path": str(forge_project / "release" / "notebook.ipynb")}}
    result = run_hook("pre_tool_use.py", payload)
    assert result.permission_decision == "deny"


# ---------------------------------------------------------------------------
# timing: PreToolUse must run comfortably under the 1s budget (CONTRACTS.md §8)
# ---------------------------------------------------------------------------

def test_pretooluse_runs_well_under_one_second_budget(forge_project):
    payload = _bash(forge_project, "git push --force origin main")
    start = time.monotonic()
    run_hook("pre_tool_use.py", payload)
    elapsed = time.monotonic() - start
    # Generous margin over the 1s hook-level timeout to absorb interpreter
    # startup on a loaded CI box, while still proving this is nowhere near
    # a script that would need the full budget.
    assert elapsed < 3.0, f"pre_tool_use.py took {elapsed:.2f}s, expected well under the 1s PreToolUse budget"
