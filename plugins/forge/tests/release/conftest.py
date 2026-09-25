"""Shared helpers for release-domain tests: import a skill's script by path, and a real
tiny git repo fixture (releasing-designs needs a real HEAD sha to check APPROVAL.toml against)."""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType

TESTS_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = TESTS_DIR.parent.parent  # plugins/forge
SKILLS_DIR = PLUGIN_ROOT / "skills"


def load_skill_module(skill: str, filename: str) -> ModuleType:
    path = SKILLS_DIR / skill / "scripts" / filename
    spec = importlib.util.spec_from_file_location(f"forge_skill_{skill.replace('-', '_')}_{filename[:-3]}", path)
    assert spec and spec.loader, f"could not load {path}"
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def init_git_repo(path: Path) -> str:
    """Initializes a real git repo at ``path`` with one commit; returns its HEAD sha."""
    run = lambda *args: subprocess.run(  # noqa: E731
        ["git", *args], cwd=path, capture_output=True, text=True, check=True
    )
    run("init", "-q")
    run("config", "user.email", "test@example.com")
    run("config", "user.name", "Forge Test")
    (path / ".gitkeep").write_text("")
    run("add", ".gitkeep")
    run("commit", "-q", "-m", "initial commit")
    return run("rev-parse", "HEAD").stdout.strip()
