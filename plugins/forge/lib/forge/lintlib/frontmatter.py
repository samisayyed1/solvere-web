"""Minimal stdlib YAML-subset parser for agent/skill frontmatter.

Real YAML is not used anywhere in Forge (CONTRACTS.md SS11: hooks and the
``forge`` CLI are Python-standard-library only, and pulling in PyYAML just
for frontmatter would break that). This parser handles exactly the
constructs Forge's own agent and skill frontmatter use:

- scalar strings, optionally single- or double-quoted;
- booleans (``true``/``false``, ``True``/``False``);
- inline lists (``key: [a, b, c]``);
- block lists (``key:`` followed by indented ``- item`` lines);
- a value spread across commas and/or whitespace (``tools: Read, Grep``
  or ``allowed-tools: Bash(cmd *) Read``), respecting parentheses so a
  ``Bash(git push *)``-style grant stays one token.

It is deliberately narrow. Anything outside this subset raises
:class:`FrontmatterError` rather than silently guessing.
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "FrontmatterError",
    "split_frontmatter",
    "parse_frontmatter",
    "as_list",
    "split_tool_tokens",
]


class FrontmatterError(ValueError):
    """Frontmatter is missing, unterminated, or outside the supported subset."""


def split_frontmatter(text: str) -> tuple[str, str]:
    """Return ``(frontmatter_yaml, body)``.

    Raises :class:`FrontmatterError` if the file doesn't open with a
    ``---`` delimiter on the very first line, or the block is never closed.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise FrontmatterError("file does not start with a '---' frontmatter delimiter on line 1")
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            fm = "\n".join(lines[1:i])
            body = "\n".join(lines[i + 1 :])
            return fm, body
    raise FrontmatterError("frontmatter opened with '---' but never closed with a second '---' line")


def _strip_quotes(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        return s[1:-1]
    return s


def _coerce_scalar(s: str) -> Any:
    s = s.strip()
    if s in ("true", "True"):
        return True
    if s in ("false", "False"):
        return False
    return _strip_quotes(s)


def _parse_inline_list(s: str) -> list[Any]:
    inner = s.strip()
    inner = inner[1:-1]  # strip [ ]
    if not inner.strip():
        return []
    return [_coerce_scalar(p) for p in inner.split(",")]


def parse_frontmatter(fm_text: str) -> dict[str, Any]:
    """Parse the narrow YAML subset described above into a ``dict``.

    Raises :class:`FrontmatterError` on anything it can't confidently
    interpret (multi-level nesting, flow mappings, anchors, ...) rather
    than silently dropping data a lint rule would otherwise need.
    """
    result: dict[str, Any] = {}
    lines = fm_text.splitlines()
    i = 0
    n = len(lines)
    while i < n:
        raw = lines[i]
        if not raw.strip() or raw.lstrip().startswith("#"):
            i += 1
            continue
        if raw[:1] in (" ", "\t"):
            raise FrontmatterError(f"unexpected indented line outside a block list: {raw!r}")
        if ":" not in raw:
            raise FrontmatterError(f"malformed frontmatter line (no ':'): {raw!r}")
        key, _, rest = raw.partition(":")
        key = key.strip()
        rest = rest.strip()
        if not key:
            raise FrontmatterError(f"empty key in line: {raw!r}")
        if not rest:
            # Either a block list on the following indented '- ' lines, or
            # an empty/omitted value.
            items: list[Any] = []
            j = i + 1
            while j < n and lines[j][:1] in (" ", "\t") and lines[j].strip().startswith("-"):
                item = lines[j].strip()[1:].strip()
                items.append(_coerce_scalar(item))
                j += 1
            result[key] = items
            i = j
            continue
        if rest.startswith("[") and rest.endswith("]"):
            result[key] = _parse_inline_list(rest)
        else:
            result[key] = _coerce_scalar(rest)
        i += 1
    return result


def split_tool_tokens(s: str) -> list[str]:
    """Split a tools-like string on commas/whitespace outside parentheses.

    ``"Bash(git push *) Read, Grep"`` -> ``["Bash(git push *)", "Read", "Grep"]``.
    Used for fields R1a documents as "comma- or space-separated" (``tools``,
    ``allowed-tools``) so a ``Bash(cmd *)`` grant survives as one token.
    """
    tokens: list[str] = []
    depth = 0
    current: list[str] = []
    for ch in s:
        if ch == "(":
            depth += 1
            current.append(ch)
        elif ch == ")":
            depth = max(0, depth - 1)
            current.append(ch)
        elif depth == 0 and (ch == "," or ch.isspace()):
            if current:
                tokens.append("".join(current).strip())
                current = []
        else:
            current.append(ch)
    if current:
        tokens.append("".join(current).strip())
    return [t for t in tokens if t]


def as_list(value: Any) -> list[str]:
    """Normalize a parsed frontmatter value to a list of strings.

    Handles the three shapes a tools-like field can take once parsed:
    already a list (block or inline list), a plain scalar string (comma-
    and/or space-separated), or absent/boolean (-> ``[]``).
    """
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, bool):
        return []
    return split_tool_tokens(str(value))
