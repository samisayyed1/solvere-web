"""Shared check-result model.

Every Forge check (version floor, tool pin, MCP lock, file lock) reports
through :class:`CheckResult`, so every failure carries the same three
things a person needs to act on it: the rule that was applied, the
measured value against what was expected, and how to fix it. A ``fail``
result without a ``fix`` string is a programming error and raises
immediately, mirroring ADR-001 section 13 rule 6 ("Every failure message
says how to fix it... the linter rejects checks without a remediation
string").
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

Status = Literal["pass", "fail", "warn", "skip"]

__all__ = ["CheckResult", "summarize", "format_report"]


@dataclass
class CheckResult:
    id: str
    status: Status
    rule: str
    measured: Any = None
    expected: Any = None
    fix: str | None = None
    detail: str | None = None

    def __post_init__(self) -> None:
        if self.status not in ("pass", "fail", "warn", "skip"):
            raise ValueError(f"invalid status {self.status!r} for check {self.id!r}")
        if self.status == "fail" and not self.fix:
            raise ValueError(
                f"check {self.id!r} reports status=fail with no remediation string; "
                "every failure must say how to fix it"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "status": self.status,
            "rule": self.rule,
            "measured": self.measured,
            "expected": self.expected,
            "fix": self.fix,
            "detail": self.detail,
        }

    def message(self) -> str:
        parts = [f"[{self.status.upper()}] {self.id}"]
        parts.append(f"rule: {self.rule}")
        if self.measured is not None or self.expected is not None:
            parts.append(f"measured={self.measured!r} expected={self.expected!r}")
        if self.detail:
            parts.append(self.detail)
        if self.fix:
            parts.append(f"fix: {self.fix}")
        return " -- ".join(parts)


def summarize(results: list[CheckResult]) -> dict[str, int]:
    counts = {"pass": 0, "fail": 0, "warn": 0, "skip": 0}
    for r in results:
        counts[r.status] += 1
    return counts


def format_report(results: list[CheckResult]) -> str:
    lines = [r.message() for r in results]
    counts = summarize(results)
    lines.append(
        "-- {pass} pass, {fail} fail, {warn} warn, {skip} skip".format(**counts)
    )
    return "\n".join(lines)
