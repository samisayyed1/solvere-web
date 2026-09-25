#!/usr/bin/env python3
"""Seeded-defect review scorer: recall and precision against committed answer keys.

    seeded_score.py --results <results/<ts>/> [--evals <plugins/forge/evals>] [--min-recall 0.8] [--json]
    seeded_score.py --key <answer_key.json> --findings <findings.json>      # score one file

Why a script: ``claude plugin eval`` graders cannot count false positives, so
precision is computed here, deterministically, from each run's
``out/review/findings.json`` and the case's ``key/answer_key.json`` (which
lives under evals/, a directory the agent under test cannot read).

Where the findings come from (``--results`` mode). ``run.sh`` runs the suite
with ``--keep-temp``; ``aggregate-result.json`` gives every run a
``tracePath`` of ``<tmp>/out/trace.jsonl``, and the run's workspace is
``<tmp>/home/cwd``. For each ``review-seeded-*`` run this script reads
``<workspace>/<findings_path>``; if the file is missing it falls back to the
content of the last Write tool call to that path in ``trace.jsonl``. The
findings it used are archived under ``<results>/findings/<case>/<arm>-<n>.json``
so the numbers can be recomputed after the temp dirs are deleted (re-running
this script prefers the archive).

Matching (deterministic). A finding is one flat object; its *text* is all its
string values joined by spaces. It matches a key entry when ``entry.file``
matches ``finding.file`` and both ``entry.locator`` and ``entry.keywords``
match the text (all regexes case-insensitive). Planted defects are assigned to
findings by maximum bipartite matching (augmenting paths, findings and
defects in file order), so one finding can satisfy at most one defect and one
defect is counted once. Remaining findings that match an ``acceptable`` entry
(a real defect we did not plant) count as correct. Any other finding that
matches a planted defect already taken is a *duplicate* (reported, excluded
from precision). Everything else is a false positive; if it matches a
``decoys`` entry (a deliberately correct item) that is noted.

    recall    = matched planted defects / planted defects
    precision = (matched + acceptable) / (matched + acceptable + false positives)

A run with no parseable findings file scores recall 0 and precision undefined
(reported as null and counted in ``runs_missing``). Standard library only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SEEDED_PREFIX = "review-seeded-"


# ---------------------------------------------------------------- matching

def _rx(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern, re.IGNORECASE)


def finding_text(finding: dict[str, Any]) -> str:
    return " ".join(str(v) for v in finding.values() if isinstance(v, (str, int, float)))


def entry_matches(entry: dict[str, Any], finding: dict[str, Any]) -> bool:
    file_value = str(finding.get("file", ""))
    text = finding_text(finding)
    return bool(_rx(entry["file"]).search(file_value)
                and _rx(entry["locator"]).search(text)
                and _rx(entry["keywords"]).search(text))


def _max_matching(findings: list[dict[str, Any]], defects: list[dict[str, Any]]) -> dict[int, int]:
    """finding index -> defect index, maximum cardinality, deterministic order."""
    edges = [[j for j, d in enumerate(defects) if entry_matches(d, f)] for f in findings]
    defect_owner: dict[int, int] = {}

    def augment(i: int, seen: set[int]) -> bool:
        for j in edges[i]:
            if j in seen:
                continue
            seen.add(j)
            if j not in defect_owner or augment(defect_owner[j], seen):
                defect_owner[j] = i
                return True
        return False

    for i in range(len(findings)):
        augment(i, set())
    return {i: j for j, i in defect_owner.items()}


def score_findings(key: dict[str, Any], findings: list[dict[str, Any]]) -> dict[str, Any]:
    defects = key["defects"]
    acceptable = key.get("acceptable", [])
    decoys = key.get("decoys", [])
    assignment = _max_matching(findings, defects)
    rows = []
    tp = acc = dup = fp = 0
    for i, f in enumerate(findings):
        if i in assignment:
            rows.append({"finding": i, "verdict": "tp", "entry": defects[assignment[i]]["id"]})
            tp += 1
            continue
        a = next((e for e in acceptable if entry_matches(e, f)), None)
        if a is not None:
            rows.append({"finding": i, "verdict": "acceptable", "entry": a["id"]})
            acc += 1
            continue
        d = next((e for e in defects if entry_matches(e, f)), None)
        if d is not None:
            rows.append({"finding": i, "verdict": "duplicate", "entry": d["id"]})
            dup += 1
            continue
        decoy = next((e for e in decoys if entry_matches(e, f)), None)
        rows.append({"finding": i, "verdict": "fp", "entry": decoy["id"] if decoy else None})
        fp += 1
    found = sorted(defects[j]["id"] for j in assignment.values())
    missed = [d["id"] for d in defects if d["id"] not in found]
    counted = tp + acc + fp
    return {
        "planted": len(defects),
        "findings": len(findings),
        "tp": tp, "acceptable": acc, "duplicates": dup, "fp": fp,
        "decoy_hits": [r["entry"] for r in rows if r["verdict"] == "fp" and r["entry"]],
        "recall": tp / len(defects) if defects else None,
        "precision": (tp + acc) / counted if counted else None,
        "found": found, "missed": missed, "rows": rows,
    }


# ---------------------------------------------------------------- loading

def parse_findings(text: str) -> list[dict[str, Any]] | None:
    try:
        doc = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None
    items = doc.get("findings") if isinstance(doc, dict) else doc
    if not isinstance(items, list):
        return None
    return [f for f in items if isinstance(f, dict)]


def findings_from_trace(trace_path: Path, rel: str) -> str | None:
    """Content of the last Write to <rel> in a trace.jsonl (fallback when the workspace is gone)."""
    if not trace_path.is_file():
        return None
    last = None
    for line in trace_path.read_text(errors="replace").splitlines():
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        content = (msg.get("message") or {}).get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if (isinstance(block, dict) and block.get("type") == "tool_use" and block.get("name") == "Write"
                    and str((block.get("input") or {}).get("file_path", "")).endswith(rel)):
                last = (block.get("input") or {}).get("content")
    return last


def workspace_of(run: dict[str, Any]) -> Path | None:
    tp = run.get("tracePath")
    if not tp:
        return None
    return Path(tp).parent.parent / "home" / "cwd"


def load_run_findings(run: dict[str, Any], rel: str, archive: Path) -> tuple[str | None, str]:
    if archive.is_file():
        return archive.read_text(), "archive"
    ws = workspace_of(run)
    if ws is not None and (ws / rel).is_file():
        text = (ws / rel).read_text(errors="replace")
        source = "workspace"
    else:
        text = findings_from_trace(Path(run["tracePath"]), rel) if run.get("tracePath") else None
        source = "trace" if text is not None else "missing"
    if text is not None:
        archive.parent.mkdir(parents=True, exist_ok=True)
        archive.write_text(text)
    return text, source


def key_for_case(evals_dir: Path, case: dict[str, Any]) -> Path:
    # cases[].dir is relative to the plugin root, e.g. "evals/review/seeded-wearable"
    rel = Path(case.get("dir", ""))
    cand = evals_dir.parent / rel / "key" / "answer_key.json"
    if cand.is_file():
        return cand
    for k in evals_dir.glob("**/key/answer_key.json"):
        if json.loads(k.read_text()).get("case") == case["name"]:
            return k
    raise FileNotFoundError(f"no answer key for case {case['name']}")


def _mean(xs: list[float]) -> float | None:
    return sum(xs) / len(xs) if xs else None


def score_results(results_dir: Path, evals_dir: Path) -> dict[str, Any]:
    agg = json.loads((results_dir / "aggregate-result.json").read_text())
    out_cases = []
    for case in agg.get("cases", []):
        if not case.get("name", "").startswith(SEEDED_PREFIX):
            continue
        key = json.loads(key_for_case(evals_dir, case).read_text())
        rel = key["findings_path"]
        arms_out: dict[str, Any] = {}
        for arm, runs in (case.get("arms") or {}).items():
            per_run = []
            for n, run in enumerate(runs, 1):
                archive = results_dir / "findings" / case["name"] / f"{arm}-{n}.json"
                text, source = load_run_findings(run, rel, archive)
                findings = parse_findings(text) if text is not None else None
                if findings is None:
                    per_run.append({"run": n, "source": source, "missing": True, "recall": 0.0, "precision": None})
                    continue
                s = score_findings(key, findings)
                s.update({"run": n, "source": source, "missing": False})
                per_run.append(s)
            arms_out[arm] = {
                "runs": per_run,
                "runs_missing": sum(1 for r in per_run if r["missing"]),
                "mean_recall": _mean([r["recall"] for r in per_run if r["recall"] is not None]),
                "mean_precision": _mean([r["precision"] for r in per_run if r["precision"] is not None]),
            }
        out_cases.append({"name": case["name"], "planted": len(key["defects"]), "arms": arms_out})
    summary: dict[str, Any] = {}
    for arm in ("with", "without"):
        rec = [r["recall"] for c in out_cases for r in c["arms"].get(arm, {}).get("runs", []) if r["recall"] is not None]
        pre = [r["precision"] for c in out_cases for r in c["arms"].get(arm, {}).get("runs", []) if r["precision"] is not None]
        summary[arm] = {"mean_recall": _mean(rec), "mean_precision": _mean(pre), "runs": len(rec)}
    return {"summary": summary, "cases": out_cases}


def _fmt(x: float | None) -> str:
    return "-" if x is None else f"{x:.2f}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--results", type=Path, help="results/<timestamp>/ directory holding aggregate-result.json")
    ap.add_argument("--evals", type=Path, default=Path(__file__).resolve().parent.parent)
    ap.add_argument("--key", type=Path)
    ap.add_argument("--findings", type=Path)
    ap.add_argument("--min-recall", type=float, default=None, help="exit 1 if with-arm mean recall is below this")
    ap.add_argument("--json", action="store_true")
    ns = ap.parse_args(argv)

    if ns.key and ns.findings:
        findings = parse_findings(ns.findings.read_text())
        if findings is None:
            print("seeded_score: findings file is not the forge.findings/1 format", file=sys.stderr)
            return 2
        report = score_findings(json.loads(ns.key.read_text()), findings)
        print(json.dumps(report, indent=2) if ns.json else
              f"recall {_fmt(report['recall'])}  precision {_fmt(report['precision'])}  "
              f"found {report['found']} missed {report['missed']} fp {report['fp']}")
        return 0
    if not ns.results:
        ap.error("give --results, or --key and --findings")
    report = score_results(ns.results, ns.evals)
    (ns.results / "seeded-report.json").write_text(json.dumps(report, indent=2) + "\n")
    if ns.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"{'case':<32} {'arm':<8} {'recall':>7} {'precision':>9} {'missing':>7}")
        for c in report["cases"]:
            for arm, a in c["arms"].items():
                print(f"{c['name']:<32} {arm:<8} {_fmt(a['mean_recall']):>7} {_fmt(a['mean_precision']):>9} "
                      f"{a['runs_missing']:>7}")
        for arm, s in report["summary"].items():
            print(f"{'ALL':<32} {arm:<8} {_fmt(s['mean_recall']):>7} {_fmt(s['mean_precision']):>9}")
    rec = report["summary"]["with"]["mean_recall"]
    if ns.min_recall is not None and (rec is None or rec < ns.min_recall):
        print(f"seeded_score: with-arm mean recall {_fmt(rec)} < target {ns.min_recall}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
