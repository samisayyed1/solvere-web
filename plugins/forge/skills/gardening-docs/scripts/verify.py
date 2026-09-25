#!/usr/bin/env python3
"""gardening-docs verify entrypoint (CONTRACTS.md §9, docs domain: links).

    forge-python skills/gardening-docs/scripts/verify.py --project <root> [--changed <path> ...] [--fast]

Three checks over every ``*.md`` under the project (excluding ``out/``, ``release/``,
``node_modules/``, ``.git/``):

1. **Broken relative links and anchors** (``gardening.links``): every inline Markdown
   link `[text](path#anchor)` whose `path` isn't `http(s)://`/`mailto:` must resolve to a
   real file relative to the linking document, and if it has a `#anchor`, that anchor must
   match a heading in the target (GitHub-style slug: lowercase, spaces -> `-`, strip
   anything not alnum/`-`/`_`). A same-document `#anchor` link is checked the same way.
2. **Stale tool versions** (``gardening.tool_versions``): a doc can pin a tool version
   inline with `<!-- forge-tool-version: <id> <version> -->`; this check compares it
   against `plugins/forge/toolchain/manifest.json`'s pinned version for that tool id and
   flags a mismatch or an unknown id.
3. **Rules with no stated enforcing mechanism** (``gardening.rule_mechanisms``): every
   top-level bullet in `.claude/rules/*.md` must either name what enforces it (hook, lint,
   check, gate, "enforced") per ADR-001 §13 point 6 ("every rule that matters has a hook,
   permission or lint counterpart"), or say explicitly that it is advisory-only (the word
   "advisory"). A bullet naming neither is flagged -- silently unstated enforcement is
   exactly what this check exists to catch. A bullet that claims a real mechanism must
   still name one of the actual words; writing "advisory" on a bullet that is genuinely
   enforced elsewhere just moves the failure from "missing mechanism" to "misdescribed
   mechanism" for a human to catch in review, so authors are pushed to cite the true
   mechanism, not to paper over the gap.

This script only *proposes* fixes (SKILL.md); it never edits a doc itself.
No `*.md` files found -> exit 0, `[SKIP] ...`.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lib"))

from forge.checkresult import Check  # noqa: E402

PLUGIN_ROOT = Path(__file__).resolve().parents[3]  # plugins/forge
EXCLUDE_DIRS = {"out", "release", "node_modules", ".git", "__pycache__", ".pytest_cache"}

# Inline links/images: "!" (image) is optional, captured so callers can tell
# a missing image from a missing link.
_MD_LINK_INLINE = re.compile(r"(!?)\[([^\]]*)\]\(([^)\s]+)\)")
# Reference-style links/images: "[text][ref]", "![alt][ref]", and the
# shortcut form "[text][]" / "![alt][]" (ref label == text/alt). S5: these
# were never resolved at all.
_MD_LINK_REF = re.compile(r"(!?)\[([^\]]*)\]\[([^\]]*)\]")
_MD_REF_DEF = re.compile(r"^\[([^\]]+)\]:\s*(\S+)", re.MULTILINE)
_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
_TOOL_VERSION_MARKER = re.compile(r"<!--\s*forge-tool-version:\s*([\w.-]+)\s+([\w.+-]+)\s*-->")
_RULE_BULLET = re.compile(r"^- (.+)$", re.MULTILINE)
_MECHANISM_WORDS = re.compile(r"\b(hook|lint|check|gate|enforced|enforc|advisory)\w*\b", re.IGNORECASE)


def find_markdown_files(project: Path) -> list[Path]:
    out = []
    for p in project.rglob("*.md"):
        if any(part in EXCLUDE_DIRS for part in p.relative_to(project).parts[:-1]):
            continue
        out.append(p)
    return sorted(out)


def filter_by_changed(files: list[Path], project: Path, changed: list[str] | None) -> list[Path]:
    if changed is None:
        return files
    changed_resolved = {Path(c).resolve() for c in changed}
    if not any(str(c).endswith(".md") for c in changed_resolved):
        # a non-.md change (e.g. toolchain/manifest.json) can still make tool-version
        # checks stale, so re-run everything rather than narrowing to nothing
        if any(Path(c).name == "manifest.json" for c in changed_resolved):
            return files
        return []
    return [f for f in files if f.resolve() in changed_resolved]


def slugify(heading: str) -> str:
    heading = re.sub(r"[`*_]", "", heading)  # strip common markdown emphasis/code markers
    slug = re.sub(r"[^\w\- ]", "", heading.lower()).strip().replace(" ", "-")
    return re.sub(r"-{2,}", "-", slug)


def anchors_in(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {slugify(m.group(2)) for m in _HEADING.finditer(path.read_text(errors="ignore"))}


def _ref_defs(text: str) -> dict[str, str]:
    """Reference-style link/image definitions ("[ref]: target"), keyed by
    the normalised (lowercased, trimmed) label -- CommonMark label matching
    is case-insensitive."""
    return {m.group(1).strip().lower(): m.group(2) for m in _MD_REF_DEF.finditer(text)}


def _check_target(md: Path, project: Path, target: str, link_repr: str,
                   broken: list[dict[str, Any]], *, is_image: bool) -> None:
    kind = "image" if is_image else "link"
    if target.startswith(("http://", "https://", "mailto:", "//")):
        return
    path_part, _, anchor = target.partition("#")
    if path_part == "":
        # same-document anchor
        if anchor and slugify(anchor) not in anchors_in(md):
            broken.append({"file": str(md.relative_to(project)), "link": link_repr,
                           "reason": f"no heading matching #{anchor} in this document"})
        return
    resolved = (md.parent / path_part).resolve()
    if not resolved.exists():
        broken.append({"file": str(md.relative_to(project)), "link": link_repr,
                       "reason": f"{path_part} does not exist relative to {md.parent} ({kind})"})
        return
    if anchor and resolved.suffix == ".md" and slugify(anchor) not in anchors_in(resolved):
        broken.append({"file": str(md.relative_to(project)), "link": link_repr,
                       "reason": f"no heading matching #{anchor} in {path_part}"})


def check_links(md_files: list[Path], project: Path) -> list[dict[str, Any]]:
    broken = []
    for md in md_files:
        text = md.read_text(errors="ignore")
        refs = _ref_defs(text)

        # Inline links "[text](url)" and images "![alt](url)".
        for bang, _label, target in _MD_LINK_INLINE.findall(text):
            _check_target(md, project, target, f"{bang}[...]({target})", broken, is_image=bool(bang))

        # Reference-style links "[text][ref]"/"[text][]" and images
        # "![alt][ref]"/"![alt][]" (S5).
        for bang, label, ref_label in _MD_LINK_REF.findall(text):
            key = (ref_label or label).strip().lower()
            link_repr = f"{bang}[{label}][{ref_label}]"
            if key not in refs:
                broken.append({"file": str(md.relative_to(project)), "link": link_repr,
                               "reason": f"reference [{ref_label or label}] has no "
                                         "[ref]: target definition in this document"})
                continue
            _check_target(md, project, refs[key], link_repr, broken, is_image=bool(bang))
    return broken


def check_tool_versions(md_files: list[Path], project: Path) -> list[dict[str, Any]]:
    manifest_path = PLUGIN_ROOT / "toolchain" / "manifest.json"
    if not manifest_path.exists():
        return []
    manifest = json.loads(manifest_path.read_text())
    pinned = {t["id"]: t["version"] for t in manifest.get("tools", [])}
    stale = []
    for md in md_files:
        for m in _TOOL_VERSION_MARKER.finditer(md.read_text(errors="ignore")):
            tool_id, doc_version = m.group(1), m.group(2)
            if tool_id not in pinned:
                stale.append({"file": str(md.relative_to(project)), "tool": tool_id, "doc_version": doc_version,
                             "reason": f"{tool_id!r} is not in plugins/forge/toolchain/manifest.json"})
            elif pinned[tool_id] != doc_version:
                stale.append({"file": str(md.relative_to(project)), "tool": tool_id, "doc_version": doc_version,
                             "reason": f"doc says {doc_version}, manifest pins {pinned[tool_id]}"})
    return stale


def check_rule_mechanisms(project: Path) -> list[dict[str, Any]]:
    rules_dir = project / ".claude" / "rules"
    if not rules_dir.exists():
        return []
    unenforced = []
    for rule_file in sorted(rules_dir.glob("*.md")):
        text = rule_file.read_text(errors="ignore")
        for m in _RULE_BULLET.finditer(text):
            bullet = m.group(1)
            if not _MECHANISM_WORDS.search(bullet):
                unenforced.append({"file": str(rule_file.relative_to(project)),
                                   "bullet": bullet[:80],
                                   "reason": "no hook/lint/check/gate/enforced/advisory mentioned"})
    return unenforced


def main(argv: list[str]) -> int:
    # Declares this entrypoint's check_id namespace so PostToolUse can bind a
    # fix message to the check that owns it, by check_id rather than which
    # out/verify/*.json file happens to have the newest mtime (M7, review #1).
    print("[FORGE_CHECK_ID_PREFIX] gardening.docs")
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True, type=Path)
    ap.add_argument("--changed", nargs="*", default=None)
    ap.add_argument("--fast", action="store_true")
    ns = ap.parse_args(argv)
    project = ns.project.resolve()

    all_files = find_markdown_files(project)
    md_files = filter_by_changed(all_files, project, ns.changed)
    if not md_files:
        suffix = " matching --changed" if ns.changed is not None else ""
        print(f"[SKIP] no *.md files{suffix}")
        return 0

    chk = Check("gardening.docs", f"{len(md_files)} markdown file(s)", project=project, level="L1")
    try:
        broken_links = check_links(md_files, project)
        chk.measure(
            "broken_links", len(broken_links), "1", max=0,
            remediation="; ".join(f"{b['file']}: {b['link']} ({b['reason']})" for b in broken_links[:10])
            or "no broken links",
        )
        stale_versions = check_tool_versions(md_files, project)
        chk.measure(
            "stale_tool_versions", len(stale_versions), "1", max=0,
            remediation="; ".join(f"{s['file']}: {s['tool']} ({s['reason']})" for s in stale_versions[:10])
            or "no stale versions",
        )
        unenforced_rules = check_rule_mechanisms(project)
        chk.measure(
            "unenforced_rule_bullets", len(unenforced_rules), "1", max=0,
            remediation="; ".join(f"{r['file']}: \"{r['bullet']}\" ({r['reason']})" for r in unenforced_rules[:10])
            or "every rule bullet names a mechanism",
        )
        return chk.finish()
    except Exception as exc:  # noqa: BLE001 -- fail closed
        return chk.error(f"{type(exc).__name__}: {exc}")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
