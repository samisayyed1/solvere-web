"""``forge trace [--project]`` -- requirement traceability graph (CONTRACTS.md §11).

Thin wrapper: the actual graph build and orphan/untested/dangling-evidence
checks live in ``skills/tracing-requirements/scripts/verify.py`` (the
skill's own entrypoint per CONTRACTS §9). Auto-discovered by
``lib/forge/cli.py`` -- never edit ``cli.py`` to add this.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

NAME = "trace"
HELP = "Requirement -> design -> test -> evidence graph (wraps tracing-requirements's verify.py)"

VERIFY_SCRIPT_REL = Path("plugins/forge/skills/tracing-requirements/scripts/verify.py")


def register(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--project", type=Path, default=Path("."), help="product repo root (default: cwd)")
    parser.add_argument("--changed", action="append", default=[], metavar="PATH",
                         help="limit the check to this changed path (repeatable)")
    parser.add_argument("--fast", action="store_true", help="fast mode, for PostToolUse hooks (<=30s)")


def run(ns: argparse.Namespace, forge_root: Path) -> int:
    verify_script = forge_root / VERIFY_SCRIPT_REL
    if not verify_script.exists():
        print(f"forge trace: verify script missing at {verify_script}", file=sys.stderr)
        return 2

    argv = [sys.executable, str(verify_script), "--project", str(Path(ns.project).resolve())]
    for changed_path in ns.changed:
        argv += ["--changed", changed_path]
    if ns.fast:
        argv.append("--fast")

    proc = subprocess.run(argv)
    return proc.returncode
