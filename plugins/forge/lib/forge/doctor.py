"""`forge doctor` orchestration (BUILD item 1.a-d).

Runs, in order:

a. Claude Code version floor (terminal CLI, plus any Desktop-bundled CLI
   found) -- :mod:`forge.version_check`.
b. Pinned-tool checks from the toolchain manifest -- :mod:`forge.toolcheck`.
c. MCP server definition lock checks -- :mod:`forge.lock`.
d. Forge's own file-integrity lock -- :mod:`forge.files_lock`.

The CLI wrapper (:mod:`forge.cli`) is what makes this fail closed: any
exception escaping :func:`run_doctor` is caught there and reported as
exit code 2, never a silent pass.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from . import files_lock, lock, toolcheck, version_check
from .checks import CheckResult, format_report, summarize

__all__ = ["DoctorReport", "run_doctor"]


@dataclass
class DoctorReport:
    results: list[CheckResult]

    @property
    def exit_code(self) -> int:
        return 1 if summarize(self.results)["fail"] > 0 else 0

    def to_dict(self) -> dict:
        return {
            "results": [r.to_dict() for r in self.results],
            "summary": summarize(self.results),
            "exit_code": self.exit_code,
        }

    def render_text(self) -> str:
        return format_report(self.results)

    def render_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


def run_doctor(
    *,
    repo_root: Path,
    quick: bool = False,
    manifest_path: Path | None = None,
    mcp_lock_path: Path | None = None,
    mcp_servers_path: Path | None = None,
    files_lock_path: Path | None = None,
    terminal_binary: str = "claude",
    home: Path | None = None,
    tool_timeout: float = 20.0,
    mcp_timeout: float = 20.0,
) -> DoctorReport:
    manifest_path = manifest_path or (repo_root / "plugins/forge/toolchain/manifest.json")
    mcp_lock_path = mcp_lock_path or (repo_root / "security/mcp-lock.json")
    mcp_servers_path = mcp_servers_path or (repo_root / "security/mcp-servers.json")
    files_lock_path = files_lock_path or (repo_root / "security/files-lock.json")

    results: list[CheckResult] = []
    results.extend(
        version_check.run_version_floor_checks(
            terminal_binary=terminal_binary, home=home, timeout=tool_timeout
        )
    )
    results.extend(toolcheck.run_tool_checks(manifest_path, timeout=tool_timeout))
    results.extend(
        lock.run_mcp_checks(mcp_servers_path, mcp_lock_path, timeout=mcp_timeout, quick=quick)
    )
    results.extend(files_lock.run_file_checks(repo_root, files_lock_path))
    return DoctorReport(results=results)
