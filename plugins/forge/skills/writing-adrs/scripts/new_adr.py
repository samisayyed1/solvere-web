#!/usr/bin/env python3
"""Scaffold the next-numbered ADR from the template (writing-adrs skill).

Usage:
    python3 new_adr.py --project <root> --title "Use tscircuit over atopile" [--status "Proposed"]

Scans docs/decisions/ADR-*.md for the highest existing number, writes
docs/decisions/ADR-<NNN>-<slug>.md from references/adr-template.md with the
number, title, date (must be passed in -- this script never calls a clock
itself, so it stays reproducible under a caller-supplied --date) and status
filled in, and prints the path. It never overwrites an existing ADR file.

Standard library only. This is a scaffolding utility, not a check -- it has
no forge.checkresult integration and no pass/fail semantics; a missing
template or a naming collision is a plain error (exit 1).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ADR_DIR_REL = Path("docs/decisions")
ADR_RE = re.compile(r"^ADR-(\d{3,})-")
TEMPLATE_REL = Path(__file__).resolve().parent.parent / "references" / "adr-template.md"


def slugify(title: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return re.sub(r"-{2,}", "-", s)


def next_number(adr_dir: Path) -> int:
    if not adr_dir.exists():
        return 1
    nums = []
    for p in adr_dir.glob("ADR-*.md"):
        m = ADR_RE.match(p.name)
        if m:
            nums.append(int(m.group(1)))
    return (max(nums) + 1) if nums else 1


def render(template: str, *, number: int, title: str, date: str, status: str) -> str:
    return (
        template
        .replace("{{NUMBER}}", f"{number:03d}")
        .replace("{{TITLE}}", title)
        .replace("{{DATE}}", date)
        .replace("{{STATUS}}", status)
    )


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", type=Path, default=Path("."))
    ap.add_argument("--title", required=True)
    ap.add_argument("--date", required=True, help="YYYY-MM-DD; the caller supplies this (no clock in the script)")
    ap.add_argument("--status", default="Proposed")
    ns = ap.parse_args(argv)

    project = ns.project.resolve()
    adr_dir = project / ADR_DIR_REL
    adr_dir.mkdir(parents=True, exist_ok=True)

    if not TEMPLATE_REL.exists():
        print(f"new_adr: template missing: {TEMPLATE_REL}", file=sys.stderr)
        return 1

    number = next_number(adr_dir)
    slug = slugify(ns.title)
    out_path = adr_dir / f"ADR-{number:03d}-{slug}.md"
    if out_path.exists():
        print(f"new_adr: {out_path} already exists", file=sys.stderr)
        return 1

    content = render(TEMPLATE_REL.read_text(), number=number, title=ns.title, date=ns.date, status=ns.status)
    out_path.write_text(content)
    print(str(out_path))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
