"""Tests for hooks/stop.py -- the evidence gate (CONTRACTS.md §8-9, ADR-001 D5).

Every rule has a seeded-wrong case that must block and a pass case. The
review #1 findings each test pins are named in the test's docstring.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

from .hookutil import (
    LIB_DIR, commit_all, forge_project, git, non_forge_project, record_run, run_hook, verify_patterns,
)

sys.path.insert(0, str(LIB_DIR))
from forge import evidence as evidence_lib  # noqa: E402
from forge import state as state_lib  # noqa: E402


def _dirty(project: Path, rel: str, content: str = "\nchanged\n") -> None:
    path = project / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as fh:
        fh.write(content)


def _stop(project: Path, **extra) -> "object":
    return run_hook("stop.py", {"cwd": str(project), **extra})


def _rewrite_manifest(project: Path, fn) -> None:
    path = project / "evidence" / "manifest.json"
    data = json.loads(path.read_text())
    fn(data["entries"])
    path.write_text(json.dumps(data, indent=2))


# ---------------------------------------------------------------------------
# basics
# ---------------------------------------------------------------------------

def test_noop_outside_forge_project(non_forge_project):
    result = _stop(non_forge_project)
    assert result.returncode == 0
    assert result.output is None


def test_no_changes_passes_silently(forge_project):
    result = _stop(forge_project)
    assert (result.returncode, result.output) == (0, None)


def test_unsatisfied_domain_blocks(forge_project):
    """Sabotage case: cad/ changed with no evidence must block."""
    _dirty(forge_project, "cad/enclosure.py")
    result = _stop(forge_project)
    assert result.returncode == 2
    assert result.output["decision"] == "block"
    assert "mech/verifying-geometry" in result.output["reason"]
    assert "cad/enclosure.py" in result.output["reason"]


def test_change_outside_any_verify_domain_passes(forge_project):
    (forge_project / "notes.txt").write_text("hello\n")
    result = _stop(forge_project)
    assert (result.returncode, result.output) == (0, None)


def test_bound_verify_run_satisfies_the_gate(forge_project):
    """Pass case: a real forge verify run recorded after the change."""
    _dirty(forge_project, "cad/enclosure.py")
    record_run(forge_project, "mech", "verifying-geometry")
    result = _stop(forge_project)
    assert (result.returncode, result.output) == (0, None), result.output
    assert state_lib.load(forge_project)["stop_block_count"] == 0


# ---------------------------------------------------------------------------
# C2: evidence must be bound to a real, passing, current check run
# ---------------------------------------------------------------------------

def test_hand_written_evidence_entry_does_not_satisfy_the_gate(forge_project):
    """C2 seeded wrong: `forge evidence add --result pass` with no check run."""
    _dirty(forge_project, "cad/enclosure.py")
    time.sleep(1.1)
    evidence_lib.add_entry(
        forge_project, artifact="cad/enclosure.py", domain="mech", claim="trust me, geometry passes",
        check_ids=["geometry.min_wall"], result="pass", level="L1", evidence_files=[], status="VERIFIED",
    )
    result = _stop(forge_project)
    assert result.returncode == 2
    assert "no `forge verify` run" in result.output["reason"]


def test_hand_edited_manifest_entry_mimicking_verify_is_rejected(forge_project):
    """C2 seeded wrong: an entry that *claims* to be a verify run but
    references a check file that was never written."""
    _dirty(forge_project, "cad/enclosure.py")
    evidence_lib.add_entry(forge_project, artifact="x", domain="mech", claim="forged verify run",
                           check_ids=["mech.x"], result="pass", level="L1",
                           evidence_files=["out/verify/mech.x.json"], status="VERIFIED",
                           _run={"entrypoint": "verifying-geometry", "recorded_by": "forge verify",
                                 "mode": "full", "scope": None, "returncode": 0,
                                 "evidence_sha256": {"out/verify/mech.x.json": "0" * 64}})
    result = _stop(forge_project)
    assert result.returncode == 2
    assert "missing or not a forge.check/1 result" in result.output["reason"]


def test_committing_the_change_does_not_bypass_the_gate(forge_project):
    """C2 seeded wrong: the old gate only read `git status`."""
    _dirty(forge_project, "cad/enclosure.py")
    commit_all(forge_project, "sneak it in")
    assert git(forge_project, "status", "--porcelain").strip() == ""
    result = _stop(forge_project)
    assert result.returncode == 2
    assert "cad/enclosure.py" in result.output["reason"]


def test_committed_change_with_bound_evidence_passes(forge_project):
    _dirty(forge_project, "cad/enclosure.py")
    commit_all(forge_project)
    record_run(forge_project, "mech", "verifying-geometry")
    assert _stop(forge_project).returncode == 0


def test_future_dated_evidence_is_rejected(forge_project):
    """C2 seeded wrong: an entry dated 2099 used to satisfy every later edit."""
    _dirty(forge_project, "cad/enclosure.py")
    record_run(forge_project, "mech", "verifying-geometry")
    _rewrite_manifest(forge_project, lambda es: es[-1].update(timestamp="2099-01-01T00:00:00Z"))
    result = _stop(forge_project)
    assert result.returncode == 2
    assert "future" in result.output["reason"]


def test_future_started_check_file_is_rejected(forge_project):
    _dirty(forge_project, "cad/enclosure.py")
    record_run(forge_project, "mech", "verifying-geometry")
    f = forge_project / "out/verify/mech.verifying_geometry.json"
    data = json.loads(f.read_text())
    data["started"] = "2099-01-01T00:00:00Z"
    f.write_text(json.dumps(data))
    result = _stop(forge_project)
    assert result.returncode == 2
    assert "future" in result.output["reason"] or "changed after the run" in result.output["reason"]


def test_change_after_the_verify_run_blocks(forge_project):
    """inputs_sha256 no longer matches the domain's files."""
    record_run(forge_project, "mech", "verifying-geometry")
    _dirty(forge_project, "cad/enclosure.py")
    result = _stop(forge_project)
    assert result.returncode == 2
    assert "inputs changed" in result.output["reason"] or "older than the change" in result.output["reason"]


def test_inputs_hash_mismatch_alone_blocks(forge_project):
    """Even with a newer check file, a different inputs digest blocks."""
    _dirty(forge_project, "cad/enclosure.py")
    record_run(forge_project, "mech", "verifying-geometry")
    _rewrite_manifest(forge_project, lambda es: es[-1].update(inputs_sha256="f" * 64))
    result = _stop(forge_project)
    assert result.returncode == 2
    assert "inputs_sha256 mismatch" in result.output["reason"]


def test_tampered_check_file_is_rejected(forge_project):
    """A check result flipped by hand after the run no longer matches its sha256."""
    _dirty(forge_project, "cad/enclosure.py")
    record_run(forge_project, "mech", "verifying-geometry", status="fail")
    # the newest run failed; now forge a 'pass' entry pointing at the same (failing) file
    f = forge_project / "out/verify/mech.verifying_geometry.json"
    data = json.loads(f.read_text())
    data["status"] = "pass"
    f.write_text(json.dumps(data))
    _rewrite_manifest(forge_project, lambda es: es[-1].update(result="pass"))
    result = _stop(forge_project)
    assert result.returncode == 2
    assert "changed after the run" in result.output["reason"]


def test_deleted_check_file_is_rejected(forge_project):
    _dirty(forge_project, "cad/enclosure.py")
    record_run(forge_project, "mech", "verifying-geometry")
    (forge_project / "out/verify/mech.verifying_geometry.json").unlink()
    result = _stop(forge_project)
    assert result.returncode == 2
    assert "missing" in result.output["reason"]


def test_fast_run_does_not_satisfy_the_gate(forge_project):
    _dirty(forge_project, "cad/enclosure.py")
    record_run(forge_project, "mech", "verifying-geometry", fast=True)
    result = _stop(forge_project)
    assert result.returncode == 2
    assert "--fast" in result.output["reason"]


def test_changed_scope_must_cover_every_changed_file(forge_project):
    _dirty(forge_project, "cad/enclosure.py")
    _dirty(forge_project, "cad/other.py")
    record_run(forge_project, "mech", "verifying-geometry", scope=["cad/other.py"])
    result = _stop(forge_project)
    assert result.returncode == 2
    assert "only verified --changed" in result.output["reason"]
    record_run(forge_project, "mech", "verifying-geometry", scope=["cad/enclosure.py", "cad/other.py"])
    assert _stop(forge_project).returncode == 0


# ---------------------------------------------------------------------------
# M6: newest entry per (domain, entrypoint), all must pass
# ---------------------------------------------------------------------------

def _two_entrypoint_project(project: Path) -> None:
    text = (project / "forge.toml").read_text().replace(
        'entrypoints = ["verifying-geometry"]', 'entrypoints = ["verifying-geometry", "checking-dfm"]')
    (project / "forge.toml").write_text(text)
    commit_all(project, "two mech entrypoints")


def test_failing_sibling_check_blocks(forge_project):
    """M6 seeded wrong: an older pass plus the newest sibling FAIL used to pass."""
    _two_entrypoint_project(forge_project)
    _dirty(forge_project, "cad/enclosure.py")
    record_run(forge_project, "mech", "verifying-geometry", status="pass")
    record_run(forge_project, "mech", "checking-dfm", status="fail")
    result = _stop(forge_project)
    assert result.returncode == 2
    assert "mech/checking-dfm" in result.output["reason"]
    assert "mech/verifying-geometry" not in result.output["reason"]


def test_newer_failing_run_supersedes_older_pass(forge_project):
    _dirty(forge_project, "cad/enclosure.py")
    record_run(forge_project, "mech", "verifying-geometry", status="pass")
    record_run(forge_project, "mech", "verifying-geometry", status="fail", check_id="mech.second")
    result = _stop(forge_project)
    assert result.returncode == 2
    assert "did not pass" in result.output["reason"]


def test_all_entrypoints_passing_satisfies_the_gate(forge_project):
    _two_entrypoint_project(forge_project)
    _dirty(forge_project, "cad/enclosure.py")
    record_run(forge_project, "mech", "verifying-geometry")
    record_run(forge_project, "mech", "checking-dfm")
    assert _stop(forge_project).returncode == 0


# ---------------------------------------------------------------------------
# C1: the docs domain
# ---------------------------------------------------------------------------

def test_docs_change_without_evidence_blocks(forge_project):
    (forge_project / "README.md").write_text("hello\n")
    result = _stop(forge_project)
    assert result.returncode == 2
    assert "docs/gardening-docs" in result.output["reason"]


def test_docs_change_with_docs_verify_run_passes(forge_project):
    """C1: `docs` is a real evidence domain now (it used to be filed under sys)."""
    assert "docs" in evidence_lib.DOMAINS
    (forge_project / "README.md").write_text("hello\n")
    record_run(forge_project, "docs", "gardening-docs")
    result = _stop(forge_project)
    assert (result.returncode, result.output) == (0, None), result.output


# ---------------------------------------------------------------------------
# last-green base (C2) and its validation
# ---------------------------------------------------------------------------

def test_last_green_limits_the_diff(forge_project):
    _dirty(forge_project, "cad/enclosure.py")
    ev = record_run(forge_project, "mech", "verifying-geometry")
    head = commit_all(forge_project)
    # re-run after the commit so the entry's git_sha is the new HEAD, then mark it green
    ev = record_run(forge_project, "mech", "verifying-geometry")
    state_lib.set_last_green(forge_project, "mech", sha=head, evidence_ids=[ev])
    assert state_lib.resolve_base(forge_project, "mech", evidence_lib.load(forge_project)) == head
    # outputs deleted: nothing changed since last green, so nothing is required
    for f in (forge_project / "out/verify").glob("*.json"):
        f.unlink()
    assert _stop(forge_project).returncode == 0


def test_forged_last_green_is_ignored(forge_project):
    """Seeded wrong: a last-green SHA with no vouching verify entries."""
    _dirty(forge_project, "cad/enclosure.py")
    head = commit_all(forge_project)
    state_lib.set_last_green(forge_project, "mech", sha=head, evidence_ids=[])
    assert state_lib.resolve_base(forge_project, "mech", evidence_lib.load(forge_project)) != head
    assert _stop(forge_project).returncode == 2
    state_lib.set_last_green(forge_project, "mech", sha=head, evidence_ids=["EV-9999"])
    assert _stop(forge_project).returncode == 2


# ---------------------------------------------------------------------------
# M3: verified params changed by any means
# ---------------------------------------------------------------------------

def test_verified_param_changed_by_shell_is_blocked_even_with_evidence(forge_project):
    """M3 seeded wrong: `sed -i` on a verified value, committed, with a fresh
    passing mech run -- the Stop diff still catches it."""
    params = forge_project / "params" / "params.toml"
    params.write_text(params.read_text().replace("value = 40.0", "value = 35.0"))
    commit_all(forge_project, "shrink")
    record_run(forge_project, "mech", "verifying-geometry")
    result = _stop(forge_project)
    assert result.returncode == 2
    assert "enclosure.height" in result.output["reason"]


def test_verified_param_changed_through_forge_params_set_passes(forge_project):
    import subprocess
    forge_bin = LIB_DIR.parent / "bin" / "forge"
    res = subprocess.run([sys.executable, str(forge_bin), "params", "--project", str(forge_project), "set",
                          "enclosure.height", "--value", "35.0",
                          "--source", "rev B drawing D-102 sheet 2, height reduced for the new PCB",
                          "--justification", "PCB stack is 5 mm shorter in rev B"],
                         capture_output=True, text=True)
    assert res.returncode == 0, res.stderr
    record_run(forge_project, "mech", "verifying-geometry")
    result = _stop(forge_project)
    assert (result.returncode, result.output) == (0, None), result.output


# ---------------------------------------------------------------------------
# block counter and the 7th-block handoff
# ---------------------------------------------------------------------------

def test_counter_increments_and_resets_on_pass(forge_project):
    _dirty(forge_project, "cad/enclosure.py")
    for _ in range(3):
        _stop(forge_project)
    assert state_lib.load(forge_project)["stop_block_count"] == 3
    record_run(forge_project, "mech", "verifying-geometry")
    _stop(forge_project)
    assert state_lib.load(forge_project)["stop_block_count"] == 0


def test_seventh_block_records_unverified_and_lets_stop_proceed(forge_project):
    _dirty(forge_project, "cad/enclosure.py")
    (forge_project / "README.md").write_text("docs change too\n")
    results = [_stop(forge_project, stop_hook_active=i > 0) for i in range(7)]
    for r in results[:6]:
        assert r.returncode == 2, "attempts 1-6 must keep blocking"
    seventh = results[6]
    assert seventh.returncode == 0, seventh.stderr
    assert "UNVERIFIED" in seventh.output["systemMessage"]
    assert "WARNING" not in seventh.output["systemMessage"]
    manifest = evidence_lib.load(forge_project)
    domains = {e["domain"] for e in manifest["entries"] if e["status"] == "UNVERIFIED"}
    assert domains == {"mech", "docs"}, "C1: the docs UNVERIFIED write must not raise"
    assert state_lib.load(forge_project)["stop_block_count"] == 0
    assert _stop(forge_project, stop_hook_active=True).returncode == 2


def test_handoff_never_raises_and_always_resets(forge_project):
    """C1 seeded wrong: an unknown forge.toml domain and an unwritable
    manifest made the old handoff raise, so the counter never reset."""
    text = (forge_project / "forge.toml").read_text() + (
        '\n[[verify]]\ndomain = "weird"\npaths = ["weird/**"]\nentrypoints = ["x"]\n')
    (forge_project / "forge.toml").write_text(text)
    commit_all(forge_project, "weird domain")
    _dirty(forge_project, "weird/a.txt")
    (forge_project / "evidence" / "manifest.json").write_text("{not json")
    results = [_stop(forge_project) for _ in range(7)]
    assert [r.returncode for r in results[:6]] == [2] * 6
    assert results[6].returncode == 0, results[6].stderr
    assert "WARNING" in results[6].output["systemMessage"]
    assert state_lib.load(forge_project)["stop_block_count"] == 0


def test_corrupt_manifest_blocks_instead_of_crashing(forge_project):
    _dirty(forge_project, "cad/enclosure.py")
    (forge_project / "evidence" / "manifest.json").write_text("[]")
    result = _stop(forge_project)
    assert result.returncode == 2
    assert result.output["decision"] == "block"
    assert "unreadable" in result.output["reason"]


def test_invalid_forge_toml_fails_closed(forge_project):
    (forge_project / "forge.toml").write_text("[[verify]\nbroken")
    _dirty(forge_project, "cad/enclosure.py")
    result = _stop(forge_project)
    assert result.returncode == 2
    assert "not valid TOML" in result.stderr


def test_stop_runs_reasonably_fast(forge_project):
    _dirty(forge_project, "cad/enclosure.py")
    start = time.monotonic()
    _stop(forge_project)
    assert time.monotonic() - start < 10.0


def test_verify_patterns_helper_matches_forge_toml(forge_project):
    assert verify_patterns(forge_project, "mech", "verifying-geometry") == ["cad/**", "params/**"]
    assert os.path.isdir(forge_project / "cad")
