"""Forge session state (``.forge/state.json``, CONTRACTS.md §13, schema ``forge.state/1``).

A product repo's ``.forge/state.json`` is gitignored, host-local state shared
by the Stop hook (the evidence gate, plus its consecutive-block counter), the
PreCompact hook (state snapshot) and SessionStart (re-injection on
``compact``, and the printed gate/drift summary). It holds:

- ``gate``: the current stage gate (mirrors ``forge.toml`` ``project.gate``).
- ``stop_block_count``: consecutive Stop-hook blocks without a passing gate,
  reset to 0 whenever the evidence gate passes (ADR-001 D5, R1a §18 "block cap").
- ``last_green``: per domain, the git SHA (or ``dirty`` marker) and timestamp
  of the last passing evidence check, so the Stop hook can tell whether files
  changed *since* that point.
- ``open_findings``: reviewer findings with verdict != PASS, carried forward
  by PreCompact so they survive compaction (R1a §14 "rules... are lost at
  compaction").
- ``modified_files`` / ``failing_checks``: the PreCompact snapshot.

Standard library only.
"""

from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any

SCHEMA = "forge.state/1"
STATE_REL_PATH = Path(".forge/state.json")

__all__ = [
    "SCHEMA",
    "STATE_REL_PATH",
    "state_path",
    "default_state",
    "load",
    "save",
    "record_stop_block",
    "reset_stop_block",
    "set_last_green",
    "write_precompact_snapshot",
    "compact_summary_text",
]


def state_path(project: Path | str) -> Path:
    return Path(project) / STATE_REL_PATH


def default_state() -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "gate": None,
        "stop_block_count": 0,
        "last_green": {},
        "open_findings": [],
        "modified_files": [],
        "failing_checks": [],
        "updated": None,
    }


def load(project: Path | str) -> dict[str, Any]:
    """Read state, tolerating a missing or corrupt file (never raises)."""
    path = state_path(project)
    data = default_state()
    if not path.exists():
        return data
    try:
        raw = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return data
    if not isinstance(raw, dict) or raw.get("schema") != SCHEMA:
        return data
    data.update(raw)
    return data


def save(project: Path | str, data: dict[str, Any]) -> None:
    """Atomic write; creates ``.forge/`` if needed."""
    data = dict(data)
    data["schema"] = SCHEMA
    data["updated"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    path = state_path(project)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    with os.fdopen(fd, "w") as fh:
        fh.write(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    os.replace(tmp, path)


def record_stop_block(project: Path | str, *, reason: str | None = None) -> int:
    """Increment the consecutive-block counter and persist it. Returns the new count."""
    data = load(project)
    data["stop_block_count"] = int(data.get("stop_block_count") or 0) + 1
    if reason:
        data["last_block_reason"] = reason
    save(project, data)
    return data["stop_block_count"]


def reset_stop_block(project: Path | str) -> None:
    data = load(project)
    if data.get("stop_block_count"):
        data["stop_block_count"] = 0
        data.pop("last_block_reason", None)
        save(project, data)


def set_last_green(project: Path | str, domain: str, *, sha: str) -> None:
    data = load(project)
    last_green = dict(data.get("last_green") or {})
    last_green[domain] = {"sha": sha, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    data["last_green"] = last_green
    save(project, data)


def write_precompact_snapshot(
    project: Path | str,
    *,
    modified_files: list[str],
    open_findings: list[dict[str, Any]],
    gate: str | None,
    failing_checks: list[str],
) -> dict[str, Any]:
    """Write the full state snapshot a PreCompact hook is required to produce."""
    data = load(project)
    data["modified_files"] = list(modified_files)
    data["open_findings"] = list(open_findings)
    data["failing_checks"] = list(failing_checks)
    if gate is not None:
        data["gate"] = gate
    save(project, data)
    return data


def compact_summary_text(project: Path | str, *, max_chars: int = 2000) -> str:
    """A short human-readable summary for SessionStart's ``compact`` re-injection."""
    data = load(project)
    lines = ["Forge state (restored after compaction):"]
    if data.get("gate"):
        lines.append(f"- gate: {data['gate']}")
    if data.get("modified_files"):
        shown = data["modified_files"][:10]
        more = len(data["modified_files"]) - len(shown)
        suffix = f" (+{more} more)" if more > 0 else ""
        lines.append(f"- modified files: {', '.join(shown)}{suffix}")
    if data.get("failing_checks"):
        lines.append(f"- failing checks: {', '.join(data['failing_checks'][:10])}")
    if data.get("open_findings"):
        lines.append(f"- open findings: {len(data['open_findings'])}")
    if data.get("stop_block_count"):
        lines.append(f"- consecutive Stop blocks: {data['stop_block_count']}")
    text = "\n".join(lines)
    if len(text) > max_chars:
        text = text[: max_chars - 3] + "..."
    return text
