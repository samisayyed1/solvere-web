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


def test_empty_model_file_is_not_a_pass(tmp_path):
    """S4: a zero-byte model file has no diagnostics from spec42, but that is
    not the same as a verified, clean model -- it must not PASS."""
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    (model_dir / "system.sysml").write_text("")
    rc = verify.run(tmp_path, None)
    assert rc != 0, "an empty model file must not PASS"
    out = json.loads((tmp_path / "out/verify/systems.sysml_check.json").read_text())
    assert out["status"] != "pass"


def test_comment_only_model_file_is_not_a_pass(tmp_path):
    """S4: a model file with only comments defines nothing and must not PASS."""
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    (model_dir / "system.sysml").write_text(
        "// TODO: write the actual model\n/* nothing here either */\n"
    )
    rc = verify.run(tmp_path, None)
    assert rc != 0, "a comment-only model file must not PASS"
    out = json.loads((tmp_path / "out/verify/systems.sysml_check.json").read_text())
    assert out["status"] != "pass"
    assert any(m["name"].endswith(".has_definitions") and not m["pass"] for m in out["measurements"])
