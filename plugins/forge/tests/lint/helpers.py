"""Shared fixture-building helpers for plugins/forge/tests/lint/.

Not a test module itself (no ``test_`` prefix, so pytest won't collect it).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def render_frontmatter(fields: dict[str, Any]) -> str:
    """Render a dict into the narrow YAML subset ``forge.lintlib.frontmatter``
    parses: block lists for list values, bare true/false for bools, plain
    scalars otherwise. Mirrors plugins/forge/agents/*.md's own authoring style."""
    lines = ["---"]
    for key, value in fields.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {item}")
        elif isinstance(value, bool):
            lines.append(f"{key}: {'true' if value else 'false'}")
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines)


def write_agent(tmp_path: Path, filename: str, fields: dict[str, Any], body: str = "Role: test agent.\n") -> Path:
    d = tmp_path / "agents"
    d.mkdir(exist_ok=True)
    path = d / filename
    path.write_text(render_frontmatter(fields) + "\n\n" + body)
    return path


BASE_MAKER_FIELDS = {
    "name": "some-maker",
    "description": "x" * 90,
    "tools": ["Read", "Grep", "Glob", "Edit", "Write", "Bash"],
    "model": "sonnet",
    "effort": "high",
    "memory": "project",
}

BASE_JUDGE_FIELDS = {
    "name": "verification-evaluator",
    "description": "x" * 90,
    "tools": ["Read", "Grep", "Glob", "Bash"],
    "disallowedTools": ["Write", "Edit", "NotebookEdit", "Agent"],
    "model": "opus",
    "effort": "xhigh",
    "omitClaudeMd": True,
}


def write_skill(
    tmp_path: Path,
    name: str,
    fields: dict[str, Any] | None = None,
    body_lines: int = 10,
    references: dict[str, str] | None = None,
    verify_py: str | None = None,
) -> Path:
    skills_dir = tmp_path / "skills"
    skill_dir = skills_dir / name
    skill_dir.mkdir(parents=True, exist_ok=True)

    merged = {
        "name": name,
        "description": f"Does the {name} thing. Do not use for unrelated work.",
    }
    if fields:
        merged.update(fields)

    body = "\n".join(f"line {i}" for i in range(body_lines)) or " "
    (skill_dir / "SKILL.md").write_text(render_frontmatter(merged) + "\n\n" + body + "\n")

    if references:
        refs_dir = skill_dir / "references"
        refs_dir.mkdir(exist_ok=True)
        for rel, content in references.items():
            p = refs_dir / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content)

    if verify_py is not None:
        scripts_dir = skill_dir / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        (scripts_dir / "verify.py").write_text(verify_py)

    return skill_dir
