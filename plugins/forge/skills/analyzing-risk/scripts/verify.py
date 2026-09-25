#!/usr/bin/env python3
"""DFMEA Action Priority check over analysis/dfmea.csv.

Invocation:
    forge-python skills/analyzing-risk/scripts/verify.py --project <root> [--changed <path> ...] [--fast]

For each row it:
  - validates severity/occurrence/detection are integers in 1..10;
  - computes the Action Priority (High/Medium/Low) via ``ap.action_priority``
    (a sourced *approximation* -- see ap.py's module docstring and
    ``references/dfmea-ap.md`` for the AIAG & VDA handbook sourcing gap);
  - FAILS any row whose AP is High and has no action + owner + due_date
    (action tracking, per the builder brief).

check_id: ``safety.dfmea_ap``. Standard library only.
"""
from __future__ import annotations

import csv
import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lib"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from forge.checkresult import Check, CheckContractError  # noqa: E402
from ap import action_priority  # noqa: E402

DFMEA_REL = Path("analysis/dfmea.csv")
CHECK_ID = "safety.dfmea_ap"
REQUIRED_COLUMNS = (
    "id", "item", "function", "failure_mode", "effect", "severity",
    "cause", "occurrence", "current_controls", "detection",
    "action", "owner", "due_date",
)


def _parse_int_1_10(raw: str) -> int | None:
    try:
        v = int(str(raw).strip())
    except (TypeError, ValueError):
        return None
    return v if 1 <= v <= 10 else None


# S16: text that looks like it fills the field but carries no real
# information ("TBD", "?", "someday", ...) must not count as a stated
# action/owner/due date.
PLACEHOLDER_VALUES = {
    "tbd", "t.b.d.", "n/a", "na", "none", "?", "??", "unknown", "someday",
    "-", "--", "pending", "asap", "later", "xxx", "todo",
}


def _is_placeholder(value: str) -> bool:
    return value.strip().lower() in PLACEHOLDER_VALUES


def _parse_iso_date(raw: str) -> datetime.date | None:
    """A due date must be a real, parseable ISO-8601 date (YYYY-MM-DD)."""
    try:
        return datetime.date.fromisoformat(raw.strip())
    except (TypeError, ValueError):
        return None


def run(project: Path, changed: list[str] | None) -> int:
    dfmea_path = project / DFMEA_REL
    if not dfmea_path.exists():
        print(f"[SKIP] no {DFMEA_REL} in this project")
        return 0
    if changed and not any(Path(c).resolve() == dfmea_path.resolve() for c in changed):
        print(f"[SKIP] {DFMEA_REL} not in --changed set")
        return 0

    with dfmea_path.open(newline="") as fh:
        reader = csv.DictReader(fh)
        missing_cols = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
        rows = list(reader)

    chk = Check(CHECK_ID, str(DFMEA_REL), level="L1", project=project)
    if missing_cols:
        return chk.error(f"{DFMEA_REL} is missing column(s) {missing_cols}; expected {list(REQUIRED_COLUMNS)}")
    if not rows:
        print(f"[SKIP] {DFMEA_REL} has a header but no rows")
        return 0

    for row in rows:
        row_id = (row.get("id") or "").strip() or "<no id>"
        loc = f"{DFMEA_REL}#{row_id}"

        s = _parse_int_1_10(row.get("severity", ""))
        o = _parse_int_1_10(row.get("occurrence", ""))
        d = _parse_int_1_10(row.get("detection", ""))
        sod_ok = None not in (s, o, d)
        chk.measure(
            f"{row_id}.sod_valid", sod_ok, "1", equals=True, location=loc,
            remediation=(
                f"{row_id}: severity/occurrence/detection must each be an integer in 1..10 "
                f"(got severity={row.get('severity')!r}, occurrence={row.get('occurrence')!r}, "
                f"detection={row.get('detection')!r})."
            ) if not sod_ok else None,
        )
        if not sod_ok:
            continue

        result = action_priority(s, o, d)
        action = (row.get("action") or "").strip()
        owner = (row.get("owner") or "").strip()
        due_date = (row.get("due_date") or "").strip()

        # S16: a placeholder ("TBD", "?", "someday", ...) is not a stated
        # action/owner/due date, and a due date must be a real ISO date.
        action_ok = bool(action) and not _is_placeholder(action)
        owner_ok = bool(owner) and not _is_placeholder(owner)
        due_parsed = _parse_iso_date(due_date) if due_date and not _is_placeholder(due_date) else None
        due_ok = due_parsed is not None
        has_action = action_ok and owner_ok and due_ok

        if result.ap == "High":
            chk.measure(
                f"{row_id}.high_ap_has_action", has_action, "1", equals=True, location=loc,
                remediation=(
                    f"{row_id} (S={s} O={o} D={d}) is Action Priority High "
                    f"({result.note}) but action={action!r} owner={owner!r} "
                    f"due_date={due_date!r} is missing, a placeholder, or not a real "
                    "ISO-8601 (YYYY-MM-DD) date. A High-AP finding needs a real action, "
                    "a real owner and a real due date, or a documented reason current "
                    "controls are enough."
                ) if not has_action else None,
            )
        else:
            # Not a failing condition, but record the classification for the
            # evidence trail; note is not "None" so nothing can silently pass.
            chk.measure(f"{row_id}.ap_{result.ap.lower()}", True, "1", equals=True, location=loc)

        # S16: whatever the AP band, a real due date that has already passed
        # is an overdue action and must be flagged, not silently carried.
        if due_ok:
            today = datetime.date.today()
            overdue = due_parsed < today
            chk.measure(
                f"{row_id}.due_date_not_overdue", not overdue, "1", equals=True, location=loc,
                remediation=(
                    f"{row_id}: due_date {due_date} is in the past (today is "
                    f"{today.isoformat()}). Close the action out or set a new due date."
                ) if overdue else None,
            )

    return chk.finish()


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
