"""Tests for forge.version_check: the Claude Code version floor (ADR-001 D1)."""

from __future__ import annotations

import stat
import sys
from pathlib import Path

from forge import version_check


def _make_fake_cli(tmp_path: Path, version_line: str, name: str = "fake-claude") -> Path:
    """A tiny stdlib-only script that prints `version_line` for --version."""
    script = tmp_path / name
    script.write_text(
        "#!/usr/bin/env python3\n"
        "import sys\n"
        f"print({version_line!r})\n"
    )
    script.chmod(script.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return script


def test_parse_version():
    assert version_check.parse_version("2.1.281 (Claude Code)") == (2, 1, 281)
    assert version_check.parse_version("no version here") is None


def test_compare_versions():
    assert version_check.compare_versions((2, 1, 281), (2, 1, 281)) == 0
    assert version_check.compare_versions((2, 1, 280), (2, 1, 281)) < 0
    assert version_check.compare_versions((2, 2, 0), (2, 1, 281)) > 0


def test_floors_are_2_1_280_hard_and_2_1_281_recommended():
    assert version_check.MIN_CLAUDE_CODE_VERSION == (2, 1, 280)
    assert version_check.RECOMMENDED_CLAUDE_CODE_VERSION == (2, 1, 281)


def test_check_claude_binary_WARNS_between_min_and_recommended(tmp_path):
    cli = _make_fake_cli(tmp_path, "2.1.280 (Claude Code)")
    result = version_check.check_claude_binary(str(cli), check_id="t")
    assert result.status == "warn"
    assert result.expected == "2.1.281"
    assert result.fix


def test_check_claude_binary_SKIPS_non_executable_format(tmp_path):
    """A binary for another OS (Desktop's Linux VM CLI) raises ENOEXEC: skip, don't fail."""
    alien = tmp_path / "claude"
    alien.write_bytes(b"\x7fELF\x02\x01\x01" + b"\x00" * 64)
    alien.chmod(0o755)
    result = version_check.check_claude_binary(str(alien), check_id="t")
    assert result.status == "skip"


def test_newest_per_install_ignores_superseded_versions(tmp_path):
    root = tmp_path / "Claude" / "claude-code"
    paths = [root / v / "claude.app" / "Contents" / "MacOS" / "claude" for v in ("2.1.270", "2.1.280", "2.1.99")]
    kept = version_check._newest_per_install(paths)
    assert kept == [paths[1]]


def test_check_claude_binary_passes_at_the_recommended_floor(tmp_path):
    cli = _make_fake_cli(tmp_path, "2.1.281 (Claude Code)")
    result = version_check.check_claude_binary(str(cli), check_id="t")
    assert result.status == "pass"
    assert result.measured == "2.1.281"


def test_check_claude_binary_passes_above_the_floor(tmp_path):
    cli = _make_fake_cli(tmp_path, "2.1.282 (Claude Code)")
    result = version_check.check_claude_binary(str(cli), check_id="t")
    assert result.status == "pass"


# --- Proof this check can actually fail on a deliberately wrong input -----


def test_check_claude_binary_FAILS_below_the_floor(tmp_path):
    """The negative case: a CLI one patch below the floor must fail, with
    the measured/expected versions and a fix string, not silently pass."""
    cli = _make_fake_cli(tmp_path, "2.1.279 (Claude Code)")
    result = version_check.check_claude_binary(str(cli), check_id="t")
    assert result.status == "fail"
    assert result.measured == "2.1.279"
    assert result.expected == "2.1.280"
    assert "upgrade" in result.fix.lower()


def test_check_claude_binary_FAILS_on_missing_binary(tmp_path):
    missing = tmp_path / "does-not-exist"
    result = version_check.check_claude_binary(str(missing), check_id="t")
    assert result.status == "fail"
    assert "not found" in result.measured.lower()
    assert result.fix


def test_check_claude_binary_FAILS_on_unparseable_output(tmp_path):
    cli = _make_fake_cli(tmp_path, "not a version string")
    result = version_check.check_claude_binary(str(cli), check_id="t")
    assert result.status == "fail"


def test_find_desktop_claude_binaries_skips_gracefully_when_absent(tmp_path):
    # tmp_path has no "Library/Application Support/Claude*" at all.
    found = version_check.find_desktop_claude_binaries(home=tmp_path)
    assert found == []


def test_find_desktop_claude_binaries_finds_a_bundled_binary(tmp_path):
    app_dir = tmp_path / "Library" / "Application Support" / "Claude-Desktop" / "resources" / "app"
    app_dir.mkdir(parents=True)
    cli = _make_fake_cli(app_dir, "2.1.280 (Claude Code)", name="claude")
    found = version_check.find_desktop_claude_binaries(home=tmp_path)
    assert cli in found


def test_run_version_floor_checks_includes_desktop_binaries(tmp_path, monkeypatch):
    app_dir = tmp_path / "Library" / "Application Support" / "Claude" / "app"
    app_dir.mkdir(parents=True)
    _make_fake_cli(app_dir, "2.1.279 (Claude Code)", name="claude")  # below hard floor

    terminal_cli = _make_fake_cli(tmp_path, "2.1.282 (Claude Code)", name="terminal-claude")

    results = version_check.run_version_floor_checks(
        terminal_binary=str(terminal_cli), home=tmp_path
    )
    statuses = {r.id.split(":")[1]: r.status for r in results}
    assert statuses["terminal"] == "pass"
    assert any(r.status == "fail" for r in results if "desktop" in r.id)
