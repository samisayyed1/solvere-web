"""``forge verify``: run domain verify entrypoints per ``forge.toml`` (CONTRACTS.md §9).

    forge verify [--all|--changed PATH...] [--project PATH] [--fast]

For each ``[[verify]]`` block in the product repo's ``forge.toml`` whose
``paths`` glob matches a changed file (or every block, under ``--all``), runs
each listed entrypoint as

    <forge-python> plugins/forge/skills/<skill>/scripts/verify.py \
        --project <root> [--changed <path> ...] [--fast]

in ladder order (the order the entrypoints are listed), aggregates the exit
codes (any ``ERROR`` -> 2, else any ``FAIL`` -> 1, else 0), and records one
evidence entry **per (domain, entrypoint) run** via
``forge.evidence.add_verify_entry``: bound to the ``out/verify/*.json`` files
that entrypoint wrote (with their sha256), its exit code, its ``--changed``
scope and ``inputs_sha256`` over every file the domain's globs cover. That
binding is what the Stop hook's evidence gate re-checks (review #1, C2/M6).

When every entrypoint of a domain ran in this invocation and passed, the
domain's last-green SHA (``.forge/state.json``) is set to HEAD, vouched for
by the entries just written (review #1, M9).

An entrypoint script that does not exist yet is not an error: it is reported
as SKIP and listed, because other builders add their ``scripts/verify.py``
independently (CONTRACTS.md §9: "Entrypoints not yet present -> SKIP,
listed."). A missing ``forge-python`` interpreter *is* an error (exit 2),
with the toolchain-install fix, never a silent pass.

Standard library only -- this module runs under the plain ``forge`` CLI
(python3), not under ``forge-python``.
"""

from __future__ import annotations

import argparse
import inspect
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from .. import evidence, state

NAME = "verify"
HELP = "run domain verify entrypoints from forge.toml in ladder order (CONTRACTS.md §9)"

RUNG_ORDER = ("syntax", "build", "validity", "numeric", "physics", "visual")


class VerifyError(RuntimeError):
    """forge.toml is missing or malformed."""


def register(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--all", action="store_true", help="run every entrypoint in forge.toml")
    parser.add_argument(
        "--changed", nargs="*", default=None, metavar="PATH",
        help="only run entrypoints whose forge.toml paths glob matches one of these",
    )
    parser.add_argument("--project", type=Path, default=Path("."), help="product-repo root (default: cwd)")
    parser.add_argument("--fast", action="store_true", help="pass --fast through to entrypoints (PostToolUse mode)")


def _load_toml(path: Path) -> dict[str, Any]:
    try:
        import tomllib  # Python >= 3.11
    except ImportError:  # pragma: no cover -- only hit on very old interpreters
        import tomli as tomllib  # type: ignore[no-redef]
    with path.open("rb") as fh:
        return tomllib.load(fh)


def _load_forge_toml(project: Path) -> dict[str, Any]:
    path = project / "forge.toml"
    if not path.exists():
        raise VerifyError(f"{path} not found (scaffold with /forge:new-project or /forge:init)")
    try:
        data = _load_toml(path)
    except Exception as exc:  # noqa: BLE001 -- report as a VerifyError, not a traceback
        raise VerifyError(f"{path} is not valid TOML: {exc}") from exc
    if "verify" not in data:
        return {"project": data.get("project", {}), "verify": []}
    return data


def _matches_any(rel_path: str, patterns: list[str]) -> bool:
    # The same matcher the hooks use, so verify and the Stop gate always agree
    # on which domain a path belongs to.
    return evidence.any_glob_match(patterns, rel_path)


def _forge_python(forge_root: Path) -> Path:
    env = os.environ.get("FORGE_PYTHON")
    if env:
        return Path(env)
    forge_home = Path(os.environ.get("FORGE_HOME", str(Path.home() / ".forge")))
    return forge_home / "bin" / "forge-python"


def _snapshot_verify_dir(project: Path) -> dict[Path, int]:
    out_dir = project / "out" / "verify"
    if not out_dir.exists():
        return {}
    return {p: p.stat().st_mtime_ns for p in out_dir.glob("*.json")}


def _is_check_result(path: Path) -> bool:
    """True if ``path`` parses as a ``forge.check/1`` result (CONTRACTS.md
    §3). Used only to tell a real check result apart from other JSON an
    entrypoint may drop in ``out/verify/`` (there should be none, but this
    mirrors ``evidence._read_check``'s own filter defensively)."""
    try:
        data = json.loads(path.read_text())
    except (OSError, UnicodeDecodeError, ValueError):
        return False
    return isinstance(data, dict) and data.get("schema") == "forge.check/1"


def _run_entrypoint(skill: str, *, plugin_root: Path, forge_python: Path, project: Path,
                     changed: list[str] | None, fast: bool) -> dict[str, Any]:
    script = plugin_root / "skills" / skill / "scripts" / "verify.py"
    if not script.exists():
        return {"skill": skill, "status": "SKIP",
                "reason": f"no skills/{skill}/scripts/verify.py yet", "check_files": []}
    if not forge_python.exists():
        return {
            "skill": skill, "status": "ERROR",
            "reason": f"forge-python not found at {forge_python}; run plugins/forge/toolchain/install.sh",
            "check_files": [],
        }
    argv = [str(forge_python), str(script), "--project", str(project)]
    if changed:
        argv += ["--changed", *changed]
    if fast:
        argv.append("--fast")
    before = _snapshot_verify_dir(project)
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=900)
    except subprocess.TimeoutExpired:
        return {"skill": skill, "status": "ERROR", "reason": f"{skill} verify.py timed out", "check_files": []}
    except OSError as exc:
        return {"skill": skill, "status": "ERROR", "reason": f"could not launch {skill} verify.py: {exc}", "check_files": []}
    after = _snapshot_verify_dir(project)
    touched = sorted(p for p, mtime in after.items() if before.get(p) != mtime)
    status = {0: "PASS", 1: "FAIL"}.get(proc.returncode, "ERROR")
    reason = None
    if status == "ERROR":
        reason = f"{skill} verify.py exited {proc.returncode}"
    elif status == "PASS" and not any(_is_check_result(p) for p in touched):
        # D1 (vacuous pass, review #2): an entrypoint that exits 0 without
        # writing a single forge.check/1 result (e.g. an empty cad/) verified
        # nothing. It must never be reported or recorded as a pass -- it is
        # its own status, N/A ("no inputs"): never a green result to cite,
        # and never counted toward last-green (see _record_last_green).
        status = "NA"
        reason = f"{skill} verify.py exited 0 but wrote no out/verify/*.json check result (nothing to verify)"
    return {
        "skill": skill, "status": status, "returncode": proc.returncode,
        "stdout": proc.stdout, "stderr": proc.stderr, "check_files": touched, "reason": reason,
    }


def _rel_changed(project: Path, changed: list[str]) -> list[str]:
    out = []
    for c in changed:
        p = Path(c)
        if p.is_absolute():
            try:
                p = p.resolve().relative_to(project)
            except ValueError:
                pass
        out.append(os.path.normpath(p.as_posix()).replace(os.sep, "/"))
    return out


def _patterns_for(toml_data: dict[str, Any], domain: str, skill: str) -> list[str]:
    pats: list[str] = []
    for b in toml_data.get("verify", []):
        if b.get("domain") == domain and skill in (b.get("entrypoints") or []):
            pats.extend(p for p in b.get("paths", []) if p not in pats)
    return pats


def _head(project: Path) -> str | None:
    try:
        res = subprocess.run(["git", "-C", str(project), "rev-parse", "--verify", "-q", "HEAD"],
                             capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return res.stdout.strip() if res.returncode == 0 and res.stdout.strip() else None


def _run_blocks(toml_data: dict[str, Any], *, plugin_root: Path, forge_python: Path, project: Path,
                 changed: list[str] | None, fast: bool) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    blocks = sorted(toml_data.get("verify", []), key=lambda b: RUNG_ORDER.index(b.get("rung", "syntax"))
                     if b.get("rung") in RUNG_ORDER else len(RUNG_ORDER))
    rels = _rel_changed(project, changed) if changed is not None else None
    files = evidence.project_files(project)
    for block in blocks:
        domain = block.get("domain", "?")
        patterns = block.get("paths", [])
        entrypoints = block.get("entrypoints", [])
        if rels is not None:
            scope = [r for r in rels if _matches_any(r, patterns)]
            if not scope:
                continue
            run_changed = changed
        else:
            scope, run_changed = None, None
        for skill in entrypoints:
            res = _run_entrypoint(skill, plugin_root=plugin_root, forge_python=forge_python,
                                   project=project, changed=run_changed, fast=fast)
            res["domain"] = domain
            res["rung"] = block.get("rung", "?")
            results.append(res)
            if res["status"] == "SKIP" or "returncode" not in res and res["status"] != "ERROR":
                continue  # the entrypoint does not exist: nothing ran, nothing to record
            try:
                add_kwargs: dict[str, Any] = dict(
                    domain=domain, entrypoint=skill, returncode=res.get("returncode", 2),
                    check_files=res.get("check_files", []),
                    patterns=_patterns_for(toml_data, domain, skill), scope=scope, fast=fast,
                    rung=block.get("rung"), model=os.environ.get("FORGE_MODEL"), files=files)
                if res["status"] == "NA" and "na" in inspect.signature(evidence.add_verify_entry).parameters:
                    # Interface note (D1): once evidence.add_verify_entry grows an
                    # ``na: bool = False`` kwarg, this starts recording the run
                    # with result="na" instead of "pass" -- see the report for the
                    # exact change. Until then this degrades to today's behaviour
                    # (recorded as a passing [SKIP] claim), which is why the N/A
                    # status is still enforced independently here for printing and
                    # last-green, regardless of what evidence.py does with it.
                    add_kwargs["na"] = True
                res["evidence_id"] = evidence.add_verify_entry(project, **add_kwargs)
            except (evidence.EvidenceError, OSError, ValueError) as exc:
                res["status"] = "ERROR"
                res["reason"] = f"evidence for {domain}/{skill} not recorded: {exc}"
                print(f"forge verify: evidence for {domain}/{skill} not recorded: {exc}", file=sys.stderr)
    return results


def _record_last_green(toml_data: dict[str, Any], project: Path, results: list[dict[str, Any]],
                       fast: bool) -> list[str]:
    """Set last-green for every domain whose every entrypoint ran here, in
    full mode and without a --changed scope, and passed -- or was N/A (D1:
    nothing to check is not a failure).

    A domain whose entrypoints are *all* N/A is deliberately excluded: an
    empty domain (no inputs at all) has nothing green to cite. Without this,
    a domain nobody ever put a file into would get last-green recorded from
    ``forge verify --all`` on a bare scaffold, and that SHA could then be
    misread elsewhere as "this domain was verified" when nothing was."""
    if fast:
        return []
    head = _head(project)
    if not head:
        return []
    green: list[str] = []
    domains = {b.get("domain") for b in toml_data.get("verify", []) if b.get("domain")}
    for domain in sorted(domains):
        needed = {(domain, ep) for b in toml_data.get("verify", []) if b.get("domain") == domain
                  for ep in b.get("entrypoints", [])}
        ran = {(r["domain"], r["skill"]): r for r in results if r.get("domain") == domain}
        if not needed or set(ran) != needed:
            continue
        statuses = {r["status"] for r in ran.values()}
        if statuses - {"PASS", "NA"}:
            continue  # any FAIL/ERROR (or an entrypoint that didn't run): never green
        if "PASS" not in statuses:
            continue  # every entrypoint was N/A: nothing was actually verified (D1)
        if not all(r.get("evidence_id") for r in ran.values()):
            continue
        state.set_last_green(project, domain, sha=head,
                             evidence_ids=[r["evidence_id"] for r in ran.values()])
        green.append(domain)
    return green


_PRINT_LABELS = {"NA": "N/A"}  # internal status -> printed label (D1: never printed as PASS)


def _print_report(results: list[dict[str, Any]]) -> None:
    if not results:
        print("[SKIP] forge verify: nothing matched (no [[verify]] blocks, or nothing under --changed)")
        return
    for r in results:
        label = _PRINT_LABELS.get(r["status"], r["status"])
        line = f"[{label}] {r.get('domain', '?')}/{r['skill']} ({r.get('rung', '?')})"
        if r.get("reason"):
            line += f" -- {r['reason']}"
        print(line)
        if r["status"] == "FAIL" and r.get("stdout"):
            for out_line in r["stdout"].splitlines():
                if out_line.strip():
                    print(f"    {out_line}")


def run(ns: argparse.Namespace, forge_root: Path) -> int:
    project = Path(ns.project).resolve()
    plugin_root = forge_root / "plugins" / "forge"
    try:
        toml_data = _load_forge_toml(project)
    except VerifyError as exc:
        print(f"forge verify: {exc}", file=sys.stderr)
        return 2

    changed = ns.changed
    if not ns.all and changed is None:
        print("forge verify: neither --all nor --changed given; defaulting to --all")
        changed = None

    forge_python = _forge_python(forge_root)
    results = _run_blocks(toml_data, plugin_root=plugin_root, forge_python=forge_python,
                           project=project, changed=changed, fast=ns.fast)
    _print_report(results)
    if changed is None:
        green = _record_last_green(toml_data, project, results, ns.fast)
        if green:
            print(f"forge verify: last-green recorded for {', '.join(green)}")

    if any(r["status"] == "ERROR" for r in results):
        return 2
    if any(r["status"] == "FAIL" for r in results):
        return 1
    return 0
