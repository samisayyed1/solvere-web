from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path

import pytest

TEMPLATE_TESTS_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = TEMPLATE_TESTS_DIR.parent.parent  # plugins/forge
REPO_ROOT = PLUGIN_ROOT.parent.parent
TEMPLATES_DIR = REPO_ROOT / "templates" / "project"
SPEC42 = Path.home() / ".forge" / "bin" / "spec42"

NEW_PROJECT_SCRIPT = PLUGIN_ROOT / "skills" / "new-project" / "scripts" / "scaffold.py"
INIT_SCRIPT = PLUGIN_ROOT / "skills" / "init" / "scripts" / "scaffold.py"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def new_project_mod():
    return _load_module("forge_new_project_scaffold", NEW_PROJECT_SCRIPT)


@pytest.fixture(scope="session")
def init_mod():
    return _load_module("forge_init_scaffold", INIT_SCRIPT)


@pytest.fixture()
def templates_dir() -> Path:
    return TEMPLATES_DIR


@pytest.fixture()
def forge_root() -> Path:
    return REPO_ROOT


@pytest.fixture()
def scaffolded_project(tmp_path, new_project_mod) -> Path:
    """A fresh scaffold of templates/project/ into an empty tmp dir."""
    target = tmp_path / "widget-project"
    new_project_mod.scaffold(target, name="Widget Alpha", forge_root=REPO_ROOT, templates_dir=TEMPLATES_DIR)
    return target


@pytest.fixture()
def spec42_bin() -> Path | None:
    return SPEC42 if SPEC42.exists() else None
