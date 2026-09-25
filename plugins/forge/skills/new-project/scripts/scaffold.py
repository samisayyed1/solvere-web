#!/usr/bin/env python3
"""Scaffold a new Forge product-engineering project from templates/project/.

Usage:
    scaffold.py <target-dir> [--name "Project Name"] [--no-commit]
                [--forge-root PATH] [--templates PATH] [--skip-doctor]

The new project is always a git repository with one baseline commit
(``git init`` if needed, then commit everything scaffolded): the Stop hook's
evidence gate diffs against that commit until the first green
``forge verify`` (lib/forge/gitbaseline.py).

Standard library only (Python 3.12+). See plugins/forge/skills/new-project/SKILL.md.

Refuses to scaffold into a directory that already has files in it -- this
tool only ever creates a fresh project. To add Forge to an existing repo,
use `/forge:init` instead (plugins/forge/skills/init/scripts/scaffold.py).
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

_SCRIPT = Path(__file__).resolve()
_SKILL_DIR = _SCRIPT.parent.parent            # plugins/forge/skills/new-project
_PLUGIN_ROOT = _SKILL_DIR.parent.parent        # plugins/forge
sys.path.insert(0, str(_PLUGIN_ROOT / "lib"))
from forge.gitbaseline import BaselineError, ensure_baseline  # noqa: E402
_DEFAULT_FORGE_ROOT = _PLUGIN_ROOT.parent.parent  # repo root
_DEFAULT_TEMPLATES = _DEFAULT_FORGE_ROOT / "templates" / "project"

_PLACEHOLDER_NAME = "{{PROJECT_NAME}}"
_PLACEHOLDER_ROOT = "${FORGE_ROOT}"

# Extensions we treat as text and run substitution on. Everything in
# templates/project/ is text; this allowlist is a safety net if a binary
# asset is ever added.
_TEXT_SUFFIXES = {
    ".md", ".json", ".toml", ".sysml", ".yml", ".yaml", ".py", "",
}
_TEXT_NAMES = {"Makefile", ".gitignore", ".gitkeep"}


class ScaffoldError(Exception):
    """A user-facing scaffold failure (bad target, bad templates dir, ...)."""


def _is_text_file(path: Path) -> bool:
    return path.suffix in _TEXT_SUFFIXES or path.name in _TEXT_NAMES


def _substitute(text: str, *, name: str, forge_root: Path) -> str:
    return text.replace(_PLACEHOLDER_NAME, name).replace(_PLACEHOLDER_ROOT, str(forge_root))


def _copy_and_substitute(templates_dir: Path, target: Path, *, name: str, forge_root: Path) -> list[Path]:
    written: list[Path] = []
    for src in sorted(templates_dir.rglob("*")):
        rel = src.relative_to(templates_dir)
        dst = target / rel
        if src.is_dir():
            dst.mkdir(parents=True, exist_ok=True)
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        if _is_text_file(src):
            text = src.read_text(encoding="utf-8")
            dst.write_text(_substitute(text, name=name, forge_root=forge_root), encoding="utf-8")
        else:
            shutil.copyfile(src, dst)
        written.append(dst)
    return written


def scaffold(
    target: Path,
    *,
    name: str | None = None,
    git_init: bool = True,
    forge_root: Path = _DEFAULT_FORGE_ROOT,
    templates_dir: Path = _DEFAULT_TEMPLATES,
) -> list[Path]:
    """Copy templates/project/ into ``target``, substituted, and return the written files.

    Raises :class:`ScaffoldError` if ``target`` exists and is not empty, or if
    ``templates_dir`` does not look like a Forge project template.
    """
    if not templates_dir.is_dir():
        raise ScaffoldError(f"template directory not found: {templates_dir}")
    if not (templates_dir / "CLAUDE.md").exists():
        raise ScaffoldError(f"{templates_dir} does not look like templates/project (no CLAUDE.md)")

    if target.exists():
        if not target.is_dir():
            raise ScaffoldError(f"{target} exists and is not a directory")
        if any(target.iterdir()):
            raise ScaffoldError(
                f"refusing to scaffold into non-empty directory {target}; "
                "choose an empty or new directory, or use /forge:init for an existing repo"
            )
    else:
        target.mkdir(parents=True)

    project_name = name or target.name
    written = _copy_and_substitute(templates_dir, target, name=project_name, forge_root=forge_root)

    if git_init:
        try:
            ensure_baseline(target, f"Scaffold Forge project {project_name} from templates/project")
        except BaselineError as exc:
            raise ScaffoldError(f"files were scaffolded, but the git baseline commit failed: {exc}. "
                                "Run `git init && git add -A && git commit -m scaffold` in the project; "
                                "the Stop hook's evidence gate needs that baseline.") from exc

    return written


def _run_doctor_quick(forge_root: Path) -> None:
    """Report `forge doctor --quick`; never fail the scaffold on its result."""
    forge_bin = forge_root / "plugins" / "forge" / "bin" / "forge"
    if not forge_bin.exists():
        print(f"[SKIP] forge doctor --quick: {forge_bin} not found", file=sys.stderr)
        return
    try:
        result = subprocess.run(
            [sys.executable, str(forge_bin), "doctor", "--quick"],
            capture_output=True, text=True, timeout=60,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"[WARN] could not run forge doctor --quick: {exc}", file=sys.stderr)
        return
    print("\n--- forge doctor --quick ---")
    print(result.stdout.strip())
    if result.stderr.strip():
        print(result.stderr.strip(), file=sys.stderr)
    if result.returncode != 0:
        print("[WARN] forge doctor --quick reported issues above -- this does not fail scaffolding.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="new-project scaffold")
    parser.add_argument("target", type=Path, help="directory to scaffold the new project into")
    parser.add_argument("--name", default=None, help="project display name (default: target dir name)")
    parser.add_argument("--git-init", action="store_true",
                        help="accepted for compatibility; git init + a baseline commit now always happen")
    parser.add_argument("--no-commit", action="store_true",
                        help="skip git init and the baseline commit (tests/tooling only; Stop then treats every "
                             "file as changed until the first commit)")
    parser.add_argument("--forge-root", type=Path, default=_DEFAULT_FORGE_ROOT,
                         help="absolute path to the Forge repo (default: auto-detected)")
    parser.add_argument("--templates", type=Path, default=_DEFAULT_TEMPLATES,
                         help="path to templates/project (default: auto-detected)")
    parser.add_argument("--skip-doctor", action="store_true", help="skip the forge doctor --quick report")
    ns = parser.parse_args(argv)

    forge_root = ns.forge_root.resolve()
    templates_dir = ns.templates.resolve()
    target = ns.target.resolve()

    try:
        written = scaffold(target, name=ns.name, git_init=not ns.no_commit,
                            forge_root=forge_root, templates_dir=templates_dir)
    except ScaffoldError as exc:
        print(f"forge new-project: {exc}", file=sys.stderr)
        return 1

    print(f"Scaffolded {len(written)} files into {target}")
    print(f"  project name: {ns.name or target.name}")
    print(f"  FORGE_ROOT:   {forge_root}")
    print()
    print("Next steps:")
    print(f"  1. cd {target}")
    print("  2. Read CLAUDE.md and fill in requirements/requirements.md, model/system.sysml, params/params.toml")
    print("  3. Review .claude/settings.json and .mcp.json before running anything that touches hardware or a fab")
    print("  4. make doctor   # toolchain, MCP-lock and file-integrity checks")
    print("  5. make verify   # once there is something to verify")

    if not ns.skip_doctor:
        _run_doctor_quick(forge_root)

    return 0


if __name__ == "__main__":
    sys.exit(main())
