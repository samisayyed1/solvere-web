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

import subprocess
from pathlib import Path
from typing import Iterable

FALLBACK_NAME = "Forge scaffold"
FALLBACK_EMAIL = "forge-scaffold@localhost"


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
