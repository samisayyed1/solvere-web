"""Tests for forge.toolcheck: pinned-tool checks from the toolchain manifest
(BUILD item 1.b)."""

from __future__ import annotations

import json
import stat
from pathlib import Path

from forge import toolcheck


def _fake_bin(tmp_path: Path, name: str, output: str) -> Path:
    script = tmp_path / name
    script.write_text(f"#!/usr/bin/env python3\nprint({output!r})\n")
    script.chmod(script.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return script


def _write_manifest(tmp_path: Path, tools: list[dict]) -> Path:
    manifest = {"forge_home": "~/.forge", "tools": tools}
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest))
    return path


def test_missing_manifest_is_a_warning_not_a_failure(tmp_path):
    results = toolcheck.run_tool_checks(tmp_path / "does-not-exist.json")
    assert len(results) == 1
    assert results[0].status == "warn"
    assert results[0].id == "toolchain_manifest"


def test_malformed_manifest_json_is_a_failure(tmp_path):
    path = tmp_path / "manifest.json"
    path.write_text("{not json")
    results = toolcheck.run_tool_checks(path)
    assert len(results) == 1
    assert results[0].status == "fail"


def test_correct_fixture_manifest_passes(tmp_path):
    """The baseline positive case: a harmless, real command with a matching
    regex must report `pass`."""
    manifest = _write_manifest(
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
    results = toolcheck.run_tool_checks(manifest)
    assert len(results) == 1
    assert results[0].status == "pass"


def test_capturing_group_regex_passes_when_version_matches(tmp_path):
    fake = _fake_bin(tmp_path, "footool", "footool version 1.2.3")
    manifest = _write_manifest(
        tmp_path,
        [
            {
                "id": "footool",
                "version": "1.2.3",
                "version_cmd": [str(fake)],
                "version_regex": r"footool version (\d+\.\d+\.\d+)",
            }
        ],
    )
    results = toolcheck.run_tool_checks(manifest)
    assert results[0].status == "pass"
    assert results[0].measured == "1.2.3"


# --- Proof each failure mode actually fails --------------------------------


def test_FAILS_on_missing_binary(tmp_path):
    manifest = _write_manifest(
        tmp_path,
        [
            {
                "id": "ghost-tool",
                "version": "1.0.0",
                "version_cmd": [str(tmp_path / "does-not-exist-binary")],
                "version_regex": r"1\.0\.0",
            }
        ],
    )
    results = toolcheck.run_tool_checks(manifest)
    assert results[0].status == "fail"
    assert "not found" in results[0].measured.lower()
    assert results[0].fix


def test_FAILS_on_version_mismatch_with_capturing_group(tmp_path):
    """The installed tool reports 1.2.4, but the manifest pins 1.2.3."""
    fake = _fake_bin(tmp_path, "footool", "footool version 1.2.4")
    manifest = _write_manifest(
        tmp_path,
        [
            {
                "id": "footool",
                "version": "1.2.3",
                "version_cmd": [str(fake)],
                "version_regex": r"footool version (\d+\.\d+\.\d+)",
            }
        ],
    )
    results = toolcheck.run_tool_checks(manifest)
    assert results[0].status == "fail"
    assert results[0].measured == "1.2.4"
    assert results[0].expected == "1.2.3"


def test_FAILS_on_version_mismatch_without_capturing_group(tmp_path):
    """No capture group: the regex is a literal pinned-version string, so a
    different installed version simply fails to match at all."""
    fake = _fake_bin(tmp_path, "footool", "footool version 9.9.9")
    manifest = _write_manifest(
        tmp_path,
        [
            {
                "id": "footool",
                "version": "1.2.3",
                "version_cmd": [str(fake)],
                "version_regex": r"footool version 1\.2\.3",
            }
        ],
    )
    results = toolcheck.run_tool_checks(manifest)
    assert results[0].status == "fail"


def test_FAILS_on_unpinned_entry(tmp_path):
    manifest = _write_manifest(
        tmp_path,
        [
            {
                "id": "unpinned-tool",
                "version": "",
                "version_cmd": ["python3", "--version"],
                "version_regex": r"Python",
            }
        ],
    )
    results = toolcheck.run_tool_checks(manifest)
    assert results[0].status == "fail"
    assert results[0].detail == "unpinned entry"
    assert "unpinned" in results[0].measured.lower()


def test_FAILS_on_unpinned_entry_missing_version_key_entirely(tmp_path):
    manifest = _write_manifest(
        tmp_path,
        [{"id": "no-version-field", "version_cmd": ["python3"], "version_regex": "x"}],
    )
    results = toolcheck.run_tool_checks(manifest)
    assert results[0].status == "fail"
    assert results[0].detail == "unpinned entry"


def test_check_result_with_fail_status_requires_a_fix_string():
    """The shared CheckResult contract (ADR-001 section 13 rule 6): a fail
    with no remediation string is a programming error, not a valid report."""
    import pytest

    from forge.checks import CheckResult

    with pytest.raises(ValueError):
        CheckResult(id="x", status="fail", rule="something must hold")
