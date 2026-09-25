#!/usr/bin/env python3
"""Weighted Pugh matrix check with a weight-sensitivity pass, over
concepts/pugh.json (CONTRACTS-style check, not a registered §9 entrypoint --
exploring-concepts has no CONTRACTS §9 row, but uses the same check-result
contract for consistency and CI).

Invocation:
    forge-python skills/exploring-concepts/scripts/verify.py --project <root> [--changed <path> ...] [--fast]

Checks (check_id ``concepts.pugh_sensitivity``):
  - at least ``minimum_concepts`` non-datum concepts are present (default 3,
    per the brief: "a dynamic workflow generates at least N concepts");
  - every concept's ``scores`` covers every criterion;
  - the top-N ranking (default top 2, per the brief's "tournament produces
    the top 2") is stable under a +/-25% perturbation of each criterion's
    weight in turn (``pugh.sensitivity_check``). An unstable ranking is not
    itself wrong -- close calls happen -- but it FAILS here unless
    ``sensitivity_reviewed_by`` is filled in, the same accepted-risk pattern
    used by ``analyzing-risk`` and ``costing-bom``: a flag needs an owner,
    not silence.

This skill never auto-selects a winner -- the report is for a human to read
and choose from (brief §3.3: "ASK the owner to choose").

Standard library only.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lib"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from forge.checkresult import Check, CheckContractError  # noqa: E402
from pugh import normalize_weights, rank, sensitivity_check  # noqa: E402

PUGH_REL = Path("concepts/pugh.json")
CHECK_ID = "concepts.pugh_sensitivity"
DEFAULT_MIN_CONCEPTS = 3
DEFAULT_TOP_N = 2


def run(project: Path, changed: list[str] | None) -> int:
    pugh_path = project / PUGH_REL
    if not pugh_path.exists():
        print(f"[SKIP] no {PUGH_REL} in this project")
        return 0
    if changed and not any(Path(c).resolve() == pugh_path.resolve() for c in changed):
        print(f"[SKIP] {PUGH_REL} not in --changed set")
        return 0

    data = json.loads(pugh_path.read_text())
    chk = Check(CHECK_ID, str(PUGH_REL), level="L1", project=project)

    if data.get("schema") != "forge.pugh/1":
        return chk.error(f"{PUGH_REL} schema is {data.get('schema')!r}, expected 'forge.pugh/1'")

    criteria = data.get("criteria", [])
    concepts = data.get("concepts", [])
    top_n = int(data.get("top_n", DEFAULT_TOP_N))
    min_concepts = int(data.get("minimum_concepts", DEFAULT_MIN_CONCEPTS))
    reviewed_by = (data.get("sensitivity_reviewed_by") or "").strip()

    if not criteria:
        return chk.error(f"{PUGH_REL} has no criteria[]")
    if not concepts:
        return chk.error(f"{PUGH_REL} has no concepts[]")

    candidate_concepts = [c for c in concepts if not c.get("datum")]
    enough = len(candidate_concepts) >= min_concepts
    chk.measure(
        "concepts.count", len(candidate_concepts), "1", min=min_concepts,
        remediation=(
            f"Only {len(candidate_concepts)} non-datum concept(s), need at least "
            f"{min_concepts}. Generate more concepts (concept-tournament workflow) "
            "before scoring the matrix."
        ) if not enough else None,
    )

    criterion_names = {c["name"] for c in criteria}
    for c in concepts:
        name = c.get("name", "<unnamed>")
        scored = set(c.get("scores", {}).keys())
        complete = criterion_names.issubset(scored)
        chk.measure(
            f"{name}.scores_complete", complete, "1", equals=True, location=str(PUGH_REL),
            remediation=(
                f"Concept {name!r} is missing scores for {sorted(criterion_names - scored)}. "
                "Every concept needs a score against every criterion."
            ) if not complete else None,
        )

    if not enough:
        return chk.finish()

    try:
        normalize_weights(criteria)
    except ValueError as exc:
        return chk.error(str(exc))

    report = sensitivity_check(criteria, concepts, top_n=top_n)
    stable = report["stable"] or bool(reviewed_by)
    chk.measure(
        "ranking.sensitivity_acknowledged", stable, "1", equals=True, location=str(PUGH_REL),
        remediation=(
            f"The top-{top_n} ranking {report['base_top']} flips under a "
            f"+/-{int(report['perturbation'] * 100)}% weight change on "
            f"{sorted({f['criterion'] for f in report['flips']})}. This is a close call the "
            "matrix can't resolve alone -- set 'sensitivity_reviewed_by' after a human looks "
            "at the flips in out/verify/concepts.pugh_report.json, or gather more "
            "discriminating criteria."
        ) if not stable else None,
    )

    ranked = rank(concepts, normalize_weights(criteria), exclude_datum=True)
    out_dir = project / "out" / "verify"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "concepts.pugh_report.json").write_text(json.dumps({
        "schema": "forge.pugh_report/1",
        "ranking": [{"name": r.name, "total": r.total} for r in ranked],
        "top_n": top_n,
        "sensitivity": report,
    }, indent=2, ensure_ascii=False) + "\n")

    top_names = [r.name for r in ranked[:top_n]]
    return chk.finish(notes=f"top-{top_n}: {top_names}; stable={report['stable']}")


def main(argv: list[str]) -> int:
    project = Path(".")
    changed: list[str] = []
    i = 0
    while i < len(argv):
        if argv[i] == "--project":
            project = Path(argv[i + 1]); i += 2
        elif argv[i] == "--changed":
            changed.append(argv[i + 1]); i += 2
        elif argv[i] == "--fast":
            i += 1
        else:
            i += 1
    try:
        return run(project.resolve(), changed or None)
    except CheckContractError as exc:
        print(f"[ERROR] {CHECK_ID}: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001 -- fail closed
        print(f"[ERROR] {CHECK_ID}: internal error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
