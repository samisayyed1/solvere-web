"""forge passk against aggregate-result.json shaped like real `claude plugin eval` output.

The run objects below copy the field set of a real 2.1.282 result
(score, passed, turns, costUsd, error, tracePath, skippedPaidGraders,
graders[{name, passed, weight, explanation, withOnly, scored}]). Every test
is a seeded-wrong check: the expected numbers differ from what a passk that
ignored scored:false, counted skipped-paid-grader runs, dropped timeouts or
accepted partial documents would print.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from forge.commands import passk

BIN = Path(__file__).resolve().parents[2] / "bin" / "forge"


def g(name, ok, scored=True, with_only=False):
    return {"name": name, "passed": ok, "weight": 1, "explanation": "", "withOnly": with_only, "scored": scored}


def run(graders, *, error=None, skipped=False, score=None, passed=None):
    s = score if score is not None else sum(x["passed"] for x in graders if x["scored"]) / max(
        1, sum(1 for x in graders if x["scored"]))
    return {"score": s, "passed": passed if passed is not None else s >= 1.0, "turns": 7, "costUsd": 0.4,
            "judgeCostUsd": 0.0, "durationSeconds": 60, "error": error, "tracePath": "/tmp/x/out/trace.jsonl",
            "skippedPaidGraders": skipped, "graders": graders}


def ok_with():      # outcome passed, skill indicator fired
    return run([g("outcome", True), g("skill-fired", True, scored=False, with_only=True)])


def ok_with_no_skill():   # outcome passed, skill indicator NOT fired (unscored: still a success)
    return run([g("outcome", True), g("skill-fired", False, scored=False, with_only=True)])


def fail_run():
    return run([g("outcome", False), g("skill-fired", True, scored=False, with_only=True)])


def doc(cases, partial=False):
    return {"schemaVersion": 1, "claudeVersion": "2.1.282", "partial": partial,
            "partialReason": "cost_ceiling" if partial else None, "costUsd": 3.2,
            "suite": {"ablation": "with-without"}, "cases": cases,
            "aggregates": {"casesTotal": len(cases), "casesPassed": 0, "overallScore": 0.5, "meanDelta": 0.1}}


def case(name, with_runs, without_runs):
    return {"name": name, "dir": f"evals/{name}", "aggregates": {"score": 0.5, "delta": 0.3},
            "arms": {"with": with_runs, "without": without_runs}}


def test_per_arm_pass_at_k_and_pass_pow_k():
    d = doc([case("c1", [ok_with(), ok_with_no_skill(), fail_run()], [fail_run(), fail_run(), ok_with_no_skill()])])
    rep = passk.compute_many([d], [1, 3])
    row = rep["cases"][0]
    w, wo = row["arms"]["with"], row["arms"]["without"]
    # with: 2/3 succeed. The failed with-only skill indicator must NOT fail run 2.
    assert (w["n"], w["c"]) == (3, 2)
    assert w["pass_at"]["1"] == pytest.approx(2 / 3)
    assert w["pass_at"]["3"] == pytest.approx(1.0)
    assert w["pass_pow"]["3"] == pytest.approx(0.0)
    assert (wo["n"], wo["c"]) == (3, 1)
    assert wo["pass_at"]["1"] == pytest.approx(1 / 3)
    assert row["delta"] == pytest.approx(1 / 3)
    assert rep["summary"]["with"]["mean_pass_pow_3"] == pytest.approx(0.0)
    assert rep["summary"]["without"]["mean_pass_at_1"] == pytest.approx(1 / 3)


def test_skipped_paid_graders_and_infra_errors_dropped_timeouts_kept():
    with_runs = [ok_with(), ok_with(), ok_with(),
                 run([g("outcome", False)], skipped=True),                      # dropped
                 run([g("outcome", False)], error="Claude usage limit reached"),  # dropped
                 run([g("outcome", False)], error="timed out after 900s")]      # counted, failure
    rep = passk.compute_many([doc([case("c", with_runs, [fail_run()] * 3)])], [3])
    w = rep["cases"][0]["arms"]["with"]
    assert (w["runs"], w["n"], w["c"]) == (6, 4, 3)
    assert w["dropped"] == {"skipped_paid_graders": 1, "infrastructure_error": 1}
    assert w["pass_pow"]["3"] == pytest.approx(1 / 4)   # C(3,3)/C(4,3); 1.0 if the timeout were dropped
    assert rep["summary"]["with"]["runs_dropped"] == 2


def test_partial_document_refused_unless_allowed():
    d = doc([case("c", [ok_with()] * 3, [fail_run()] * 3)], partial=True)
    with pytest.raises(passk.PassKError, match="partial"):
        passk.compute_many([d], [1])
    rep = passk.compute_many([d], [1], allow_partial=True)
    assert rep["summary"]["partial"] is True
    assert rep["cases"][0]["arms"]["with"]["pass_at"]["1"] == pytest.approx(1.0)


def test_pooling_two_result_files():
    a = doc([case("c", [ok_with(), fail_run()], [fail_run()])])
    b = doc([case("c", [ok_with()], [fail_run(), ok_with_no_skill()])])
    rep = passk.compute_many([a, b], [3])
    w, wo = rep["cases"][0]["arms"]["with"], rep["cases"][0]["arms"]["without"]
    assert (w["n"], w["c"], wo["n"], wo["c"]) == (3, 2, 3, 1)


def test_insufficient_runs_per_arm_and_k():
    rep = passk.compute_many([doc([case("c", [ok_with()] * 3, [fail_run()] * 2)])], [1, 3])
    wo = rep["cases"][0]["arms"]["without"]
    assert wo["insufficient"] == [3] and "3" not in wo["pass_at"]
    assert rep["summary"]["without"]["cases_scored_k3"] == 0


def test_success_rule_passed_uses_harness_flag():
    # harness 'passed' follows --threshold (0.5 here): a half-scored run is a success
    # under --success passed but not under the default grader rule.
    r = run([g("a", True), g("b", False)], passed=True)
    d = doc([case("c", [r, r, r], [])])
    assert passk.compute_many([d], [1])["cases"][0]["arms"]["with"]["c"] == 0
    assert passk.compute_many([d], [1], success="passed")["cases"][0]["arms"]["with"]["c"] == 3


def test_cli_end_to_end(tmp_path):
    p1 = tmp_path / "a.json"
    p1.write_text(json.dumps(doc([case("c", [ok_with(), ok_with(), fail_run()], [fail_run()] * 3)])))
    out = tmp_path / "rep.json"
    r = subprocess.run([sys.executable, str(BIN), "passk", str(p1), "--k", "1,3", "--out", str(out)],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert "pass@3" in r.stdout and "without" in r.stdout
    rep = json.loads(out.read_text())
    assert rep["cases"][0]["arms"]["with"]["pass_pow"]["3"] == pytest.approx(0.0)
    p2 = tmp_path / "p.json"
    p2.write_text(json.dumps(doc([case("c", [ok_with()], [])], partial=True)))
    r = subprocess.run([sys.executable, str(BIN), "passk", str(p2), "--k", "1"], capture_output=True, text=True)
    assert r.returncode == 2 and "partial" in r.stderr
