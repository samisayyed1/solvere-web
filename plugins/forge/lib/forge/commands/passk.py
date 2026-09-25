"""``forge passk``: pass@k and pass^k per case and per arm from ``claude plugin eval`` results.

    forge passk <aggregate-result.json> [<more.json> ...] --k 1,3 [--json] [--out report.json]
                [--allow-partial] [--success graders|passed|score]

``claude plugin eval`` reports a mean score, a mean Delta and a "Perfect runs"
share; it computes **no** pass@k or pass^k (ADR-001 §10, CONTRACTS.md §11).
This command computes both, for every case and for each arm (``with`` = plugin
loaded, ``without`` = the no-plugin baseline), from the per-run results under
``cases[].arms.{with,without}[]``, using the unbiased estimators

    pass@k = 1 - C(n-c, k) / C(n, k)     (at least one of k sampled runs succeeds)
    pass^k =     C(c, k)   / C(n, k)     (all k of k sampled runs succeed)

where *n* is the number of runs **counted** for that case and arm and *c* the
number that succeeded. Several result files may be given; runs of the same
case and arm are pooled (e.g. two 3-run jobs give n = 6).

**What a success is** (``--success``, default ``graders``): every grader the
harness *scored* passed (``scored: false`` graders, such as the with-only
``tool_used: Skill`` indicator, are excluded, so the two arms are judged on the
same graders). ``passed`` uses the harness's own per-run ``passed`` flag (which
depends on ``--threshold``); ``score`` requires ``score >= 1``. A run with none
of the fields the chosen rule needs falls back in the order graders -> passed
-> score; a run with none of them raises :class:`PassKError`, so an
unrecognised result file is never silently scored as a fail.

**Which runs are dropped** (not counted in *n*; ADR-001 §10 "drop partial runs
and runs with skipped paid graders"; plugin-evals docs "leave partial: true
documents and runs with skippedPaidGraders out of any trend"):

* ``skippedPaidGraders: true`` -- the cost ceiling skipped its judge graders,
  so its score is not comparable;
* ``partial: true`` on the run;
* ``aborted`` -- a mock's ``expect`` stopped it (no agent outcome to judge);
* an ``error`` that is an *infrastructure* failure (rate or usage limit,
  overload, auth, network, the run could not start). An error the agent owns
  (timed out, hit max turns) is **not** dropped: the harness still graded what
  the run produced, and dropping it would inflate the pass rate.

A result document with top-level ``partial: true`` (cost ceiling hit,
interrupted, auth failure) is refused (exit 2) unless ``--allow-partial`` is
given, in which case only its completed runs count and the report is marked
partial. Cases with fewer than *k* counted runs are reported as
``insufficient_runs`` rather than silently dropped.

Standard library only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from math import comb
from pathlib import Path
from typing import Any

NAME = "passk"
HELP = "compute pass@k and pass^k per case and per arm from aggregate-result.json (CONTRACTS.md §11)"

ARMS = ("with", "without")
INFRA_ERROR_RE = re.compile(
    r"rate[ _-]?limit|usage[ _-]?limit|quota|overload|\b(429|5\d\d)\b|auth|credential|"
    r"could not (be )?start|failed to (launch|start|spawn)|ECONN|ETIMEDOUT|network|socket hang|"
    r"api error|internal server error|service unavailable",
    re.IGNORECASE,
)


class PassKError(ValueError):
    """The result file, or one run inside it, doesn't match a schema this tool understands."""


def register(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("result_path", type=Path, nargs="+", help="aggregate-result.json file(s); runs are pooled")
    parser.add_argument("--k", required=True, help="k, or a comma list such as 1,3 (1 <= k <= counted runs)")
    parser.add_argument("--success", choices=["graders", "passed", "score"], default="graders",
                        help="what counts as a successful run (default: every scored grader passed)")
    parser.add_argument("--allow-partial", action="store_true",
                        help="accept result documents marked partial: true (report is marked partial)")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON instead of a table")
    parser.add_argument("--out", type=Path, default=None, help="also write the JSON report to this path")


# ---------------------------------------------------------------- estimators

def _check(n: int, c: int, k: int) -> None:
    if n < 0 or c < 0 or c > n:
        raise PassKError(f"invalid n={n}, c={c}")
    if k <= 0:
        raise PassKError(f"k must be >= 1, got {k}")
    if k > n:
        raise PassKError(f"k={k} exceeds n={n} counted runs")


def pass_at_k(n: int, c: int, k: int) -> float:
    """Unbiased estimator: probability at least one of k sampled attempts (of n) succeeds."""
    _check(n, c, k)
    if n - c < k:
        return 1.0
    return 1.0 - comb(n - c, k) / comb(n, k)


def pass_pow_k(n: int, c: int, k: int) -> float:
    """Probability all k of k sampled attempts (of n) succeed."""
    _check(n, c, k)
    return comb(c, k) / comb(n, k)


# ---------------------------------------------------------------- runs

def drop_reason(run: dict[str, Any]) -> str | None:
    """Why a run is not counted, or None if it is counted."""
    if run.get("skippedPaidGraders"):
        return "skipped_paid_graders"
    if run.get("partial"):
        return "partial"
    if run.get("aborted"):
        return "aborted"
    err = run.get("error")
    if err and INFRA_ERROR_RE.search(str(err)):
        return "infrastructure_error"
    return None


def run_succeeded(run: dict[str, Any], success: str = "graders") -> bool:
    graders = run.get("graders")
    order = {"graders": ("graders", "passed", "score"),
             "passed": ("passed", "graders", "score"),
             "score": ("score", "graders", "passed")}[success]
    for rule in order:
        if rule == "graders" and isinstance(graders, list) and graders:
            scored = [g for g in graders if g.get("scored", True) is not False]
            if not scored:          # harness: all-excluded graders are scored normally
                scored = graders
            return all(bool(g.get("passed")) for g in scored)
        if rule == "passed" and isinstance(run.get("passed"), bool):
            return bool(run["passed"])
        if rule == "score" and run.get("score") is not None:
            return float(run["score"]) >= 1.0 - 1e-9
    raise PassKError(
        "run has none of a non-empty 'graders' list, 'passed' or 'score'; "
        "aggregate-result.json schema not recognised"
    )


def arm_stats(runs: list[dict[str, Any]], ks: list[int], success: str) -> dict[str, Any]:
    dropped: dict[str, int] = {}
    counted = []
    for r in runs:
        why = drop_reason(r)
        if why:
            dropped[why] = dropped.get(why, 0) + 1
        else:
            counted.append(r)
    n = len(counted)
    c = sum(1 for r in counted if run_succeeded(r, success))
    out: dict[str, Any] = {"runs": len(runs), "n": n, "c": c, "dropped": dropped,
                           "rate": (c / n) if n else None, "pass_at": {}, "pass_pow": {}, "insufficient": []}
    for k in ks:
        if n < k:
            out["insufficient"].append(k)
            continue
        out["pass_at"][str(k)] = pass_at_k(n, c, k)
        out["pass_pow"][str(k)] = pass_pow_k(n, c, k)
    return out


# ---------------------------------------------------------------- compute

def _pool(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_name: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for res in results:
        for case in res.get("cases", []):
            name = case.get("name", "?")
            if name not in by_name:
                by_name[name] = {"name": name, "arms": {a: [] for a in ARMS}, "aggregates": case.get("aggregates", {})}
                order.append(name)
            for arm in ARMS:
                by_name[name]["arms"][arm].extend((case.get("arms") or {}).get(arm) or [])
    return [by_name[n] for n in order]


def _mean(xs: list[float]) -> float | None:
    return sum(xs) / len(xs) if xs else None


def compute_many(results: list[dict[str, Any]], ks: list[int], *, success: str = "graders",
                 allow_partial: bool = False) -> dict[str, Any]:
    if not results:
        raise PassKError("no result documents")
    partial = [r.get("partialReason") or "partial" for r in results if r.get("partial")]
    if partial and not allow_partial:
        raise PassKError(f"result document is partial ({', '.join(map(str, partial))}); "
                         "rerun, or pass --allow-partial to count only its completed runs")
    cases = _pool(results)
    if not cases:
        raise PassKError("aggregate-result.json has no 'cases'")
    rows = []
    for case in cases:
        row: dict[str, Any] = {"name": case["name"], "arms": {}}
        for arm in ARMS:
            if case["arms"][arm]:
                row["arms"][arm] = arm_stats(case["arms"][arm], ks, success)
        w, wo = row["arms"].get("with"), row["arms"].get("without")
        if w and wo and w["rate"] is not None and wo["rate"] is not None:
            row["delta"] = w["rate"] - wo["rate"]
        else:
            row["delta"] = case.get("aggregates", {}).get("delta")
            row["delta_source"] = "reported" if row["delta"] is not None else None
        # flat with-arm fields for the first k (backward compatible with earlier callers)
        k0 = str(ks[0])
        if w:
            row.update({"n": w["n"], "c": w["c"], "k": ks[0], "with_rate": w["rate"]})
            if ks[0] in w["insufficient"]:
                row["status"] = "insufficient_runs"
                row["reason"] = f"only {w['n']} counted run(s), need >= k={ks[0]}"
            else:
                row["status"] = "ok"
                row["pass_at_k"] = w["pass_at"][k0]
                row["pass_pow_k"] = w["pass_pow"][k0]
        else:
            row.update({"n": 0, "c": 0, "k": ks[0], "status": "insufficient_runs", "reason": "no with-arm runs"})
        if wo:
            row.update({"n_baseline": wo["n"], "c_baseline": wo["c"], "without_rate": wo["rate"]})
        rows.append(row)

    summary: dict[str, Any] = {"k": ks, "cases_total": len(rows),
                               "partial": bool(partial), "partial_reason": partial or None, "success_rule": success}
    for arm in ARMS:
        per: dict[str, Any] = {"cases": sum(1 for r in rows if arm in r["arms"])}
        for k in ks:
            ok = [r["arms"][arm] for r in rows if arm in r["arms"] and k not in r["arms"][arm]["insufficient"]]
            per[f"cases_scored_k{k}"] = len(ok)
            per[f"mean_pass_at_{k}"] = _mean([a["pass_at"][str(k)] for a in ok])
            per[f"mean_pass_pow_{k}"] = _mean([a["pass_pow"][str(k)] for a in ok])
        per["runs_dropped"] = sum(sum(r["arms"][arm]["dropped"].values()) for r in rows if arm in r["arms"])
        summary[arm] = per
    deltas = [r["delta"] for r in rows if r.get("delta") is not None]
    summary["mean_delta"] = _mean(deltas)
    ok_rows = [r for r in rows if r["status"] == "ok"]
    summary.update({
        "cases_scored": len(ok_rows),
        "cases_insufficient": len(rows) - len(ok_rows),
        "mean_pass_at_k": _mean([r["pass_at_k"] for r in ok_rows]),
        "mean_pass_pow_k": _mean([r["pass_pow_k"] for r in ok_rows]),
    })
    return {"summary": summary, "cases": rows}


def compute(result: dict[str, Any], k: int, **kw: Any) -> dict[str, Any]:
    """Single document, single k (kept for callers of the first version)."""
    return compute_many([result], [k], **kw)


# ---------------------------------------------------------------- output

def _fmt(x: float | None) -> str:
    return "-" if x is None else f"{x:.3f}"


def _print_table(report: dict[str, Any]) -> None:
    s = report["summary"]
    ks = s["k"]
    if s["partial"]:
        print(f"WARNING: partial result ({s['partial_reason']}); only completed runs are counted.", file=sys.stderr)
    head = f"{'case':<36} {'arm':<8} {'n':>3} {'c':>3} {'drop':>4} " + " ".join(
        f"{'pass@' + str(k):>8} {'pass^' + str(k):>8}" for k in ks) + f" {'delta':>7}"
    print(head)
    for row in report["cases"]:
        for arm in ARMS:
            a = row["arms"].get(arm)
            if not a:
                continue
            cells = " ".join(
                f"{'n<k':>8} {'n<k':>8}" if k in a["insufficient"]
                else f"{_fmt(a['pass_at'][str(k)]):>8} {_fmt(a['pass_pow'][str(k)]):>8}" for k in ks)
            delta = _fmt(row.get("delta")) if arm == "with" else ""
            print(f"{row['name'][:36]:<36} {arm:<8} {a['n']:>3} {a['c']:>3} {sum(a['dropped'].values()):>4} "
                  f"{cells} {delta:>7}")
    print("-" * len(head))
    for arm in ARMS:
        per = s[arm]
        if not per["cases"]:
            continue
        parts = [f"pass@{k}={_fmt(per[f'mean_pass_at_{k}'])} pass^{k}={_fmt(per[f'mean_pass_pow_{k}'])}" for k in ks]
        print(f"{arm:<8} {per['cases']} cases, {per['runs_dropped']} runs dropped: " + "; ".join(parts))
    print(f"mean delta (with - without pass rate) = {_fmt(s['mean_delta'])}")


def _parse_ks(raw: Any) -> list[int]:
    if isinstance(raw, int):
        return [raw]
    try:
        ks = [int(x) for x in str(raw).split(",") if x.strip()]
    except ValueError as exc:
        raise PassKError(f"--k must be an integer or a comma list, got {raw!r}") from exc
    if not ks or any(k < 1 for k in ks):
        raise PassKError(f"--k values must be >= 1, got {raw!r}")
    return ks


def run(ns: argparse.Namespace, forge_root: Path) -> int:
    paths = ns.result_path if isinstance(ns.result_path, list) else [ns.result_path]
    docs = []
    for path in map(Path, paths):
        if not path.exists():
            print(f"forge passk: {path} not found", file=sys.stderr)
            return 2
        try:
            docs.append(json.loads(path.read_text()))
        except json.JSONDecodeError as exc:
            print(f"forge passk: {path} is not valid JSON: {exc}", file=sys.stderr)
            return 2
    try:
        report = compute_many(docs, _parse_ks(ns.k), success=getattr(ns, "success", "graders"),
                              allow_partial=getattr(ns, "allow_partial", False))
    except PassKError as exc:
        print(f"forge passk: {exc}", file=sys.stderr)
        return 2
    out = getattr(ns, "out", None)
    if out:
        Path(out).write_text(json.dumps(report, indent=2) + "\n")
    if ns.json:
        print(json.dumps(report, indent=2))
    else:
        _print_table(report)
    return 0
