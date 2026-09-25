"""Find Forge's pinned external tools (CONTRACTS.md §10).

The toolchain installer links pinned builds (ngspice, kicad-cli, ccx,
freecadcmd, blender, spec42, renode, srt, ...) into ``$FORGE_HOME/bin``
(default ``~/.forge/bin``). Every script resolves a tool here first and only
then falls back to ``PATH``, so the pinned version wins over whatever the
host happens to have, and a tool that is installed but not on ``PATH`` is
still found. Standard library only.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

__all__ = ["forge_home", "forge_bin", "find_tool", "tool_env"]


def forge_home() -> Path:
    return Path(os.environ.get("FORGE_HOME") or Path.home() / ".forge")


def forge_bin() -> Path:
    return forge_home() / "bin"


def find_tool(name: str) -> str | None:
    """Absolute path of ``name``: ``$FORGE_HOME/bin/<name>`` if it exists and
    is executable, else the first ``PATH`` hit, else ``None``."""
    pinned = forge_bin() / name
    if pinned.is_file() and os.access(pinned, os.X_OK):
        return str(pinned)
    return shutil.which(name)


def tool_env(base: dict[str, str] | None = None) -> dict[str, str]:
    """An environment whose ``PATH`` starts with ``$FORGE_HOME/bin``, for
    subprocesses that look tools up by bare name themselves."""
    env = dict(os.environ if base is None else base)
    env["PATH"] = str(forge_bin()) + os.pathsep + env.get("PATH", "")
    return env
