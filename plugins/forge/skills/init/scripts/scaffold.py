#!/usr/bin/env python3
"""Add Forge to an EXISTING repository, non-destructively.

Usage:
    scaffold.py [target-dir] [--name "Project Name"] [--forge-root PATH]
                [--templates PATH]

Standard library only (Python 3.12+). See plugins/forge/skills/init/SKILL.md.

Rules (never negotiable, per CONTRACTS.md and the brief):
- **Never overwrite an existing file.** Any `templates/project/` file that
  already exists at the destination is left untouched and reported as a
  conflict for the human to reconcile by hand.
- **`.gitignore` is merged, not skipped or overwritten**: lines from the
  template that are missing from the existing file are appended.
- Directories are created as needed even when their files are skipped.
- Nothing here ever deletes or truncates a file that already exists.
- The repo is ``git init``-ed if needed, and exactly the files Forge wrote
  or merged are committed as the Forge baseline (never the user's other
  uncommitted work): the Stop hook's evidence gate diffs against it.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SCRIPT = Path(__file__).resolve()
_SKILL_DIR = _SCRIPT.parent.parent            # plugins/forge/skills/init
_PLUGIN_ROOT = _SKILL_DIR.parent.parent        # plugins/forge
_DEFAULT_FORGE_ROOT = _PLUGIN_ROOT.parent.parent  # repo root
_DEFAULT_TEMPLATES = _DEFAULT_FORGE_ROOT / "templates" / "project"
sys.path.insert(0, str(_PLUGIN_ROOT / "lib"))
from forge.gitbaseline import BaselineError, ensure_baseline  # noqa: E402
from forge.template_files import list_template_files  # noqa: E402

_PLACEHOLDER_NAME = "{{PROJECT_NAME}}"
_PLACEHOLDER_ROOT = "${FORGE_ROOT}"

_TEXT_SUFFIXES = {".md", ".json", ".toml", ".sysml", ".yml", ".yaml", ".py", ""}
_TEXT_NAMES = {"Makefile", ".gitignore", ".gitkeep"}

_MERGE_FILES = {".gitignore"}


class InitError(Exception):
    pass


def _is_text_file(path: Path) -> bool:
    return path.suffix in _TEXT_SUFFIXES or path.name in _TEXT_NAMES


def _substitute(text: str, *, name: str, forge_root: Path) -> str:
    return text.replace(_PLACEHOLDER_NAME, name).replace(_PLACEHOLDER_ROOT, str(forge_root))


def _merge_gitignore(src: Path, dst: Path) -> int:
    """Append lines from ``src`` that ``dst`` doesn't already have. Returns the count added."""
    existing_lines = dst.read_text(encoding="utf-8").splitlines() if dst.exists() else []
    existing_set = {line.strip() for line in existing_lines if line.strip() and not line.strip().startswith("#")}
    new_lines = src.read_text(encoding="utf-8").splitlines()
    to_add = [line for line in new_lines if line.strip() and not line.strip().startswith("#")
              and line.strip() not in existing_set]
    if not to_add:
        return 0
    dst.parent.mkdir(parents=True, exist_ok=True)
    with dst.open("a", encoding="utf-8") as fh:
        if existing_lines and existing_lines[-1].strip() != "":
            fh.write("\n")
        fh.write("# --- added by /forge:init ---\n")
        for line in to_add:
            fh.write(line + "\n")
    return len(to_add)


class InitReport:
    def __init__(self) -> None:
        self.written: list[Path] = []
        self.conflicts: list[Path] = []
        self.merged: dict[Path, int] = {}
        self.baseline: str | None = None

    def render(self, target: Path) -> str:
        lines = [f"forge init: {target}", ""]
        lines.append(f"Written ({len(self.written)} new file(s)):")
        for p in self.written:
            lines.append(f"  + {p.relative_to(target)}")
        if self.merged:
            lines.append("")
            lines.append("Merged:")
            for p, n in self.merged.items():
                lines.append(f"  ~ {p.relative_to(target)} ({n} line(s) added)")
        if self.conflicts:
            lines.append("")
            lines.append(f"Conflicts -- left untouched, review by hand ({len(self.conflicts)}):")
            for p in self.conflicts:
                lines.append(f"  ! {p.relative_to(target)}")
        else:
            lines.append("")
            lines.append("No conflicts.")
        return "\n".join(lines)


def init(target: Path, *, name: str | None = None, forge_root: Path = _DEFAULT_FORGE_ROOT,
         templates_dir: Path = _DEFAULT_TEMPLATES, commit: bool = True) -> InitReport:
    if not templates_dir.is_dir():
        raise InitError(f"template directory not found: {templates_dir}")
    if not (templates_dir / "CLAUDE.md").exists():
        raise InitError(f"{templates_dir} does not look like templates/project (no CLAUDE.md)")
    target.mkdir(parents=True, exist_ok=True)

    project_name = name or target.name
    report = InitReport()

    # D3 (review #2): only files the template actually tracks (or, outside
    # git, that aren't in the generated/cache exclude list) are ever copied
    # -- never out/, __pycache__/, .pytest_cache/ etc. See lib/forge/template_files.py.
    for rel in list_template_files(templates_dir):
        src = templates_dir / rel
        dst = target / rel
        dst.parent.mkdir(parents=True, exist_ok=True)

        if src.name in _MERGE_FILES:
            added = _merge_gitignore(src, dst)
            if added:
                report.merged[dst] = added
            continue

        if dst.exists():
            report.conflicts.append(dst)
            continue

        if _is_text_file(src):
            text = src.read_text(encoding="utf-8")
            dst.write_text(_substitute(text, name=project_name, forge_root=forge_root), encoding="utf-8")
        else:
            dst.write_bytes(src.read_bytes())
        report.written.append(dst)

    if commit:
        paths = list(report.written) + list(report.merged)
        if paths:
            try:
                report.baseline = ensure_baseline(target, "Add Forge (forge init)", paths=paths)
            except BaselineError as exc:
                raise InitError(f"Forge files were written, but the git baseline commit failed: {exc}. "
                                "Commit the files listed above by hand; the Stop hook's evidence gate "
                                "needs that baseline.") from exc
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="init scaffold")
    parser.add_argument("target", type=Path, nargs="?", default=Path("."),
                         help="existing repo root to add Forge to (default: cwd)")
    parser.add_argument("--name", default=None, help="project display name (default: target dir name)")
    parser.add_argument("--forge-root", type=Path, default=_DEFAULT_FORGE_ROOT,
                         help="absolute path to the Forge repo (default: auto-detected)")
    parser.add_argument("--templates", type=Path, default=_DEFAULT_TEMPLATES,
                         help="path to templates/project (default: auto-detected)")
    parser.add_argument("--no-commit", action="store_true",
                        help="skip git init and the Forge baseline commit")
    ns = parser.parse_args(argv)

    forge_root = ns.forge_root.resolve()
    templates_dir = ns.templates.resolve()
    target = ns.target.resolve()

    try:
        report = init(target, name=ns.name, forge_root=forge_root, templates_dir=templates_dir,
                      commit=not ns.no_commit)
    except InitError as exc:
        print(f"forge init: {exc}", file=sys.stderr)
        return 1

    print(report.render(target))
    if report.baseline:
        print(f"\nCommitted the Forge files as baseline {report.baseline[:12]}.")
    if report.conflicts:
        print()
        print("Nothing was overwritten. Reconcile each conflict by hand, "
              "e.g. diff the template's version against yours.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
