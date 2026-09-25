"""``forge verify``: run domain verify entrypoints per ``forge.toml`` (CONTRACTS.md §9).

    forge verify [--all|--changed PATH...] [--project PATH] [--fast]

For each ``[[verify]]`` block in the product repo's ``forge.toml`` whose
``paths`` glob matches a changed file (or every block, under ``--all``), runs
each listed entrypoint as

    <forge-python> plugins/forge/skills/<skill>/scripts/verify.py \
        --project <root> [--changed <path> ...] [--fast]

in ladder order (the order the entrypoints are listed), aggregates the exit
codes (any ``ERROR`` -> 2, else any ``FAIL`` -> 1, else 0), and records one
evidence entry per domain via ``forge.evidence.add_from_checks`` over
whichever ``out/verify/*.json`` files the entrypoint(s) for that domain wrote
or touched during this run.

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
import fnmatch
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from .. import evidence

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
    return any(fnmatch.fnmatch(rel_path, pat) for pat in patterns)


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
    return {
        "skill": skill, "status": status, "returncode": proc.returncode,
        "stdout": proc.stdout, "stderr": proc.stderr, "check_files": touched, "reason": reason,
    }


def _evidence_domain(domain: str) -> str:
    # evidence.DOMAINS (CONTRACTS.md §4) has no "docs" entry -- forge.toml's docs blocks
    # (e.g. gardening-docs) record their evidence under "sys" rather than erroring.
    return domain if domain in evidence.DOMAINS else "sys"


def _run_blocks(toml_data: dict[str, Any], *, plugin_root: Path, forge_python: Path, project: Path,
                 changed: list[str] | None, fast: bool) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    blocks = sorted(toml_data.get("verify", []), key=lambda b: RUNG_ORDER.index(b.get("rung", "syntax"))
                     if b.get("rung") in RUNG_ORDER else len(RUNG_ORDER))
    for block in blocks:
        domain = block.get("domain", "?")
        patterns = block.get("paths", [])
        entrypoints = block.get("entrypoints", [])
        if changed is not None:
            rels = [Path(c).as_posix() for c in changed]
            if not any(_matches_any(r, patterns) for r in rels):
                continue
            run_changed = changed
        else:
            run_changed = None
        block_results = []
        for skill in entrypoints:
            res = _run_entrypoint(skill, plugin_root=plugin_root, forge_python=forge_python,
                                   project=project, changed=run_changed, fast=fast)
            res["domain"] = domain
            res["rung"] = block.get("rung", "?")
            block_results.append(res)
            results.append(res)
        check_files = [f for r in block_results for f in r.get("check_files", [])]
        if check_files:
            try:
                evidence.add_from_checks(
                    project, check_files, artifact=", ".join(entrypoints),
                    domain=_evidence_domain(domain),
                    claim=f"forge verify ({block.get('rung', '?')} rung) for domain {domain}",
                    model=os.environ.get("FORGE_MODEL"),
                )
            except evidence.EvidenceError as exc:
                print(f"forge verify: evidence for domain {domain} not recorded: {exc}", file=sys.stderr)
    return results


def _print_report(results: list[dict[str, Any]]) -> None:
    if not results:
        print("[SKIP] forge verify: nothing matched (no [[verify]] blocks, or nothing under --changed)")
        return
    for r in results:
        line = f"[{r['status']}] {r.get('domain', '?')}/{r['skill']} ({r.get('rung', '?')})"
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

    if any(r["status"] == "ERROR" for r in results):
        return 2
    if any(r["status"] == "FAIL" for r in results):
        return 1
    return 0
