#!/usr/bin/env python3
"""UserPromptExpansion: gate release / fab / flash slash commands (CONTRACTS.md §13, brief §3.4).

Blocks ``/forge:releasing-designs``, ``/forge:testing-on-hardware`` and any
command whose name contains a fab-export or flash step, unless
``release/APPROVAL.toml`` exists, parses, has every required field
(``approved_by``, ``date``, ``git_sha``, ``scope``, ``gate``), and its
``git_sha`` equals the current ``HEAD``. This is the direct ``/command``
path, which a PreToolUse hook never sees (R1a §21 note (d) / Implications
#11) -- the underlying tool calls those commands eventually make are a
second, PreToolUse-level layer, not this hook's job.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import find_project_root, head_sha, tomllib  # noqa: E402

# Substrings of `command_name` that require a signed release/APPROVAL.toml.
# "releasing-designs" and "testing-on-hardware" are the brief's named
# side-effect skills (CONTRACTS.md §13); "fab"/"flash" cast a wide net over
# any later skill for fabrication export or hardware flashing (e.g.
# "exporting-fab-files", "flashing-firmware") -- fail closed on the name,
# since a real fab-export/flash skill not yet named here is exactly the
# gap this hook exists to cover.
GATED_SUBSTRINGS = ("releasing-designs", "testing-on-hardware", "fab", "flash")

REQUIRED_APPROVAL_FIELDS = ("approved_by", "date", "git_sha", "scope", "gate")


def _is_gated(command_name: str) -> bool:
    name = (command_name or "").lower()
    return any(s in name for s in GATED_SUBSTRINGS)


def _block(command_name: str, reason: str) -> tuple[int, dict]:
    return 2, {"decision": "block", "reason": f"/{command_name}: {reason}"}


def handle(data: dict) -> tuple[int, dict | None]:
    project = find_project_root(data.get("cwd"))
    if project is None:
        return 0, None  # not a Forge product repo: no-op fast (brief §3.4)

    command_name = data.get("command_name") or ""
    if not _is_gated(command_name):
        return 0, None

    approval_path = project / "release" / "APPROVAL.toml"
    if not approval_path.is_file():
        return _block(command_name, "requires a human-written release/APPROVAL.toml (CONTRACTS.md §13); "
                      "none found. A human must create it with approved_by, date, git_sha, scope and gate.")

    if tomllib is None:
        return _block(command_name, "forge hook internal: no TOML parser available to check release/APPROVAL.toml.")

    try:
        approval = tomllib.loads(approval_path.read_text())
    except tomllib.TOMLDecodeError as exc:
        return _block(command_name, f"release/APPROVAL.toml does not parse as TOML: {exc}")

    missing = [f for f in REQUIRED_APPROVAL_FIELDS if not approval.get(f)]
    if missing:
        return _block(command_name, f"release/APPROVAL.toml is missing required field(s): {', '.join(missing)}.")

    head = head_sha(project)
    approved_sha = str(approval.get("git_sha"))
    if approved_sha != head:
        return _block(command_name, f"release/APPROVAL.toml git_sha ({approved_sha!r}) does not match "
                      f"HEAD ({head!r}); a human must re-approve at the current commit.")

    return 0, None


if __name__ == "__main__":
    from _failclosed import run_hook
    run_hook(handle)
