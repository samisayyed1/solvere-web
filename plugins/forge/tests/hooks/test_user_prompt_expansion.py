"""Tests for hooks/user_prompt_expansion.py -- release/fab/flash gating (CONTRACTS.md §13)."""

from __future__ import annotations

import subprocess

from .hookutil import forge_project, non_forge_project, run_hook


def _approval_toml(project, **overrides):
    fields = {
        "approved_by": "Alice Chen", "date": "2026-09-25",
        "git_sha": subprocess.run(["git", "-C", str(project), "rev-parse", "HEAD"],
                                   capture_output=True, text=True, check=True).stdout.strip(),
        "scope": "release v1", "gate": "G6",
    }
    fields.update(overrides)
    release_dir = project / "release"
    release_dir.mkdir(exist_ok=True)
    lines = "\n".join(f'{k} = "{v}"' for k, v in fields.items())
    (release_dir / "APPROVAL.toml").write_text(lines + "\n")


def test_noop_outside_forge_project(non_forge_project):
    result = run_hook("user_prompt_expansion.py", {
        "cwd": str(non_forge_project), "command_name": "forge:releasing-designs",
    })
    assert result.returncode == 0
    assert result.output is None


def test_non_gated_command_allowed(forge_project):
    result = run_hook("user_prompt_expansion.py", {
        "cwd": str(forge_project), "command_name": "forge:writing-requirements",
    })
    assert result.returncode == 0
    assert result.output is None


def test_releasing_designs_without_approval_blocked(forge_project):
    """Sabotage case: no release/APPROVAL.toml at all must block."""
    result = run_hook("user_prompt_expansion.py", {
        "cwd": str(forge_project), "command_name": "forge:releasing-designs",
    })
    assert result.returncode == 2
    assert result.output["decision"] == "block"
    assert "APPROVAL.toml" in result.output["reason"]


def test_testing_on_hardware_without_approval_blocked(forge_project):
    result = run_hook("user_prompt_expansion.py", {
        "cwd": str(forge_project), "command_name": "forge:testing-on-hardware",
    })
    assert result.returncode == 2


def test_fab_export_and_flash_named_commands_blocked(forge_project):
    for name in ("forge:exporting-fab-files", "forge:flashing-firmware"):
        result = run_hook("user_prompt_expansion.py", {"cwd": str(forge_project), "command_name": name})
        assert result.returncode == 2, name


def test_releasing_designs_with_valid_approval_allowed(forge_project):
    _approval_toml(forge_project)
    result = run_hook("user_prompt_expansion.py", {
        "cwd": str(forge_project), "command_name": "forge:releasing-designs",
    })
    assert result.returncode == 0
    assert result.output is None


def test_approval_with_stale_git_sha_blocked(forge_project):
    """Sabotage case: an approval signed for an older commit must not carry over."""
    _approval_toml(forge_project, git_sha="0" * 40)
    result = run_hook("user_prompt_expansion.py", {
        "cwd": str(forge_project), "command_name": "forge:releasing-designs",
    })
    assert result.returncode == 2
    assert "HEAD" in result.output["reason"]


def test_approval_missing_required_field_blocked(forge_project):
    _approval_toml(forge_project, approved_by="")
    result = run_hook("user_prompt_expansion.py", {
        "cwd": str(forge_project), "command_name": "forge:releasing-designs",
    })
    assert result.returncode == 2
    assert "approved_by" in result.output["reason"]


def test_malformed_approval_toml_blocked(forge_project):
    release_dir = forge_project / "release"
    release_dir.mkdir(exist_ok=True)
    (release_dir / "APPROVAL.toml").write_text("not valid toml [[[")
    result = run_hook("user_prompt_expansion.py", {
        "cwd": str(forge_project), "command_name": "forge:releasing-designs",
    })
    assert result.returncode == 2
