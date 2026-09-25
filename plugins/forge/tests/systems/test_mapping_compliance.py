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
radios = ["wifi_2g4"]
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


def _write_profile(tmp_path, text: str, *, with_radio_trace: bool = True):
    d = tmp_path / "compliance"
    d.mkdir(parents=True, exist_ok=True)
    (d / "product-profile.toml").write_text(text)
    if with_radio_trace:
        # BASE_PROFILE declares has_radio/radios; the radios.* cross-check (K1) needs a
        # requirements/params file naming the same radio family, or it fails on its own
        # (radios.cross_check_inputs_present / radios.profile_radio_untraced).
        req_dir = tmp_path / "requirements"
        req_dir.mkdir(parents=True, exist_ok=True)
        (req_dir / "requirements.md").write_text(
            "## REQ-ELEC-001\nThe device shall transmit sensor data over Wi-Fi.\n"
            "Rationale: local network connectivity.\nVerify: test\n"
        )
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


def test_no_profile_is_an_error_not_a_pass(tmp_path):
    """K1 (review-2 addendum): a project with no compliance/product-profile.toml at all
    must be an ERROR (non-pass), never SKIP-as-0/pass -- CONTRACTS.md §3 has no N/A
    status, and mapping nothing must not read as success."""
    rc = verify.run(tmp_path, None)
    assert rc == 2
    out = json.loads((tmp_path / "out/verify/compliance.standards_map.json").read_text())
    assert out["status"] == "error"
    assert "product-profile.toml" in out["error"]
    assert "NOT a pass" in out["error"]


# --- K1 (review-2 addendum / FAIL-0001..0004): unknown market codes, radio profile /
# requirements mismatches in both directions, UK + RED-core + spectrum rows, and
# IEC 62368-1 on adapter-powered (not just mains) ICT ---

def test_unknown_market_code_fails_with_the_specific_check_id(tmp_path):
    """FAIL-0001 seeded-wrong case: 'EUU' (a typo of 'EU') is not a recognised market
    code. Before the fix there was no [[market]] vocabulary at all, and any string
    passed straight through to the predicate matcher as a silent no-op."""
    profile = BASE_PROFILE.replace('target_markets = ["US", "EU", "CA"]', 'target_markets = ["US", "EUU"]')
    project = _write_profile(tmp_path, profile)
    rc = verify.run(project, None)
    assert rc == 1
    out = json.loads((project / "out/verify/compliance.standards_map.json").read_text())
    m = next(x for x in out["measurements"] if x["name"] == "profile.target_markets_valid")
    assert m["pass"] is False
    assert "EUU" in str(m["value"])
    assert len(m["remediation"]) >= 10


def test_known_market_codes_pass(tmp_path):
    project = _write_profile(tmp_path, BASE_PROFILE)  # US, EU, CA -- all valid
    rc = verify.run(project, None)
    assert rc == 0
    out = json.loads((project / "out/verify/compliance.standards_map.json").read_text())
    m = next(x for x in out["measurements"] if x["name"] == "profile.target_markets_valid")
    assert m["pass"] is True


def test_radio_named_in_requirements_but_missing_from_profile_fails(tmp_path):
    """FAIL-0002 seeded-wrong case, direction 1: requirements name Bluetooth, but the
    profile's radios list has no bluetooth entry."""
    profile = BASE_PROFILE  # radios = ["wifi_2g4"] only
    project = _write_profile(tmp_path, profile, with_radio_trace=False)
    req_dir = project / "requirements"
    req_dir.mkdir(parents=True, exist_ok=True)
    (req_dir / "requirements.md").write_text(
        "## REQ-ELEC-001\nThe device shall transmit sensor data over Wi-Fi.\nRationale: x.\nVerify: test\n\n"
        "## REQ-ELEC-002\nThe device shall pair over Bluetooth Low Energy (BLE).\nRationale: setup.\nVerify: demo\n"
    )
    rc = verify.run(project, None)
    assert rc == 1
    out = json.loads((project / "out/verify/compliance.standards_map.json").read_text())
    m = next(x for x in out["measurements"] if x["name"] == "radios.requirements_named_radio_missing")
    assert m["pass"] is False
    assert "bluetooth" in str(m["value"])


def test_radio_in_profile_but_untraced_in_requirements_fails(tmp_path):
    """FAIL-0002 seeded-wrong case, direction 2: the profile claims a radar radio that
    no requirement or param text names at all."""
    profile = BASE_PROFILE.replace('radios = ["wifi_2g4"]', 'radios = ["wifi_2g4", "radar_60ghz"]')
    project = _write_profile(tmp_path, profile)  # requirements only name Wi-Fi
    rc = verify.run(project, None)
    assert rc == 1
    out = json.loads((project / "out/verify/compliance.standards_map.json").read_text())
    m = next(x for x in out["measurements"] if x["name"] == "radios.profile_radio_untraced")
    assert m["pass"] is False
    assert "radar" in str(m["value"])


def test_radio_traced_both_ways_passes(tmp_path):
    project = _write_profile(tmp_path, BASE_PROFILE)  # radios=["wifi_2g4"], reqs name Wi-Fi
    rc = verify.run(project, None)
    assert rc == 0
    out = json.loads((project / "out/verify/compliance.standards_map.json").read_text())
    by_name = {m["name"]: m for m in out["measurements"]}
    assert by_name["radios.requirements_named_radio_missing"]["pass"] is True
    assert by_name["radios.profile_radio_untraced"]["pass"] is True


def test_uk_radio_product_maps_red_core_and_spectrum_and_emc_rows(tmp_path):
    """FAIL-0003: a UK-market radio product must match the UK/RED-core/radio-EMC/
    spectrum rows added from R5f (uk-rer-2017, en-301-489-*, en-300-328), not just the
    generic standards a market-less/radio-less profile would already match."""
    profile = BASE_PROFILE.replace('target_markets = ["US", "EU", "CA"]', 'target_markets = ["UK"]')
    project = _write_profile(tmp_path, profile)
    rc = verify.run(project, None)
    assert rc == 0
    map_md = (project / "compliance" / "standards-map.md").read_text()
    for std_id in ("uk-rer-2017", "en-301-489-1", "en-301-489-17", "en-300-328"):
        assert std_id in map_md, f"{std_id} missing from standards-map.md for a UK wifi_2g4 profile"


def test_iec_62368_1_applies_to_adapter_and_usb_powered_ict_not_just_mains(tmp_path):
    """FAIL-0004: an external-adapter/USB-powered (no radio) ICT product must still match
    iec-62368-1 -- the old trigger only fired for power_source == mains."""
    profile = """\
category = "consumer_iot"
power_source = ["usb", "external_adapter"]
has_radio = false
has_pcb = true
has_plastic_enclosure = false
has_web_or_app_ui = false
connects_to_internet = false
contract_manufactured = false
has_safety_function = false
is_toy_or_childcare = false
allows_blank_password = false
target_markets = ["US"]
"""
    project = _write_profile(tmp_path, profile, with_radio_trace=False)
    (project / "requirements").mkdir(parents=True, exist_ok=True)
    (project / "requirements" / "requirements.md").write_text(
        "## REQ-SYS-001\nThe device shall be powered from a USB port or wall adapter.\n"
        "Rationale: no internal battery.\nVerify: inspection\n"
    )
    rc = verify.run(project, None)
    assert rc == 0
    map_md = (project / "compliance" / "standards-map.md").read_text()
    assert "iec-62368-1" in map_md
