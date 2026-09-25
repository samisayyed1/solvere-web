"""mapping-compliance/scripts/verify.py: product-profile -> applicable
standards map, and the EN 18031 restricted-clause tripwires (R5e)."""
from __future__ import annotations

import json

from .conftest import load_skill_module

verify = load_skill_module("mapping-compliance")

BASE_PROFILE = """\
category = "consumer_iot"
power_source = "battery"
has_radio = true
has_pcb = true
has_plastic_enclosure = true
has_web_or_app_ui = true
connects_to_internet = true
contract_manufactured = true
has_safety_function = false
is_toy_or_childcare = false
allows_blank_password = false
target_markets = ["US", "EU", "CA"]
"""


def _write_profile(tmp_path, text: str):
    d = tmp_path / "compliance"
    d.mkdir(parents=True, exist_ok=True)
    (d / "product-profile.toml").write_text(text)
    return tmp_path


def test_well_formed_profile_passes_and_generates_disclaimer(tmp_path):
    project = _write_profile(tmp_path, BASE_PROFILE)
    assert verify.run(project, None) == 0
    map_md = (project / "compliance" / "standards-map.md").read_text()
    assert "not a compliance determination" in map_md
    assert "ised-rss" in map_md or "fcc-part15" in map_md  # radio + US/CA market matched


def test_blank_password_tripwire_unmitigated_fails(tmp_path):
    profile = BASE_PROFILE.replace("allows_blank_password = false", "allows_blank_password = true")
    project = _write_profile(tmp_path, profile)
    assert verify.run(project, None) == 1
    out = json.loads((project / "out/verify/compliance.standards_map.json").read_text())
    assert any(m["name"] == "tripwire.no_blank_password_unmitigated" and not m["pass"]
               for m in out["measurements"])


def test_blank_password_tripwire_mitigated_passes(tmp_path):
    profile = (
        BASE_PROFILE.replace("allows_blank_password = false", "allows_blank_password = true")
        + 'password_mitigation_note = "notified body route planned; owner J. Doe; 2026-12-01"\n'
    )
    project = _write_profile(tmp_path, profile)
    assert verify.run(project, None) == 0


def test_missing_required_field_fails(tmp_path):
    project = _write_profile(tmp_path, 'power_source = "battery"\ntarget_markets = ["US"]\n')
    assert verify.run(project, None) == 1
    out = json.loads((project / "out/verify/compliance.standards_map.json").read_text())
    assert any(m["name"] == "profile.required_fields" and not m["pass"] for m in out["measurements"])


def test_no_profile_is_skip(tmp_path):
    assert verify.run(tmp_path, None) == 0
    assert not (tmp_path / "out").exists()
