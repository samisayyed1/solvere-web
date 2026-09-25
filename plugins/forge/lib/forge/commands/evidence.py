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

    status_p = sub.add_parser("status", help="the latest `forge verify` entry per (domain, entrypoint), "
                                             "rolled up per domain as the worst result (S19)")
    status_p.add_argument("--json", action="store_true")


def _entry_rank(entry: dict) -> int:
    """S19 roll-up ranking: lower is worse. A FAIL or an UNVERIFIED entry
    (even a would-be pass, e.g. from a --fast/partial run) is worse than an
    N/A ("nothing verified"), which is worse than a clean VERIFIED pass."""
    if entry.get("result") == "fail" or entry.get("status") == "UNVERIFIED":
        return 0
    if entry.get("result") == "na":
        return 1
    return 2


def _worst_result(entries) -> dict:
    """The worst-ranked entry among ``entries`` (S19): FAIL/UNVERIFIED worst,
    then N/A, then a clean pass."""
    return min(entries, key=_entry_rank)


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
        # S19: a per-domain "latest entry" hides a failing (or N/A) sibling
        # entrypoint behind whichever one happened to run last -- the
        # addendum's exact probe (verifying-geometry FAIL, then
        # checking-dfm N/A, reported as "mech: pass"). Report the newest
        # entry of every (domain, unit) pair, ``unit`` being the
        # ``entrypoint`` of a `forge verify` run or, for a hand-made claim
        # (`forge evidence add`, which has no entrypoint), its ``artifact``
        # -- so distinct entrypoints/artifacts never shadow one another --
        # and roll each domain up to the worst of its units.
        latest_by_unit: dict[tuple[str, str], dict] = {}
        for entry in entries:
            unit = entry.get("entrypoint") or entry.get("artifact") or ""
            key = (entry.get("domain"), unit)
            # manifest entries are append-only in chronological order, so the
            # later one in the list is always the newer one.
            latest_by_unit[key] = entry
        by_domain: dict[str, dict[str, dict]] = {}
        for (domain, unit), entry in latest_by_unit.items():
            by_domain.setdefault(domain, {})[unit] = entry
        rollup = {domain: _worst_result(units.values()) for domain, units in by_domain.items()}
        if ns.json:
            payload = {domain: dict(rollup[domain], by_unit=units) for domain, units in by_domain.items()}
            print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
        elif not by_domain:
            print("forge evidence status: no entries")
        else:
            for domain in sorted(by_domain):
                worst = rollup[domain]
                print(f"{domain}: {worst['result']} {worst['status']} "
                      f"(worst of {len(by_domain[domain])} unit(s))")
                for unit in sorted(by_domain[domain]):
                    entry = by_domain[domain][unit]
                    print(f"  {domain}/{unit}: {entry['result']} {entry['level']} {entry['status']} "
                          f"({entry['id']}, {entry['timestamp']})")
        return 0

    print(f"forge evidence: unknown subcommand {ns.evidence_command!r}", file=sys.stderr)
    return 2
