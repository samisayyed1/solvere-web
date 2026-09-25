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
from .commands import sync_template

__all__ = ["DoctorReport", "run_doctor"]


def _template_drift_check(repo_root: Path, project_dir: Path) -> CheckResult:
    """D4: warn when the current working directory is a scaffolded product
    project whose files have drifted from (or conflict with) the Forge
    template it was scaffolded from. ``skip`` when it isn't one -- most
    ``forge doctor`` runs are not inside a product project at all."""
    check_id = "template:drift"
    rule = "a scaffolded project should not silently drift from its Forge template (run `forge sync-template`)."
    from . import gitbaseline
    if not (project_dir / "forge.toml").is_file():
        return CheckResult(id=check_id, status="skip", rule=rule,
                           detail=f"{project_dir} is not a Forge product project (no forge.toml)")
    if not gitbaseline.scaffold_manifest_path(project_dir).is_file():
        return CheckResult(id=check_id, status="skip", rule=rule,
                           detail="no .forge/scaffold.json (scaffolded before D4, or it was removed); "
                                  "`forge sync-template` cannot tell drift from an intentional edit here")
    try:
        report = sync_template.diff(project_dir, templates_dir=None, forge_root=repo_root)
    except Exception as exc:  # noqa: BLE001 -- a doctor check must never raise
        return CheckResult(id=check_id, status="warn", rule=rule, measured=f"{type(exc).__name__}: {exc}",
                           fix="run `forge sync-template` directly to see the full error.")
    if "error" in report:
        return CheckResult(id=check_id, status="warn", rule=rule, measured=report["error"],
                           fix="pass --templates to `forge sync-template`, or fix the template path.")
    drift = len(report["new"]) + len(report["drifted"])
    conflicts = len(report["conflicts"])
    if not drift and not conflicts:
        return CheckResult(id=check_id, status="pass", rule=rule, measured="up to date")
    return CheckResult(
        id=check_id, status="warn", rule=rule,
        measured=f"{drift} new/changed, {conflicts} conflicting file(s)",
        expected="no drift",
        fix="run `forge sync-template` for the full report; `--write` applies new/changed files that were "
            "never edited since scaffold (conflicts are always left for a human to reconcile).",
    )


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
    project_dir: Path | None = None,
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
    # D4: only meaningful when `forge doctor` is run from inside a
    # scaffolded product project (the common case: `make doctor` there).
    results.append(_template_drift_check(repo_root, project_dir or Path.cwd()))
    return DoctorReport(results=results)
