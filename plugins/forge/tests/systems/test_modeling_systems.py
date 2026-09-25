"""modeling-systems/scripts/verify.py: spec42 check --warnings-as-errors over
model/**/*.sysml (CONTRACTS.md §9). Skips if spec42 isn't installed."""
from __future__ import annotations

import json

import pytest

from .conftest import load_skill_module, require_tool

verify = load_skill_module("modeling-systems")


@pytest.fixture(autouse=True)
def _tool():
    require_tool("spec42")


def test_clean_model_passes(tmp_path):
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    (model_dir / "system.sysml").write_text(
        "package HydroSenseModel {\n"
        "    part def Sensor;\n"
        "    part hydroSense : Sensor;\n"
        "}\n"
    )
    assert verify.run(tmp_path, None) == 0
    out = json.loads((tmp_path / "out/verify/systems.sysml_check.json").read_text())
    assert out["status"] == "pass"


def test_sysml_syntax_error_fails(tmp_path):
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    (model_dir / "system.sysml").write_text(
        "package Broken {\n"
        "    part def Sensor {\n"
        "        attribute mass : Real\n"
        "    this is not valid syntax @@@\n"
    )
    assert verify.run(tmp_path, None) == 1
    out = json.loads((tmp_path / "out/verify/systems.sysml_check.json").read_text())
    assert out["status"] == "fail"
    assert any(not m["pass"] for m in out["measurements"])
    assert any("missing_closing_brace" in m["name"] for m in out["measurements"])


def test_no_model_dir_is_skip(tmp_path):
    assert verify.run(tmp_path, None) == 0
    assert not (tmp_path / "out").exists()
