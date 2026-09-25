#!/usr/bin/env python3
"""BOM roll-up and supply-chain risk flags over bom/bom.csv.

Invocation:
    forge-python skills/costing-bom/scripts/verify.py --project <root> [--changed <path> ...] [--fast]

Columns (see ``references/bom-format.md``):
    ref_des,description,mpn,manufacturer,qty_per_unit,lifecycle,
    lead_time_weeks,alternates,risk_note,price_<qty1>,price_<qty2>,...

For every line item it FAILS (check_id ``supply.bom_rollup``) when either
condition holds *and* ``risk_note`` is blank:
  - **single-source**: ``alternates`` is empty (no alternate MPN listed);
  - **lifecycle risk**: ``lifecycle`` is not ``Active`` (NRND, EOL, Obsolete,
    Preview, ...).

A populated ``risk_note`` is the accepted-risk record (mirrors DFMEA action
tracking) -- the line then passes but the flag is still recorded in the
roll-up notes so it stays visible to a reviewer.

The roll-up itself (extended cost per volume tier, price columns summed
across all line items x qty_per_unit) is written into the check's ``notes``
field and to ``out/verify/bom.rollup.json`` -- it is bookkeeping, not a
pass/fail condition.

Standard library only.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lib"))

from forge.checkresult import Check, CheckContractError  # noqa: E402

BOM_REL = Path("bom/bom.csv")
CHECK_ID = "supply.bom_rollup"
REQUIRED_COLUMNS = (
    "ref_des", "description", "mpn", "manufacturer", "qty_per_unit",
    "lifecycle", "lead_time_weeks", "alternates", "risk_note",
)
PRICE_COL_RE = re.compile(r"^price_(\d+)$")
ACTIVE_LIFECYCLE = "active"


def _parse_float(raw: str) -> float | None:
    try:
        return float(str(raw).strip())
    except (TypeError, ValueError):
        return None


def run(project: Path, changed: list[str] | None) -> int:
    bom_path = project / BOM_REL
    if not bom_path.exists():
        print(f"[SKIP] no {BOM_REL} in this project")
        return 0
    if changed and not any(Path(c).resolve() == bom_path.resolve() for c in changed):
        print(f"[SKIP] {BOM_REL} not in --changed set")
        return 0

    with bom_path.open(newline="") as fh:
        reader = csv.DictReader(fh)
        fieldnames = reader.fieldnames or []
        missing_cols = [c for c in REQUIRED_COLUMNS if c not in fieldnames]
        rows = list(reader)

    chk = Check(CHECK_ID, str(BOM_REL), level="L1", project=project)
    if missing_cols:
        return chk.error(f"{BOM_REL} is missing column(s) {missing_cols}; expected at least {list(REQUIRED_COLUMNS)}")
    if not rows:
        print(f"[SKIP] {BOM_REL} has a header but no rows")
        return 0

    tier_cols = sorted((m.group(0), int(m.group(1))) for c in fieldnames if (m := PRICE_COL_RE.match(c)))
    tier_totals: dict[int, float] = {qty: 0.0 for _, qty in tier_cols}
    single_source_n = 0
    lifecycle_risk_n = 0
    unpriced_lines: list[str] = []

    # S17: a duplicate ref_des (the same designator(s) billed twice) either
    # double-counts the BOM cost or silently drops one of the two lines'
    # real content -- count occurrences of each non-blank ref_des value
    # up front so every row past the first can be flagged.
    ref_des_counts: dict[str, int] = {}
    for row in rows:
        raw_ref = (row.get("ref_des") or "").strip()
        if raw_ref:
            ref_des_counts[raw_ref] = ref_des_counts.get(raw_ref, 0) + 1

    for row in rows:
        ref = (row.get("ref_des") or "").strip() or "<no ref_des>"
        loc = f"{BOM_REL}#{ref}"

        if ref != "<no ref_des>" and ref_des_counts.get(ref, 0) > 1:
            chk.measure(
                f"{ref}.ref_des_unique", False, "1", equals=True, location=loc,
                remediation=(
                    f"ref_des {ref!r} appears on {ref_des_counts[ref]} BOM lines -- a duplicate "
                    "double-counts cost/qty or hides that one of the lines is wrong. Merge the "
                    "lines or use each designator once."
                ),
            )

        qty = _parse_float(row.get("qty_per_unit", ""))
        qty_ok = qty is not None and qty > 0
        chk.measure(
            f"{ref}.qty_valid", qty_ok, "1", equals=True, location=loc,
            remediation=(
                f"{ref}: qty_per_unit={row.get('qty_per_unit')!r} must be a positive number."
            ) if not qty_ok else None,
        )
        if not qty_ok:
            continue

        lifecycle = (row.get("lifecycle") or "").strip()
        alternates = (row.get("alternates") or "").strip()
        risk_note = (row.get("risk_note") or "").strip()
        mpn = (row.get("mpn") or "").strip()
        lead_time = (row.get("lead_time_weeks") or "").strip()

        mpn_ok = bool(mpn)
        chk.measure(
            f"{ref}.mpn_present", mpn_ok, "1", equals=True, location=loc,
            remediation=(
                f"{ref}: mpn is blank -- bom-format.md requires an exact manufacturer part "
                "number for every line. Fill it in."
            ) if not mpn_ok else None,
        )

        lead_time_ok = bool(lead_time)
        chk.measure(
            f"{ref}.lead_time_present", lead_time_ok, "1", equals=True, location=loc,
            remediation=(
                f"{ref} ({mpn or '<no mpn>'}): lead_time_weeks is blank -- bom-format.md marks it "
                "required. Quote and fill in the current lead time in weeks."
            ) if not lead_time_ok else None,
        )

        alt_list = [a.strip() for a in alternates.split(";") if a.strip()]
        if mpn_ok:
            self_listed = [a for a in alt_list if a.lower() == mpn.lower()]
            alternates_distinct = not self_listed
            chk.measure(
                f"{ref}.alternates_distinct_from_own_mpn", alternates_distinct, "1", equals=True, location=loc,
                remediation=(
                    f"{ref}: alternates lists {mpn!r} (its own mpn) as its own alternate -- this "
                    "hides a real single-source risk instead of covering it. List a genuinely "
                    "different alternate MPN, or leave alternates empty and cover the risk in "
                    "risk_note."
                ) if not alternates_distinct else None,
            )
            # A self-listed "alternate" is not a real second source: treat the
            # line as single-source for the covered-by-risk-note check below.
            if self_listed and len(alt_list) == len(self_listed):
                alternates = ""

        is_single_source = not alternates
        is_lifecycle_risk = lifecycle.lower() != ACTIVE_LIFECYCLE
        if is_single_source:
            single_source_n += 1
        if is_lifecycle_risk:
            lifecycle_risk_n += 1

        if is_single_source:
            covered = bool(risk_note)
            chk.measure(
                f"{ref}.single_source_acknowledged", covered, "1", equals=True, location=loc,
                remediation=(
                    f"{ref} ({row.get('mpn')}) has no alternates listed -- single-source risk. "
                    "Add an alternate MPN to 'alternates', or explain the mitigation in 'risk_note' "
                    "(e.g. second-source qualification in progress, owner, date)."
                ) if not covered else None,
            )
        if is_lifecycle_risk:
            covered = bool(risk_note)
            chk.measure(
                f"{ref}.lifecycle_risk_acknowledged", covered, "1", equals=True, location=loc,
                remediation=(
                    f"{ref} ({row.get('mpn')}) lifecycle is {lifecycle!r}, not Active "
                    "(NRND/EOL/Obsolete/Preview all carry sourcing risk). Add a 'risk_note' "
                    "with the replacement plan or last-time-buy status."
                ) if not covered else None,
            )

        line_has_price = False
        for col, tier_qty in tier_cols:
            price = _parse_float(row.get(col, ""))
            if price is not None:
                line_has_price = True
                price_ok = price >= 0
                chk.measure(
                    f"{ref}.{col}_nonnegative", price_ok, "1", equals=True, location=loc,
                    remediation=(
                        f"{ref} ({mpn or '<no mpn>'}): {col} = {price} is negative -- a price can't "
                        "be negative. Fix the quoted unit price."
                    ) if not price_ok else None,
                )
                if price_ok:
                    tier_totals[tier_qty] += price * qty
        if not line_has_price and tier_cols:
            unpriced_lines.append(ref)

    if unpriced_lines:
        chk.measure(
            "bom.all_lines_priced", False, "1", equals=True,
            remediation=(
                f"Line(s) with no price at any volume tier: {unpriced_lines}. "
                "Add at least one price_<qty> column value per line before costing the BOM."
            ),
        )
    else:
        chk.measure("bom.all_lines_priced", True, "1", equals=True)

    rollup_lines = [f"volume {qty}: extended cost ${total:,.2f}" for qty, total in sorted(tier_totals.items())]
    notes = (
        f"{len(rows)} line(s); {single_source_n} single-source; {lifecycle_risk_n} lifecycle-risk. "
        + "; ".join(rollup_lines)
    )

    out_dir = project / "out" / "verify"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "bom.rollup.json").write_text(json.dumps({
        "schema": "forge.bom_rollup/1",
        "line_count": len(rows),
        "single_source_count": single_source_n,
        "lifecycle_risk_count": lifecycle_risk_n,
        "tier_totals_usd": {str(q): round(t, 2) for q, t in sorted(tier_totals.items())},
    }, indent=2) + "\n")

    return chk.finish(notes=notes)


def main(argv: list[str]) -> int:
    # CONTRACTS.md §9 check_id namespace: printed first, on every run, so PostToolUse
    # binds fix messages to this entrypoint by check_id prefix.
    print(f"[FORGE_CHECK_ID_PREFIX] {CHECK_ID}")
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
