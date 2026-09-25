#!/usr/bin/env python3
"""PostToolUse: path-dispatched verification (CONTRACTS.md §8-9, brief §3.4).

Matched on ``Write|Edit|MultiEdit`` in ``hooks/hooks.json``. Maps the
changed path through the product repo's ``forge.toml`` ``[[verify]]``
entries to verify entrypoints (CONTRACTS §9), and runs each with
``--fast --changed <path>`` via ``~/.forge/bin/forge-python`` (the skill
scripts' pinned CAD/EDA interpreter, CONTRACTS §10), under a 30 s *total*
budget across all matched entrypoints.

- No mapped entrypoints for this path -> exit 0, no output.
- An entrypoint script that doesn't exist yet (another builder's skill not
  built) -> skipped with a note; this is reported via ``systemMessage`` and
  never counted as a pass.
- Any entrypoint that fails or errors -> exit 2 with ``decision: "block"``
  and a <=1500-char summary built from the check-result JSONs'
  ``remediation`` strings (CONTRACTS §3), never free text.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import find_project_root, load_forge_toml, any_glob_match, truncate  # noqa: E402

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
TOTAL_BUDGET_S = 30.0
SUMMARY_MAX_CHARS = 1500
FORGE_PYTHON = Path.home() / ".forge" / "bin" / "forge-python"


def _rel_path(project: Path, file_path: str) -> str | None:
    try:
        p = Path(file_path)
        if not p.is_absolute():
            p = project / p
        return p.resolve().relative_to(project.resolve()).as_posix()
    except (OSError, ValueError):
        return None


def _matched_entrypoints(project: Path, rel: str) -> list[str]:
    toml = load_forge_toml(project)
    entrypoints: list[str] = []
    for entry in toml.get("verify") or []:
        if not isinstance(entry, dict):
            continue
        paths = entry.get("paths") or []
        if any_glob_match(paths, rel):
            for ep in entry.get("entrypoints") or []:
                if ep not in entrypoints:
                    entrypoints.append(ep)
    return entrypoints


def _collect_remediations(project: Path, since: float) -> list[str]:
    out: list[str] = []
    verify_dir = project / "out" / "verify"
    if not verify_dir.is_dir():
        return out
    for f in sorted(verify_dir.glob("*.json")):
        try:
            if f.stat().st_mtime < since - 1.0:
                continue
            data = json.loads(f.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        check_id = data.get("check_id", f.stem)
        if data.get("status") == "error" and data.get("error"):
            out.append(f"{check_id}: ERROR: {data['error']}")
        for m in data.get("measurements", []):
            if not m.get("pass", True) and m.get("remediation"):
                out.append(f"{check_id}: {m['remediation']}")
    return out


def _run_entrypoint(project: Path, entrypoint: str, rel: str, deadline: float, interpreter: Path) -> dict:
    script = PLUGIN_ROOT / "skills" / entrypoint / "scripts" / "verify.py"
    if not script.is_file():
        return {"entrypoint": entrypoint, "status": "skip", "note": f"entrypoint not built yet ({script})"}
    if not interpreter.is_file():
        return {"entrypoint": entrypoint, "status": "skip",
                 "note": f"forge-python not installed at {interpreter}; run plugins/forge/toolchain/install.sh"}
    remaining = deadline - time.time()
    if remaining <= 0.2:
        return {"entrypoint": entrypoint, "status": "skip", "note": "PostToolUse 30s budget exhausted"}
    start = time.time()
    try:
        proc = subprocess.run(
            [str(interpreter), str(script), "--project", str(project), "--changed", rel, "--fast"],
            capture_output=True, text=True, timeout=min(remaining, TOTAL_BUDGET_S),
        )
    except subprocess.TimeoutExpired:
        return {"entrypoint": entrypoint, "status": "error", "remediations": [], "note": "timed out"}
    except OSError as exc:
        return {"entrypoint": entrypoint, "status": "error", "remediations": [], "note": str(exc)}
    status = "pass" if proc.returncode == 0 else ("fail" if proc.returncode == 1 else "error")
    remediations = _collect_remediations(project, since=start)
    note = None
    if status == "error" and not remediations:
        note = truncate((proc.stderr or proc.stdout or "no output").strip(), 300)
    return {"entrypoint": entrypoint, "status": status, "remediations": remediations, "note": note}


def handle(data: dict) -> tuple[int, dict | None]:
    project = find_project_root(data.get("cwd"))
    if project is None:
        return 0, None

    tool_input = data.get("tool_input") or {}
    file_path = tool_input.get("file_path")
    if not file_path:
        return 0, None
    rel = _rel_path(project, file_path)
    if rel is None:
        return 0, None

    entrypoints = _matched_entrypoints(project, rel)
    if not entrypoints:
        return 0, None

    deadline = time.time() + TOTAL_BUDGET_S
    results = [_run_entrypoint(project, ep, rel, deadline, FORGE_PYTHON) for ep in entrypoints]

    bad = [r for r in results if r["status"] in ("fail", "error")]
    skipped = [r for r in results if r["status"] == "skip"]

    if bad:
        lines = []
        for r in bad:
            lines.append(f"[{r['status'].upper()}] {r['entrypoint']} ({rel})")
            for rem in r.get("remediations") or []:
                lines.append(f"  - {rem}")
            if r.get("note"):
                lines.append(f"  - {r['note']}")
        summary = truncate("\n".join(lines), SUMMARY_MAX_CHARS)
        return 2, {"decision": "block", "reason": summary}

    if skipped:
        note = "; ".join(f"{r['entrypoint']}: {r['note']}" for r in skipped)
        return 0, {"systemMessage": truncate(f"Forge: skipped (not run, not passed): {note}", 500)}

    return 0, None


if __name__ == "__main__":
    from _failclosed import run_hook
    run_hook(handle)
