"""``forge sync-template`` (D4, review #2 addendum).

Reports drift between a scaffolded project and the Forge template it was
scaffolded from (``templates/project/``), and -- with ``--write`` -- applies
it, but **only** to files the project has not touched since scaffold time.

``.forge/scaffold.json`` (written by both scaffolders, ``lib/forge/gitbaseline.py``
:func:`~forge.gitbaseline.write_scaffold_manifest`) records the sha256 of
every file's *scaffolded* (post-substitution) content. A file is:

- **new**: the current template has it, the project doesn't -- ``--write``
  adds it;
- **unmodified, drifted**: the project's file still hashes to what was
  scaffolded, but the current template would render something different --
  ``--write`` refreshes it (safe: nothing of the project's own is lost);
- **conflict**: the project's file no longer hashes to what was scaffolded
  (a human or agent edited it) *and* differs from what the template renders
  today -- never touched by ``--write``, always listed for a human to
  reconcile by hand;
- **up to date**: matches the current template render either way.

A project with no ``.forge/scaffold.json`` (scaffolded before D4, or the
file was removed) cannot be compared safely, so nothing is treated as safe
to write; every existing project file lists as a conflict alongside "no
scaffold manifest" in the report.

Standard library only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from .. import gitbaseline
from ..template_files import list_template_files

NAME = "sync-template"
HELP = "report (or --write apply) drift between a scaffolded project and its Forge template (D4)"

_PLACEHOLDER_NAME = "{{PROJECT_NAME}}"
_PLACEHOLDER_ROOT = "${FORGE_ROOT}"
_TEXT_SUFFIXES = {".md", ".json", ".toml", ".sysml", ".yml", ".yaml", ".py", ""}
_TEXT_NAMES = {"Makefile", ".gitignore", ".gitkeep"}


def register(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--project", type=Path, default=Path("."), help="scaffolded project root (default: cwd)")
    parser.add_argument("--templates", type=Path, default=None,
                        help="path to templates/project to compare against (default: the scaffold manifest's, "
                             "or <forge-root>/templates/project)")
    parser.add_argument("--write", action="store_true",
                        help="apply drifted/new files (never touches a conflict); updates .forge/scaffold.json")
    parser.add_argument("--json", action="store_true")


def _is_text_file(path: Path) -> bool:
    return path.suffix in _TEXT_SUFFIXES or path.name in _TEXT_NAMES


def _render(src: Path, *, name: str, forge_root: str) -> bytes:
    if _is_text_file(src):
        text = src.read_text(encoding="utf-8")
        return text.replace(_PLACEHOLDER_NAME, name).replace(_PLACEHOLDER_ROOT, forge_root).encode("utf-8")
    return src.read_bytes()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def diff(project: Path, *, templates_dir: Path | None, forge_root: Path) -> dict[str, Any]:
    """Compute the drift report. Never raises for an ordinary missing-manifest
    or missing-templates-dir case (reported instead); returns
    ``{"error": "..."}`` only for that.
    """
    project = Path(project).resolve()
    manifest = gitbaseline.read_scaffold_manifest(project)
    recorded_files: dict[str, str] = dict((manifest or {}).get("files") or {})
    project_name = (manifest or {}).get("project_name") or project.name
    manifest_forge_root = (manifest or {}).get("forge_root")

    tpl_dir = templates_dir
    if tpl_dir is None:
        recorded_tpl = (manifest or {}).get("templates_dir")
        tpl_dir = Path(recorded_tpl) if recorded_tpl else (Path(forge_root) / "templates" / "project")
    tpl_dir = Path(tpl_dir).resolve()

    if not tpl_dir.is_dir() or not (tpl_dir / "CLAUDE.md").exists():
        return {"error": f"{tpl_dir} does not look like templates/project (no CLAUDE.md)"}

    render_root = manifest_forge_root or str(Path(forge_root).resolve())

    new_files: list[str] = []
    drifted: list[str] = []
    conflicts: list[str] = []
    up_to_date: list[str] = []
    removed_from_template: list[str] = []

    current_template_files = set()
    for rel in list_template_files(tpl_dir):
        rel_s = rel.as_posix()
        current_template_files.add(rel_s)
        src = tpl_dir / rel
        expected = _sha256(_render(src, name=project_name, forge_root=render_root))
        dst = project / rel
        scaffolded_hash = recorded_files.get(rel_s)

        if not dst.is_file():
            new_files.append(rel_s)
            continue

        try:
            current_hash = _sha256(dst.read_bytes())
        except OSError:
            conflicts.append(rel_s)
            continue

        if current_hash == expected:
            up_to_date.append(rel_s)
        elif scaffolded_hash is not None and current_hash == scaffolded_hash:
            drifted.append(rel_s)  # unmodified since scaffold, template moved on: safe to refresh
        else:
            conflicts.append(rel_s)  # edited since scaffold (or no manifest to prove otherwise)

    removed_from_template = sorted(set(recorded_files) - current_template_files)

    return {
        "templates_dir": str(tpl_dir),
        "has_manifest": manifest is not None,
        "new": sorted(new_files),
        "drifted": sorted(drifted),
        "conflicts": sorted(conflicts),
        "up_to_date": sorted(up_to_date),
        "removed_from_template": removed_from_template,
        "_render_params": {"project_name": project_name, "forge_root": render_root, "templates_dir": str(tpl_dir)},
    }


def apply_write(project: Path, report: dict[str, Any]) -> list[str]:
    """Write ``new`` and ``drifted`` files from the current template, and
    record their new hashes in the scaffold manifest. Never touches a
    conflict. Returns the paths written."""
    project = Path(project).resolve()
    params = report["_render_params"]
    tpl_dir = Path(params["templates_dir"])
    written: list[str] = []
    new_hashes: dict[str, str] = {}
    for rel_s in report["new"] + report["drifted"]:
        src = tpl_dir / rel_s
        content = _render(src, name=params["project_name"], forge_root=params["forge_root"])
        dst = project / rel_s
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(content)
        new_hashes[rel_s] = _sha256(content)
        written.append(rel_s)
    if new_hashes:
        gitbaseline.update_scaffold_manifest(project, files=new_hashes)
    return written


def _render_text_report(report: dict[str, Any], *, wrote: list[str] | None) -> str:
    lines = [f"forge sync-template: comparing against {report['templates_dir']}"]
    if not report["has_manifest"]:
        lines.append("WARNING: no .forge/scaffold.json (scaffolded before D4, or it was removed); "
                     "nothing can be proven unmodified, so every differing file below is a conflict.")
    if wrote is not None:
        lines.append(f"Wrote {len(wrote)} file(s): " + (", ".join(wrote) if wrote else "(none)"))
    else:
        if report["new"]:
            lines.append(f"New in the template ({len(report['new'])}, --write would add):")
            lines += [f"  + {p}" for p in report["new"]]
        if report["drifted"]:
            lines.append(f"Drifted, unmodified since scaffold ({len(report['drifted'])}, --write would refresh):")
            lines += [f"  ~ {p}" for p in report["drifted"]]
    if report["conflicts"]:
        lines.append(f"Conflicts -- edited since scaffold, never auto-written ({len(report['conflicts'])}):")
        lines += [f"  ! {p}" for p in report["conflicts"]]
    if report["removed_from_template"]:
        lines.append(f"No longer in the template (left alone): {', '.join(report['removed_from_template'])}")
    if not (report["new"] or report["drifted"] or report["conflicts"]):
        lines.append(f"Up to date ({len(report['up_to_date'])} file(s)).")
    return "\n".join(lines)


def run(ns: argparse.Namespace, forge_root: Path) -> int:
    project = ns.project.resolve()
    if not project.is_dir():
        print(f"forge sync-template: {project} is not a directory", file=sys.stderr)
        return 2
    templates_dir = ns.templates.resolve() if ns.templates else None
    report = diff(project, templates_dir=templates_dir, forge_root=forge_root)
    if "error" in report:
        print(f"forge sync-template: {report['error']}", file=sys.stderr)
        return 2

    wrote = apply_write(project, report) if ns.write else None

    if ns.json:
        payload = dict(report)
        payload.pop("_render_params", None)
        if wrote is not None:
            payload["wrote"] = wrote
        print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
    else:
        print(_render_text_report(report, wrote=wrote))

    if report["conflicts"]:
        return 1
    if not ns.write and (report["new"] or report["drifted"]):
        return 1  # drift exists, not yet applied
    return 0
