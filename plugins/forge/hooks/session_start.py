#!/usr/bin/env python3
"""SessionStart: print the live Forge status (CONTRACTS.md §13, ADR-001 §4-5, brief §3.4).

Matcher ``startup|resume|clear|compact``. This is the one hook that still
does something outside a Forge product repo (a one-line hint); every other
hook is a fast no-op there (brief §3.4).

Inside a Forge project, builds a single ``additionalContext`` block
(<=2000 chars, ADR-001 §4) covering:

- the current gate (``forge.toml`` ``project.gate``);
- failing checks from ``out/verify/*.json``;
- open items in ``ASSUMPTIONS.md``/``RISKS.md``: the scaffolder
  (``templates/project/``) uses a markdown table under a ``## Open`` /
  ``## Retired`` split for ``ASSUMPTIONS.md``, and one table with a
  ``Status`` column for ``RISKS.md``; both are parsed positionally (first
  table row is the header, an optional ``|---|`` row is dropped), so this
  doesn't depend on the exact column wording;
- open review findings (non-PASS criteria across ``reviews/G*.md``);
- ``forge doctor`` drift, read from a fresh (<=24h) ``security/*.doctor-cache.json``
  when available, else a capped ``forge doctor --quick --json`` subprocess
  (10 s budget) -- both keyed to the Forge *installation* (this repo), not
  the product project, matching where ``security/mcp-lock.json`` actually lives;
- a Claude Code version-floor warning (``forge.version_check``, always run
  directly since it's cheap and independent of the doctor-cache path);
- on ``source == "compact"``, the ``.forge/state.json`` summary written by
  the PreCompact hook, so state survives compaction (R1a §14/§18).
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (  # noqa: E402
    FORGE_REPO_ROOT, find_project_root, load_forge_toml, failing_checks, open_review_findings,
    read_json, truncate,
)
from forge import state, version_check  # noqa: E402

ADDITIONAL_CONTEXT_MAX_CHARS = 2000
DOCTOR_CACHE_MAX_AGE_S = 24 * 3600
DOCTOR_SUBPROCESS_TIMEOUT_S = 10.0

_HEADING_RE_TMPL = r"^##\s+{}\s*$"
_SEPARATOR_ROW_RE = re.compile(r"^\|[\s\-:|]+\|\s*$")


def _read_text(path: Path) -> str:
    try:
        return path.read_text()
    except OSError:
        return ""


def _section_text(text: str, heading: str) -> str:
    """Text of a ``## <heading>`` section, up to the next ``##`` heading or EOF."""
    m = re.search(_HEADING_RE_TMPL.format(re.escape(heading)), text, re.MULTILINE)
    if not m:
        return ""
    start = m.end()
    nxt = re.search(r"^##\s+", text[start:], re.MULTILINE)
    return text[start:start + nxt.start()] if nxt else text[start:]


def _table_lines(text: str) -> list[str]:
    return [line for line in text.splitlines() if line.strip().startswith("|")]


def _table_data_rows(lines: list[str]) -> list[str]:
    """Drop the header row and an optional ``|---|---|`` separator row,
    purely by position -- this doesn't depend on the header's wording."""
    if not lines:
        return []
    rows = lines[1:]
    if rows and _SEPARATOR_ROW_RE.match(rows[0].strip()):
        rows = rows[1:]
    return rows


def _count_open_assumptions(text: str) -> int:
    """``templates/project/ASSUMPTIONS.md``: a table under ``## Open`` /
    ``## Retired``; every row in the ``## Open`` table is an open item."""
    if not text:
        return 0
    return len(_table_data_rows(_table_lines(_section_text(text, "Open"))))


def _count_open_risks(text: str) -> int:
    """``templates/project/RISKS.md``: one table with a ``Status`` column
    (open|mitigating|closed|accepted, see the file's own legend)."""
    if not text:
        return 0
    lines = _table_lines(text)
    if not lines:
        return 0
    header_cells = [c.strip().lower() for c in lines[0].strip().strip("|").split("|")]
    data_rows = _table_data_rows(lines)
    try:
        status_idx = header_cells.index("status")
    except ValueError:
        return len(data_rows)  # no Status column found; fall back to "every row is open"
    count = 0
    for row in data_rows:
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        if status_idx < len(cells) and cells[status_idx].lower() in ("open", "mitigating"):
            count += 1
    return count


def _mcp_cache_paths() -> list[Path]:
    sec_dir = FORGE_REPO_ROOT / "security"
    if not sec_dir.is_dir():
        return []
    return sorted(sec_dir.glob("*.doctor-cache.json"))


def _doctor_drift() -> list[str] | None:
    """Failing check ids, or ``None`` if drift could not be determined
    (missing forge dev tree, timeout, bad JSON) -- never an error."""
    caches = _mcp_cache_paths()
    now = time.time()
    if caches and all(now - p.stat().st_mtime <= DOCTOR_CACHE_MAX_AGE_S for p in caches):
        fails: list[str] = []
        for p in caches:
            data = read_json(p, {}) or {}
            for server, entry in data.items():
                for r in entry.get("results", []):
                    if r.get("status") == "fail":
                        fails.append(f"{server}:{r.get('id')}")
        return fails

    forge_bin = FORGE_REPO_ROOT / "plugins" / "forge" / "bin" / "forge"
    if not forge_bin.is_file():
        return None
    try:
        proc = subprocess.run(
            [sys.executable, str(forge_bin), "doctor", "--quick", "--json"],
            capture_output=True, text=True, timeout=DOCTOR_SUBPROCESS_TIMEOUT_S,
        )
        report = json.loads(proc.stdout)
    except (subprocess.TimeoutExpired, OSError, json.JSONDecodeError):
        return None
    return [r["id"] for r in report.get("results", [])
            if r.get("status") == "fail" and not str(r.get("id", "")).startswith("claude_code_version:")]


def _version_warning() -> str | None:
    try:
        results = version_check.run_version_floor_checks(timeout=5.0)
    except Exception:  # noqa: BLE001 -- purely advisory, never let this break SessionStart
        return None
    bad = [r for r in results if r.status in ("fail", "warn")]
    if not bad:
        return None
    return "; ".join(f"{r.id} {r.status} (have {r.measured}, need {r.expected})" for r in bad)


def _no_project_hint() -> dict:
    return {"additionalContext": (
        "Forge: no forge.toml found above this directory; this isn't a Forge product repo. "
        "Run /forge:new-project or /forge:init to scaffold one."
    )}


def handle(data: dict) -> tuple[int, dict | None]:
    project = find_project_root(data.get("cwd"))
    if project is None:
        return 0, _no_project_hint()

    source = data.get("source")
    toml = load_forge_toml(project)
    gate = (toml.get("project") or {}).get("gate") or "(unset)"

    failing = failing_checks(project)
    assumptions_open = _count_open_assumptions(_read_text(project / "ASSUMPTIONS.md"))
    risks_open = _count_open_risks(_read_text(project / "RISKS.md"))
    findings = open_review_findings(project)
    drift = _doctor_drift()
    version_warning = _version_warning()

    lines = [f"Forge: gate {gate}."]
    if failing:
        shown = ", ".join(failing[:8]) + (f" (+{len(failing) - 8} more)" if len(failing) > 8 else "")
        lines.append(f"Failing checks ({len(failing)}): {shown}")
    if assumptions_open or risks_open:
        lines.append(f"Open items: {assumptions_open} in ASSUMPTIONS.md, {risks_open} in RISKS.md.")
    if findings:
        lines.append(f"Open review findings: {len(findings)} (non-PASS criteria in reviews/G*.md).")
    if drift:
        shown = ", ".join(drift[:5]) + (f" (+{len(drift) - 5} more)" if len(drift) > 5 else "")
        lines.append(f"forge doctor drift: {shown}")
    if version_warning:
        lines.append(f"Claude Code version: {version_warning}")
    if source == "compact":
        lines.append(state.compact_summary_text(project, max_chars=900))

    text = truncate("\n".join(lines), ADDITIONAL_CONTEXT_MAX_CHARS)
    return 0, {"additionalContext": text}


if __name__ == "__main__":
    from _failclosed import run_hook
    run_hook(handle)
