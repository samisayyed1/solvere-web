#!/usr/bin/env python3
"""capturing-failures: scaffold docs/failures/<id>.md (brief §3.3, §7).

    forge-python skills/capturing-failures/scripts/new_failure.py --project <root> --title "..."

Deterministically allocates the next ``FAIL-NNNN`` id (scanning existing
``docs/failures/FAIL-*.md`` files) and writes a template with the required sections: the
failure itself, 5 whys, the new mechanism (rule/hook/check/eval), and a proof section that
must show the new check failing on the *original* artifact before it's fixed -- a check
added here that can't be shown failing on the original failure hasn't proven anything
(brief §0: "prove every new check fails on a deliberately wrong input").

This script only scaffolds the file; the 5-whys analysis and the proof are written by
whoever is capturing the failure (human or agent) -- that reasoning isn't automatable.
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path

_ID_RE = re.compile(r"^FAIL-(\d{4,})\.md$")

TEMPLATE = """\
# {fid} -- {title}

Date: {date}

## What happened

<!-- The failure itself: what was claimed or shipped, what was actually wrong. -->

## Five whys

1. Why did it happen? ...
2. Why? ...
3. Why? ...
4. Why? ...
5. Why (root cause)? ...

## New mechanism

<!-- The rule, hook, check or eval case this failure produced. Name the file(s). -->

- Mechanism:
- File(s):

## Proof it catches the original failure

<!-- Required: run the new check against the ORIGINAL (unfixed) artifact and show it
     FAILS. A check that only ever ran against the fixed version proves nothing. -->

- Check result before the fix: `out/verify/....json` (status: fail)
- Check result after the fix: `out/verify/....json` (status: pass)

## Eval case

<!-- Which plugins/forge/evals/ case now covers this, if any. -->
"""


def next_id(failures_dir: Path) -> str:
    nums = [int(m.group(1)) for p in failures_dir.glob("FAIL-*.md") if (m := _ID_RE.match(p.name))]
    return f"FAIL-{(max(nums) + 1 if nums else 1):04d}"


def scaffold(project: Path, title: str) -> Path:
    failures_dir = project / "docs" / "failures"
    failures_dir.mkdir(parents=True, exist_ok=True)
    fid = next_id(failures_dir)
    path = failures_dir / f"{fid}.md"
    date = time.strftime("%Y-%m-%d", time.gmtime())
    path.write_text(TEMPLATE.format(fid=fid, title=title, date=date))
    return path


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True, type=Path)
    ap.add_argument("--title", required=True)
    ns = ap.parse_args(argv)
    path = scaffold(ns.project.resolve(), ns.title)
    print(f"[OK] wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
