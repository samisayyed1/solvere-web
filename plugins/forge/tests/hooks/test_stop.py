"""Tests for hooks/stop.py -- the evidence gate (CONTRACTS.md §8-9, ADR-001 D5)."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

from .hookutil import LIB_DIR, forge_project, non_forge_project, run_hook

sys.path.insert(0, str(LIB_DIR))
from forge import evidence as evidence_lib  # noqa: E402
from forge import state as state_lib  # noqa: E402


def _dirty(project: Path, rel: str, content: str = "\nchanged\n") -> None:
    with (project / rel).open("a") as fh:
        fh.write(content)


def test_noop_outside_forge_project(non_forge_project):
    result = run_hook("stop.py", {"cwd": str(non_forge_project)})
    assert result.returncode == 0
    assert result.output is None


def test_no_changes_passes_silently(forge_project):
    result = run_hook("stop.py", {"cwd": str(forge_project)})
    assert result.returncode == 0
    assert result.output is None


def test_unsatisfied_domain_blocks(forge_project):
    """Sabotage case: cad/ changed with no fresh passing evidence must block."""
    _dirty(forge_project, "cad/enclosure.py")
    result = run_hook("stop.py", {"cwd": str(forge_project)})
    assert result.returncode == 2
    assert result.output["decision"] == "block"
    assert "mech" in result.output["reason"]
    assert "cad/enclosure.py" in result.output["reason"]


def test_change_outside_any_verify_domain_passes(forge_project):
    (forge_project / "README.md").write_text("hello\n")
    result = run_hook("stop.py", {"cwd": str(forge_project)})
    assert result.returncode == 0
    assert result.output is None


def test_passing_fresh_evidence_satisfies_the_gate(forge_project):
    _dirty(forge_project, "cad/enclosure.py")
    time.sleep(1.1)  # evidence timestamp must be newer than the file mtime
    evidence_lib.add_entry(
        forge_project, artifact="cad/enclosure.py", domain="mech", claim="geometry checks pass",
        check_ids=["geometry.min_wall"], result="pass", level="L1", evidence_files=[], status="VERIFIED",
    )
    result = run_hook("stop.py", {"cwd": str(forge_project)})
    assert result.returncode == 0
    assert result.output is None
    assert state_lib.load(forge_project)["stop_block_count"] == 0


def test_stale_evidence_older_than_change_still_blocks(forge_project):
    evidence_lib.add_entry(
        forge_project, artifact="cad/enclosure.py", domain="mech", claim="old check",
        check_ids=["geometry.min_wall"], result="pass", level="L1", evidence_files=[], status="VERIFIED",
    )
    time.sleep(1.1)
    _dirty(forge_project, "cad/enclosure.py")  # change happens AFTER the evidence
    result = run_hook("stop.py", {"cwd": str(forge_project)})
    assert result.returncode == 2
    assert result.output["decision"] == "block"


def test_failing_evidence_does_not_satisfy_the_gate(forge_project):
    _dirty(forge_project, "cad/enclosure.py")
    time.sleep(1.1)
    evidence_lib.add_entry(
        forge_project, artifact="cad/enclosure.py", domain="mech", claim="geometry checks fail",
        check_ids=["geometry.min_wall"], result="fail", level="L1", evidence_files=[], status="VERIFIED",
    )
    result = run_hook("stop.py", {"cwd": str(forge_project)})
    assert result.returncode == 2


def test_counter_increments_and_resets_on_pass(forge_project):
    _dirty(forge_project, "cad/enclosure.py")
    for _ in range(3):
        run_hook("stop.py", {"cwd": str(forge_project)})
    assert state_lib.load(forge_project)["stop_block_count"] == 3

    time.sleep(1.1)
    evidence_lib.add_entry(
        forge_project, artifact="cad/enclosure.py", domain="mech", claim="now verified",
        check_ids=["geometry.min_wall"], result="pass", level="L1", evidence_files=[], status="VERIFIED",
    )
    run_hook("stop.py", {"cwd": str(forge_project)})
    assert state_lib.load(forge_project)["stop_block_count"] == 0


def test_seventh_block_records_unverified_and_lets_stop_proceed(forge_project):
    """The 7th consecutive block (before the platform's 8-block cap) must
    stop blocking, write an UNVERIFIED evidence entry, and explain why."""
    _dirty(forge_project, "cad/enclosure.py")

    results = []
    for i in range(7):
        r = run_hook("stop.py", {"cwd": str(forge_project), "stop_hook_active": i > 0})
        results.append(r)

    for r in results[:6]:
        assert r.returncode == 2, "attempts 1-6 must keep blocking"
    seventh = results[6]
    assert seventh.returncode == 0, "the 7th attempt must let Stop proceed"
    assert "systemMessage" in seventh.output
    assert "UNVERIFIED" in seventh.output["systemMessage"] or "7-block" in seventh.output["systemMessage"]

    manifest = evidence_lib.load(forge_project)
    unverified = [e for e in manifest["entries"] if e["status"] == "UNVERIFIED" and e["domain"] == "mech"]
    assert unverified, "an UNVERIFIED evidence entry must be recorded at the handoff"

    assert state_lib.load(forge_project)["stop_block_count"] == 0

    # And the gate is still not fooled into thinking this counts as passing:
    eighth = run_hook("stop.py", {"cwd": str(forge_project), "stop_hook_active": True})
    assert eighth.returncode == 2


def test_stop_runs_reasonably_fast(forge_project):
    _dirty(forge_project, "cad/enclosure.py")
    start = time.monotonic()
    run_hook("stop.py", {"cwd": str(forge_project)})
    elapsed = time.monotonic() - start
    assert elapsed < 10.0
