"""Shared helpers for elec/fw skill tests: import a skill's scripts/verify.py by path,
and skip cleanly when a real tool (ngspice, srt, kicad-cli, cc) isn't on this machine."""
from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path
from types import ModuleType

TESTS_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = TESTS_DIR.parent.parent  # plugins/forge
SKILLS_DIR = PLUGIN_ROOT / "skills"


def load_skill_module(skill: str, filename: str = "verify.py") -> ModuleType:
    """Import ``plugins/forge/skills/<skill>/scripts/<filename>`` as a standalone module."""
    path = SKILLS_DIR / skill / "scripts" / filename
    spec = importlib.util.spec_from_file_location(f"forge_skill_{skill.replace('-', '_')}", path)
    assert spec and spec.loader, f"could not load {path}"
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def require_tool(name: str) -> str:
    path = shutil.which(name) or str(Path.home() / ".forge" / "bin" / name)
    if not Path(path).exists() and not shutil.which(name):
        import pytest
        pytest.skip(f"{name} not installed on this machine")
    return path
