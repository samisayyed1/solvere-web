"""lib/forge/tools.py: pinned tools resolve from $FORGE_HOME/bin before PATH."""

from __future__ import annotations

import os
import re
from pathlib import Path

from forge import tools

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
PINNED_TOOLS = ("ngspice", "kicad-cli", "blender", "freecadcmd", "spec42", "renode", "ccx", "srt")


def _exe(path: Path, mode: int = 0o755) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/bin/sh\nexit 0\n")
    path.chmod(mode)
    return path


def test_forge_home_bin_wins_over_path(tmp_path, monkeypatch):
    """Seeded wrong: a decoy ngspice earlier on PATH must not be picked."""
    home = tmp_path / "fh"
    pinned = _exe(home / "bin" / "ngspice")
    decoy = _exe(tmp_path / "decoy" / "ngspice")
    monkeypatch.setenv("FORGE_HOME", str(home))
    monkeypatch.setenv("PATH", str(decoy.parent) + os.pathsep + os.environ["PATH"])
    assert tools.find_tool("ngspice") == str(pinned)


def test_falls_back_to_path_when_not_pinned(tmp_path, monkeypatch):
    decoy = _exe(tmp_path / "onpath" / "kicad-cli")
    monkeypatch.setenv("FORGE_HOME", str(tmp_path / "empty"))
    monkeypatch.setenv("PATH", str(decoy.parent))
    assert tools.find_tool("kicad-cli") == str(decoy)


def test_non_executable_pinned_file_is_ignored(tmp_path, monkeypatch):
    home = tmp_path / "fh"
    _exe(home / "bin" / "spec42", mode=0o644)
    monkeypatch.setenv("FORGE_HOME", str(home))
    monkeypatch.setenv("PATH", str(tmp_path / "nothing"))
    assert tools.find_tool("spec42") is None


def test_default_forge_home_is_dot_forge(monkeypatch):
    monkeypatch.delenv("FORGE_HOME", raising=False)
    assert tools.forge_bin() == Path.home() / ".forge" / "bin"


def test_tool_env_puts_forge_bin_first(tmp_path, monkeypatch):
    monkeypatch.setenv("FORGE_HOME", str(tmp_path))
    assert tools.tool_env({"PATH": "/usr/bin"})["PATH"].split(os.pathsep)[0] == str(tmp_path / "bin")


def test_no_skill_script_looks_pinned_tools_up_on_path_only():
    """Regression guard: every skill script goes through forge.tools for pinned tools."""
    pat = re.compile(r"shutil\.which\(\s*[\"'](" + "|".join(map(re.escape, PINNED_TOOLS)) + r")[\"']")
    home_pat = re.compile(r"Path\.home\(\)\s*/\s*[\"']\.forge[\"']\s*/\s*[\"']bin[\"']")
    offenders = []
    for f in sorted((PLUGIN_ROOT / "skills").glob("*/scripts/*.py")):
        text = f.read_text()
        if pat.search(text) or home_pat.search(text):
            offenders.append(str(f.relative_to(PLUGIN_ROOT)))
    assert offenders == []
