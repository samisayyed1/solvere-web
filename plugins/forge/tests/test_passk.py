"""forge passk: pass@k / pass^k from aggregate-result.json (CONTRACTS.md §11)."""
from __future__ import annotations

import json

import pytest

from forge.commands import passk


def test_known_answer_pass_at_k_and_pass_pow_k():
    # n=5, c=3, k=2: pass@2 = 1 - C(2,2)/C(5,2) = 1 - 1/10 = 0.9
    #                pass^2 =     C(3,2)/C(5,2) =     3/10 = 0.3
    assert passk.pass_at_k(5, 3, 2) == pytest.approx(0.9)
    assert passk.pass_pow_k(5, 3, 2) == pytest.approx(0.3)


def test_known_answer_edge_cases():
    assert passk.pass_at_k(3, 3, 3) == pytest.approx(1.0)   # every run succeeded
    assert passk.pass_pow_k(3, 3, 3) == pytest.approx(1.0)
    assert passk.pass_at_k(3, 0, 2) == pytest.approx(0.0)   # every run failed
    assert passk.pass_pow_k(3, 0, 2) == pytest.approx(0.0)


def test_k_greater_than_n_rejected():
    with pytest.raises(passk.PassKError):
        passk.pass_at_k(2, 1, 3)
    with pytest.raises(passk.PassKError):
        passk.pass_pow_k(2, 1, 3)


def _agg(cases):
    return {"schemaVersion": 1, "partial": False, "cases": cases}


def test_compute_end_to_end_matches_known_answer():
    result = _agg([{
        "name": "known-answer",
        "arms": {
            "with": [{"passed": True}] * 3 + [{"passed": False}] * 2,
            "without": [{"passed": False}] * 5,
        },
    }])
    report = passk.compute(result, 2)
    row = report["cases"][0]
    assert row["status"] == "ok"
    assert (row["n"], row["c"]) == (5, 3)
    assert row["pass_at_k"] == pytest.approx(0.9)
    assert row["pass_pow_k"] == pytest.approx(0.3)
    assert row["with_rate"] == pytest.approx(0.6)
    assert row["without_rate"] == pytest.approx(0.0)
    assert row["delta"] == pytest.approx(0.6)
    assert report["summary"]["cases_scored"] == 1


def test_dropped_runs_error_aborted_partial_skipped_paid_graders():
    result = _agg([{
        "name": "drops",
        "arms": {"with": [
            {"passed": True},
            {"passed": True},
            {"passed": False, "error": "timeout"},
            {"passed": True, "aborted": True},
            {"passed": False, "partial": True},
            {"passed": False, "skippedPaidGraders": True},
        ]},
    }])
    report = passk.compute(result, 2)
    row = report["cases"][0]
    # only the first two runs are counted
    assert (row["n"], row["c"]) == (2, 2)
    assert row["pass_at_k"] == pytest.approx(1.0)


def test_insufficient_runs_reported_not_silently_dropped():
    result = _agg([{"name": "too-few", "arms": {"with": [{"passed": True}]}}])
    report = passk.compute(result, 3)
    row = report["cases"][0]
    assert row["status"] == "insufficient_runs"
    assert "reason" in row
    assert report["summary"]["cases_insufficient"] == 1
    assert report["summary"]["cases_scored"] == 0


def test_score_field_used_when_no_passed_field():
    result = _agg([{"name": "scores", "arms": {"with": [{"score": 1.0}, {"score": 0.5}, {"score": 1.0}]}}])
    report = passk.compute(result, 2)
    row = report["cases"][0]
    assert (row["n"], row["c"]) == (3, 2)  # only the two score==1.0 runs count as success


def test_graders_list_used_when_no_passed_or_score():
    result = _agg([{"name": "graders", "arms": {"with": [
        {"graders": [{"passed": True}, {"passed": True}]},
        {"graders": [{"passed": True}, {"passed": False}]},
        {"graders": [{"passed": True}]},
    ]}}])
    report = passk.compute(result, 2)
    row = report["cases"][0]
    assert (row["n"], row["c"]) == (3, 2)


def test_unrecognized_run_schema_raises_not_silently_scored_as_fail():
    result = _agg([{"name": "mystery", "arms": {"with": [{"someOtherField": 1}, {"passed": True}]}}])
    with pytest.raises(passk.PassKError):
        passk.compute(result, 2)


def test_reported_delta_used_when_no_baseline_arm_present():
    result = _agg([{
        "name": "no-baseline",
        "arms": {"with": [{"passed": True}] * 3},
        "aggregates": {"delta": 0.42},
    }])
    report = passk.compute(result, 2)
    row = report["cases"][0]
    assert row["delta"] == pytest.approx(0.42)
    assert row.get("delta_source") == "reported"


def test_cli_run_missing_file_exits_2(tmp_path):
    class NS:
        result_path = tmp_path / "nope.json"
        k = 2
        json = False
    assert passk.run(NS(), tmp_path) == 2


def test_cli_run_bad_json_exits_2(tmp_path):
    bad = tmp_path / "agg.json"
    bad.write_text("{not json")

    class NS:
        result_path = bad
        k = 2
        json = False
    assert passk.run(NS(), tmp_path) == 2


def test_cli_run_writes_json_report(tmp_path, capsys):
    path = tmp_path / "agg.json"
    path.write_text(json.dumps(_agg([{
        "name": "known-answer",
        "arms": {"with": [{"passed": True}] * 3 + [{"passed": False}] * 2},
    }])))

    class NS:
        result_path = path
        k = 2
        json = True
    assert passk.run(NS(), tmp_path) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["cases"][0]["pass_at_k"] == pytest.approx(0.9)
