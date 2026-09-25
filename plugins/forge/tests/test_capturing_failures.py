"""capturing-failures new_failure.py: deterministic id allocation and template completeness."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def mod():
    path = PLUGIN_ROOT / "skills" / "capturing-failures" / "scripts" / "new_failure.py"
    spec = importlib.util.spec_from_file_location("forge_skill_capturing_failures", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_first_id_is_0001(mod, tmp_path):
    path = mod.scaffold(tmp_path, "a first failure")
    assert path.name == "FAIL-0001.md"
    assert path.exists()


def test_ids_increment_and_never_collide(mod, tmp_path):
    first = mod.scaffold(tmp_path, "one")
    second = mod.scaffold(tmp_path, "two")
    third = mod.scaffold(tmp_path, "three")
    assert [p.name for p in (first, second, third)] == ["FAIL-0001.md", "FAIL-0002.md", "FAIL-0003.md"]


def test_next_id_resumes_after_a_gap(mod, tmp_path):
    failures_dir = tmp_path / "docs" / "failures"
    failures_dir.mkdir(parents=True)
    (failures_dir / "FAIL-0001.md").write_text("x")
    (failures_dir / "FAIL-0007.md").write_text("x")
    assert mod.next_id(failures_dir) == "FAIL-0008"


def test_template_has_required_sections(mod, tmp_path):
    path = mod.scaffold(tmp_path, "missing wall thickness check")
    text = path.read_text()
    for heading in ("## Five whys", "## New mechanism", "## Proof it catches the original failure", "## Eval case"):
        assert heading in text
    assert "missing wall thickness check" in text
