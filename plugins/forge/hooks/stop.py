#!/usr/bin/env python3
"""Stop: the evidence gate (CONTRACTS.md §8-9, ADR-001 D5, brief §3.4).

For every ``forge.toml`` ``[[verify]]`` domain whose ``paths`` cover a file
with uncommitted changes (``git status``, which also catches Bash-made
edits PostToolUse never sees, R1a §19), this requires a passing
``evidence/manifest.json`` entry for that domain newer than every changed
file's mtime. Any domain that fails this is reported and the turn is
blocked (``decision: "block"``) so Claude keeps working instead of
declaring victory on unverified changes -- "verification is the product"
(brief §0).

**Block-cap handling** (R1a §18: the platform overrides *any* Stop hook
after 8 consecutive blocks and force-ends the turn with a warning):
Forge keeps its own consecutive-block counter in ``.forge/state.json``
(``forge.state``), incremented on every unsatisfied-gate Stop. On the
**7th** consecutive block -- one before the platform's own cap -- this
hook stops blocking: it appends an ``UNVERIFIED`` evidence entry for every
still-unsatisfied domain (so nothing downstream can mistake the state for
verified) and lets the turn end, with a ``systemMessage`` explaining why.
The counter resets to 0 the moment the gate is satisfied.

``stop_hook_active`` (true when this Stop is a re-invocation after an
earlier block this turn) is recorded in state for observability; the block
counter itself is what drives the 7-before-8 handoff, so a genuinely fresh
Stop and a retry are treated the same way -- both count towards the cap,
matching how the platform's own cap counts consecutive blocks regardless
of cause (R1a §18).
"""

from __future__ import annotations

import calendar
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import find_project_root, load_forge_toml, any_glob_match, changed_paths, truncate  # noqa: E402
from forge import evidence, state  # noqa: E402

BLOCK_CAP_HANDOFF = 7  # one before the platform's 8-consecutive-block cap (R1a §18)
REASON_MAX_CHARS = 1800
SYSTEM_MESSAGE_MAX_CHARS = 1800


def _parse_iso(ts: str | None) -> float | None:
    if not ts:
        return None
    try:
        return calendar.timegm(time.strptime(ts, "%Y-%m-%dT%H:%M:%SZ"))
    except ValueError:
        return None


def _domains_needing_evidence(toml: dict, changed: list[str]) -> dict[str, set[str]]:
    needed: dict[str, set[str]] = {}
    for entry in toml.get("verify") or []:
        if not isinstance(entry, dict):
            continue
        domain = entry.get("domain")
        paths = entry.get("paths") or []
        if not domain:
            continue
        matched = {p for p in changed if any_glob_match(paths, p)}
        if matched:
            needed.setdefault(domain, set()).update(matched)
    return needed


def _domain_satisfied(project: Path, manifest: dict, domain: str, paths: set[str]) -> bool:
    passing = [e for e in manifest.get("entries", []) if e.get("domain") == domain and e.get("result") == "pass"]
    if not passing:
        return False
    # (timestamp, position): manifest entries are append-only in chronological
    # order, so on a same-second timestamp tie the later entry is still newer.
    latest = max(enumerate(passing), key=lambda pair: (_parse_iso(pair[1].get("timestamp")) or 0.0, pair[0]))[1]
    entry_time = _parse_iso(latest.get("timestamp"))
    if entry_time is None:
        return False
    for rel in paths:
        try:
            mtime = (project / rel).stat().st_mtime
        except OSError:
            continue  # deleted since; nothing to re-verify against
        if mtime > entry_time:
            return False
    return True


def _entrypoints_by_domain(toml: dict) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for entry in toml.get("verify") or []:
        if not isinstance(entry, dict) or not entry.get("domain"):
            continue
        out.setdefault(entry["domain"], []).extend(entry.get("entrypoints") or [])
    return out


def _build_reason(unsatisfied: list[str], needed: dict[str, set[str]], toml: dict) -> str:
    by_domain = _entrypoints_by_domain(toml)
    lines = ["Forge evidence gate: the following domains changed without fresh passing evidence"
             " (evidence/manifest.json, CONTRACTS.md §9):"]
    for domain in sorted(unsatisfied):
        paths = sorted(needed[domain])
        shown = ", ".join(paths[:5]) + (f" (+{len(paths) - 5} more)" if len(paths) > 5 else "")
        entrypoints = ", ".join(by_domain.get(domain) or []) or "(none registered in forge.toml)"
        lines.append(f"- {domain}: changed {shown}. Run {entrypoints} (forge verify --domain {domain}), "
                     f"then `forge evidence add|from-checks` to record a passing entry.")
    return truncate("\n".join(lines), REASON_MAX_CHARS)


def handle(data: dict) -> tuple[int, dict | None]:
    project = find_project_root(data.get("cwd"))
    if project is None:
        return 0, None  # not a Forge product repo: no-op fast (brief §3.4)

    toml = load_forge_toml(project)
    changed = changed_paths(project)
    needed = _domains_needing_evidence(toml, changed) if changed else {}

    if not needed:
        state.reset_stop_block(project)
        return 0, None

    manifest = evidence.load(project)
    unsatisfied = [d for d, paths in needed.items() if not _domain_satisfied(project, manifest, d, paths)]

    if not unsatisfied:
        state.reset_stop_block(project)
        return 0, None

    reason = _build_reason(unsatisfied, needed, toml)
    count = state.record_stop_block(project, reason=reason)

    if count >= BLOCK_CAP_HANDOFF:
        for domain in unsatisfied:
            evidence.add_entry(
                project, artifact=f"domain:{domain}", domain=domain,
                claim=(f"{domain} changed but was not verified after {count} consecutive Stop attempts; "
                       "recorded UNVERIFIED so downstream gates cannot mistake this for passing evidence."),
                check_ids=[], result="fail", level="L0", evidence_files=[], status="UNVERIFIED",
            )
        state.reset_stop_block(project)
        msg = (f"Forge: evidence gate reached its {BLOCK_CAP_HANDOFF}-block handoff (before the platform's "
               f"8-block cap) for {', '.join(sorted(unsatisfied))}; recorded UNVERIFIED evidence and let the "
               "turn stop. These domains still need real verification before anything downstream (release, "
               "fab) can proceed.")
        return 0, {"systemMessage": truncate(msg, SYSTEM_MESSAGE_MAX_CHARS)}

    return 2, {"decision": "block", "reason": reason}


if __name__ == "__main__":
    from _failclosed import run_hook
    run_hook(handle)
