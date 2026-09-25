"""templates/project/ content checks (BUILD item: forge product-engineering
template, builder A). Each assertion below is proven able to fail: it is run
once against the real scaffolded output (must pass) and once against a
deliberately broken fixture (must fail)."""

from __future__ import annotations

import json

import pytest

from template._checks import (
    claude_md_line_count,
    forge_toml_missing_entrypoints,
    rules_missing_paths,
    settings_missing_required,
)


# --- CLAUDE.md is a table of contents, under 100 lines ----------------------

def test_claude_md_under_100_lines(scaffolded_project):
    assert claude_md_line_count(scaffolded_project / "CLAUDE.md") < 100


def test_claude_md_length_check_can_fail(tmp_path):
    bloated = tmp_path / "CLAUDE.md"
    bloated.write_text("\n".join(f"line {i}" for i in range(150)) + "\n")
    assert claude_md_line_count(bloated) >= 100


def test_claude_md_imports_agents_md(scaffolded_project):
    text = (scaffolded_project / "CLAUDE.md").read_text()
    assert "@AGENTS.md" in text


# --- every rule has paths: frontmatter ---------------------------------

EXPECTED_RULES = {
    "mechanical.md", "electrical.md", "firmware.md", "software.md",
    "systems.md", "simulation.md", "manufacturing.md", "compliance.md",
}


def test_all_rules_present(scaffolded_project):
    rules_dir = scaffolded_project / ".claude" / "rules"
    names = {p.name for p in rules_dir.glob("*.md")}
    assert EXPECTED_RULES <= names


def test_every_rule_has_paths(scaffolded_project):
    rules_dir = scaffolded_project / ".claude" / "rules"
    assert rules_missing_paths(rules_dir) == []


def test_rules_paths_check_can_fail(tmp_path):
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()
    (rules_dir / "no-frontmatter.md").write_text("# a rule with no frontmatter at all\n")
    (rules_dir / "empty-frontmatter.md").write_text("---\nname: x\n---\n# body\n")
    missing = rules_missing_paths(rules_dir)
    assert "no-frontmatter.md" in missing
    assert "empty-frontmatter.md" in missing


# --- settings.json parses and carries the required deny/ask/sandbox rules ---

def test_settings_json_parses(scaffolded_project):
    settings = json.loads((scaffolded_project / ".claude" / "settings.json").read_text())
    assert settings["permissions"]["deny"]
    assert settings["permissions"]["ask"]


def test_settings_json_has_required_rules(scaffolded_project):
    settings = json.loads((scaffolded_project / ".claude" / "settings.json").read_text())
    assert settings_missing_required(settings) == []


def test_settings_required_rules_check_can_fail():
    broken = {
        "permissions": {"deny": [], "ask": []},
        "sandbox": {"enabled": False, "failIfUnavailable": False,
                     "allowUnsandboxedCommands": True, "network": {}, "filesystem": {}},
    }
    missing = settings_missing_required(broken)
    assert len(missing) >= 7  # every requirement is violated


def test_settings_json_denies_kicad_pricing_tool(scaffolded_project):
    settings = json.loads((scaffolded_project / ".claude" / "settings.json").read_text())
    assert "mcp__kicad-mcp-pro__lib_get_bom_with_pricing" in settings["permissions"]["deny"]


def test_settings_json_enables_forge_plugin(scaffolded_project):
    settings = json.loads((scaffolded_project / ".claude" / "settings.json").read_text())
    assert settings["enabledPlugins"]["forge@forge-local"] is True


# --- forge.toml maps every registered entrypoint (CONTRACTS.md §9) ---------

def test_forge_toml_maps_every_entrypoint(scaffolded_project):
    assert forge_toml_missing_entrypoints(scaffolded_project / "forge.toml") == set()


def test_forge_toml_entrypoint_check_can_fail(tmp_path):
    broken = tmp_path / "forge.toml"
    broken.write_text(
        '[project]\nname = "x"\ngate = "G0"\n\n'
        '[[verify]]\ndomain = "mech"\npaths = ["cad/**"]\n'
        'entrypoints = ["verifying-geometry"]\nrung = "numeric"\n'
    )
    missing = forge_toml_missing_entrypoints(broken)
    assert "checking-dfm" in missing
    assert "writing-requirements" in missing


# --- params.toml, evidence manifest, requirements are well-formed ----------

def test_params_toml_parses(scaffolded_project):
    import tomllib
    data = tomllib.loads((scaffolded_project / "params" / "params.toml").read_text())
    assert "enclosure" in data
    wall = data["enclosure"]["wall_thickness"]
    assert wall["unit"] == "mm"
    assert wall["status"] in {"assumed", "datasheet", "measured", "verified"}


def test_evidence_manifest_is_empty_and_well_formed(scaffolded_project):
    manifest = json.loads((scaffolded_project / "evidence" / "manifest.json").read_text())
    assert manifest == {"schema": "forge.evidence/1", "entries": []}


def test_project_name_substituted_everywhere(scaffolded_project):
    for rel in ("CLAUDE.md", "AGENTS.md", "forge.toml"):
        text = (scaffolded_project / rel).read_text()
        assert "Widget Alpha" in text
        assert "{{PROJECT_NAME}}" not in text


def test_forge_root_placeholder_substituted(scaffolded_project, forge_root):
    text = (scaffolded_project / ".mcp.json").read_text()
    assert "${FORGE_ROOT}" not in text
    assert str(forge_root) in text
