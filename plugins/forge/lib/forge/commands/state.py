"""``forge state show`` (CONTRACTS.md §11, §13).

Prints the ``.forge/state.json`` snapshot a product repo's Stop and
PreCompact hooks maintain: the current gate, the consecutive Stop-block
counter, last-green domains, open review findings, failing checks and
modified files. Read-only; this command never writes state (the hooks own
that).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .. import state as state_lib

NAME = "state"
HELP = "show the .forge/state.json snapshot for a product project"


def register(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--project", type=Path, default=Path("."), help="product repo root (default: cwd)")
    sub = parser.add_subparsers(dest="state_command", required=True)
    show_p = sub.add_parser("show", help="print the current .forge/state.json snapshot")
    show_p.add_argument("--json", action="store_true", help="emit the raw state JSON")


def run(ns: argparse.Namespace, forge_root: Path) -> int:  # noqa: ARG001 -- forge_root unused, part of the interface
    project = ns.project.resolve()
    data = state_lib.load(project)

    if ns.json:
        print(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False))
        return 0

    print(f"gate: {data.get('gate') or '(unset)'}")
    print(f"consecutive Stop blocks: {data.get('stop_block_count', 0)}")
    last_green = data.get("last_green") or {}
    if last_green:
        print("last green by domain:")
        for domain, info in sorted(last_green.items()):
            print(f"  {domain}: {info.get('sha')} @ {info.get('timestamp')}")
    findings = data.get("open_findings") or []
    print(f"open findings: {len(findings)}")
    for finding in findings[:20]:
        print(f"  - [{finding.get('verdict')}] {finding.get('id')}: {finding.get('finding')}")
    failing = data.get("failing_checks") or []
    if failing:
        print(f"failing checks: {', '.join(failing)}")
    modified = data.get("modified_files") or []
    if modified:
        print(f"modified files: {', '.join(modified)}")
    print(f"updated: {data.get('updated') or '(never)'}")
    return 0
