"""Tests for `forge evidence add|from-checks|list|status` (lib/forge/commands/evidence.py)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from forge import evidence as evidence_lib
from forge.cli import main


def _run(capsys, argv, repo_root):
    code = main(argv, repo_root=repo_root)
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def test_add_writes_an_entry(tmp_path, capsys, repo_root):
    code, out, _err = _run(capsys, [
        "evidence", "--project", str(tmp_path), "add",
        "--artifact", "cad/enclosure.step", "--domain", "mech", "--claim", "walls meet minimum",
        "--check-id", "geometry.min_wall", "--result", "pass", "--level", "L1",
    ], repo_root)
    assert code == 0
    assert "EV-0001" in out
    manifest = evidence_lib.load(tmp_path)
    assert manifest["entries"][0]["domain"] == "mech"


def test_add_requires_signed_by_at_l4(tmp_path, capsys, repo_root):
    code, _out, err = _run(capsys, [
        "evidence", "--project", str(tmp_path), "add",
        "--artifact", "x", "--domain", "mech", "--claim", "physically tested",
        "--result", "pass", "--level", "L4",
    ], repo_root)
    assert code == 1
    assert "signed_by" in err


def test_from_checks_summarizes_check_files(tmp_path, capsys, repo_root):
    check_path = tmp_path / "out" / "verify" / "geometry.min_wall.json"
    check_path.parent.mkdir(parents=True)
    check_path.write_text(json.dumps({
        "schema": "forge.check/1", "check_id": "geometry.min_wall", "target": "cad/enclosure.py",
        "status": "pass", "level": "L1", "measurements": [{"name": "min_wall", "value": 2.1, "unit": "mm",
        "limit": {"min": 2.0}, "pass": True}], "tool_versions": {"build123d": "0.11.1"}, "git_sha": "x",
        "started": "2026-01-01T00:00:00Z", "duration_s": 0.2,
    }))
    code, out, _err = _run(capsys, [
        "evidence", "--project", str(tmp_path), "from-checks",
        "--check", str(check_path), "--artifact", "cad/enclosure.step", "--domain", "mech",
        "--claim", "geometry checks pass",
    ], repo_root)
    assert code == 0
    assert "EV-0001" in out
    manifest = evidence_lib.load(tmp_path)
    assert manifest["entries"][0]["result"] == "pass"
    assert manifest["entries"][0]["level"] == "L1"


def test_list_filters_by_domain_and_status(tmp_path, capsys, repo_root):
    evidence_lib.add_entry(tmp_path, artifact="a", domain="mech", claim="claim one", check_ids=[],
                            result="pass", level="L1", evidence_files=[], status="VERIFIED")
    evidence_lib.add_entry(tmp_path, artifact="b", domain="elec", claim="claim two", check_ids=[],
                            result="fail", level="L0", evidence_files=[], status="UNVERIFIED")
    code, out, _err = _run(capsys, ["evidence", "--project", str(tmp_path), "list", "--domain", "mech"], repo_root)
    assert code == 0
    assert "EV-0001" in out
    assert "EV-0002" not in out


def test_status_shows_latest_entry_per_domain(tmp_path, capsys, repo_root):
    evidence_lib.add_entry(tmp_path, artifact="a", domain="mech", claim="first", check_ids=[],
                            result="fail", level="L1", evidence_files=[], status="VERIFIED")
    evidence_lib.add_entry(tmp_path, artifact="a", domain="mech", claim="second, now passing", check_ids=[],
                            result="pass", level="L1", evidence_files=[], status="VERIFIED")
    code, out, _err = _run(capsys, ["evidence", "--project", str(tmp_path), "status"], repo_root)
    assert code == 0
    assert "mech: pass" in out


def test_status_json_output(tmp_path, capsys, repo_root):
    evidence_lib.add_entry(tmp_path, artifact="a", domain="mech", claim="checks pass", check_ids=[],
                            result="pass", level="L1", evidence_files=[], status="VERIFIED")
    code, out, _err = _run(capsys, ["evidence", "--project", str(tmp_path), "status", "--json"], repo_root)
    assert code == 0
    data = json.loads(out)
    assert data["mech"]["result"] == "pass"


def test_add_bad_tool_version_format_is_rejected(tmp_path, capsys, repo_root):
    code, _out, err = _run(capsys, [
        "evidence", "--project", str(tmp_path), "add",
        "--artifact", "a", "--domain", "mech", "--claim", "x", "--result", "pass", "--level", "L1",
        "--tool-version", "not-a-pair",
    ], repo_root)
    assert code == 1
    assert "NAME=VERSION" in err
