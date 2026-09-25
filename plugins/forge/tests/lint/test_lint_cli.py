"""End-to-end tests for the `forge lint` command dispatcher
(plugins/forge/lib/forge/commands/lint.py): argument parsing, default
paths, and exit codes (0 all pass, 1 any fail)."""

from __future__ import annotations

import argparse

from forge.commands import lint as lint_cmd

from .helpers import BASE_JUDGE_FIELDS, BASE_MAKER_FIELDS, write_agent, write_skill


def _parse(argv):
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    lint_cmd.register(sub.add_parser("lint"))
    ns = parser.parse_args(["lint", *argv])
    return ns


def _fake_forge_root(tmp_path, with_agents=True):
    root = tmp_path / "repo"
    (root / "plugins" / "forge").mkdir(parents=True)
    if with_agents:
        write_agent(root / "plugins" / "forge", "some-maker.md", BASE_MAKER_FIELDS)
    return root


def test_registered_as_lint_with_help(capsys):
    assert lint_cmd.NAME == "lint"
    assert lint_cmd.HELP


def test_run_agents_target_PASSES_on_good_fixture(tmp_path, capsys):
    root = _fake_forge_root(tmp_path)
    ns = _parse(["agents", str(root / "plugins" / "forge" / "agents")])
    assert lint_cmd.run(ns, root) == 0


def test_run_agents_target_FAILS_on_bad_fixture(tmp_path, capsys):
    root = _fake_forge_root(tmp_path, with_agents=False)
    fields = dict(BASE_JUDGE_FIELDS)
    fields["memory"] = "project"  # seeded-wrong: judge with memory
    write_agent(root / "plugins" / "forge", "verification-evaluator.md", fields)
    ns = _parse(["agents", str(root / "plugins" / "forge" / "agents")])
    assert lint_cmd.run(ns, root) == 1


def test_run_agents_default_dir_resolves_under_forge_root(tmp_path):
    root = _fake_forge_root(tmp_path)
    ns = _parse(["agents"])
    assert ns.dir is None
    assert lint_cmd.run(ns, root) == 0


def test_run_skills_default_dir_skip_is_not_a_failure(tmp_path):
    root = tmp_path / "repo"
    (root / "plugins" / "forge").mkdir(parents=True)
    ns = _parse(["skills"])
    assert lint_cmd.run(ns, root) == 0


def test_run_skills_target_on_explicit_dir(tmp_path):
    root = tmp_path / "repo"
    write_skill(root / "plugins" / "forge", "checking-dfm")
    ns = _parse(["skills", str(root / "plugins" / "forge" / "skills")])
    assert lint_cmd.run(ns, root) == 0


def test_run_claudemd_default_paths(tmp_path):
    root = tmp_path / "repo"
    (root / "templates" / "project").mkdir(parents=True)
    (root / "templates" / "project" / "CLAUDE.md").write_text("\n".join(f"l{i}" for i in range(10)) + "\n")
    ns = _parse(["claudemd"])
    assert lint_cmd.run(ns, root) == 0


def test_run_claudemd_explicit_path_FAILS_over_100_lines(tmp_path):
    root = tmp_path / "repo"
    root.mkdir(parents=True, exist_ok=True)
    bad = root / "CLAUDE.md"
    bad.write_text("\n".join(f"l{i}" for i in range(150)) + "\n")
    ns = _parse(["claudemd", str(bad)])
    assert lint_cmd.run(ns, root) == 1


def test_run_wording_explicit_path_FAILS(tmp_path):
    root = tmp_path / "repo"
    root.mkdir(parents=True, exist_ok=True)
    bad = root / "note.md"
    bad.write_text("This is validated for shipping.\n")
    ns = _parse(["wording", str(bad)])
    assert lint_cmd.run(ns, root) == 1


def test_run_wording_default_scope_on_empty_repo_PASSES(tmp_path):
    root = tmp_path / "repo"
    root.mkdir(parents=True, exist_ok=True)
    ns = _parse(["wording"])
    assert lint_cmd.run(ns, root) == 0


def test_run_manifest_on_empty_repo_PASSES(tmp_path):
    root = tmp_path / "repo"
    root.mkdir(parents=True, exist_ok=True)
    ns = _parse(["manifest"])
    assert lint_cmd.run(ns, root) == 0


def test_run_all_aggregates_every_rule_family(tmp_path):
    root = _fake_forge_root(tmp_path)
    ns = _parse(["all"])
    assert lint_cmd.run(ns, root) == 0


def test_run_all_FAILS_if_any_family_fails(tmp_path):
    root = _fake_forge_root(tmp_path, with_agents=False)
    fields = dict(BASE_MAKER_FIELDS)
    fields["hooks"] = ["PreToolUse"]  # seeded-wrong
    write_agent(root / "plugins" / "forge", "some-maker.md", fields)
    ns = _parse(["all"])
    assert lint_cmd.run(ns, root) == 1
