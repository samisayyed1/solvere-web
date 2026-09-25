"""The `forge` CLI: doctor, lock mcp, lock files.

Fail-closed by construction: :func:`main` wraps the whole dispatch in a
single ``try/except`` so that *any* unexpected exception -- a bug, a
malformed file, anything not already turned into a ``CheckResult`` by the
lower layers -- is reported as exit code 2, never a silent 0. Expected,
nameable failures (a version mismatch, drift, a missing lock entry) are
reported as ordinary ``fail`` check results and exit code 1; only the
unexpected case is 2.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from pathlib import Path

import importlib
import pkgutil

from . import checks, doctor, files_lock
from . import lock as lock_module
from . import commands as commands_pkg


def _plugin_commands() -> dict:
    """Discover ``forge.commands.<name>`` modules.

    Each module defines ``NAME``, ``HELP``, ``register(parser)`` and
    ``run(ns, forge_root) -> int``, so parallel builders add subcommands
    without editing this file. Project-scoped commands take ``--project``
    (default: the current directory).
    """
    found = {}
    for info in pkgutil.iter_modules(commands_pkg.__path__):
        if info.name.startswith("_"):
            continue
        mod = importlib.import_module(f"{commands_pkg.__name__}.{info.name}")
        found[mod.NAME] = mod
    return found

__all__ = ["main"]


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="forge")
    sub = parser.add_subparsers(dest="command", required=True)

    doctor_p = sub.add_parser("doctor", help="run all Forge health checks")
    doctor_p.add_argument("--quick", action="store_true", help="skip slow MCP probes")
    doctor_p.add_argument("--json", action="store_true", help="emit a JSON report")
    doctor_p.add_argument(
        "--manifest", type=Path, default=None, help="path to the toolchain manifest.json"
    )
    doctor_p.add_argument(
        "--lock", type=Path, default=None, help="path to security/mcp-lock.json"
    )

    lock_p = sub.add_parser("lock", help="human-run lock maintenance commands")
    lock_sub = lock_p.add_subparsers(dest="lock_command", required=True)

    lock_mcp_p = lock_sub.add_parser("mcp", help="probe MCP server(s) and print the canonical lock entry")
    lock_mcp_p.add_argument("--server", default=None, help="only this server id")
    lock_mcp_p.add_argument(
        "--write", action="store_true", help="update security/mcp-lock.json (human-run only)"
    )

    lock_files_p = lock_sub.add_parser("files", help="hash Forge's own protected files")
    lock_files_p.add_argument(
        "--write", action="store_true", help="update security/files-lock.json (human-run only)"
    )

    for name, mod in sorted(_plugin_commands().items()):
        mod.register(sub.add_parser(name, help=mod.HELP))

    return parser


def _cmd_doctor(ns: argparse.Namespace, repo_root: Path) -> int:
    report = doctor.run_doctor(
        repo_root=repo_root,
        quick=ns.quick,
        manifest_path=ns.manifest,
        mcp_lock_path=ns.lock,
    )
    print(report.render_json() if ns.json else report.render_text())
    return report.exit_code


def _cmd_lock_mcp(ns: argparse.Namespace, repo_root: Path) -> int:
    servers_path = repo_root / "security/mcp-servers.json"
    lock_path = repo_root / "security/mcp-lock.json"

    servers = lock_module.load_servers_config(servers_path)
    if ns.server:
        servers = [s for s in servers if s.id == ns.server]
        if not servers:
            print(f"forge lock mcp: no server {ns.server!r} in {servers_path}", file=sys.stderr)
            return 1

    existing = lock_module.load_lock(lock_path)
    servers_dict = dict(existing.get("servers") or {})
    had_error = False

    for config in servers:
        if config.pending_install:
            print(
                f"forge lock mcp: {config.id}: pending_install=true, skipping probe "
                "(no real launch command yet)"
            )
            continue
        try:
            entry = lock_module.probe_and_build_entry(config)
        except Exception as exc:  # noqa: BLE001 -- report per-server, keep going
            print(f"forge lock mcp: {config.id}: probe failed: {exc}", file=sys.stderr)
            had_error = True
            continue
        print(json.dumps(entry, indent=2, sort_keys=True, ensure_ascii=False))
        servers_dict[config.id] = entry

    if ns.write:
        new_lock = {
            "schema": lock_module.LOCK_SCHEMA,
            "generated_at": _now_iso(),
            "servers": servers_dict,
            "lock_hash": lock_module.compute_lock_hash(servers_dict),
        }
        lock_module.save_lock(lock_path, new_lock)
        print(f"forge lock mcp: wrote {lock_path}")
    else:
        print("forge lock mcp: dry run -- pass --write to update security/mcp-lock.json")
        print("forge lock mcp: only a human should run --write, never an agent.")

    return 1 if had_error else 0


def _cmd_lock_files(ns: argparse.Namespace, repo_root: Path) -> int:
    lock_path = repo_root / "security/files-lock.json"
    if not ns.write:
        results = files_lock.run_file_checks(repo_root, lock_path)
        print(checks.format_report(results))
        print("forge lock files: dry run -- pass --write to update security/files-lock.json")
        print("forge lock files: only a human should run --write, never an agent.")
        return 0
    lock_obj = files_lock.write_lock(repo_root, lock_path)
    print(f"forge lock files: wrote {lock_path} ({len(lock_obj['files'])} file(s) tracked)")
    return 0


def _dispatch(argv: list[str], repo_root: Path) -> int:
    parser = _build_parser()
    ns = parser.parse_args(argv)
    if ns.command == "doctor":
        return _cmd_doctor(ns, repo_root)
    if ns.command == "lock":
        if ns.lock_command == "mcp":
            return _cmd_lock_mcp(ns, repo_root)
        if ns.lock_command == "files":
            return _cmd_lock_files(ns, repo_root)
    plugin = _plugin_commands().get(ns.command)
    if plugin is not None:
        return int(plugin.run(ns, repo_root))
    parser.error(f"unknown command {ns.command!r}")
    return 2  # unreachable; parser.error() exits


def _default_repo_root() -> Path:
    # lib/forge/cli.py -> lib/forge -> lib -> plugins/forge -> plugins -> repo_root
    return Path(__file__).resolve().parents[4]


def main(argv: list[str] | None = None, *, repo_root: Path | None = None) -> int:
    """Entry point used by bin/forge. Fail closed: never returns 0 on an
    internal error, only on checks actually passing."""
    if repo_root is None:
        repo_root = _default_repo_root()
    try:
        return _dispatch(list(sys.argv[1:] if argv is None else argv), repo_root)
    except SystemExit:
        raise  # argparse's own --help / usage-error exits pass straight through
    except Exception as exc:  # noqa: BLE001 -- fail closed, see module docstring
        print(f"forge: internal error: {exc}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return 2
