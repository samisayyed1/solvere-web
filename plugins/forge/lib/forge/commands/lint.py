"""``forge lint``: static hygiene checks for agents, skills, CLAUDE.md,
evidence-level wording and the plugin manifest (CONTRACTS.md SS11-13).

Auto-discovered by :mod:`forge.cli` (CONTRACTS SS11): this module defines
``NAME``, ``HELP``, ``register(parser)`` and ``run(ns, forge_root) -> int``.
Rule logic itself lives in :mod:`forge.lintlib`, one module per rule
family, so each subcommand here is a thin dispatcher.

Every subcommand exits 0 if nothing failed (``skip``/``warn`` don't block)
and 1 if any rule failed -- never a silent 0 on an unexpected error, since
an uncaught exception here propagates up to :func:`forge.cli.main`'s
fail-closed wrapper, which reports exit 2.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from ..checks import CheckResult, format_report, summarize
from ..lintlib import agents as agents_lint
from ..lintlib import claudemd as claudemd_lint
from ..lintlib import manifest as manifest_lint
from ..lintlib import skills as skills_lint
from ..lintlib import wording as wording_lint

NAME = "lint"
HELP = "static hygiene checks: agents, skills, claudemd, wording, manifest"

_TARGETS = ("agents", "skills", "claudemd", "wording", "manifest", "all")


def register(parser: argparse.ArgumentParser) -> None:
    sub = parser.add_subparsers(dest="lint_target", required=True)

    p_agents = sub.add_parser("agents", help="lint agents/*.md frontmatter (CONTRACTS SS12)")
    p_agents.add_argument("dir", nargs="?", default=None, type=Path, help="default: plugins/forge/agents")

    p_skills = sub.add_parser("skills", help="lint skills/<name>/SKILL.md (CONTRACTS SS12-13)")
    p_skills.add_argument("dir", nargs="?", default=None, type=Path, help="default: plugins/forge/skills")

    p_claudemd = sub.add_parser("claudemd", help="lint CLAUDE.md line counts (brief SS3.1)")
    p_claudemd.add_argument(
        "paths", nargs="*", type=Path, help="default: templates/project/CLAUDE.md and repo-root CLAUDE.md"
    )

    p_wording = sub.add_parser(
        "wording", help="lint validated/certified/production-ready wording (CONTRACTS SS4)"
    )
    p_wording.add_argument(
        "paths", nargs="*", type=Path, help="files or dirs to scan; default: reviews/, docs/, release/, root *.md"
    )

    sub.add_parser("manifest", help="lint plugin.json / marketplace.json (ADR-001 SS3)")
    sub.add_parser("all", help="run every lint rule for the Forge repo")


def _print(results: list[CheckResult]) -> int:
    print(format_report(results))
    return 1 if summarize(results)["fail"] > 0 else 0


def _run_agents(dir_arg: Path | None, forge_root: Path) -> list[CheckResult]:
    directory = dir_arg if dir_arg is not None else (forge_root / "plugins" / "forge" / "agents")
    return agents_lint.lint_agents_dir(directory)


def _run_skills(dir_arg: Path | None, forge_root: Path) -> list[CheckResult]:
    directory = dir_arg if dir_arg is not None else (forge_root / "plugins" / "forge" / "skills")
    return skills_lint.lint_skills_dir(directory)


def _run_claudemd(paths_arg: list[Path] | None, forge_root: Path) -> list[CheckResult]:
    paths = paths_arg or [
        forge_root / "templates" / "project" / "CLAUDE.md",
        forge_root / "CLAUDE.md",
    ]
    return claudemd_lint.lint_claudemd(paths)


def _run_wording(paths_arg: list[Path] | None, forge_root: Path) -> list[CheckResult]:
    if paths_arg:
        paths = wording_lint.collect_markdown_files(paths_arg)
    else:
        paths = wording_lint.default_scope(forge_root)
    return wording_lint.lint_wording(paths)


def _run_manifest(forge_root: Path) -> list[CheckResult]:
    plugin_root = forge_root / "plugins" / "forge"
    return manifest_lint.lint_manifest(plugin_root, forge_root)


def run(ns: argparse.Namespace, forge_root: Path) -> int:
    target = ns.lint_target
    if target == "agents":
        return _print(_run_agents(ns.dir, forge_root))
    if target == "skills":
        return _print(_run_skills(ns.dir, forge_root))
    if target == "claudemd":
        return _print(_run_claudemd(ns.paths, forge_root))
    if target == "wording":
        return _print(_run_wording(ns.paths, forge_root))
    if target == "manifest":
        return _print(_run_manifest(forge_root))
    if target == "all":
        results: list[CheckResult] = []
        results += _run_agents(None, forge_root)
        results += _run_skills(None, forge_root)
        results += _run_claudemd(None, forge_root)
        results += _run_wording(None, forge_root)
        results += _run_manifest(forge_root)
        return _print(results)
    raise ValueError(f"unknown lint target {target!r} (expected one of {_TARGETS})")
