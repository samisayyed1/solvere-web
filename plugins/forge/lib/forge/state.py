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
import subprocess
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
    "resolve_base",
    "scaffold_base",
    "base_sha_path",
    "ensure_base_pinned",
    "changed_since",
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


def set_last_green(project: Path | str, domain: str, *, sha: str,
                   evidence_ids: list[str] | None = None) -> None:
    """Record ``sha`` (the HEAD a fully passing ``forge verify`` ran on) as the
    last green point of ``domain``. ``evidence_ids`` are the verify entries
    that proved it; :func:`resolve_base` only trusts a last-green SHA that
    those passing manifest entries vouch for."""
    data = load(project)
    last_green = dict(data.get("last_green") or {})
    last_green[domain] = {"sha": sha, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                          "evidence_ids": list(evidence_ids or [])}
    data["last_green"] = last_green
    save(project, data)


# ---------------------------------------------------------------------------
# git: the base the Stop gate diffs against (review #1, C2)
# ---------------------------------------------------------------------------

def _git(project: Path | str, *args: str) -> tuple[int, str]:
    try:
        res = subprocess.run(["git", "-c", "core.quotepath=off", "-C", str(project), *args], capture_output=True, text=True, timeout=10)
        return res.returncode, res.stdout
    except (OSError, subprocess.SubprocessError):
        return 128, ""


def _is_commit(project: Path | str, sha: str) -> bool:
    return bool(sha) and _git(project, "cat-file", "-e", f"{sha}^{{commit}}")[0] == 0


def _is_ancestor(project: Path | str, sha: str, of: str = "HEAD") -> bool:
    return _git(project, "merge-base", "--is-ancestor", sha, of)[0] == 0


def scaffold_base(project: Path | str) -> str | None:
    """The oldest commit that added ``forge.toml`` (the scaffold commit), or
    ``None`` when there is no such commit (no git, no commits yet)."""
    code, out = _git(project, "log", "--diff-filter=A", "--format=%H", "--", "forge.toml")
    shas = [line.strip() for line in out.splitlines() if line.strip()] if code == 0 else []
    return shas[-1] if shas else None


BASE_SHA_REL_PATH = Path(".forge/base_sha")


def base_sha_path(project: Path | str) -> Path:
    return Path(project) / BASE_SHA_REL_PATH


def ensure_base_pinned(project: Path | str) -> str | None:
    """The pinned scaffold-base commit SHA (N11).

    ``.forge/base_sha`` is a static anchor for the evidence gate and for
    PreToolUse's amend/reset guards, so they never have to trust *current*
    git history (which ``git commit --amend`` on the scaffold commit, or a
    reset to a fabricated root, can rewrite out from under them).

    Bootstraps the pin on first use -- when it has never been pinned before
    (tracked by ``base_sha_pinned`` in ``.forge/state.json``, not merely by
    whether ``.forge/`` exists, since other Forge state such as
    ``last_green`` can legitimately create that directory first): computes
    it once from :func:`scaffold_base` and writes it. Once it has been
    pinned, a missing ``base_sha`` file means it was deleted, and this
    returns ``None`` (fail closed) instead of silently re-deriving a fresh
    one from whatever git history says now.
    """
    path = base_sha_path(project)
    try:
        text = path.read_text().strip()
        if text:
            return text
    except OSError:
        pass
    data = load(project)
    if data.get("base_sha_pinned"):
        return None  # was pinned before; the file is gone now (removed)
    sha = scaffold_base(project)
    if sha:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(sha + "\n")
        data["base_sha_pinned"] = True
        save(project, data)
    return sha


def resolve_base(project: Path | str, domain: str, manifest: dict[str, Any] | None = None) -> str | None:
    """The commit the gate diffs ``domain`` against.

    The domain's last-green SHA when it is a real commit, an ancestor of
    HEAD, and vouched for by passing ``forge verify`` entries recorded on it;
    otherwise the **pinned** scaffold commit (``.forge/base_sha``, N11 --
    static, so it survives an amend or reset that rewrites current git
    history out from under a dynamically-derived base); otherwise ``None``
    (every file counts as changed).
    """
    info = (load(project).get("last_green") or {}).get(domain) or {}
    sha = str(info.get("sha") or "")
    ids = set(info.get("evidence_ids") or [])
    if sha and ids and manifest is not None and _is_commit(project, sha) and _is_ancestor(project, sha):
        entries = {e.get("id"): e for e in manifest.get("entries") or [] if isinstance(e, dict)}
        vouched = all(
            i in entries and entries[i].get("domain") == domain and entries[i].get("result") == "pass"
            and entries[i].get("status") == "VERIFIED" and entries[i].get("recorded_by") == "forge verify"
            and str(entries[i].get("git_sha", "")).startswith(sha)
            for i in ids)
        if vouched:
            return sha
    return ensure_base_pinned(project) or scaffold_base(project)


def changed_since(project: Path | str, base: str | None) -> list[str] | None:
    """Files (posix, relative to ``project``) that differ between ``base`` and
    the working tree -- committed, staged, unstaged, deleted and untracked
    (non-ignored). ``base=None`` means "everything is new". Returns ``None``
    when ``project`` is not in a git work tree."""
    code, _ = _git(project, "rev-parse", "--is-inside-work-tree")
    if code != 0:
        return None
    changed: set[str] = set()
    if base:
        code, out = _git(project, "diff", "--name-only", "--no-renames", "--relative", base, "--", ".")
        if code != 0:
            return None
        changed.update(line for line in out.splitlines() if line)
        code, out = _git(project, "ls-files", "--others", "--exclude-standard")
    else:
        code, out = _git(project, "ls-files", "--cached", "--others", "--exclude-standard")
    if code != 0:
        return None
    changed.update(line for line in out.splitlines() if line)
    return sorted(changed)


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
