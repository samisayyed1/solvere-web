"""Tests for `forge lint agents` (CONTRACTS.md SS12, ADR-001 SS6).

Every rule gets a passing fixture and a seeded-wrong fixture that must
fail, plus a run against Forge's own real agents/ directory."""

from __future__ import annotations

from forge.lintlib import agents as agents_lint

from .helpers import BASE_JUDGE_FIELDS, BASE_MAKER_FIELDS, write_agent


def _status(results, check_id):
    for r in results:
        if r.id == check_id:
            return r
    raise AssertionError(f"no result with id {check_id!r} in {[r.id for r in results]}")


# --------------------------------------------------------------------------
# Rejected / allowed fields
# --------------------------------------------------------------------------


def test_maker_with_only_allowed_fields_PASSES(tmp_path):
    write_agent(tmp_path, "some-maker.md", BASE_MAKER_FIELDS)
    results = agents_lint.lint_agents_dir(tmp_path / "agents")
    assert _status(results, "agents.rejected_fields:some-maker").status == "pass"
    assert _status(results, "agents.allowed_fields:some-maker").status == "pass"


def test_agent_with_hooks_field_FAILS(tmp_path):
    fields = dict(BASE_MAKER_FIELDS)
    fields["hooks"] = ["PreToolUse"]
    write_agent(tmp_path, "some-maker.md", fields)
    results = agents_lint.lint_agents_dir(tmp_path / "agents")
    r = _status(results, "agents.rejected_fields:some-maker")
    assert r.status == "fail"
    assert "hooks" in r.measured


def test_agent_with_mcp_servers_field_FAILS(tmp_path):
    fields = dict(BASE_MAKER_FIELDS)
    fields["mcpServers"] = ["some-server"]
    write_agent(tmp_path, "some-maker.md", fields)
    results = agents_lint.lint_agents_dir(tmp_path / "agents")
    assert _status(results, "agents.rejected_fields:some-maker").status == "fail"


def test_agent_with_permission_mode_or_initial_prompt_FAILS(tmp_path):
    fields = dict(BASE_MAKER_FIELDS)
    fields["permissionMode"] = "bypassPermissions"
    fields["initialPrompt"] = "go"
    write_agent(tmp_path, "some-maker.md", fields)
    results = agents_lint.lint_agents_dir(tmp_path / "agents")
    r = _status(results, "agents.rejected_fields:some-maker")
    assert r.status == "fail"
    assert set(r.measured) == {"permissionMode", "initialPrompt"}


def test_agent_with_unknown_non_reserved_field_FAILS(tmp_path):
    fields = dict(BASE_MAKER_FIELDS)
    fields["favouriteColour"] = "blue"
    write_agent(tmp_path, "some-maker.md", fields)
    results = agents_lint.lint_agents_dir(tmp_path / "agents")
    r = _status(results, "agents.allowed_fields:some-maker")
    assert r.status == "fail"
    assert r.measured == ["favouriteColour"]


# --------------------------------------------------------------------------
# Description length
# --------------------------------------------------------------------------


def test_description_over_80_chars_PASSES(tmp_path):
    write_agent(tmp_path, "some-maker.md", BASE_MAKER_FIELDS)
    results = agents_lint.lint_agents_dir(tmp_path / "agents")
    assert _status(results, "agents.description_length:some-maker").status == "pass"


def test_description_under_80_chars_FAILS(tmp_path):
    fields = dict(BASE_MAKER_FIELDS)
    fields["description"] = "too short"
    write_agent(tmp_path, "some-maker.md", fields)
    results = agents_lint.lint_agents_dir(tmp_path / "agents")
    r = _status(results, "agents.description_length:some-maker")
    assert r.status == "fail"
    assert r.measured == len("too short")


# --------------------------------------------------------------------------
# Judges: model / effort / memory / tools / disallowedTools / omitClaudeMd
# --------------------------------------------------------------------------


def test_judge_with_correct_frontmatter_PASSES(tmp_path):
    write_agent(tmp_path, "verification-evaluator.md", BASE_JUDGE_FIELDS)
    results = agents_lint.lint_agents_dir(tmp_path / "agents")
    for check in (
        "agents.judge_model",
        "agents.judge_effort",
        "agents.judge_no_memory",
        "agents.judge_tools",
        "agents.judge_disallowed",
        "agents.judge_omit_claudemd",
    ):
        assert _status(results, f"{check}:verification-evaluator").status == "pass"


def test_judge_with_memory_field_FAILS(tmp_path):
    """The seeded-wrong case named in the build brief: 'judge with memory'."""
    fields = dict(BASE_JUDGE_FIELDS)
    fields["memory"] = "project"
    write_agent(tmp_path, "verification-evaluator.md", fields)
    results = agents_lint.lint_agents_dir(tmp_path / "agents")
    r = _status(results, "agents.judge_no_memory:verification-evaluator")
    assert r.status == "fail"
    assert r.measured == "project"


def test_judge_with_write_in_tools_FAILS(tmp_path):
    """The seeded-wrong case named in the build brief: 'judge with Write'."""
    fields = dict(BASE_JUDGE_FIELDS)
    fields["tools"] = ["Read", "Grep", "Glob", "Bash", "Write"]
    write_agent(tmp_path, "verification-evaluator.md", fields)
    results = agents_lint.lint_agents_dir(tmp_path / "agents")
    r = _status(results, "agents.judge_tools:verification-evaluator")
    assert r.status == "fail"
    assert r.measured == ["Write"]


def test_judge_missing_disallowed_entry_FAILS(tmp_path):
    fields = dict(BASE_JUDGE_FIELDS)
    fields["disallowedTools"] = ["Write", "Edit"]  # missing NotebookEdit, Agent
    write_agent(tmp_path, "verification-evaluator.md", fields)
    results = agents_lint.lint_agents_dir(tmp_path / "agents")
    r = _status(results, "agents.judge_disallowed:verification-evaluator")
    assert r.status == "fail"
    assert set(r.measured) == {"Write", "Edit"}


def test_judge_wrong_model_FAILS(tmp_path):
    fields = dict(BASE_JUDGE_FIELDS)
    fields["name"] = "red-team"
    fields["model"] = "sonnet"
    write_agent(tmp_path, "red-team.md", fields)
    results = agents_lint.lint_agents_dir(tmp_path / "agents")
    assert _status(results, "agents.judge_model:red-team").status == "fail"


def test_judge_wrong_effort_FAILS(tmp_path):
    fields = dict(BASE_JUDGE_FIELDS)
    fields["name"] = "red-team"
    fields["effort"] = "high"
    write_agent(tmp_path, "red-team.md", fields)
    results = agents_lint.lint_agents_dir(tmp_path / "agents")
    assert _status(results, "agents.judge_effort:red-team").status == "fail"


def test_judge_missing_omit_claude_md_FAILS(tmp_path):
    fields = dict(BASE_JUDGE_FIELDS)
    fields["name"] = "red-team"
    del fields["omitClaudeMd"]
    write_agent(tmp_path, "red-team.md", fields)
    results = agents_lint.lint_agents_dir(tmp_path / "agents")
    assert _status(results, "agents.judge_omit_claudemd:red-team").status == "fail"


# --------------------------------------------------------------------------
# Makers: memory: project, model: sonnet
# --------------------------------------------------------------------------


def test_agent_without_isolation_field_PASSES(tmp_path):
    write_agent(tmp_path, "some-maker.md", BASE_MAKER_FIELDS)
    results = agents_lint.lint_agents_dir(tmp_path / "agents")
    assert _status(results, "agents.no_isolation:some-maker").status == "pass"


def test_agent_with_isolation_worktree_FAILS(tmp_path):
    # ADR-001 SS6: isolation: worktree is for parallel writers and is set per-workflow,
    # never baked into an agent's own frontmatter -- otherwise a maker's edits land in a
    # throwaway worktree instead of the real tree.
    fields = dict(BASE_MAKER_FIELDS)
    fields["isolation"] = "worktree"
    write_agent(tmp_path, "some-maker.md", fields)
    results = agents_lint.lint_agents_dir(tmp_path / "agents")
    r = _status(results, "agents.no_isolation:some-maker")
    assert r.status == "fail"
    assert r.measured == "worktree"


def test_maker_with_correct_memory_and_model_PASSES(tmp_path):
    write_agent(tmp_path, "some-maker.md", BASE_MAKER_FIELDS)
    results = agents_lint.lint_agents_dir(tmp_path / "agents")
    assert _status(results, "agents.maker_memory:some-maker").status == "pass"
    assert _status(results, "agents.maker_model:some-maker").status == "pass"


def test_maker_missing_memory_FAILS(tmp_path):
    fields = dict(BASE_MAKER_FIELDS)
    del fields["memory"]
    write_agent(tmp_path, "some-maker.md", fields)
    results = agents_lint.lint_agents_dir(tmp_path / "agents")
    r = _status(results, "agents.maker_memory:some-maker")
    assert r.status == "fail"
    assert r.measured is None


def test_maker_wrong_model_FAILS(tmp_path):
    fields = dict(BASE_MAKER_FIELDS)
    fields["model"] = "opus"
    write_agent(tmp_path, "some-maker.md", fields)
    results = agents_lint.lint_agents_dir(tmp_path / "agents")
    r = _status(results, "agents.maker_model:some-maker")
    assert r.status == "fail"
    assert r.measured == "opus"


# --------------------------------------------------------------------------
# Malformed frontmatter / directory-level behaviour
# --------------------------------------------------------------------------


def test_malformed_frontmatter_FAILS(tmp_path):
    d = tmp_path / "agents"
    d.mkdir()
    (d / "broken.md").write_text("no frontmatter here at all\n")
    results = agents_lint.lint_agent_file(d / "broken.md")
    assert len(results) == 1
    assert results[0].status == "fail"


def test_missing_agents_dir_is_SKIP(tmp_path):
    results = agents_lint.lint_agents_dir(tmp_path / "does-not-exist")
    assert len(results) == 1
    assert results[0].status == "skip"


def test_empty_agents_dir_is_WARN(tmp_path):
    d = tmp_path / "agents"
    d.mkdir()
    results = agents_lint.lint_agents_dir(d)
    assert len(results) == 1
    assert results[0].status == "warn"


# --------------------------------------------------------------------------
# The real thing: Forge's own 16 shipped agents must lint clean.
# --------------------------------------------------------------------------


def test_forge_real_agents_directory_PASSES(repo_root):
    real_dir = repo_root / "plugins" / "forge" / "agents"
    results = agents_lint.lint_agents_dir(real_dir)
    failures = [r for r in results if r.status == "fail"]
    assert not failures, "\n".join(r.message() for r in failures)
    # Sanity: all 16 agents from the brief were actually found and linted.
    names = {r.id.split(":", 1)[1] for r in results if ":" in r.id}
    expected = {
        "product-manager", "systems-engineer", "industrial-designer", "ux-designer",
        "mechanical-engineer", "manufacturing-engineer", "electrical-engineer",
        "embedded-engineer", "software-architect", "simulation-engineer",
        "rf-emc-engineer", "test-engineer", "safety-compliance-engineer",
        "supply-chain-engineer", "verification-evaluator", "red-team",
    }
    assert expected <= names
