"""``forge lint claudemd`` (brief SS3.1, ADR-001 D3): the root/TOC CLAUDE.md
stays under 100 lines. Domain knowledge belongs in skills and path-scoped
rules, which load lazily; CLAUDE.md is only a table of contents pointing
into them (brief: "Context is the scarcest resource").
"""

from __future__ import annotations

from pathlib import Path

from ..checks import CheckResult

__all__ = ["lint_claudemd", "MAX_LINES"]

MAX_LINES = 100


def lint_claudemd(paths: list[Path]) -> list[CheckResult]:
    results: list[CheckResult] = []
    for raw in paths:
        p = Path(raw)
        if not p.exists():
            results.append(
                CheckResult(
                    id=f"claudemd.exists:{p}",
                    status="skip",
                    rule="CLAUDE.md target exists",
                    measured=str(p),
                    expected="present (may be owned by another Forge builder)",
                )
            )
            continue
        n = len(p.read_text(encoding="utf-8", errors="replace").splitlines())
        if n <= MAX_LINES:
            results.append(
                CheckResult(
                    id=f"claudemd.length:{p}",
                    status="pass",
                    rule=f"CLAUDE.md is a table of contents, <= {MAX_LINES} lines (brief SS3.1)",
                    measured=n,
                    expected=f"<= {MAX_LINES}",
                )
            )
        else:
            results.append(
                CheckResult(
                    id=f"claudemd.length:{p}",
                    status="fail",
                    rule=f"CLAUDE.md is a table of contents, <= {MAX_LINES} lines (brief SS3.1, ADR-001 D3)",
                    measured=n,
                    expected=f"<= {MAX_LINES}",
                    fix=f"{p} has {n} lines; move detail into skills/rules and keep only pointers here.",
                )
            )
    return results
