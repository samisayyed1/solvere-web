#!/usr/bin/env python3
"""PreCompact: write the state snapshot (CONTRACTS.md §13, brief §3.4).

Matcher ``manual|auto``. R1a §18 notes ``systemMessage`` and ``continue``
are discarded on PreCompact, and path rules / hook-added context are lost
at compaction -- so this hook's only job is to persist
``.forge/state.json`` (modified files, open review findings, the current
gate, failing checks) so SessionStart's ``compact`` matcher can re-inject a
short summary afterwards (see ``session_start.py``).

This never blocks compaction: it always exits 0.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import find_project_root, load_forge_toml, changed_paths, failing_checks, open_review_findings  # noqa: E402
from forge import state  # noqa: E402


def handle(data: dict) -> tuple[int, dict | None]:
    project = find_project_root(data.get("cwd"))
    if project is None:
        return 0, None  # not a Forge product repo: no-op fast (brief §3.4)

    toml = load_forge_toml(project)
    gate = (toml.get("project") or {}).get("gate")

    state.write_precompact_snapshot(
        project,
        modified_files=changed_paths(project),
        open_findings=open_review_findings(project),
        gate=gate,
        failing_checks=failing_checks(project),
    )
    return 0, None


if __name__ == "__main__":
    from _failclosed import run_hook
    run_hook(handle)
