#!/usr/bin/env python3
"""Deterministic regression diff for the ``regression-sweep`` workflow (M9,
review #1: "That diff is done by an LLM with no schema").

    forge-python plugins/forge/workflows/scripts/regression_diff.py --project <root>
        [--current out/verify] [--previous out/verify.previous]

Compares the just-finished ``forge verify --all`` run (``out/verify/*.json``,
``forge.check/1`` results) against a preserved previous run
(``out/verify.previous/*.json``, if any) and classifies every check_id as
NEW / REMOVED / UNCHANGED / REGRESSED (pass -> fail/error) / FIXED (fail/error
-> pass) -- exact string comparison of ``status``, never an LLM's judgement
call. Separately, for each evidence domain (CONTRACTS §4), reads the
product repo's git-tracked changes and the domain's recorded
``last_green`` state (``.forge/state.json``, read through
``forge.state.load()``'s public API -- this script never writes state) to
flag a domain whose files have moved since its last green SHA as
``stale`` -- CONTRACTS §4/§9's "UNVERIFIED" risk, computed mechanically
instead of an agent eyeballing ``git status``.

Writes nothing; prints one ``forge.regression_diff/1`` JSON object to
stdout and exits 0. Never raises for "nothing to diff" (no previous run,
no state file, not a git repo) -- those are reported fields, not errors.
Standard library only.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lib"))

from forge import state as forge_state  # noqa: E402
from forge.checkresult import git_sha  # noqa: E402

SCHEMA = "forge.regression_diff/1"
CHECK_SCHEMA = "forge.check/1"

# Product-repo domain -> the path globs its work lives under (CONTRACTS.md
# §1 layout, §4 DOMAINS). Static and conservative: a path not matched by any
# domain here is simply not attributed to one, never silently ignored (it
# still shows up in `git status` output if the caller wants it).
DOMAIN_PATH_PREFIXES: dict[str, tuple[str, ...]] = {
    "mech": ("cad/", "params/"),
    "elec": ("ecad/", "circuits/"),
    "fw": ("firmware/",),
    "sw": ("app/", "services/"),
    "sys": ("requirements/", "model/"),
    "sim": ("analysis/",),
    "mfg": ("mfg/", "bom/"),
    "compliance": ("compliance/",),
}


def _load_checks(check_dir: Path) -> dict[str, dict[str, Any]]:
    """{check_id: result} for every well-formed forge.check/1 file directly
    under check_dir (non-recursive -- matches out/verify/*.json's own
    convention of holding only check results at its top level)."""
    out: dict[str, dict[str, Any]] = {}
    if not check_dir.is_dir():
        return out
    for f in sorted(check_dir.glob("*.json")):
        try:
            data = json.loads(f.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict) or data.get("schema") != CHECK_SCHEMA:
            continue
        check_id = data.get("check_id") or f.stem
        out[check_id] = data
    return out


def _remediations(result: dict[str, Any]) -> list[str]:
    out = []
    if result.get("status") == "error" and result.get("error"):
        out.append(str(result["error"]))
    for m in result.get("measurements", []):
        if not m.get("pass", True) and m.get("remediation"):
            out.append(str(m["remediation"]))
    return out


def diff_checks(current: dict[str, dict[str, Any]], previous: dict[str, dict[str, Any]]) -> dict[str, Any]:
    ids = sorted(set(current) | set(previous))
    new: list[str] = []
    removed: list[str] = []
    unchanged: list[str] = []
    regressed: list[dict[str, Any]] = []
    fixed: list[dict[str, Any]] = []
    passing = {"pass"}
    failing = {"fail", "error"}
    for check_id in ids:
        cur = current.get(check_id)
        prev = previous.get(check_id)
        if cur is not None and prev is None:
            new.append(check_id)
            continue
        if cur is None and prev is not None:
            removed.append(check_id)
            continue
        cur_status = cur.get("status")
        prev_status = prev.get("status")
        if cur_status == prev_status:
            unchanged.append(check_id)
        elif prev_status in passing and cur_status in failing:
            regressed.append({
                "check_id": check_id, "previous_status": prev_status, "current_status": cur_status,
                "remediation": _remediations(cur),
            })
        elif prev_status in failing and cur_status in passing:
            fixed.append({"check_id": check_id, "previous_status": prev_status, "current_status": cur_status})
        else:
            # e.g. fail -> error, or error -> fail: still worth flagging, but
            # neither a clean regression from green nor a clean fix.
            unchanged.append(check_id)
    return {"new": new, "removed": removed, "unchanged": unchanged, "regressed": regressed, "fixed": fixed}


def _git_changed_paths(project: Path) -> list[str]:
    """Every path git considers changed: uncommitted (git status --porcelain)
    union tracked-but-uncommitted. Never raises outside a git repo."""
    try:
        proc = subprocess.run(
            ["git", "-C", str(project), "status", "--porcelain", "--untracked-files=all"],
            capture_output=True, text=True, timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    if proc.returncode != 0:
        return []
    paths = []
    for line in proc.stdout.splitlines():
        # porcelain format: "XY path" (or "XY orig -> path" for renames)
        rest = line[3:] if len(line) > 3 else ""
        path = rest.split(" -> ")[-1].strip().strip('"')
        if path:
            paths.append(path)
    return paths


def diff_domains(project: Path) -> list[dict[str, Any]]:
    changed = _git_changed_paths(project)
    current_sha = git_sha(project)
    data = forge_state.load(project)  # public read API (forge.state.load) -- never writes
    last_green = data.get("last_green") or {}
    out = []
    for domain, prefixes in DOMAIN_PATH_PREFIXES.items():
        domain_changed = sorted(p for p in changed if p.startswith(prefixes))
        entry = last_green.get(domain)
        if not domain_changed:
            stale = False
            reason = "no changed files in this domain"
        elif entry is None:
            stale = True
            reason = "domain has changed files but no last_green entry was ever recorded"
        elif entry.get("sha") != current_sha:
            stale = True
            reason = (
                f"domain has changed files; last_green sha {entry.get('sha')!r} != current {current_sha!r}"
            )
        else:
            stale = False
            reason = "last_green sha matches the current tree"
        out.append({
            "domain": domain, "changed_paths": domain_changed, "last_green": entry,
            "current_sha": current_sha, "stale": stale, "reason": reason,
        })
    return out


def run(project: Path, current_dir: Path, previous_dir: Path) -> dict[str, Any]:
    has_previous = previous_dir.is_dir() and any(previous_dir.glob("*.json"))
    current = _load_checks(current_dir)
    previous = _load_checks(previous_dir) if has_previous else {}
    checks = diff_checks(current, previous) if has_previous else {
        "new": sorted(current), "removed": [], "unchanged": [], "regressed": [], "fixed": [],
    }
    domains = diff_domains(project)
    stale_domains = [d["domain"] for d in domains if d["stale"]]
    summary = (
        f"{len(checks['regressed'])} regressed, {len(checks['fixed'])} fixed, "
        f"{len(checks['unchanged'])} unchanged, {len(checks['new'])} new, "
        f"{len(stale_domains)} stale-domain risk(s)"
        + (f" ({', '.join(stale_domains)})" if stale_domains else "")
    )
    return {
        "schema": SCHEMA,
        "project": str(project),
        "current_dir": str(current_dir.relative_to(project)) if current_dir.is_relative_to(project) else str(current_dir),
        "previous_dir": str(previous_dir.relative_to(project)) if previous_dir.is_relative_to(project) else str(previous_dir),
        "has_previous": has_previous,
        "checks": checks,
        "domains": domains,
        "summary": summary,
    }


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True, type=Path)
    ap.add_argument("--current", default="out/verify")
    ap.add_argument("--previous", default="out/verify.previous")
    ns = ap.parse_args(argv)
    project = ns.project.resolve()
    result = run(project, project / ns.current, project / ns.previous)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
