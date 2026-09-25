"""Tests for intaking-datasheets (CONTRACTS.md §2, §3, §9).

The named seeded-wrong case is "datasheet param without a page reference"
-- a param sourced from text with no page markers must FAIL, not be
silently accepted as evidence (CONTRACTS.md §2: source "required, with a
page ref for datasheets").
"""
from __future__ import annotations

import json
import subprocess
import sys
import tomllib
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[2] / "skills" / "intaking-datasheets"
SCRIPTS_DIR = SKILL_DIR / "scripts"
VERIFY_PY = SCRIPTS_DIR / "verify.py"
FORGE_PYTHON = Path.home() / ".forge" / "bin" / "forge-python"
PY = str(FORGE_PYTHON) if FORGE_PYTHON.exists() else sys.executable

DATASHEET_WITH_PAGES = (
    "ACME Battery Module Datasheet\nModel: ACME-1234\n\n"
    "Electrical characteristics\nCapacity: 3400 mAh\nNominal Voltage: 3.7 V\n"
    "\f\n"
    "Mechanical characteristics\nWall thickness: 2.2 mm\nLength: 65.0 mm\n"
)

INTAKE_SPEC = """
[datasheet]
doc = "ACME-1234 Rev C"
text_file = "docs/datasheets/acme-1234.txt"

[[param]]
id = "battery.capacity_mah"
pattern = 'Capacity:\\s*([\\d.]+)\\s*mAh'
unit = "mAh"

[[param]]
id = "battery.nominal_voltage_v"
pattern = 'Nominal Voltage:\\s*([\\d.]+)\\s*V'
unit = "V"

[[param]]
id = "enclosure.wall_thickness"
pattern = 'Wall thickness:\\s*([\\d.]+)\\s*mm'
unit = "mm"
tol_plus = 0.1
tol_minus = 0.1

[[param]]
id = "battery.cycle_life"
pattern = 'Cycle life:\\s*([\\d.]+)'
unit = "cycles"
"""


def _run_verify(project: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PY, str(VERIFY_PY), "--project", str(project)],
        capture_output=True, text=True, timeout=60,
    )


def _write_good_fixture(project: Path) -> None:
    (project / "docs" / "datasheets").mkdir(parents=True)
    (project / "docs" / "datasheets" / "acme-1234.txt").write_text(DATASHEET_WITH_PAGES)
    (project / "docs" / "datasheets" / "acme-1234-intake.toml").write_text(INTAKE_SPEC)


def test_verify_py_passes_known_answer_extraction(tmp_path):
    _write_good_fixture(tmp_path)
    r = _run_verify(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr

    params = tomllib.loads((tmp_path / "params" / "params.toml").read_text())
    assert params["battery"]["capacity_mah"]["value"] == 3400.0
    assert params["battery"]["capacity_mah"]["status"] == "datasheet"
    assert params["battery"]["capacity_mah"]["source"] == "ACME-1234 Rev C, p.1"
    assert params["enclosure"]["wall_thickness"]["value"] == 2.2
    assert params["enclosure"]["wall_thickness"]["source"] == "ACME-1234 Rev C, p.2"
    assert params["enclosure"]["wall_thickness"]["tol"] == {"minus": 0.1, "plus": 0.1}

    out = json.loads((tmp_path / "out" / "verify" / "mech.datasheet_acme_1234_rev_c.json").read_text())
    assert out["status"] == "pass"
    by_name = {m["name"]: m for m in out["measurements"]}
    assert by_name["matched_params_in_params_toml"]["value"] == 3
    assert by_name["datasheet_params_have_page_ref"]["value"] == 3


def test_datasheet_silence_produces_measurement_procedure_not_a_guess(tmp_path):
    _write_good_fixture(tmp_path)
    r = _run_verify(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr

    params = tomllib.loads((tmp_path / "params" / "params.toml").read_text())
    assert "cycle_life" not in params.get("battery", {}), "a silent param must never get an invented value"

    proc = tmp_path / "docs" / "measurements" / "battery_cycle_life.md"
    assert proc.exists()
    text = proc.read_text()
    assert "5 independent measurements" in text
    assert "0.01 mm" in text  # instrument resolution stated


def test_verify_py_FAILS_when_datasheet_param_has_no_page_reference(tmp_path):
    """The named seeded-wrong case: a param sourced from text with no page markers must FAIL."""
    (tmp_path / "docs" / "datasheets").mkdir(parents=True)
    (tmp_path / "docs" / "datasheets" / "widget.txt").write_text(
        "Widget Datasheet. Weight: 12.5 g. No page breaks in this text at all.\n"
    )
    (tmp_path / "docs" / "datasheets" / "widget-intake.toml").write_text("""
[datasheet]
doc = "Widget Doc"
text_file = "docs/datasheets/widget.txt"

[[param]]
id = "widget.weight_g"
pattern = 'Weight:\\s*([\\d.]+)\\s*g'
unit = "g"
""")
    r = _run_verify(tmp_path)
    assert r.returncode == 1, r.stdout + r.stderr
    out = json.loads((tmp_path / "out" / "verify" / "mech.datasheet_widget_doc.json").read_text())
    assert out["status"] == "fail"
    by_name = {m["name"]: m for m in out["measurements"]}
    assert by_name["datasheet_params_have_page_ref"]["pass"] is False
    assert len(by_name["datasheet_params_have_page_ref"]["remediation"]) >= 10

    params = tomllib.loads((tmp_path / "params" / "params.toml").read_text())
    assert params["widget"]["weight_g"]["source"] == "Widget Doc, p.unknown"


def test_verify_py_ERRORS_on_spec_with_no_params(tmp_path):
    (tmp_path / "docs" / "datasheets").mkdir(parents=True)
    (tmp_path / "docs" / "datasheets" / "empty.txt").write_text("nothing here\n")
    (tmp_path / "docs" / "datasheets" / "empty-intake.toml").write_text("""
[datasheet]
doc = "Empty Doc"
text_file = "docs/datasheets/empty.txt"
""")
    r = _run_verify(tmp_path)
    assert r.returncode == 2, r.stdout + r.stderr


def test_verify_py_is_idempotent_no_duplicate_params_on_rerun(tmp_path):
    _write_good_fixture(tmp_path)
    r1 = _run_verify(tmp_path)
    assert r1.returncode == 0
    r2 = _run_verify(tmp_path)
    assert r2.returncode == 0
    text = (tmp_path / "params" / "params.toml").read_text()
    assert text.count("[battery.capacity_mah]") == 1


def test_verify_py_skips_cleanly_with_no_specs(tmp_path):
    r = _run_verify(tmp_path)
    assert r.returncode == 0
    assert "[SKIP]" in r.stdout


# --- S13 (review-2 addendum): the unit is captured from the datasheet text itself and
# compared to the spec's declared unit, not just trusted from the spec ---

def test_verify_py_FAILS_when_text_unit_disagrees_with_declared_unit(tmp_path):
    """S13 seeded-wrong case: 'Length: 2.56 in' matched by a pattern that captures only
    the number (no unit literal in the pattern), with the spec declaring unit = 'mm'.
    Before the fix the value was written to params.toml as 2.56 mm regardless of what the
    text actually said -- must FAIL, and the mismatched param must never be written."""
    (tmp_path / "docs" / "datasheets").mkdir(parents=True)
    (tmp_path / "docs" / "datasheets" / "widget.txt").write_text(
        "Widget Datasheet\n\fLength: 2.56 in\nWeight: 12.5 g\n"
    )
    (tmp_path / "docs" / "datasheets" / "widget-intake.toml").write_text("""
[datasheet]
doc = "Widget Doc"
text_file = "docs/datasheets/widget.txt"

[[param]]
id = "enclosure.length_mm"
pattern = 'Length:\\s*([\\d.]+)'
unit = "mm"

[[param]]
id = "widget.weight_g"
pattern = 'Weight:\\s*([\\d.]+)\\s*g'
unit = "g"
""")
    r = _run_verify(tmp_path)
    assert r.returncode == 1, r.stdout + r.stderr
    out = json.loads((tmp_path / "out" / "verify" / "mech.datasheet_widget_doc.json").read_text())
    assert out["status"] == "fail"
    by_name = {m["name"]: m for m in out["measurements"]}
    unit_check = by_name["matched_params_unit_agrees_with_text"]
    assert unit_check["pass"] is False
    assert unit_check["value"] == 1
    assert "length_mm" in unit_check["remediation"]
    assert "'in'" in unit_check["remediation"] or '"in"' in unit_check["remediation"]
    assert len(unit_check["remediation"]) >= 10

    params = tomllib.loads((tmp_path / "params" / "params.toml").read_text())
    assert "length_mm" not in params.get("enclosure", {}), "a wrong-unit match must never be written"
    # the correctly-matched param (unit genuinely agrees) still lands in params.toml
    assert params["widget"]["weight_g"]["value"] == 12.5


def test_verify_py_passes_when_text_unit_agrees(tmp_path):
    """Pass case for the same unit-agreement check: the text's unit matches the spec."""
    (tmp_path / "docs" / "datasheets").mkdir(parents=True)
    (tmp_path / "docs" / "datasheets" / "widget.txt").write_text(
        "Widget Datasheet\n\fLength: 25.6 mm\n"
    )
    (tmp_path / "docs" / "datasheets" / "widget-intake.toml").write_text("""
[datasheet]
doc = "Widget Doc"
text_file = "docs/datasheets/widget.txt"

[[param]]
id = "enclosure.length_mm"
pattern = 'Length:\\s*([\\d.]+)'
unit = "mm"
""")
    r = _run_verify(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    params = tomllib.loads((tmp_path / "params" / "params.toml").read_text())
    assert params["enclosure"]["length_mm"]["value"] == 25.6
