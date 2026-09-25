"""Sanity/lint checks on checking-dfm/references/rules/*.toml: every rule is
well-formed, sourced, and resolvable, whether or not it is exercised by the
fixture project. Guards against a future edit silently breaking the tables
(CONTRACTS §3: every rule number must cite its source)."""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

RULES_DIR = Path(__file__).resolve().parents[2] / "skills" / "checking-dfm" / "references" / "rules"
PROCESS_FILES = [p for p in RULES_DIR.glob("*.toml") if p.stem != "snap_fit"]
KNOWN_FAMILIES = {
    "geometry.min_wall", "geometry.hole_diameter", "geometry.clearance", "geometry.draft",
    "geometry.overhang", "geometry.min_radius", "geometry.hole_edge", "geometry.boss_rib", "unsupported",
}
KNOWN_COMPARISONS = {
    "min", "max", "min_from_vertical", "min_from_horizontal", "min_ratio_of_wall", "max_ratio_of_wall",
}


@pytest.mark.parametrize("path", PROCESS_FILES, ids=lambda p: p.stem)
def test_process_rule_table_is_well_formed(path):
    doc = tomllib.loads(path.read_text())
    rules = doc.get("rule", [])
    assert rules, f"{path.name} has no [[rule]] entries"
    seen_ids = set()
    for rule in rules:
        assert rule.get("id"), f"{path.name}: a rule is missing 'id'"
        assert rule["id"] not in seen_ids, f"{path.name}: duplicate rule id {rule['id']!r}"
        seen_ids.add(rule["id"])
        assert rule.get("check_family") in KNOWN_FAMILIES, f"{path.name}:{rule['id']}: unknown check_family"
        assert rule.get("source"), f"{path.name}:{rule['id']}: missing a 'source' citation"
        if rule["check_family"] != "unsupported":
            assert rule.get("comparison") in KNOWN_COMPARISONS, f"{path.name}:{rule['id']}: unknown comparison"
            has_value = any(k in rule for k in ("value_mm", "value_deg", "value_ratio"))
            assert has_value, f"{path.name}:{rule['id']}: no value_mm/value_deg/value_ratio"
        # 'conflict' key must exist (possibly empty string) per the documented convention.
        assert "conflict" in rule, f"{path.name}:{rule['id']}: missing 'conflict' field (use \"\" if none)"


def test_every_rule_source_mentions_a_cited_provider():
    # Loose smoke check that sources look like citations, not placeholders.
    placeholders = {"TODO", "TBD", "FIXME", "xxx"}
    for path in PROCESS_FILES:
        doc = tomllib.loads(path.read_text())
        for rule in doc.get("rule", []):
            source = rule["source"]
            assert not any(p in source for p in placeholders), f"{path.name}:{rule['id']}: placeholder source"
            assert len(source) > 15, f"{path.name}:{rule['id']}: source too short to be a real citation"


def test_snap_fit_table_is_well_formed():
    doc = tomllib.loads((RULES_DIR / "snap_fit.toml").read_text())
    meta = doc["meta"]
    for key in ("frequent_use_factor", "k_constant_rectangle", "k_tapered_to_half_thickness",
                "k_tapered_width_quarter"):
        assert key in meta, f"snap_fit.toml [meta] missing {key!r}"
    materials = doc.get("material", [])
    assert len(materials) >= 10
    seen = set()
    for m in materials:
        assert m.get("id") and m["id"] not in seen
        seen.add(m["id"])
        assert m.get("name")
        assert isinstance(m.get("allowable_strain_once_pct"), (int, float))
        assert 0 < m["allowable_strain_once_pct"] < 100
        assert m.get("source")


def test_rule_ids_referenced_by_the_fixture_project_actually_exist():
    fixture_dfm = Path(__file__).resolve().parents[1] / "fixtures" / "mech_project" / "requirements" / "dfm"
    tables = {p.stem: {r["id"] for r in tomllib.loads(p.read_text()).get("rule", [])} for p in PROCESS_FILES}
    for spec_path in fixture_dfm.glob("*.toml"):
        spec = tomllib.loads(spec_path.read_text())
        process = spec["part"]["process"]
        for check in spec.get("check", []):
            assert check["rule"] in tables[process], f"{spec_path.name} references unknown rule {check['rule']!r}"
