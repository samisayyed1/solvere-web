#!/usr/bin/env python3
"""SubagentStop: enforce the reviewer verdict schema (CONTRACTS.md §5, §13).

For ``agent_type`` ``forge:verification-evaluator`` or ``forge:red-team``
(the two judges, CONTRACTS §13 -- specialist gate-review agents also return
a verdict block but are matched by the gate-review workflow, not here),
this extracts the **last** fenced ```json block from ``last_assistant_message``
and validates it against ``schemas/verdict.schema.json`` (via
``forge.minischema``, the stdlib-only validator). Missing or invalid ->
``decision: "block"`` with the precise schema errors, which (per R1a §18)
keeps the subagent running so it can fix its own output, rather than
letting a free-form "looks good to me" pass as a verdict.

On top of the schema (which itself encodes the rule), the hook checks the
CONTRACTS §5 consistency rule explicitly, so the reason names the offending
criteria: ``overall`` may be ``PASS`` only if every criterion is ``PASS``
(review #1, M5). A judge that reports a critical FAIL under an overall PASS
is blocked and must fix its verdict.

Every other ``agent_type`` (including the empty string used by internal
agents, R1a §16) is left alone.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import find_project_root, is_judge, load_forge_toml, truncate  # noqa: E402
from forge import minischema  # noqa: E402

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = PLUGIN_ROOT / "schemas" / "verdict.schema.json"
REASON_MAX_CHARS = 1800

_FENCE_RE = re.compile(r"```json\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)


def _last_json_block(text: str) -> str | None:
    blocks = _FENCE_RE.findall(text or "")
    return blocks[-1] if blocks else None


def handle(data: dict) -> tuple[int, dict | None]:
    project = find_project_root(data.get("cwd"))
    if project is None:
        return 0, None  # not a Forge product repo: no-op fast (brief §3.4)

    load_forge_toml(project)  # N1: raises (fail closed) if forge.toml is missing but the project is real

    agent_type = data.get("agent_type")
    if not is_judge(agent_type):
        return 0, None

    message = data.get("last_assistant_message") or ""
    block = _last_json_block(message)
    if block is None:
        return 2, {"decision": "block", "reason": (
            f"{agent_type} must end its final message with exactly one fenced "
            "```json block matching schemas/verdict.schema.json (CONTRACTS.md §5); none was found. "
            "Emit the verdict JSON block and stop."
        )}

    try:
        payload = json.loads(block)
    except json.JSONDecodeError as exc:
        return 2, {"decision": "block", "reason": (
            f"{agent_type}'s final ```json verdict block does not parse as JSON: {exc}. Fix the JSON and stop."
        )}

    try:
        schema = json.loads(SCHEMA_PATH.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return 2, {"decision": "block", "reason": f"forge hook internal: could not load verdict schema: {exc}"}

    errors = minischema.validate(payload, schema)
    if isinstance(payload, dict) and payload.get("overall") == "PASS":
        not_pass = [f"{c.get('id')}={c.get('verdict')}" for c in payload.get("criteria") or []
                    if isinstance(c, dict) and c.get("verdict") != "PASS"]
        if not_pass:
            errors.insert(0, "overall is PASS but these criteria are not PASS: " + ", ".join(not_pass)
                          + " (CONTRACTS.md §5: overall is PASS only if every criterion is PASS)")
    if errors:
        reason = (f"{agent_type}'s verdict does not match schemas/verdict.schema.json:\n"
                  + "\n".join(f"- {e}" for e in errors) + "\nFix the verdict JSON block and stop.")
        return 2, {"decision": "block", "reason": truncate(reason, REASON_MAX_CHARS)}

    return 0, None


if __name__ == "__main__":
    from _failclosed import run_hook
    run_hook(handle)
