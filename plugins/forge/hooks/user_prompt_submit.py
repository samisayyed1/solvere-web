#!/usr/bin/env python3
"""UserPromptSubmit: lightweight keyword -> skill suggestion (brief §3.4).

Never blocks: it only ever exits 0. When the prompt contains a keyword
associated with a Forge skill, it prints a short **plain-text** line to
stdout (not JSON) -- R1a §17 is explicit that plain stdout becomes
additional context only for UserPromptSubmit, UserPromptExpansion,
SessionStart and PostModelSwitch, so this is the simplest, best-attested
way to add a pointer here without guessing at an undocumented
``hookSpecificOutput`` shape for this event.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import find_project_root, truncate  # noqa: E402

MAX_CONTEXT_CHARS = 1500
MAX_SUGGESTIONS = 3

# Keyword -> skill (plugins/forge/skills/<name>, brief §3.3). Checked as a
# case-insensitive substring of the prompt; order is insertion order, so
# more specific keywords are listed before broader ones where they overlap.
KEYWORD_SKILLS: dict[str, str] = {
    "ears": "writing-requirements",
    "requirement": "writing-requirements",
    "stakeholder": "interviewing-stakeholders",
    "sysml": "modeling-systems",
    "systems model": "modeling-systems",
    "traceability": "tracing-requirements",
    "trace matrix": "tracing-requirements",
    "architecture decision": "writing-adrs",
    "write an adr": "writing-adrs",
    "concept tournament": "exploring-concepts",
    "brainstorm concepts": "exploring-concepts",
    "datasheet": "intaking-datasheets",
    "build123d": "modeling-cad-parts",
    "snap-fit": "modeling-cad-parts",
    "min wall": "verifying-geometry",
    "wall thickness": "verifying-geometry",
    "bounding box": "verifying-geometry",
    "render pack": "inspecting-renders",
    "exploded view": "inspecting-renders",
    "dfm": "checking-dfm",
    "manufacturab": "checking-dfm",
    "gd&t": "stacking-tolerances",
    "tolerance stack": "stacking-tolerances",
    "techdraw": "drafting-drawings",
    "drawing pdf": "drafting-drawings",
    "gmsh": "running-fea",
    "calculix": "running-fea",
    "convergence study": "running-fea",
    "ngspice": "designing-circuits",
    "schematic": "designing-circuits",
    "kicad-cli": "checking-ecad",
    "erc/drc": "checking-ecad",
    "renode": "building-firmware",
    "firmware": "building-firmware",
    "hil test": "testing-on-hardware",
    "hardware-in-the-loop": "testing-on-hardware",
    "stpa": "analyzing-risk",
    "dfmea": "analyzing-risk",
    "hazard analysis": "analyzing-risk",
    "compliance": "mapping-compliance",
    "pre-scan": "mapping-compliance",
    "bom": "costing-bom",
    "mpn": "costing-bom",
    "gate review": "reviewing-designs",
    "red-team": "reviewing-designs",
    "release bundle": "releasing-designs",
    "fab export": "releasing-designs",
    "root cause": "capturing-failures",
    "gardening-docs": "gardening-docs",
    "stale doc": "gardening-docs",
}


def _matches(prompt_lower: str) -> list[str]:
    matched: list[str] = []
    for keyword, skill in KEYWORD_SKILLS.items():
        if keyword in prompt_lower and skill not in matched:
            matched.append(skill)
        if len(matched) >= MAX_SUGGESTIONS:
            break
    return matched


def handle(data: dict) -> tuple[int, dict | None]:
    project = find_project_root(data.get("cwd"))
    if project is None:
        return 0, None  # not a Forge product repo: no-op fast (brief §3.4)

    prompt = (data.get("prompt") or "").lower()
    if not prompt:
        return 0, None

    matched = _matches(prompt)
    if not matched:
        return 0, None

    suggestions = ", ".join(f"/forge:{s}" for s in matched)
    text = f"Forge: this prompt may relate to {suggestions}. Not required -- only a pointer."
    print(truncate(text, MAX_CONTEXT_CHARS))
    return 0, None


if __name__ == "__main__":
    from _failclosed import run_hook
    run_hook(handle)
