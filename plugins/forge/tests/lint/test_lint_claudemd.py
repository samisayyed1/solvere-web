"""Tests for `forge lint claudemd` (brief SS3.1, ADR-001 D3)."""

from __future__ import annotations

from forge.lintlib import claudemd


def _write(tmp_path, name, n_lines):
    p = tmp_path / name
    p.write_text("\n".join(f"line {i}" for i in range(n_lines)) + "\n")
    return p


def test_claudemd_at_100_lines_PASSES(tmp_path):
    p = _write(tmp_path, "CLAUDE.md", 100)
    results = claudemd.lint_claudemd([p])
    assert len(results) == 1
    assert results[0].status == "pass"
    assert results[0].measured == 100


def test_claudemd_at_101_lines_FAILS(tmp_path):
    """The seeded-wrong case named in the build brief: '101-line CLAUDE.md'."""
    p = _write(tmp_path, "CLAUDE.md", 101)
    results = claudemd.lint_claudemd([p])
    assert len(results) == 1
    assert results[0].status == "fail"
    assert results[0].measured == 101
    assert "CLAUDE.md" in results[0].fix


def test_missing_claudemd_target_is_SKIP(tmp_path):
    results = claudemd.lint_claudemd([tmp_path / "nope" / "CLAUDE.md"])
    assert len(results) == 1
    assert results[0].status == "skip"


def test_multiple_paths_are_each_checked_independently(tmp_path):
    short = _write(tmp_path, "short.md", 10)
    long = _write(tmp_path, "long.md", 150)
    results = claudemd.lint_claudemd([short, long, tmp_path / "missing.md"])
    statuses = {str(r.id).split(":", 1)[1]: r.status for r in results if r.id.startswith("claudemd.length") or r.id.startswith("claudemd.exists")}
    assert statuses[str(short)] == "pass"
    assert statuses[str(long)] == "fail"
    assert statuses[str(tmp_path / "missing.md")] == "skip"
