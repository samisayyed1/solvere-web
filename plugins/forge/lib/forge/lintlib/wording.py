"""``forge lint wording`` (CONTRACTS.md SS4, ADR-001 D15): the evidence-level
wording rule. "Validated" needs an L4 or L5 citation on the same line;
"certified", "production-ready", "ready for production" and "prod-ready"
need L5. A claim is not flagged when
it's negated ("not validated", "never ... validated", "nothing ...
validated"), or sits inside a fenced code block or a blockquote (a quoted
rule, e.g. this very docstring's examples if it were markdown).
"""

from __future__ import annotations

import re
from pathlib import Path

from ..checks import CheckResult

__all__ = [
    "lint_wording",
    "lint_wording_file",
    "default_scope",
    "collect_markdown_files",
    "EXEMPT_DIR_PREFIXES",
    "is_exempt",
]

# The wording rule polices Forge's own normative content (and, through the product
# repo's docs/, product content) -- not text that only *quotes* someone else's claim.
# docs/research/** transcribes external sources (vendor docs, papers, standards) and
# docs/brief/** quotes the project owner's own brief verbatim; both can legitimately
# contain "validated"/"certified" inside a quoted passage the lint has no business
# rewriting. Everything else under docs/ (standards/, decisions/, the root docs) is
# Forge's own authored claims and stays in scope.
EXEMPT_DIR_PREFIXES = ("docs/research", "docs/brief")

# word/phrase -> the evidence-level tokens that excuse it on the same line.
_REQUIRED_LEVELS = {
    "validated": ("L4", "L5"),
    "certified": ("L5",),
    "production-ready": ("L5",),
    "ready for production": ("L5",),
    "prod-ready": ("L5",),
}
_WORD_RE = re.compile(
    r"\b(validated|certified|production-ready|ready for production|prod-ready)\b", re.IGNORECASE
)
_NEGATION_RE = re.compile(r"\b(not|never|nothing)\b", re.IGNORECASE)
_LEVEL_RE = {
    ("L4", "L5"): re.compile(r"\bL[45]\b"),
    ("L5",): re.compile(r"\bL5\b"),
}
_CODE_SPAN_RE = re.compile(r"`[^`]*`")
_NEGATION_WINDOW = 30  # characters looked back from the flagged word for a negation


def is_exempt(root: Path, path: Path) -> bool:
    """True if ``path`` (relative to ``root``) falls under an exempt directory
    (see ``EXEMPT_DIR_PREFIXES``): it quotes external/owner sources rather than
    stating Forge's own normative claims, so the wording rule skips it."""
    try:
        rel = Path(path).resolve().relative_to(Path(root).resolve())
    except ValueError:
        return False
    rel_posix = rel.as_posix()
    return any(
        rel_posix == prefix or rel_posix.startswith(prefix + "/") for prefix in EXEMPT_DIR_PREFIXES
    )


def default_scope(root: Path) -> list[Path]:
    """CONTRACTS SS4 / task default: reviews/, docs/, release/ (recursive)
    plus *.md files directly at the project root -- excluding EXEMPT_DIR_PREFIXES."""
    root = Path(root)
    files: list[Path] = []
    for name in ("reviews", "docs", "release"):
        d = root / name
        if d.exists():
            files.extend(sorted(p for p in d.rglob("*.md") if p.is_file()))
    files.extend(sorted(p for p in root.glob("*.md") if p.is_file()))
    return [p for p in files if not is_exempt(root, p)]


def collect_markdown_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            files.extend(sorted(q for q in p.rglob("*.md") if q.is_file()))
        elif p.is_file():
            files.append(p)
    return files


def _line_findings(raw: str) -> list[str]:
    check_line = _CODE_SPAN_RE.sub("", raw)
    findings = []
    for m in _WORD_RE.finditer(check_line):
        word = m.group(1).lower()
        window = check_line[max(0, m.start() - _NEGATION_WINDOW) : m.start()]
        if _NEGATION_RE.search(window):
            continue
        levels = _REQUIRED_LEVELS[word]
        if _LEVEL_RE[levels].search(check_line):
            continue
        findings.append(word)
    return findings


def lint_wording_file(path: Path) -> CheckResult:
    path = Path(path)
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    in_fence = False
    bad: list[str] = []
    for lineno, raw in enumerate(lines, start=1):
        stripped = raw.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence or stripped.startswith(">"):
            continue
        for word in _line_findings(raw):
            bad.append(f"{path}:{lineno}: {word!r}")

    check_id = f"wording.{path}"
    if bad:
        return CheckResult(
            id=check_id,
            status="fail",
            rule=(
                "'validated' needs an L4/L5 citation on the same line; 'certified'/'production-ready'/"
                "'ready for production'/'prod-ready' need L5; unless negated, or inside a code "
                "block/quote (CONTRACTS SS4, ADR-001 D15)"
            ),
            measured=bad,
            expected="every claim cites its evidence level",
            fix="Add the evidence level (e.g. '(L4)') to the cited line(s), negate the claim, or remove the "
            "word: " + "; ".join(bad),
        )
    return CheckResult(
        id=check_id,
        status="pass",
        rule="validated/certified/production-ready wording is evidence-cited",
        measured=[],
        expected=[],
    )


def lint_wording(paths: list[Path]) -> list[CheckResult]:
    if not paths:
        return [
            CheckResult(
                id="wording.scope",
                status="skip",
                rule="at least one markdown file is in scope",
                measured=0,
                expected=">= 1 file (nothing to lint yet)",
            )
        ]
    return [lint_wording_file(p) for p in paths]
