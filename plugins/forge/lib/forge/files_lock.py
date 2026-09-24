"""File-integrity locking for Forge's own attack surface (BUILD item 1.d).

docs/research/R6 section 9: "Forge's own `.claude/**` files are an attack
surface for other tools too (Cursor CVE-2026-48124 ran hooks from
`.claude/settings.local.json`)." This module hashes an explicit set of
files -- `.claude/**`, Forge's own hooks and settings -- and lets
``forge doctor`` fail closed the moment any of them changes outside a
reviewed ``forge lock files --write``.

The tracked file set lives *in* ``security/files-lock.json`` itself: once
written, a plain ``forge lock files --write`` re-hashes exactly the
files already recorded there (a refresh after a reviewed change). Before
anything has been recorded, it falls back to scanning a small set of
default locations relative to the repo root, skipping any that don't
exist -- which is why a freshly-created lock with nothing installed yet
is legitimately empty.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

from .checks import CheckResult

__all__ = [
    "FILES_LOCK_SCHEMA",
    "DEFAULT_PROTECTED_GLOBS",
    "sha256_file",
    "discover_default_paths",
    "load_lock",
    "write_lock",
    "run_file_checks",
]

FILES_LOCK_SCHEMA = 1

#: Relative-to-repo-root glob patterns scanned when the lock has no
#: previously-recorded file set to refresh.
DEFAULT_PROTECTED_GLOBS = (
    ".claude/**/*",
    ".claude-plugin/**/*",
    "plugins/forge/.claude-plugin/**/*",
    "plugins/forge/hooks/**/*",
    "plugins/forge/bin/**/*",
)

_CHUNK_SIZE = 1024 * 1024


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(_CHUNK_SIZE)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def discover_default_paths(repo_root: Path) -> list[Path]:
    found: list[Path] = []
    for pattern in DEFAULT_PROTECTED_GLOBS:
        for path in sorted(repo_root.glob(pattern)):
            if path.is_file():
                found.append(path)
    return found


def _entry_for(repo_root: Path, path: Path) -> tuple[str, dict[str, Any]]:
    rel = path.relative_to(repo_root).as_posix()
    return rel, {"sha256": sha256_file(path), "size": path.stat().st_size}


def load_lock(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schema": FILES_LOCK_SCHEMA, "generated_at": None, "files": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path} is not valid JSON: {exc}") from exc


def _atomic_write_json(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    tmp = path.with_suffix(path.suffix + f".{os.getpid()}.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def write_lock(
    repo_root: Path, lock_path: Path, *, paths: list[Path] | None = None
) -> dict[str, Any]:
    """(Re-)hash ``paths`` (default: the previously-tracked set, or the
    default globs if nothing is tracked yet) and write ``lock_path``."""
    if paths is None:
        existing = load_lock(lock_path)
        if existing.get("files"):
            paths = [repo_root / rel for rel in existing["files"]]
        else:
            paths = discover_default_paths(repo_root)

    files: dict[str, Any] = {}
    for path in sorted(set(paths)):
        if not path.exists() or not path.is_file():
            continue
        rel, entry = _entry_for(repo_root, path)
        files[rel] = entry

    lock_obj = {
        "schema": FILES_LOCK_SCHEMA,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "files": files,
    }
    _atomic_write_json(lock_path, lock_obj)
    return lock_obj


def run_file_checks(repo_root: Path, lock_path: Path) -> list[CheckResult]:
    try:
        lock_obj = load_lock(lock_path)
    except ValueError as exc:
        return [
            CheckResult(
                id="files_lock",
                status="fail",
                rule="security/files-lock.json must be valid JSON.",
                measured=str(exc),
                expected="valid JSON matching the files-lock schema",
                fix=f"fix or regenerate {lock_path}.",
            )
        ]

    tracked = lock_obj.get("files", {}) or {}
    if not tracked:
        return [
            CheckResult(
                id="files_lock",
                status="warn",
                rule="security/files-lock.json should track Forge's own .claude/**, hooks and settings.",
                measured="<no files tracked>",
                expected="one or more tracked files",
                fix="once those files exist, a human should run `forge lock files --write`.",
            )
        ]

    results: list[CheckResult] = []
    for rel in sorted(tracked):
        expected_entry = tracked[rel]
        path = repo_root / rel
        check_id = f"file:{rel}"
        rule = f"{rel} must match the sha256 recorded in security/files-lock.json."
        if not path.is_file():
            results.append(
                CheckResult(
                    id=check_id,
                    status="fail",
                    rule=rule,
                    measured="<missing>",
                    expected=expected_entry.get("sha256"),
                    fix=(
                        f"restore {rel}, or if its removal is intentional, a human must "
                        "run `forge lock files --write`."
                    ),
                )
            )
            continue
        actual_sha256 = sha256_file(path)
        if actual_sha256 != expected_entry.get("sha256"):
            results.append(
                CheckResult(
                    id=check_id,
                    status="fail",
                    rule=rule,
                    measured=actual_sha256,
                    expected=expected_entry.get("sha256"),
                    fix=(
                        f"if this change to {rel} is expected, a human (never an agent) must "
                        "review it and run `forge lock files --write`; otherwise revert it."
                    ),
                )
            )
            continue
        results.append(
            CheckResult(id=check_id, status="pass", rule=rule, measured=actual_sha256, expected=expected_entry.get("sha256"))
        )
    return results
