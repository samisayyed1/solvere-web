"""Give a freshly scaffolded Forge project a git baseline commit.

The Stop hook's evidence gate diffs every domain against its last-green SHA,
or, before the first green ``forge verify``, against the commit that added
``forge.toml`` (``forge.state.scaffold_base``). Without that commit every file
counts as changed and Stop blocks until ``forge verify --all`` has run, so
``/forge:new-project`` and ``/forge:init`` both end by committing what they
wrote (review #1, scaffold baseline).

Standard library only.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import time
from pathlib import Path
from typing import Any, Iterable

FALLBACK_NAME = "Forge scaffold"
FALLBACK_EMAIL = "forge-scaffold@localhost"

#: ``.forge/scaffold.json`` (D4): what a scaffolder wrote, so `forge
#: sync-template` can later tell an unmodified file (safe to refresh from
#: the current template) from one the project has since edited (a conflict,
#: never overwritten). Gitignored, like the rest of ``.forge/``.
SCAFFOLD_MANIFEST_REL = Path(".forge/scaffold.json")
SCAFFOLD_SCHEMA = "forge.scaffold/1"


def scaffold_manifest_path(target: Path | str) -> Path:
    return Path(target) / SCAFFOLD_MANIFEST_REL


def write_scaffold_manifest(target: Path, *, templates_dir: Path, written: Iterable[Path],
                            project_name: str, forge_root: Path) -> Path:
    """Record, for every file a scaffolder just wrote, its template-relative
    path and the sha256 of its scaffolded (post-substitution) content --
    plus ``project_name``/``forge_root`` (the substitution parameters), so a
    later ``forge sync-template`` can re-derive "what the template would
    write today" and compare. Returns the manifest path."""
    target = Path(target).resolve()
    files: dict[str, str] = {}
    for f in written:
        p = Path(f).resolve()
        try:
            rel = p.relative_to(target).as_posix()
        except ValueError:
            continue
        try:
            content = p.read_bytes()
        except OSError:
            continue
        files[rel] = hashlib.sha256(content).hexdigest()
    data: dict[str, Any] = {
        "schema": SCAFFOLD_SCHEMA,
        "scaffolded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "templates_dir": str(Path(templates_dir).resolve()),
        "forge_root": str(Path(forge_root).resolve()),
        "project_name": project_name,
        "files": files,
    }
    path = scaffold_manifest_path(target)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    return path


def read_scaffold_manifest(target: Path | str) -> dict[str, Any] | None:
    """The scaffold manifest, or ``None`` if there is none / it is unreadable
    (an older project scaffolded before D4, or a corrupt file -- never
    raises)."""
    path = scaffold_manifest_path(target)
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict) or data.get("schema") != SCAFFOLD_SCHEMA:
        return None
    return data


def update_scaffold_manifest(target: Path | str, *, files: dict[str, str]) -> None:
    """Merge new ``{rel_path: sha256}`` entries into the manifest after
    ``forge sync-template --write`` refreshes some files, so they read back
    as "unmodified since scaffold" (of the just-applied version) next time."""
    data = read_scaffold_manifest(target) or {
        "schema": SCAFFOLD_SCHEMA, "scaffolded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "templates_dir": "", "forge_root": "", "project_name": "", "files": {},
    }
    data["files"] = dict(data.get("files") or {}, **files)
    path = scaffold_manifest_path(target)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n")


class BaselineError(RuntimeError):
    """git is missing, or the baseline commit could not be made."""


def _git(target: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    try:
        res = subprocess.run(["git", "-C", str(target), *args], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as exc:
        raise BaselineError(f"git {' '.join(args[:2])} failed: {exc}") from exc
    if check and res.returncode != 0:
        raise BaselineError(f"git {' '.join(args[:2])} failed: {(res.stderr or res.stdout).strip()}")
    return res


def _identity_args(target: Path) -> list[str]:
    """Use the user's git identity; fall back to a neutral one only if none is set."""
    name = _git(target, "config", "user.name", check=False).stdout.strip()
    email = _git(target, "config", "user.email", check=False).stdout.strip()
    args: list[str] = []
    if not name:
        args += ["-c", f"user.name={FALLBACK_NAME}"]
    if not email:
        args += ["-c", f"user.email={FALLBACK_EMAIL}"]
    return args


def ensure_baseline(target: Path, message: str, *, paths: Iterable[Path] | None = None) -> str:
    """``git init`` ``target`` if it is not inside a work tree, then commit.

    ``paths=None`` commits everything in ``target`` (a brand-new project).
    Otherwise only ``paths`` are staged and committed, so an existing repo's
    unrelated uncommitted work is never swept into the baseline. Repository
    commit hooks are bypassed (``--no-verify``): this commit only records
    template files. Returns the new HEAD SHA.
    """
    target = Path(target).resolve()
    inside = _git(target, "rev-parse", "--is-inside-work-tree", check=False)
    if inside.returncode != 0 or inside.stdout.strip() != "true":
        _git(target, "init", "-q")
    if paths is None:
        _git(target, "add", "-A", "--", ".")
        pathspec: list[str] = []
    else:
        rels = [Path(p).resolve().relative_to(target).as_posix() for p in paths]
        ignored = set(_git(target, "check-ignore", "--", *rels, check=False).stdout.split("\n")) if rels else set()
        rels = [r for r in rels if r not in ignored]  # e.g. out/ is gitignored by the template
        if not rels:
            raise BaselineError("nothing to commit (every written file is gitignored)")
        _git(target, "add", "--", *rels)
        pathspec = ["--", *rels]
    _git(target, *_identity_args(target), "commit", "-q", "--no-verify", "-m", message, *pathspec)
    return _git(target, "rev-parse", "HEAD").stdout.strip()
