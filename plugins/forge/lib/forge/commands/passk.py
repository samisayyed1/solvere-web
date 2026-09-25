"""``forge passk``: pass@k and pass^k from a ``claude plugin eval`` ``aggregate-result.json``.

    forge passk <aggregate-result.json> --k N [--json]

``claude plugin eval`` reports only a mean score, a mean Delta and a
"Perfect runs" share; it computes **no** pass@k or pass^k (ADR-001 D14, §10,
§15 point 7; CONTRACTS.md §11). This module computes both, per case and in
aggregate, from the per-run results nested under ``cases[].arms.with`` (and
``cases[].arms.without`` for baseline comparison), using the standard
unbiased estimators:

    pass@k = 1 - C(n-c, k) / C(n, k)     (>=1 of k sampled attempts succeeds)
    pass^k =     C(c, k)   / C(n, k)     (all k of k sampled attempts succeed)

where *n* is the number of runs actually counted for a case's arm and *c* is
how many of those succeeded.

**Dropped runs (CONTRACTS.md §11, ADR-001 §10 D14):** a run is *not* counted
toward *n* when it is ``aborted``, ``partial``, carries an ``error``, or has
``skippedPaidGraders`` set -- these fields are the ones the runner's JSON
schema documents (R1c §4.7). Cases with fewer than *k* counted runs cannot
support pass@k/pass^k at that *k* and are reported as ``insufficient_runs``
rather than silently dropped from the report.

**Per-run success (schema gap, R1c §4.7: "partially documented [U]"):** the
runner's JSON does not fully document a per-run pass/fail field. This module
uses, in order: an explicit ``passed`` boolean; else ``score >= 1.0``; else
``graders`` (a list of ``{passed: bool}``) all passing. A run matching none
of these is a schema mismatch and raises :class:`PassKError`, so a result
file this module cannot interpret is never silently scored as a fail.

Standard library only.
"""

from __future__ import annotations

import argparse
import json
import sys
from math import comb
from pathlib import Path
from typing import Any

NAME = "passk"
HELP = "compute pass@k and pass^k from an aggregate-result.json (CONTRACTS.md §11)"


class PassKError(ValueError):
    """The result file, or one run inside it, doesn't match a schema this tool understands."""


def register(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("result_path", type=Path, help="path to aggregate-result.json")
    parser.add_argument("--k", type=int, required=True, help="k for pass@k / pass^k (1 <= k <= runs per case)")
    parser.add_argument("--baseline", default="without", choices=["without"],
                        help="which arm is the no-plugin baseline (reserved; currently always 'without')")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON instead of a table")


def pass_at_k(n: int, c: int, k: int) -> float:
    """Unbiased estimator: probability at least one of k sampled attempts (of n) succeeds."""
    if n < 0 or c < 0 or c > n:
        raise PassKError(f"invalid n={n}, c={c}")
    if k <= 0:
        raise PassKError(f"k must be >= 1, got {k}")
    if k > n:
        raise PassKError(f"k={k} exceeds n={n} counted runs")
    if n - c < k:
        return 1.0
    return 1.0 - comb(n - c, k) / comb(n, k)


def pass_pow_k(n: int, c: int, k: int) -> float:
    """Probability all k of k sampled attempts (of n) succeed."""
    if n < 0 or c < 0 or c > n:
        raise PassKError(f"invalid n={n}, c={c}")
    if k <= 0:
        raise PassKError(f"k must be >= 1, got {k}")
    if k > n:
        raise PassKError(f"k={k} exceeds n={n} counted runs")
    return comb(c, k) / comb(n, k)


def _is_counted(run: dict[str, Any]) -> bool:
    return not (run.get("error") or run.get("aborted") or run.get("partial") or run.get("skippedPaidGraders"))


def _run_succeeded(run: dict[str, Any]) -> bool:
    if "passed" in run:
        return bool(run["passed"])
    if "score" in run and run["score"] is not None:
        return float(run["score"]) >= 1.0
    graders = run.get("graders")
    if isinstance(graders, list) and graders:
        return all(bool(g.get("passed")) for g in graders)
    raise PassKError(
        "run has none of 'passed', 'score' or a non-empty 'graders' list; "
        "aggregate-result.json schema not recognized (R1c §4.7 marks this partially documented)"
    )


def _arm_counts(arm_runs: list[dict[str, Any]]) -> tuple[int, int]:
    counted = [r for r in arm_runs if _is_counted(r)]
    c = sum(1 for r in counted if _run_succeeded(r))
    return len(counted), c


def compute_case(case: dict[str, Any], k: int) -> dict[str, Any]:
    name = case.get("name", "?")
    arms = case.get("arms", {})
    with_runs = arms.get("with", [])
    without_runs = arms.get("without", [])

    n_with, c_with = _arm_counts(with_runs)
    row: dict[str, Any] = {"name": name, "n": n_with, "c": c_with, "k": k}

    if n_with < k:
        row["status"] = "insufficient_runs"
        row["reason"] = f"only {n_with} counted run(s), need >= k={k}"
        return row

    row["status"] = "ok"
    row["pass_at_k"] = pass_at_k(n_with, c_with, k)
    row["pass_pow_k"] = pass_pow_k(n_with, c_with, k)
    row["with_rate"] = c_with / n_with if n_with else None

    if without_runs:
        n_without, c_without = _arm_counts(without_runs)
        row["n_baseline"] = n_without
        row["c_baseline"] = c_without
        if n_without:
            row["without_rate"] = c_without / n_without
            row["delta"] = row["with_rate"] - row["without_rate"]
        else:
            row["without_rate"] = None
            row["delta"] = None
    else:
        row["delta"] = case.get("aggregates", {}).get("delta")
        row["delta_source"] = "reported" if row["delta"] is not None else None

    return row


def compute(result: dict[str, Any], k: int) -> dict[str, Any]:
    cases = result.get("cases", [])
    if not cases:
        raise PassKError("aggregate-result.json has no 'cases'")
    rows = [compute_case(case, k) for case in cases]
    ok_rows = [r for r in rows if r["status"] == "ok"]
    summary = {
        "k": k,
        "cases_total": len(rows),
        "cases_scored": len(ok_rows),
        "cases_insufficient": len(rows) - len(ok_rows),
        "mean_pass_at_k": (sum(r["pass_at_k"] for r in ok_rows) / len(ok_rows)) if ok_rows else None,
        "mean_pass_pow_k": (sum(r["pass_pow_k"] for r in ok_rows) / len(ok_rows)) if ok_rows else None,
        "mean_delta": (
            sum(r["delta"] for r in ok_rows if r.get("delta") is not None)
            / max(1, sum(1 for r in ok_rows if r.get("delta") is not None))
        ) if any(r.get("delta") is not None for r in ok_rows) else None,
        "partial": result.get("partial", False),
        "partial_reason": result.get("partialReason"),
    }
    return {"summary": summary, "cases": rows}


def _fmt(x: float | None) -> str:
    return "-" if x is None else f"{x:.3f}"


def _print_table(report: dict[str, Any]) -> None:
    s = report["summary"]
    if s["partial"]:
        print(f"WARNING: aggregate-result.json is a partial run ({s['partial_reason']}); "
              "scored cases still computed, but coverage may be incomplete.", file=sys.stderr)
    print(f"{'case':<32} {'n':>4} {'c':>4} {'pass@' + str(s['k']):>10} {'pass^' + str(s['k']):>10} {'delta':>8}")
    for row in report["cases"]:
        if row["status"] != "ok":
            print(f"{row['name']:<32} {'-':>4} {'-':>4} {'insufficient (' + row['reason'] + ')':>10}")
            continue
        print(f"{row['name']:<32} {row['n']:>4} {row['c']:>4} "
              f"{_fmt(row['pass_at_k']):>10} {_fmt(row['pass_pow_k']):>10} {_fmt(row.get('delta')):>8}")
    print("-" * 72)
    print(f"{s['cases_scored']}/{s['cases_total']} cases scored (k={s['k']}); "
          f"mean pass@k={_fmt(s['mean_pass_at_k'])} mean pass^k={_fmt(s['mean_pass_pow_k'])} "
          f"mean delta={_fmt(s['mean_delta'])}")


def run(ns: argparse.Namespace, forge_root: Path) -> int:
    path = Path(ns.result_path)
    if not path.exists():
        print(f"forge passk: {path} not found", file=sys.stderr)
        return 2
    try:
        result = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        print(f"forge passk: {path} is not valid JSON: {exc}", file=sys.stderr)
        return 2
    try:
        report = compute(result, ns.k)
    except PassKError as exc:
        print(f"forge passk: {exc}", file=sys.stderr)
        return 2

    if ns.json:
        print(json.dumps(report, indent=2))
    else:
        _print_table(report)
    return 0
