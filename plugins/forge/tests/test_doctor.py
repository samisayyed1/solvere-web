"""Tests for `forge doctor` end to end and the CLI's fail-closed wrapper
(BUILD item 1; the "verification is the product" contract: exit 0 all
good, 1 any failure, 2 internal error -- never a silent 0)."""

from __future__ import annotations

import json
import stat

from forge import cli, doctor


def _fake_cli(tmp_path, version_line, name="fake-claude"):
    script = tmp_path / name
    script.write_text(f"#!/usr/bin/env python3\nprint({version_line!r})\n")
    script.chmod(script.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return script


def _empty_security(repo_root):
    security = repo_root / "security"
    security.mkdir(parents=True, exist_ok=True)
    (security / "mcp-servers.json").write_text(json.dumps({"schema": 1, "servers": []}))
    (security / "mcp-lock.json").write_text(json.dumps({"schema": 1, "servers": {}}))
    (security / "files-lock.json").write_text(json.dumps({"schema": 1, "files": {}}))


def _manifest(tmp_path, tools):
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps({"forge_home": "~/.forge", "tools": tools}))
    return path


def _empty_home(tmp_path):
    home = tmp_path / "empty-home"
    home.mkdir(exist_ok=True)
    return home


# --------------------------------------------------------------------------
# Passing baseline
# --------------------------------------------------------------------------


def test_doctor_PASSES_on_a_correct_fixture(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _empty_security(repo_root)
    manifest = _manifest(
        tmp_path,
        [
            {
                "id": "python3",
                "tier": "T0",
                "version": "3",
                "install": "system",
                "path": "python3",
                "version_cmd": ["python3", "--version"],
                "version_regex": r"Python 3\.",
            }
        ],
    )
    terminal_cli = _fake_cli(tmp_path, "2.1.282 (Claude Code)")

    report = doctor.run_doctor(
        repo_root=repo_root,
        manifest_path=manifest,
        terminal_binary=str(terminal_cli),
        home=_empty_home(tmp_path),
        project_dir=repo_root,  # deterministic (not the test runner's own cwd); not a product project: skip
    )
    assert report.exit_code == 0
    # "skip" (D4's template:drift, correctly, since repo_root has no forge.toml) is as
    # healthy as "pass"/"warn" here -- it is a pre-existing CheckResult status (lock.py,
    # version_check.py already use it for "not applicable").
    assert all(r.status in ("pass", "warn", "skip") for r in report.results)
    assert any(r.status == "pass" for r in report.results)


# --------------------------------------------------------------------------
# D4: template:drift
# --------------------------------------------------------------------------

def test_template_drift_check_skips_a_non_product_directory(tmp_path):
    r = doctor._template_drift_check(tmp_path, tmp_path)
    assert r.status == "skip" and r.id == "template:drift"


def test_template_drift_check_seeded_wrong_reports_warn_on_drift(tmp_path):
    """Seeded wrong: the project's file was never touched since scaffold,
    but the template it came from has since changed -- template:drift must
    warn, not silently pass."""
    from forge import gitbaseline

    tpl = tmp_path / "templates" / "project"
    tpl.mkdir(parents=True)
    (tpl / "CLAUDE.md").write_text("# {{PROJECT_NAME}}\n")
    project = tmp_path / "product"
    project.mkdir()
    (project / "forge.toml").write_text('[project]\nname = "x"\n')
    (project / "CLAUDE.md").write_text("# Widget\n")
    # the manifest records the template dir used, so diff() finds it even
    # though the `repo_root` passed below is unrelated to `tpl`.
    gitbaseline.write_scaffold_manifest(project, templates_dir=tpl, written=[project / "CLAUDE.md"],
                                        project_name="Widget", forge_root=tpl)

    r = doctor._template_drift_check(tmp_path, project)
    assert r.status == "pass"  # nothing has changed yet

    (tpl / "CLAUDE.md").write_text("# {{PROJECT_NAME}}\nnew guidance\n")
    r = doctor._template_drift_check(tmp_path, project)
    assert r.status == "warn" and r.id == "template:drift"
    assert "1 new/changed" in r.measured


def test_template_drift_check_passes_when_up_to_date(tmp_path):
    from forge import gitbaseline

    tpl = tmp_path / "templates" / "project"
    tpl.mkdir(parents=True)
    (tpl / "CLAUDE.md").write_text("# {{PROJECT_NAME}}\n")
    project = tmp_path / "product"
    project.mkdir()
    (project / "forge.toml").write_text('[project]\nname = "x"\n')
    (project / "CLAUDE.md").write_text("# Widget\n")
    gitbaseline.write_scaffold_manifest(project, templates_dir=tpl, written=[project / "CLAUDE.md"],
                                        project_name="Widget", forge_root=tpl)

    r = doctor._template_drift_check(tmp_path, project)
    assert r.status == "pass" and r.id == "template:drift"


# --------------------------------------------------------------------------
# Each failure mode, at the doctor level
# --------------------------------------------------------------------------


def test_doctor_FAILS_on_missing_binary(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _empty_security(repo_root)
    manifest = _manifest(
        tmp_path,
        [
            {
                "id": "ghost",
                "version": "1.0.0",
                "version_cmd": [str(tmp_path / "no-such-binary")],
                "version_regex": r"1\.0\.0",
            }
        ],
    )
    report = doctor.run_doctor(
        repo_root=repo_root,
        manifest_path=manifest,
        terminal_binary=str(_fake_cli(tmp_path, "2.1.282")),
        home=_empty_home(tmp_path),
    )
    assert report.exit_code == 1
    assert any(r.id == "tool:ghost" and r.status == "fail" for r in report.results)


def test_doctor_FAILS_on_version_mismatch(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _empty_security(repo_root)
    wrong_tool = _fake_cli(tmp_path, "9.9.9", name="wrong-version-tool")
    manifest = _manifest(
        tmp_path,
        [
            {
                "id": "footool",
                "version": "1.0.0",
                "version_cmd": [str(wrong_tool)],
                "version_regex": r"(\d+\.\d+\.\d+)",
            }
        ],
    )
    report = doctor.run_doctor(
        repo_root=repo_root,
        manifest_path=manifest,
        terminal_binary=str(_fake_cli(tmp_path, "2.1.282")),
        home=_empty_home(tmp_path),
    )
    assert report.exit_code == 1
    tool_result = next(r for r in report.results if r.id == "tool:footool")
    assert tool_result.status == "fail"
    assert tool_result.measured == "9.9.9"
    assert tool_result.expected == "1.0.0"


def test_doctor_FAILS_on_unpinned_entry(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _empty_security(repo_root)
    manifest = _manifest(
        tmp_path,
        [{"id": "unpinned", "version": "", "version_cmd": ["python3"], "version_regex": "x"}],
    )
    report = doctor.run_doctor(
        repo_root=repo_root,
        manifest_path=manifest,
        terminal_binary=str(_fake_cli(tmp_path, "2.1.282")),
        home=_empty_home(tmp_path),
    )
    assert report.exit_code == 1
    tool_result = next(r for r in report.results if r.id == "tool:unpinned")
    assert tool_result.status == "fail"
    assert tool_result.detail == "unpinned entry"


def test_doctor_FAILS_on_claude_code_below_the_version_floor(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _empty_security(repo_root)
    manifest = _manifest(tmp_path, [])
    report = doctor.run_doctor(
        repo_root=repo_root,
        manifest_path=manifest,
        terminal_binary=str(_fake_cli(tmp_path, "2.1.200 (Claude Code)")),
        home=_empty_home(tmp_path),
    )
    assert report.exit_code == 1
    assert any(r.id == "claude_code_version:terminal" and r.status == "fail" for r in report.results)


# --------------------------------------------------------------------------
# CLI fail-closed wrapper: exit 2 on an internal error, never a silent 0
# --------------------------------------------------------------------------


def test_cli_doctor_returns_2_on_an_INJECTED_INTERNAL_ERROR(tmp_path, monkeypatch, capsys):
    def boom(**kwargs):
        raise RuntimeError("injected failure to prove the fail-closed wrapper")

    monkeypatch.setattr(doctor, "run_doctor", boom)
    code = cli.main(["doctor"], repo_root=tmp_path)
    assert code == 2
    captured = capsys.readouterr()
    assert "internal error" in captured.err.lower()


def test_cli_doctor_never_returns_0_when_run_doctor_raises(tmp_path, monkeypatch):
    """The fail-closed guarantee stated verbatim: never exit 0 on an
    internal error."""

    def boom(**kwargs):
        raise ValueError("boom")

    monkeypatch.setattr(doctor, "run_doctor", boom)
    code = cli.main(["doctor"], repo_root=tmp_path)
    assert code != 0
    assert code == 2


def test_cli_doctor_json_output_is_valid_json(tmp_path, capsys):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _empty_security(repo_root)
    (tmp_path / "manifest.json").write_text(json.dumps({"forge_home": "~/.forge", "tools": []}))

    code = cli.main(
        [
            "doctor",
            "--json",
            "--manifest",
            str(tmp_path / "manifest.json"),
        ],
        repo_root=repo_root,
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert "results" in payload and "summary" in payload and "exit_code" in payload
    assert payload["exit_code"] == code


# --------------------------------------------------------------------------
# CLI lock subcommands
# --------------------------------------------------------------------------


def test_cli_lock_files_write_then_check_passes(tmp_path, capsys):
    repo_root = tmp_path / "repo"
    (repo_root / ".claude").mkdir(parents=True)
    (repo_root / ".claude" / "settings.json").write_text("{}")
    _empty_security(repo_root)

    code = cli.main(["lock", "files", "--write"], repo_root=repo_root)
    assert code == 0
    lock_obj = json.loads((repo_root / "security" / "files-lock.json").read_text())
    assert ".claude/settings.json" in lock_obj["files"]


def test_cli_lock_files_dry_run_does_not_write(tmp_path):
    repo_root = tmp_path / "repo"
    (repo_root / ".claude").mkdir(parents=True)
    (repo_root / ".claude" / "settings.json").write_text("{}")
    _empty_security(repo_root)

    before = (repo_root / "security" / "files-lock.json").read_text()
    cli.main(["lock", "files"], repo_root=repo_root)
    after = (repo_root / "security" / "files-lock.json").read_text()
    assert before == after


def test_cli_lock_mcp_write_then_doctor_passes(fake_server_argv, tmp_path, capsys):
    repo_root = tmp_path / "repo"
    (repo_root / "security").mkdir(parents=True)
    (repo_root / "security" / "mcp-servers.json").write_text(
        json.dumps(
            {
                "schema": 1,
                "servers": [
                    {
                        "id": "fake",
                        "pending_install": False,
                        "command": fake_server_argv,
                        "env": [],
                        "artifact": {"ecosystem": "test", "name": "fake", "version": "1.0.0"},
                    }
                ],
            }
        )
    )
    (repo_root / "security" / "mcp-lock.json").write_text(
        json.dumps({"schema": 1, "servers": {}, "lock_hash": None})
    )
    (repo_root / "security" / "files-lock.json").write_text(json.dumps({"schema": 1, "files": {}}))
    (tmp_path / "manifest.json").write_text(json.dumps({"forge_home": "~/.forge", "tools": []}))

    code = cli.main(["lock", "mcp", "--write"], repo_root=repo_root)
    assert code == 0
    lock_obj = json.loads((repo_root / "security" / "mcp-lock.json").read_text())
    assert "fake" in lock_obj["servers"]

    report = doctor.run_doctor(
        repo_root=repo_root,
        manifest_path=tmp_path / "manifest.json",
        terminal_binary=str(_fake_cli(tmp_path, "2.1.282")),
        home=_empty_home(tmp_path),
    )
    fake_result = next(r for r in report.results if r.id == "mcp:fake")
    assert fake_result.status == "pass"
