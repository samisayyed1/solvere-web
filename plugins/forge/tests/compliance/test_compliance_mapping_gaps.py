"""mapping-compliance: regression tests for FAIL-0001..FAIL-0004 (docs/failures/).

Each seeded-wrong case asserts the SPECIFIC failing measurement (sub-check id)
in out/verify/compliance.standards_map.json, not just the exit code.

To prove these tests fail on the original skill, point them at a copy of it:

    FORGE_COMPLIANCE_VERIFY=/path/to/old/skills/mapping-compliance/scripts/verify.py \\
        forge-python -m pytest plugins/forge/tests/compliance -q

(the old copy needs ``lib/`` three levels up, as in the plugin). The capture
records in docs/failures/ quote that run.

Forge must stay product-agnostic (test_product_agnostic.py) -- this file never names a
real product. The optional real-product regression test below is opted into by pointing
``FORGE_REAL_PRODUCT_DIR`` at any product's root (a sibling repo scaffolded by
/forge:new-project, or one nested in this checkout); it SKIPs otherwise.
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = PLUGIN_ROOT.parents[1]
SCRIPT = Path(os.environ.get("FORGE_COMPLIANCE_VERIFY")
              or PLUGIN_ROOT / "skills" / "mapping-compliance" / "scripts" / "verify.py")
REAL_PRODUCT_ENV = "FORGE_REAL_PRODUCT_DIR"
REAL_PRODUCT = Path(os.environ[REAL_PRODUCT_ENV]) if os.environ.get(REAL_PRODUCT_ENV) else None
RESULT = "out/verify/compliance.standards_map.json"


def _load():
    spec = importlib.util.spec_from_file_location("forge_compliance_gaps_verify", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


verify = _load()

REQS_BLE = """\
# Requirements

### REQ-RF-001
The tag shall advertise its temperature reading over Bluetooth LE every 10 s.
"""

REQS_NO_RADIO = """\
# Requirements

### REQ-MECH-001
The enclosure wall shall be at least 2.0 mm thick, and the cable exit shall use a strain relief.

Rationale: see the dimension TABLE in params; the M3 thread is cut in the boss.
"""

PROFILE = """\
category = "consumer_iot"
power_source = {power}
has_radio = {has_radio}
{radios_line}
has_pcb = true
has_plastic_enclosure = true
has_web_or_app_ui = false
connects_to_internet = false
contract_manufactured = false
has_safety_function = false
is_toy_or_childcare = false
allows_blank_password = false
target_markets = {markets}
"""


def make_project(tmp_path: Path, *, markets='["US", "EU"]', power='["battery"]', has_radio="true",
                 radios='radios = ["ble"]', reqs: str | None = REQS_BLE, params: str | None = None,
                 extra: str = "") -> Path:
    (tmp_path / "compliance").mkdir(parents=True, exist_ok=True)
    (tmp_path / "compliance" / "product-profile.toml").write_text(
        PROFILE.format(markets=markets, power=power, has_radio=has_radio, radios_line=radios) + extra)
    if reqs is not None:
        (tmp_path / "requirements").mkdir(exist_ok=True)
        (tmp_path / "requirements" / "requirements.md").write_text(reqs)
    if params is not None:
        (tmp_path / "params").mkdir(exist_ok=True)
        (tmp_path / "params" / "params.toml").write_text(params)
    return tmp_path


def result(project: Path) -> dict:
    return json.loads((project / RESULT).read_text())


def failing(project: Path) -> set[str]:
    return {m["name"] for m in result(project)["measurements"] if not m["pass"]}


def mapped(project: Path) -> set[str]:
    text = (project / "compliance" / "standards-map.md").read_text()
    return {line.split()[1] for line in text.splitlines() if line.startswith("## ") and " -- " in line}


# ------------------------------------------------------------ FAIL-0001 market codes

def test_typo_market_code_fails_naming_valid_codes(tmp_path):
    p = make_project(tmp_path, markets='["US", "EUU"]')
    assert verify.run(p, None) == 1
    assert "profile.target_markets_valid" in failing(p)
    m = next(m for m in result(p)["measurements"] if m["name"] == "profile.target_markets_valid")
    assert m["value"] == "EUU"
    for code in ("US", "CA", "EU", "UK"):
        assert f"'{code}'" in m["remediation"]
    assert "R5f" in m["remediation"]  # the valid list is sourced


def test_gb_alias_maps_to_uk_and_passes(tmp_path):
    p = make_project(tmp_path, markets='["GB"]')
    assert verify.run(p, None) == 0, failing(p)
    assert "uk-rer-2017" in mapped(p)


# ------------------------------------------------------------ FAIL-0002 radio cross-check

def test_profile_missing_a_radio_the_requirements_name_fails(tmp_path):
    p = make_project(tmp_path, has_radio="false", radios="radios = []")
    assert verify.run(p, None) == 1
    assert "radios.requirements_named_radio_missing" in failing(p)
    m = next(m for m in result(p)["measurements"] if m["name"] == "radios.requirements_named_radio_missing")
    assert m["value"] == "bluetooth" and "requirements/requirements.md:4" in m["remediation"]


def test_has_radio_false_with_no_radios_field_still_fails(tmp_path):
    p = make_project(tmp_path, has_radio="false", radios="")
    assert verify.run(p, None) == 1
    assert "radios.requirements_named_radio_missing" in failing(p)


def test_radio_named_only_in_params_is_caught(tmp_path):
    p = make_project(tmp_path, has_radio="false", radios="radios = []", reqs=REQS_NO_RADIO,
                     params='[radar]\nfreq_ghz = 60  # 58 GHz to 62 GHz FMCW\n')
    assert verify.run(p, None) == 1
    m = next(m for m in result(p)["measurements"] if m["name"] == "radios.requirements_named_radio_missing")
    assert m["value"] == "radar" and "params/params.toml:1" in m["remediation"]


def test_profile_claims_radio_no_requirement_names_is_a_fail(tmp_path):
    """Decision: an untraced radio claim is a FAIL (the Check format has no warning status)."""
    p = make_project(tmp_path, radios='radios = ["ble", "wifi_2g4"]')
    assert verify.run(p, None) == 1
    assert failing(p) == {"radios.profile_radio_untraced"}
    m = next(m for m in result(p)["measurements"] if m["name"] == "radios.profile_radio_untraced")
    assert m["value"] == "wifi"


def test_has_radio_contradicting_radios_list_fails(tmp_path):
    p = make_project(tmp_path, has_radio="false", radios='radios = ["ble"]')
    assert verify.run(p, None) == 1
    assert "radios.has_radio_consistent" in failing(p)


def test_has_radio_true_without_radios_list_fails(tmp_path):
    p = make_project(tmp_path, radios="")
    assert verify.run(p, None) == 1
    assert "profile.radios_declared" in failing(p)


def test_unknown_radio_id_fails(tmp_path):
    p = make_project(tmp_path, radios='radios = ["bluetooth_le"]')
    assert verify.run(p, None) == 1
    assert "profile.radios_valid" in failing(p)


def test_no_false_positive_on_table_cable_thread(tmp_path):
    """'TABLE', 'cable', 'thread', 'wall' never name a radio."""
    p = make_project(tmp_path, has_radio="false", radios="radios = []", reqs=REQS_NO_RADIO,
                     params="[enclosure]\nwall = 2.0\ncable_d = 4.0\nthread = 'M3'\n")
    assert verify.run(p, None) == 0, failing(p)


def test_requirement_that_rules_a_radio_out_can_be_excluded(tmp_path):
    reqs = REQS_NO_RADIO + "\n### REQ-SEC-001\nThe device shall not include a Wi-Fi radio.\n"
    p = make_project(tmp_path, has_radio="false", radios="radios = []", reqs=reqs)
    assert verify.run(p, None) == 1
    assert failing(p) == {"radios.requirements_named_radio_missing"}
    p2 = make_project(tmp_path / "b", has_radio="false", radios="radios = []", reqs=reqs,
                      extra='\n[radios_excluded]\nwifi = "REQ-SEC-001 forbids Wi-Fi"\n')
    assert verify.run(p2, None) == 0, failing(p2)


def test_no_requirements_or_params_fails_cross_check(tmp_path):
    p = make_project(tmp_path, reqs=None)
    assert verify.run(p, None) == 1
    assert "radios.cross_check_inputs_present" in failing(p)


# ------------------------------------------------------------ FAIL-0003 missing rows

def test_uk_market_maps_the_uk_rows(tmp_path):
    p = make_project(tmp_path, markets='["UK"]', extra="")
    (p / "compliance" / "product-profile.toml").write_text(
        (p / "compliance" / "product-profile.toml").read_text().replace(
            "connects_to_internet = false", "connects_to_internet = true"))
    assert verify.run(p, None) == 0, failing(p)
    assert {"uk-ukca-route", "uk-rer-2017", "uk-psti"} <= mapped(p)
    assert "uk-emc-2016" not in mapped(p)  # RER 2017 equipment is outside the EMC Regs (reg 3(2)(a))


def test_uk_non_radio_product_maps_uk_emc_regs(tmp_path):
    p = make_project(tmp_path, markets='["UK"]', has_radio="false", radios="radios = []", reqs=REQS_NO_RADIO)
    assert verify.run(p, None) == 0, failing(p)
    assert "uk-emc-2016" in mapped(p) and "uk-rer-2017" not in mapped(p)


def test_eu_2g4_radio_maps_en_300_328_and_en_301_489(tmp_path):
    p = make_project(tmp_path, markets='["EU"]')
    assert verify.run(p, None) == 0, failing(p)
    assert {"en-300-328", "en-301-489-1", "en-301-489-17",
            "eu-red-3-1-a", "eu-red-3-1-b", "eu-red-3-2"} <= mapped(p)
    assert "en-305-550-radar-60ghz" not in mapped(p)


@pytest.mark.parametrize("market,rows", [
    ("EU", {"en-305-550-radar-60ghz", "en-301-489-3", "eu-red-3-2"}),
    ("UK", {"en-305-550-radar-60ghz", "en-301-489-3", "uk-rer-2017"}),
    ("US", {"fcc-15-255"}),
    ("CA", {"ised-rss-210"}),
])
def test_60ghz_radar_maps_spectrum_rows_per_market(tmp_path, market, rows):
    reqs = "# R\n### REQ-SYS-001\nThe 60 GHz FMCW radar shall detect presence at 3 m.\n"
    p = make_project(tmp_path, markets=f'["{market}"]', radios='radios = ["radar_60ghz"]', reqs=reqs)
    assert verify.run(p, None) == 0, failing(p)
    got = mapped(p)
    assert rows <= got, rows - got
    assert not {"en-300-328", "fcc-15-247", "ised-rss-247"} & got  # no 2.4 GHz rows for a radar only


def test_every_r5f_row_is_tagged_and_human_flagged():
    data = verify.tomllib.loads(verify.STANDARDS_DATA.read_text())
    assert verify.rows_missing_sourcing(data["standard"]) == []
    r5f = [s for s in data["standard"] if "R5f" in verify._as_list(s["source_file"])]
    assert len(r5f) >= 17
    for s in r5f:
        assert s["tag"] in ("V", "U") and s["source_url"].startswith("http")
        assert s["human_confirms_applicability"] is True


def test_unsourced_row_fails_data_check(tmp_path, monkeypatch):
    bad = tmp_path / "standards.toml"
    bad.write_text(verify.STANDARDS_DATA.read_text() + '\n[[standard]]\nid = "made-up"\nname = "x"\n'
                   'edition = "1"\nbody = "b"\nsource_file = "R5f"\ntrigger = "t"\nneeds_human = "h"\n'
                   'applies_if = [ { field = "has_pcb", op = "true", value = true } ]\n')
    monkeypatch.setattr(verify, "STANDARDS_DATA", bad)
    p = make_project(tmp_path / "p")
    assert verify.run(p, None) == 1
    assert "data.rows_sourced" in failing(p)


# ------------------------------------------------------------ FAIL-0004 IEC 62368-1 trigger

@pytest.mark.parametrize("power", ['["usb", "external_adapter"]', '["external_adapter"]', '["mains"]',
                                   '"battery_and_mains"', '["battery"]'])
def test_powered_ict_equipment_maps_iec_62368_1(tmp_path, power):
    p = make_project(tmp_path, power=power)
    assert verify.run(p, None) == 0, failing(p)
    assert "iec-62368-1" in mapped(p)


def test_documented_string_mains_maps_iec_62368_1(tmp_path):
    """The SKILL.md example wrote power_source = "mains" (a string); the old 'in' op never matched it."""
    p = make_project(tmp_path, power='"mains"')
    assert verify.run(p, None) == 0, failing(p)
    assert "iec-62368-1" in mapped(p)


def test_medical_device_does_not_map_iec_62368_1(tmp_path):
    p = make_project(tmp_path, power='["usb"]')
    prof = p / "compliance" / "product-profile.toml"
    prof.write_text(prof.read_text().replace('category = "consumer_iot"', 'category = "medical"'))
    assert verify.run(p, None) == 0, failing(p)
    assert "iec-62368-1" not in mapped(p) and "iec-60601-1" in mapped(p)


def test_unknown_power_source_fails(tmp_path):
    p = make_project(tmp_path, power='["usb_c_5v_external_adapter"]')
    assert verify.run(p, None) == 1
    assert "profile.power_source_valid" in failing(p)


# ------------------------------------------------------------ absent profile: never a pass

def test_missing_profile_is_an_error_not_a_pass(tmp_path):
    assert verify.run(tmp_path, None) == 2
    r = result(tmp_path)
    assert r["status"] == "error" and "NOT a pass" in r["error"]


def test_missing_profile_via_cli_exits_2(tmp_path):
    proc = subprocess.run([sys.executable, str(SCRIPT), "--project", str(tmp_path)],
                          capture_output=True, text=True, timeout=60)
    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert "[FORGE_CHECK_ID_PREFIX] compliance.standards_map" in proc.stdout
    assert "[PASS]" not in proc.stdout


# ------------------------------------------------------------ pass case + real-product regression

def test_consistent_profile_passes(tmp_path):
    p = make_project(tmp_path, markets='["US", "EU", "UK", "CA"]', power='["usb", "external_adapter"]')
    assert verify.run(p, None) == 0, failing(p)
    assert result(p)["status"] == "pass"
    text = (p / "compliance" / "standards-map.md").read_text()
    assert "not a compliance determination" in text
    assert "a qualified human confirms whether it applies" in text


@pytest.mark.skipif(not REAL_PRODUCT or not (REAL_PRODUCT / "compliance" / "product-profile.toml").is_file(),
                    reason=f"set ${REAL_PRODUCT_ENV} to a real product's root to run this regression test")
def test_real_product_regression(tmp_path):
    """A real product's profile, copied to tmp: as written it now FAILS (it used to pass with 11 rows
    and no UK/RED/radio-spectrum/IEC 62368-1 rows); with its radios declared and its power source in
    the vocabulary, the missing rows appear. This test is opted into per-machine via
    ``FORGE_REAL_PRODUCT_DIR`` (see the module docstring) -- Forge's own test source never names a
    real product, and the literal profile text below is this particular product's own, read from its
    files at runtime, not hard-coded here."""
    for d in ("compliance", "requirements", "params"):
        shutil.copytree(REAL_PRODUCT / d, tmp_path / "orig" / d)
    orig = tmp_path / "orig"
    assert verify.run(orig, None) == 1
    assert {"profile.power_source_valid", "profile.radios_declared",
            "radios.requirements_named_radio_missing"} <= failing(orig)

    shutil.copytree(orig, tmp_path / "fixed")
    fixed = tmp_path / "fixed"
    prof = fixed / "compliance" / "product-profile.toml"
    text = prof.read_text()
    assert 'power_source = ["usb_c_5v_external_adapter"]' in text
    text = text.replace('power_source = ["usb_c_5v_external_adapter"]', 'power_source = ["usb", "external_adapter"]')
    text = text.replace("has_radio = true\n",
                        'has_radio = true\nradios = ["radar_60ghz", "wifi_2g4", "ble", "ieee802154_2g4"]\n', 1)
    prof.write_text(text)
    assert verify.run(fixed, None) == 0, failing(fixed)
    expected = {
        "iec-62368-1", "uk-ukca-route", "uk-rer-2017", "uk-psti",
        "eu-red-3-1-a", "eu-red-3-1-b", "eu-red-3-2",
        "en-301-489-1", "en-301-489-17", "en-301-489-3", "en-300-328", "en-305-550-radar-60ghz",
        "fcc-15-247", "fcc-15-255", "ised-rss-247", "ised-rss-210",
    }
    got = mapped(fixed)
    assert expected <= got, expected - got
    assert "uk-emc-2016" not in got
