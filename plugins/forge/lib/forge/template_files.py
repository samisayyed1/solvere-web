"""Which files of ``templates/project/`` a scaffolder should copy (D3, review #2).

``templates/project/`` can pick up gitignored or generated files during
development (``out/``, ``__pycache__/``, ``.pytest_cache/`` ...): a stray
``out/verify/*.json`` left over from someone running ``forge verify`` inside
the template tree is not part of the template, but a naive ``rglob("*")``
copies it into every new project anyway (review #2, D3).

:func:`list_template_files` is the single source of truth both scaffolders
(``skills/new-project`` and ``skills/init``) use to decide what to copy:

- when ``templates_dir`` is inside a git work tree, it is exactly
  ``git ls-files`` (tracked files) plus any untracked-but-not-ignored files,
  via the same ``git ls-files -z --cached --others --exclude-standard`` call
  ``evidence.project_files`` uses elsewhere -- so a template file only ever
  ships once it is actually committed or deliberately added, and anything
  ``.gitignore`` (or a generated dir like ``out/``) excludes never ships;
- outside a git work tree (e.g. a copied-out template with no ``.git``, or
  git not installed), falls back to an explicit exclude list
  (:data:`EXCLUDED_DIR_NAMES`, :data:`EXCLUDED_FILE_SUFFIXES`) so the same
  generated/cache paths are still never copied.

Standard library only.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

__all__ = ["EXCLUDED_DIR_NAMES", "EXCLUDED_FILE_SUFFIXES", "list_template_files"]

#: Directory (path-part) names that are never template content, wherever
#: they appear under templates_dir -- generated/cache output, not source.
EXCLUDED_DIR_NAMES = frozenset({
    "out", "__pycache__", ".pytest_cache", ".venv", "node_modules", ".git",
})

#: File suffixes that are never template content.
EXCLUDED_FILE_SUFFIXES = frozenset({".pyc", ".pyo"})

#: Exact file names that are never template content.
EXCLUDED_FILE_NAMES = frozenset({".DS_Store"})


def _is_excluded(rel: Path) -> bool:
    if any(part in EXCLUDED_DIR_NAMES for part in rel.parts):
        return True
    if rel.suffix in EXCLUDED_FILE_SUFFIXES or rel.name in EXCLUDED_FILE_NAMES:
        return True
    return False


def _git_tracked_or_untracked(templates_dir: Path) -> list[str] | None:
    """``git ls-files`` (tracked + untracked-not-ignored) relative to
    ``templates_dir``, or ``None`` if it isn't inside a usable git work tree."""
    try:
        res = subprocess.run(
            ["git", "-C", str(templates_dir), "rev-parse", "--is-inside-work-tree"],
            capture_output=True, text=True, timeout=10,
        )
        if res.returncode != 0 or res.stdout.strip() != "true":
            return None
        res = subprocess.run(
            ["git", "-C", str(templates_dir), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            capture_output=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if res.returncode != 0:
        return None
    names = sorted({n for n in res.stdout.decode("utf-8", "surrogateescape").split("\0") if n})
    return names


def list_template_files(templates_dir: Path) -> list[Path]:
    """Every file of ``templates_dir`` a scaffolder should copy, as paths
    relative to it, sorted. See the module docstring for the two strategies."""
    templates_dir = Path(templates_dir)
    tracked = _git_tracked_or_untracked(templates_dir)
    if tracked is not None:
        out = []
        for n in tracked:
            rel = Path(n)
            if _is_excluded(rel):
                continue
            if (templates_dir / rel).is_file():
                out.append(rel)
        return sorted(out)

    # No usable git repo: walk the tree and apply the explicit exclude list.
    out = []
    for p in sorted(templates_dir.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(templates_dir)
        if _is_excluded(rel):
            continue
        out.append(rel)
    return sorted(out)
