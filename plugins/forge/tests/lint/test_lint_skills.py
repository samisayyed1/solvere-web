"""Tests for `forge lint skills` (CONTRACTS.md SS12-13, brief SS3.3).

Every rule gets a passing fixture and a seeded-wrong fixture that must
fail."""

from __future__ import annotations

from forge.lintlib import skills as skills_lint

from .helpers import write_skill


def _status(results, check_id):
    for r in results:
        if r.id == check_id:
            return r
    raise AssertionError(f"no result with id {check_id!r} in {[r.id for r in results]}")


DEFAULT_ALLOWED_TOOLS = ["Read", "Bash(${CLAUDE_SKILL_DIR}/scripts/verify.py *)"]


# --------------------------------------------------------------------------
# name == folder
# --------------------------------------------------------------------------


def test_name_matches_folder_PASSES(tmp_path):
    write_skill(tmp_path, "modeling-cad-parts")
    results = skills_lint.lint_skills_dir(tmp_path / "skills")
    assert _status(results, "skills.name_matches_dir:modeling-cad-parts").status == "pass"


def test_name_mismatched_folder_FAILS(tmp_path):
    write_skill(tmp_path, "modeling-cad-parts", fields={"name": "totally-different"})
    results = skills_lint.lint_skills_dir(tmp_path / "skills")
    r = _status(results, "skills.name_matches_dir:modeling-cad-parts")
    assert r.status == "fail"
    assert r.measured == "totally-different"


# --------------------------------------------------------------------------
# gerund naming
# --------------------------------------------------------------------------


def test_gerund_folder_name_PASSES(tmp_path):
    write_skill(tmp_path, "checking-dfm")
    results = skills_lint.lint_skills_dir(tmp_path / "skills")
    assert _status(results, "skills.gerund_name:checking-dfm").status == "pass"


def test_non_gerund_folder_name_FAILS(tmp_path):
    write_skill(tmp_path, "dfm-checks")
    results = skills_lint.lint_skills_dir(tmp_path / "skills")
    assert _status(results, "skills.gerund_name:dfm-checks").status == "fail"


def test_new_project_and_init_are_EXEMPT_from_gerund_rule(tmp_path):
    write_skill(tmp_path, "new-project")
    write_skill(tmp_path, "init")
    results = skills_lint.lint_skills_dir(tmp_path / "skills")
    assert _status(results, "skills.gerund_name:new-project").status == "pass"
    assert _status(results, "skills.gerund_name:init").status == "pass"


# --------------------------------------------------------------------------
# description length + when-not-to-use wording
# --------------------------------------------------------------------------


def test_description_within_limit_and_with_when_not_PASSES(tmp_path):
    write_skill(tmp_path, "checking-dfm")  # helper's default description includes "Do not use for"
    results = skills_lint.lint_skills_dir(tmp_path / "skills")
    assert _status(results, "skills.description_length:checking-dfm").status == "pass"
    assert _status(results, "skills.when_not_to_use:checking-dfm").status == "pass"


def test_description_over_1024_chars_FAILS(tmp_path):
    write_skill(tmp_path, "checking-dfm", fields={"description": "x" * 1025})
    results = skills_lint.lint_skills_dir(tmp_path / "skills")
    r = _status(results, "skills.description_length:checking-dfm")
    assert r.status == "fail"
    assert r.measured == 1025


def test_description_missing_when_not_to_use_wording_FAILS(tmp_path):
    write_skill(tmp_path, "checking-dfm", fields={"description": "Runs a DFM check on the current geometry."})
    results = skills_lint.lint_skills_dir(tmp_path / "skills")
    assert _status(results, "skills.when_not_to_use:checking-dfm").status == "fail"


# --------------------------------------------------------------------------
# body length
# --------------------------------------------------------------------------


def test_short_body_PASSES(tmp_path):
    write_skill(tmp_path, "checking-dfm", body_lines=20)
    results = skills_lint.lint_skills_dir(tmp_path / "skills")
    assert _status(results, "skills.body_length:checking-dfm").status == "pass"


def test_body_of_500_or_more_lines_FAILS(tmp_path):
    write_skill(tmp_path, "checking-dfm", body_lines=501)
    results = skills_lint.lint_skills_dir(tmp_path / "skills")
    r = _status(results, "skills.body_length:checking-dfm")
    assert r.status == "fail"
    assert r.measured >= 500


# --------------------------------------------------------------------------
# references/ depth
# --------------------------------------------------------------------------


def test_references_one_level_deep_PASSES(tmp_path):
    write_skill(tmp_path, "checking-dfm", references={"rules.md": "...", "process/fdm.md": "..."})
    results = skills_lint.lint_skills_dir(tmp_path / "skills")
    assert _status(results, "skills.references_depth:checking-dfm").status == "pass"


def test_references_two_levels_deep_FAILS(tmp_path):
    write_skill(tmp_path, "checking-dfm", references={"process/fdm/nested.md": "..."})
    results = skills_lint.lint_skills_dir(tmp_path / "skills")
    r = _status(results, "skills.references_depth:checking-dfm")
    assert r.status == "fail"
    assert "process/fdm/nested.md" in r.measured


# --------------------------------------------------------------------------
# allowed-tools: never bare Bash / Bash(*) / wildcard
# --------------------------------------------------------------------------


def test_narrow_allowed_tools_PASSES(tmp_path):
    write_skill(tmp_path, "checking-dfm", fields={"allowed-tools": DEFAULT_ALLOWED_TOOLS})
    results = skills_lint.lint_skills_dir(tmp_path / "skills")
    assert _status(results, "skills.allowed_tools:checking-dfm").status == "pass"


def test_bare_bash_allowed_tools_FAILS(tmp_path):
    """The seeded-wrong case named in the build brief: 'skill with bare Bash'."""
    write_skill(tmp_path, "checking-dfm", fields={"allowed-tools": ["Read", "Bash"]})
    results = skills_lint.lint_skills_dir(tmp_path / "skills")
    r = _status(results, "skills.allowed_tools:checking-dfm")
    assert r.status == "fail"
    assert "Bash" in r.measured


def test_bash_wildcard_allowed_tools_FAILS(tmp_path):
    write_skill(tmp_path, "checking-dfm", fields={"allowed-tools": ["Bash(*)"]})
    results = skills_lint.lint_skills_dir(tmp_path / "skills")
    assert _status(results, "skills.allowed_tools:checking-dfm").status == "fail"


def test_narrow_bash_with_trailing_arg_wildcard_PASSES(tmp_path):
    """A scoped command with a trailing '*' for its own args (R1a's own
    narrow-grant example) must NOT be treated as an unscoped wildcard."""
    write_skill(
        tmp_path,
        "checking-dfm",
        fields={"allowed-tools": ["Bash(${CLAUDE_PLUGIN_ROOT}/bin/forge-drc *)"]},
    )
    results = skills_lint.lint_skills_dir(tmp_path / "skills")
    assert _status(results, "skills.allowed_tools:checking-dfm").status == "pass"


# --------------------------------------------------------------------------
# side-effect skills require disable-model-invocation: true
# --------------------------------------------------------------------------


def test_side_effect_skill_with_disable_model_invocation_PASSES(tmp_path):
    write_skill(tmp_path, "releasing-designs", fields={"disable-model-invocation": True})
    results = skills_lint.lint_skills_dir(tmp_path / "skills")
    assert _status(results, "skills.disable_model_invocation:releasing-designs").status == "pass"


def test_side_effect_skill_without_disable_model_invocation_FAILS(tmp_path):
    """The seeded-wrong case named in the build brief: 'side-effect skill
    without disable-model-invocation'."""
    write_skill(tmp_path, "releasing-designs")
    results = skills_lint.lint_skills_dir(tmp_path / "skills")
    r = _status(results, "skills.disable_model_invocation:releasing-designs")
    assert r.status == "fail"
    assert r.measured is None


def test_non_side_effect_skill_has_no_disable_model_invocation_check(tmp_path):
    write_skill(tmp_path, "checking-dfm")
    results = skills_lint.lint_skills_dir(tmp_path / "skills")
    assert not [r for r in results if r.id == "skills.disable_model_invocation:checking-dfm"]


# --------------------------------------------------------------------------
# registered scripts/verify.py must be executable-by-python
# --------------------------------------------------------------------------


def test_registered_verify_py_with_main_guard_PASSES(tmp_path):
    write_skill(
        tmp_path,
        "checking-dfm",
        verify_py="def main():\n    pass\n\nif __name__ == '__main__':\n    main()\n",
    )
    results = skills_lint.lint_skills_dir(tmp_path / "skills")
    assert _status(results, "skills.verify_entrypoint:checking-dfm").status == "pass"


def test_registered_verify_py_without_main_guard_FAILS(tmp_path):
    write_skill(tmp_path, "checking-dfm", verify_py="def main():\n    pass\n")
    results = skills_lint.lint_skills_dir(tmp_path / "skills")
    r = _status(results, "skills.verify_entrypoint:checking-dfm")
    assert r.status == "fail"
    assert r.measured is False


def test_unregistered_skill_has_no_verify_entrypoint_check(tmp_path):
    # exploring-concepts is not in CONTRACTS SS9's registered-entrypoints table.
    write_skill(tmp_path, "exploring-concepts", verify_py="print('no guard')\n")
    results = skills_lint.lint_skills_dir(tmp_path / "skills")
    assert not [r for r in results if r.id == "skills.verify_entrypoint:exploring-concepts"]


# --------------------------------------------------------------------------
# context: value (S20)
# --------------------------------------------------------------------------


def test_context_fork_PASSES(tmp_path):
    write_skill(tmp_path, "reviewing-designs", fields={"context": "fork"})
    results = skills_lint.lint_skills_dir(tmp_path / "skills")
    assert _status(results, "skills.context_value:reviewing-designs").status == "pass"


def test_context_typo_FAILS(tmp_path):
    write_skill(tmp_path, "reviewing-designs", fields={"context": "frok"})
    results = skills_lint.lint_skills_dir(tmp_path / "skills")
    r = _status(results, "skills.context_value:reviewing-designs")
    assert r.status == "fail"
    assert r.measured == "frok"


def test_no_context_field_has_no_context_check(tmp_path):
    write_skill(tmp_path, "modeling-cad-parts")
    results = skills_lint.lint_skills_dir(tmp_path / "skills")
    assert not [r for r in results if r.id == "skills.context_value:modeling-cad-parts"]


# --------------------------------------------------------------------------
# directory-level behaviour: missing skills dir / no skills yet is SKIP,
# never a fail, because skills/ is owned by a different Forge builder.
# --------------------------------------------------------------------------


def test_missing_skills_dir_is_SKIP(tmp_path):
    results = skills_lint.lint_skills_dir(tmp_path / "does-not-exist")
    assert len(results) == 1
    assert results[0].status == "skip"


def test_empty_skills_dir_is_SKIP(tmp_path):
    d = tmp_path / "skills"
    d.mkdir()
    results = skills_lint.lint_skills_dir(d)
    assert len(results) == 1
    assert results[0].status == "skip"


def test_skill_dir_without_skill_md_FAILS(tmp_path):
    d = tmp_path / "skills" / "half-built-thing"
    d.mkdir(parents=True)
    results = skills_lint.lint_skill_dir(d)
    assert len(results) == 1
    assert results[0].status == "fail"


# --------------------------------------------------------------------------
# review #1: interpreter grants must name one skill script; judge-facing
# skills grant no interpreter at all
# --------------------------------------------------------------------------

import pytest  # noqa: E402


@pytest.mark.parametrize("grant", [
    "Bash(~/.forge/bin/forge-python *)",
    "Bash(forge-python:*)",
    "Bash(python3 *)",
    "Bash(~/.forge/bin/forge-python ${CLAUDE_SKILL_DIR}/scripts/*)",
    "Bash(~/.forge/bin/forge-python ${CLAUDE_SKILL_DIR}/scripts/*.py:*)",
    "Bash(~/.forge/bin/forge-python -c *)",
    "Bash(~/.forge/bin/forge-python /tmp/anything.py *)",
])
def test_broad_interpreter_grant_FAILS(tmp_path, grant):
    write_skill(tmp_path, "checking-dfm", fields={"allowed-tools": ["Read", grant]})
    r = _status(skills_lint.lint_skills_dir(tmp_path / "skills"), "skills.allowed_tools:checking-dfm")
    assert r.status == "fail"
    assert grant in r.measured


@pytest.mark.parametrize("grant", [
    "Bash(~/.forge/bin/forge-python ${CLAUDE_SKILL_DIR}/scripts/verify.py:*)",
    "Bash(forge-python ${CLAUDE_SKILL_DIR}/scripts/verify.py *)",
    "Bash(~/.forge/bin/forge-python ${CLAUDE_PLUGIN_ROOT}/skills/verifying-geometry/scripts/verify.py:*)",
])
def test_scoped_interpreter_grant_PASSES(tmp_path, grant):
    write_skill(tmp_path, "checking-dfm", fields={"allowed-tools": ["Read", grant]})
    r = _status(skills_lint.lint_skills_dir(tmp_path / "skills"), "skills.allowed_tools:checking-dfm")
    assert r.status == "pass"


def _judge_agent(tmp_path, skill):
    agents = tmp_path / "agents"
    agents.mkdir(exist_ok=True)
    (agents / "red-team.md").write_text(f"---\nname: red-team\nskills:\n  - {skill}\n---\nbody\n")


def test_judge_facing_skill_with_any_interpreter_FAILS(tmp_path):
    _judge_agent(tmp_path, "reviewing-designs")
    write_skill(tmp_path, "reviewing-designs", fields={"allowed-tools": [
        "Read", "Bash(~/.forge/bin/forge-python ${CLAUDE_SKILL_DIR}/scripts/verify.py:*)"]})
    r = _status(skills_lint.lint_skills_dir(tmp_path / "skills"), "skills.judge_no_interpreter:reviewing-designs")
    assert r.status == "fail"


def test_judge_facing_skill_without_interpreter_PASSES(tmp_path):
    _judge_agent(tmp_path, "reviewing-designs")
    write_skill(tmp_path, "reviewing-designs", fields={"allowed-tools": ["Read", "Bash(git log *)"]})
    r = _status(skills_lint.lint_skills_dir(tmp_path / "skills"), "skills.judge_no_interpreter:reviewing-designs")
    assert r.status == "pass"


def test_real_plugin_skills_have_no_broad_interpreter_grant():
    from pathlib import Path
    plugin = Path(__file__).resolve().parents[2]
    results = skills_lint.lint_skills_dir(plugin / "skills")
    bad = [r for r in results if r.status == "fail"]
    assert not bad, [(r.id, r.measured) for r in bad]
    assert any(r.id == "skills.judge_no_interpreter:reviewing-designs" and r.status == "pass" for r in results)
