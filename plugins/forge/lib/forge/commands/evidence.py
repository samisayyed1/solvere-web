"""``forge evidence add|from-checks|list|status`` (CONTRACTS.md §4, §11).

A thin CLI over :mod:`forge.evidence`, which owns the append-only manifest
contract; this module is only argument handling and formatting.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .. import evidence as evidence_lib

NAME = "evidence"
HELP = "add, summarize or inspect evidence/manifest.json entries"


def register(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--project", type=Path, default=Path("."), help="product repo root (default: cwd)")
    sub = parser.add_subparsers(dest="evidence_command", required=True)

    add_p = sub.add_parser("add", help="append one evidence entry directly")
    add_p.add_argument("--artifact", required=True)
    add_p.add_argument("--domain", required=True, choices=evidence_lib.DOMAINS)
    add_p.add_argument("--claim", required=True)
    add_p.add_argument("--check-id", dest="check_ids", action="append", default=[])
    add_p.add_argument("--result", required=True, choices=("pass", "fail"))
    add_p.add_argument("--level", required=True, choices=evidence_lib.LEVELS)
    add_p.add_argument("--evidence-file", dest="evidence_files", action="append", default=[])
    add_p.add_argument("--input", dest="inputs", action="append", default=[],
                        help="file to fold into inputs_sha256 (repeatable)")
    add_p.add_argument("--model", default=None)
    add_p.add_argument("--tool-version", dest="tool_versions", action="append", default=[],
                        metavar="NAME=VERSION")
    add_p.add_argument("--status", default="VERIFIED", choices=("VERIFIED", "UNVERIFIED"))
    add_p.add_argument("--signed-by", default=None, help="required for L4/L5")
    add_p.add_argument("--notes", default=None)

    fc_p = sub.add_parser("from-checks", help="summarize forge.check/1 result file(s) into one entry")
    fc_p.add_argument("--check", dest="checks", action="append", required=True,
                       help="out/verify/<check_id>.json path (repeatable)")
    fc_p.add_argument("--artifact", required=True)
    fc_p.add_argument("--domain", required=True, choices=evidence_lib.DOMAINS)
    fc_p.add_argument("--claim", required=True)
    fc_p.add_argument("--input", dest="inputs", action="append", default=[])
    fc_p.add_argument("--model", default=None)

    list_p = sub.add_parser("list", help="list evidence entries")
    list_p.add_argument("--domain", default=None, choices=evidence_lib.DOMAINS)
    list_p.add_argument("--status", default=None, choices=("VERIFIED", "UNVERIFIED"))
    list_p.add_argument("--json", action="store_true")

    status_p = sub.add_parser("status", help="the latest entry per domain")
    status_p.add_argument("--json", action="store_true")


def _parse_tool_versions(pairs: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for pair in pairs:
        if "=" not in pair:
            raise ValueError(f"--tool-version must be NAME=VERSION, got {pair!r}")
        name, version = pair.split("=", 1)
        out[name] = version
    return out


def run(ns: argparse.Namespace, forge_root: Path) -> int:  # noqa: ARG001
    project = ns.project.resolve()

    try:
        if ns.evidence_command == "add":
            entry_id = evidence_lib.add_entry(
                project, artifact=ns.artifact, domain=ns.domain, claim=ns.claim,
                check_ids=ns.check_ids, result=ns.result, level=ns.level,
                evidence_files=ns.evidence_files, inputs=[Path(p) for p in ns.inputs],
                model=ns.model, tool_versions=_parse_tool_versions(ns.tool_versions),
                status=ns.status, signed_by=ns.signed_by, notes=ns.notes,
            )
            print(f"forge evidence add: wrote {entry_id}")
            return 0

        if ns.evidence_command == "from-checks":
            entry_id = evidence_lib.add_from_checks(
                project, [Path(p) for p in ns.checks], artifact=ns.artifact, domain=ns.domain,
                claim=ns.claim, inputs=[Path(p) for p in ns.inputs], model=ns.model,
            )
            print(f"forge evidence from-checks: wrote {entry_id}")
            return 0
    except (evidence_lib.EvidenceError, ValueError, OSError) as exc:
        print(f"forge evidence {ns.evidence_command}: {exc}", file=sys.stderr)
        return 1

    data = evidence_lib.load(project)
    entries = data.get("entries", [])

    if ns.evidence_command == "list":
        if ns.domain:
            entries = [e for e in entries if e.get("domain") == ns.domain]
        if ns.status:
            entries = [e for e in entries if e.get("status") == ns.status]
        if ns.json:
            print(json.dumps(entries, indent=2, sort_keys=True, ensure_ascii=False))
        elif not entries:
            print("forge evidence list: no entries")
        else:
            for entry in entries:
                print(f"{entry['id']}  {entry['domain']:<11} {entry['result']:<4} {entry['level']:<2} "
                      f"{entry['status']:<10} {entry['timestamp']}  {entry['claim']}")
        return 0

    if ns.evidence_command == "status":
        latest_by_domain: dict[str, dict] = {}
        for entry in entries:
            domain = entry.get("domain")
            # >= (not >): manifest entries are append-only in chronological order, so on a
            # same-second timestamp tie the later entry in the list is still the newer one.
            if domain not in latest_by_domain or entry.get("timestamp", "") >= latest_by_domain[domain].get("timestamp", ""):
                latest_by_domain[domain] = entry
        if ns.json:
            print(json.dumps(latest_by_domain, indent=2, sort_keys=True, ensure_ascii=False))
        elif not latest_by_domain:
            print("forge evidence status: no entries")
        else:
            for domain in sorted(latest_by_domain):
                entry = latest_by_domain[domain]
                print(f"{domain}: {entry['result']} {entry['level']} {entry['status']} "
                      f"({entry['id']}, {entry['timestamp']})")
        return 0

    print(f"forge evidence: unknown subcommand {ns.evidence_command!r}", file=sys.stderr)
    return 2
