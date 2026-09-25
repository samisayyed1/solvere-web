"""releasing-designs release.py: refuses without approval, or with a stale sha
(CONTRACTS.md §13)."""
from __future__ import annotations

import json

import pytest

from .conftest import init_git_repo, load_skill_module

BLANK_SIGNOFF = "Human sign-off: ____________  Name: ____  Date: ____  Decision: PASS / FAIL"
PASS_SIGNOFF = "Human sign-off: /s/ Jane Doe  Name: Jane Doe  Date: 2026-09-25  Decision: PASS"
FAIL_SIGNOFF = "Human sign-off: /s/ Jane Doe  Name: Jane Doe  Date: 2026-09-25  Decision: FAIL"


@pytest.fixture
def release_mod():
    return load_skill_module("releasing-designs", "release.py")


@pytest.fixture
def project(tmp_path):
    sha = init_git_repo(tmp_path)
    return tmp_path, sha


def _write_gate(project, gate, signoff_line):
    reviews = project / "reviews"
    reviews.mkdir(parents=True, exist_ok=True)
    (reviews / f"{gate}.md").write_text(f"# Gate {gate}\n\n...\n\n{signoff_line}\n")


def _write_approval(project, *, git_sha, gate="G2", **overrides):
    fields = {"approved_by": "jane.doe", "date": "2026-09-25", "git_sha": git_sha,
              "scope": "release v0.1.0", "gate": gate}
    fields.update(overrides)
    release_dir = project / "release"
    release_dir.mkdir(parents=True, exist_ok=True)
    body = "\n".join(f'{k} = "{v}"' for k, v in fields.items())
    (release_dir / "APPROVAL.toml").write_text(body + "\n")


def test_refuses_without_approval_file(release_mod, project):
    proj, sha = project
    rc = release_mod.main(["--project", str(proj)])
    assert rc == 1
    assert not (proj / "release" / "0.1.0").exists()


def test_refuses_with_stale_git_sha(release_mod, project):
    proj, sha = project
    _write_approval(proj, git_sha="0" * 40, gate="G2")  # deliberately not HEAD
    _write_gate(proj, "G2", PASS_SIGNOFF)
    rc = release_mod.main(["--project", str(proj)])
    assert rc == 1
    # no bundle should have been built
    assert not list((proj / "release").glob("*/RELEASE-MANIFEST.json"))


def test_refuses_when_gate_record_missing(release_mod, project):
    proj, sha = project
    _write_approval(proj, git_sha=sha, gate="G2")
    rc = release_mod.main(["--project", str(proj)])
    assert rc == 1


def test_refuses_when_signoff_still_blank(release_mod, project):
    proj, sha = project
    _write_approval(proj, git_sha=sha, gate="G2")
    _write_gate(proj, "G2", BLANK_SIGNOFF)
    rc = release_mod.main(["--project", str(proj)])
    assert rc == 1


def test_refuses_when_gate_signed_fail(release_mod, project):
    proj, sha = project
    _write_approval(proj, git_sha=sha, gate="G2")
    _write_gate(proj, "G2", FAIL_SIGNOFF)
    rc = release_mod.main(["--project", str(proj)])
    assert rc == 1


def test_refuses_with_missing_required_field(release_mod, project):
    proj, sha = project
    _write_approval(proj, git_sha=sha, gate="G2", approved_by="")
    _write_gate(proj, "G2", PASS_SIGNOFF)
    rc = release_mod.main(["--project", str(proj)])
    assert rc == 1


def test_builds_bundle_when_fresh_approval_and_pass_signoff(release_mod, project):
    proj, sha = project
    _write_approval(proj, git_sha=sha, gate="G2")
    _write_gate(proj, "G2", PASS_SIGNOFF)
    rc = release_mod.main(["--project", str(proj), "--version", "0.1.0"])
    assert rc == 0
    manifest_path = proj / "release" / "0.1.0" / "RELEASE-MANIFEST.json"
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text())
    assert manifest["git_sha"] == sha
    assert manifest["approval"]["gate"] == "G2"
    # nothing was staged (no cad/ecad/bom/firmware in this bare project) -> every part skipped, not silently dropped
    for part_name, part in manifest["parts"].items():
        assert part["status"] in ("skipped", "included"), part_name
        if part["status"] == "skipped":
            assert "reason" in part
    assert (proj / "release" / "0.1.0" / "GIT_SHA.txt").read_text().strip() == sha


def test_bundle_includes_evidence_manifest_when_present(release_mod, project):
    proj, sha = project
    _write_approval(proj, git_sha=sha, gate="G2")
    _write_gate(proj, "G2", PASS_SIGNOFF)
    (proj / "evidence").mkdir()
    (proj / "evidence" / "manifest.json").write_text(json.dumps({"schema": "forge.evidence/1", "entries": []}))
    rc = release_mod.main(["--project", str(proj), "--version", "0.1.0"])
    assert rc == 0
    assert (proj / "release" / "0.1.0" / "evidence" / "manifest.json").exists()
    manifest = json.loads((proj / "release" / "0.1.0" / "RELEASE-MANIFEST.json").read_text())
    assert manifest["parts"]["evidence"]["status"] == "included"


def _write_evidence(project, entries):
    ev_dir = project / "evidence"
    ev_dir.mkdir(parents=True, exist_ok=True)
    (ev_dir / "manifest.json").write_text(json.dumps({"schema": "forge.evidence/1", "entries": entries}))


def _valid_evidence_entry(**overrides):
    entry = {
        "id": "EV-0001", "artifact": "cad/enclosure.py", "domain": "mech", "claim": "wall ok",
        "check_ids": ["geometry.min_wall"], "result": "pass", "level": "L1", "evidence_files": [],
        "inputs_sha256": "0" * 64, "tool_versions": {}, "git_sha": "nogit",
        "model": "test", "timestamp": "2026-01-01T00:00:00Z", "status": "VERIFIED",
    }
    entry.update(overrides)
    return entry


def test_refuses_when_evidence_has_an_unverified_entry(release_mod, project):
    """M9 (review #1): ADR-001 SS11 says UNVERIFIED evidence blocks releases;
    nothing enforced it before this fix."""
    proj, sha = project
    _write_approval(proj, git_sha=sha, gate="G2")
    _write_gate(proj, "G2", PASS_SIGNOFF)
    _write_evidence(proj, [_valid_evidence_entry(status="UNVERIFIED")])
    rc = release_mod.main(["--project", str(proj), "--version", "0.1.0"])
    assert rc == 1
    assert not list((proj / "release").glob("0.1.0/RELEASE-MANIFEST.json"))


def test_refuses_when_evidence_records_a_failing_result(release_mod, project):
    """The other half of M9: a VERIFIED-but-failing entry also blocks a release."""
    proj, sha = project
    _write_approval(proj, git_sha=sha, gate="G2")
    _write_gate(proj, "G2", PASS_SIGNOFF)
    _write_evidence(proj, [_valid_evidence_entry(result="fail")])
    rc = release_mod.main(["--project", str(proj), "--version", "0.1.0"])
    assert rc == 1
    assert not list((proj / "release").glob("0.1.0/RELEASE-MANIFEST.json"))


def test_refuses_when_a_check_result_file_is_failing(release_mod, project):
    """A failing out/verify/*.json blocks a release even if it was never
    rolled up into evidence/manifest.json at all."""
    proj, sha = project
    _write_approval(proj, git_sha=sha, gate="G2")
    _write_gate(proj, "G2", PASS_SIGNOFF)
    verify_dir = proj / "out" / "verify"
    verify_dir.mkdir(parents=True)
    (verify_dir / "geometry.min_wall.json").write_text(json.dumps({
        "schema": "forge.check/1", "check_id": "geometry.min_wall", "target": "cad/x.py",
        "status": "fail", "level": "L1",
        "measurements": [{"name": "min_wall", "value": 1.0, "unit": "mm", "limit": {"min": 2.0},
                           "pass": False, "remediation": "thicken the wall to >= 2.0 mm"}],
        "tool_versions": {}, "git_sha": "nogit", "started": "2026-01-01T00:00:00Z", "duration_s": 0.1,
    }))
    rc = release_mod.main(["--project", str(proj), "--version", "0.1.0"])
    assert rc == 1
    assert not list((proj / "release").glob("0.1.0/RELEASE-MANIFEST.json"))


def test_builds_when_evidence_is_all_verified_and_passing(release_mod, project):
    """The positive case: a clean evidence manifest (and a passing check
    result) must not block an otherwise-approved release."""
    proj, sha = project
    _write_approval(proj, git_sha=sha, gate="G2")
    _write_gate(proj, "G2", PASS_SIGNOFF)
    _write_evidence(proj, [_valid_evidence_entry()])
    verify_dir = proj / "out" / "verify"
    verify_dir.mkdir(parents=True)
    (verify_dir / "geometry.min_wall.json").write_text(json.dumps({
        "schema": "forge.check/1", "check_id": "geometry.min_wall", "target": "cad/x.py",
        "status": "pass", "level": "L1",
        "measurements": [{"name": "min_wall", "value": 2.5, "unit": "mm", "limit": {"min": 2.0}, "pass": True}],
        "tool_versions": {}, "git_sha": "nogit", "started": "2026-01-01T00:00:00Z", "duration_s": 0.1,
    }))
    rc = release_mod.main(["--project", str(proj), "--version", "0.1.0"])
    assert rc == 0
    manifest_path = proj / "release" / "0.1.0" / "RELEASE-MANIFEST.json"
    assert manifest_path.exists()


def test_signoff_detector_rejects_blank_and_accepts_filled(release_mod):
    filled_ok, decision = release_mod.gate_signed_off(f"# Gate G2\n{PASS_SIGNOFF}\n")
    assert filled_ok is True and decision == "PASS"
    blank_ok, reason = release_mod.gate_signed_off(f"# Gate G2\n{BLANK_SIGNOFF}\n")
    assert blank_ok is False
