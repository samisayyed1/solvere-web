"""checking-ecad verify.py: ERC on the KiCad demo FAILS with the exact violation count,
and a waiver missing an approver is rejected (CONTRACTS.md §9)."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from .conftest import load_skill_module, require_tool

DEMO_DIR = Path.home() / ".forge" / "opt" / "kicad-demos" / "sonde xilinx"
EXPECTED_ERC_VIOLATIONS = 31  # docs/brief/FORGE-BRIEF.md task text; reproduced by `kicad-cli sch erc` directly


@pytest.fixture(autouse=True)
def _tools():
    require_tool("kicad-cli")
    if not DEMO_DIR.exists():
        pytest.skip("KiCad demos not installed at ~/.forge/opt/kicad-demos")


@pytest.fixture
def verify_mod():
    return load_skill_module("checking-ecad")


def _copy_demo(project: Path, *, with_pcb: bool = True) -> Path:
    ecad_dir = project / "ecad"
    ecad_dir.mkdir(parents=True, exist_ok=True)
    dest = ecad_dir / "sonde-xilinx"
    shutil.copytree(DEMO_DIR, dest)
    if not with_pcb:
        (dest / "sonde xilinx.kicad_pcb").unlink()
    return dest


def test_erc_on_demo_fails_with_the_exact_violation_count(verify_mod, tmp_path):
    _copy_demo(tmp_path, with_pcb=False)
    rc = verify_mod.main(["--project", str(tmp_path)])
    assert rc == 1

    result_files = list((tmp_path / "out/verify").glob("ecad.*.json"))
    assert len(result_files) == 1
    result = json.loads(result_files[0].read_text())
    assert result["status"] == "fail"

    warnings = next(m for m in result["measurements"] if m["name"] == "erc_warnings")
    errors = next(m for m in result["measurements"] if m["name"] == "erc_errors")
    assert warnings["value"] == EXPECTED_ERC_VIOLATIONS
    assert warnings["pass"] is False
    assert errors["value"] == 0
    assert errors["pass"] is True

    erc_json = json.loads((tmp_path / "out/verify/erc.sonde xilinx.json").read_text())
    total = sum(len(s["violations"]) for s in erc_json["sheets"])
    assert total == EXPECTED_ERC_VIOLATIONS


def test_waiver_without_approver_is_rejected(verify_mod, tmp_path):
    _copy_demo(tmp_path, with_pcb=False)
    (tmp_path / "ecad" / "waivers.toml").write_text("""\
[[waiver]]
rule_id = "footprint_link_issues"
reason = "Demo board; library metadata not relevant to this smoke test."
# approver deliberately omitted
""")
    rc = verify_mod.main(["--project", str(tmp_path)])
    assert rc == 2
    result = json.loads((tmp_path / "out/verify/ecad.waivers.json").read_text())
    assert result["status"] == "error"
    assert "approver" in result["error"].lower()


def test_waiver_without_reason_is_rejected(verify_mod, tmp_path):
    _copy_demo(tmp_path, with_pcb=False)
    (tmp_path / "ecad" / "waivers.toml").write_text("""\
[[waiver]]
rule_id = "footprint_link_issues"
approver = "jane.doe"
""")
    rc = verify_mod.main(["--project", str(tmp_path)])
    assert rc == 2


def test_valid_waiver_covering_all_occurrences_makes_erc_pass(verify_mod, tmp_path):
    _copy_demo(tmp_path, with_pcb=False)
    (tmp_path / "ecad" / "waivers.toml").write_text(f"""\
[[waiver]]
rule_id = "footprint_link_issues"
reason = "Demo board ships without library metadata; confirmed non-functional for this smoke test."
approver = "jane.doe"
date = "2026-09-25"
max_count = {EXPECTED_ERC_VIOLATIONS}
""")
    rc = verify_mod.main(["--project", str(tmp_path)])
    assert rc == 0
    result_files = list((tmp_path / "out/verify").glob("ecad.*.json"))
    result = json.loads(result_files[0].read_text())
    assert result["status"] == "pass"
    warnings = next(m for m in result["measurements"] if m["name"] == "erc_warnings")
    assert warnings["value"] == 0


def test_partial_waiver_cap_leaves_remainder_failing(verify_mod, tmp_path):
    _copy_demo(tmp_path, with_pcb=False)
    (tmp_path / "ecad" / "waivers.toml").write_text("""\
[[waiver]]
rule_id = "footprint_link_issues"
reason = "Only the first few are reviewed so far."
approver = "jane.doe"
max_count = 5
""")
    rc = verify_mod.main(["--project", str(tmp_path)])
    assert rc == 1
    result_files = list((tmp_path / "out/verify").glob("ecad.*.json"))
    result = json.loads(result_files[0].read_text())
    warnings = next(m for m in result["measurements"] if m["name"] == "erc_warnings")
    assert warnings["value"] == EXPECTED_ERC_VIOLATIONS - 5


def test_no_ecad_files_is_a_clean_skip(verify_mod, tmp_path):
    assert verify_mod.main(["--project", str(tmp_path)]) == 0


def _waived_demo_project(tmp_path):
    """The demo board with its (unrelated) ERC/DRC noise fully waived, so a
    project's overall status/exit code reflects the DFM checks alone."""
    _copy_demo(tmp_path, with_pcb=True)
    (tmp_path / "ecad" / "waivers.toml").write_text(f"""\
[[waiver]]
rule_id = "footprint_link_issues"
reason = "Demo board; library metadata not relevant to this smoke test."
approver = "jane.doe"
max_count = {EXPECTED_ERC_VIOLATIONS}

[[waiver]]
rule_id = "lib_footprint_mismatch"
reason = "Vendored demo library copy differs cosmetically from the project library."
approver = "jane.doe"
max_count = 10
""")
    return tmp_path


def test_dfm_passes_when_board_trace_width_is_above_the_fab_floor(verify_mod, tmp_path):
    """The no-op version of this test (review #1, m1) was named '...fails_when...'
    but only ever asserted a pass and never checked the exit code -- this is
    now the genuine passing case, and the next test is the real seeded-wrong
    failing case."""
    project = _waived_demo_project(tmp_path)
    rc = verify_mod.main(["--project", str(project)])
    assert rc == 0, "with ERC/DRC noise waived, a board comfortably inside every DFM floor must pass overall"
    result_files = list((project / "out/verify").glob("ecad.*.json"))
    result = json.loads(result_files[0].read_text())
    assert result["status"] == "pass"
    dfm_width = next(m for m in result["measurements"] if m["name"] == "dfm_min_track_width")
    # the demo board's measured min track width (0.4318 mm) is well above both fabs'
    # 0.10 mm floor
    assert dfm_width["pass"] is True
    assert dfm_width["value"] == pytest.approx(0.4318, abs=1e-3)


def test_dfm_fails_when_board_trace_width_below_fab_floor(verify_mod, tmp_path, monkeypatch):
    """m1 (review #1) seeded-wrong case: a fab floor genuinely tighter than
    the board's measured value must FAIL the specific dfm_min_track_width
    check and the overall run, not just record a passing measurement."""
    project = _waived_demo_project(tmp_path)
    real_load_fab_rules = verify_mod.load_fab_rules

    def _strict_fab_rules(fab: str) -> dict:
        rules = dict(real_load_fab_rules(fab))
        rules["min_track_width_mm"] = 10.0  # far above the demo board's real 0.4318 mm
        return rules

    monkeypatch.setattr(verify_mod, "load_fab_rules", _strict_fab_rules)
    rc = verify_mod.main(["--project", str(project)])
    assert rc == 1
    result_files = list((project / "out/verify").glob("ecad.*.json"))
    result = json.loads(result_files[0].read_text())
    assert result["status"] == "fail"
    dfm_width = next(m for m in result["measurements"] if m["name"] == "dfm_min_track_width")
    assert dfm_width["pass"] is False
    assert dfm_width["value"] == pytest.approx(0.4318, abs=1e-3)
    assert dfm_width["limit"]["min"] == pytest.approx(10.0)
    assert len(dfm_width["remediation"]) >= 10


# --- m1 (review #1): annular ring and copper-to-edge were never checked ---

def test_annular_ring_and_copper_to_edge_are_measured_and_pass(verify_mod, tmp_path):
    """kicad-cli's `pcb export stats` reports neither value directly -- both
    are extracted via a scratch DRC pass (see _measure_via_scratch_drc) and
    must show up as real measurements, not be silently absent."""
    project = _waived_demo_project(tmp_path)
    rc = verify_mod.main(["--project", str(project)])
    assert rc == 0
    result_files = list((project / "out/verify").glob("ecad.*.json"))
    result = json.loads(result_files[0].read_text())
    by_name = {m["name"]: m for m in result["measurements"]}
    assert "dfm_min_annular_ring" in by_name
    assert "dfm_copper_to_edge" in by_name
    assert by_name["dfm_min_annular_ring"]["unit"] == "mm"
    assert by_name["dfm_min_annular_ring"]["pass"] is True
    assert by_name["dfm_copper_to_edge"]["pass"] is True
    # never mutate the real board or leave the scratch DRC copy inside ecad/
    assert not list((project / "ecad").rglob("*.kicad_dru"))


def test_annular_ring_fails_when_below_a_stricter_floor(verify_mod, tmp_path, monkeypatch):
    """m1 (review #1) seeded-wrong case for the specific check this finding
    named: an annular-ring floor tighter than the board's real minimum
    (0.35 mm) must FAIL, with the exact failing check identified."""
    project = _waived_demo_project(tmp_path)
    real_load_fab_rules = verify_mod.load_fab_rules

    def _strict_fab_rules(fab: str) -> dict:
        rules = dict(real_load_fab_rules(fab))
        rules["min_annular_ring_mm"] = 5.0  # far above the demo board's real ~0.35 mm
        return rules

    monkeypatch.setattr(verify_mod, "load_fab_rules", _strict_fab_rules)
    rc = verify_mod.main(["--project", str(project)])
    assert rc == 1
    result_files = list((project / "out/verify").glob("ecad.*.json"))
    result = json.loads(result_files[0].read_text())
    assert result["status"] == "fail"
    m = next(x for x in result["measurements"] if x["name"] == "dfm_min_annular_ring")
    assert m["pass"] is False
    assert m["limit"]["min"] == pytest.approx(5.0)
    assert m["value"] < 5.0
    assert len(m["remediation"]) >= 10


def test_missing_annular_ring_rule_key_is_a_hard_error_not_a_silent_skip(verify_mod, tmp_path, monkeypatch):
    """m1 (review #1): a fab_rules.toml missing a required key must ERROR
    (exit 2), never silently skip that rule and report a clean pass."""
    project = _waived_demo_project(tmp_path)
    real_load_fab_rules = verify_mod.load_fab_rules

    def _missing_key_fab_rules(fab: str) -> dict:
        rules = dict(real_load_fab_rules(fab))
        del rules["min_annular_ring_mm"]
        return rules

    monkeypatch.setattr(verify_mod, "load_fab_rules", _missing_key_fab_rules)
    rc = verify_mod.main(["--project", str(project)])
    assert rc == 2
    result_files = list((project / "out/verify").glob("ecad.*.json"))
    result = json.loads(result_files[0].read_text())
    assert result["status"] == "error"
    assert "min_annular_ring_mm" in result["error"]


# --- S1 (review-2 addendum): kicad-cli failing to load the schematic must ERROR, never PASS ---

def test_garbage_schematic_errors_not_passes(verify_mod, tmp_path):
    """S1 seeded-wrong case: a `.kicad_sch` that kicad-cli cannot load at all (garbage
    content, not a corrupt-but-parseable board) exits non-{0,5} with no report written --
    before the fix, `run_kicad_cli` ignored the exit code and an absent report was silently
    read as `{}` (0 violations), giving a PASS. Must be ERROR, and the erc.*.json report
    file must never be written for a load that never happened."""
    ecad_dir = tmp_path / "ecad"
    ecad_dir.mkdir(parents=True)
    (ecad_dir / "x.kicad_sch").write_text("this is not a kicad schematic at all, just garbage\n\x00\x01")
    rc = verify_mod.main(["--project", str(tmp_path)])
    assert rc == 2
    result_files = list((tmp_path / "out/verify").glob("ecad.*.json"))
    assert len(result_files) == 1
    result = json.loads(result_files[0].read_text())
    assert result["status"] == "error"
    assert "kicad-cli" in result["error"]
    assert not (tmp_path / "out" / "verify" / "erc.x.json").exists()


# --- tscircuit ERC noise (eval defect): a correct tscircuit export must be ERC-clean,
# but a genuinely floating pin must still fail. Fixtures are the real, unmodified output
# of `TSCI_TELEMETRY_DISABLED=1 tsci build --kicad-project --ci` on the tiny LDO+caps
# circuit in fixtures/tscircuit_ldo_*/index.circuit.tsx (source kept alongside for
# provenance), reproduced directly against kicad-cli before this fix: 17 violations
# (14 endpoint_off_grid, 3 lib_symbol_issues), all warnings, on the CLEAN circuit alone. ---

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def _copy_fixture_sch(fixture_name: str, project: Path) -> Path:
    ecad_dir = project / "ecad"
    ecad_dir.mkdir(parents=True, exist_ok=True)
    dest = ecad_dir / "ldo.kicad_sch"
    shutil.copy(FIXTURES_DIR / fixture_name / "ldo.kicad_sch", dest)
    return dest


def test_tscircuit_export_of_a_correct_circuit_is_erc_clean(verify_mod, tmp_path):
    """A tscircuit LDO-with-caps circuit with every pin connected must export ERC-clean --
    the 17 pre-fix violations (endpoint_off_grid: schematic-editor grid alignment, no
    electrical meaning; lib_symbol_issues: tscircuit's fully self-contained/embedded
    symbols aren't registered in a project sym-lib-table) carry no electrical information."""
    _copy_fixture_sch("tscircuit_ldo_clean", tmp_path)
    rc = verify_mod.main(["--project", str(tmp_path)])
    assert rc == 0
    result_files = list((tmp_path / "out/verify").glob("ecad.*.json"))
    result = json.loads(result_files[0].read_text())
    assert result["status"] == "pass"
    errors = next(m for m in result["measurements"] if m["name"] == "erc_errors")
    warnings = next(m for m in result["measurements"] if m["name"] == "erc_warnings")
    assert errors["value"] == 0
    assert warnings["value"] == 0
    # the raw kicad-cli report on disk still shows all 17 -- nothing was hidden, only
    # excluded from the pass/fail count as non-electrical
    raw = json.loads((tmp_path / "out" / "verify" / "erc.ldo.json").read_text())
    raw_total = sum(len(s["violations"]) for s in raw["sheets"])
    assert raw_total == 17


def test_tscircuit_export_with_a_genuinely_floating_pin_still_fails(verify_mod, tmp_path):
    """No blanket waiver: the same circuit with C_OUT's ground pin left unconnected
    (a real `pin_not_connected` ERC error) must still FAIL, alongside the same
    non-electrical noise types being dropped."""
    _copy_fixture_sch("tscircuit_ldo_floating_pin", tmp_path)
    rc = verify_mod.main(["--project", str(tmp_path)])
    assert rc == 1
    result_files = list((tmp_path / "out/verify").glob("ecad.*.json"))
    result = json.loads(result_files[0].read_text())
    assert result["status"] == "fail"
    errors = next(m for m in result["measurements"] if m["name"] == "erc_errors")
    assert errors["value"] == 1
    assert errors["pass"] is False
    warnings = next(m for m in result["measurements"] if m["name"] == "erc_warnings")
    assert warnings["value"] == 0  # endpoint_off_grid / lib_symbol_issues noise still dropped


def test_drop_nonelectrical_erc_noise_keeps_unresolvable_lib_symbol_issues(verify_mod):
    """drop_nonelectrical_erc_noise unit test: a lib_symbol_issues violation for a symbol
    that is NOT embedded in the schematic's own lib_symbols (a genuinely broken/missing
    reference -- the real case this ERC rule exists to catch) must be kept, not dropped."""
    sch_text = '(kicad_sch (lib_symbols (symbol "Device:R" (pin_names))))'  # no "Ghost:Missing" defined
    violations = [
        {"type": "endpoint_off_grid", "description": "off grid"},
        {"type": "lib_symbol_issues",
         "description": "The current configuration does not include the symbol library 'Device'",
         "items": [{"description": "Symbol R1 [R]"}]},
        {"type": "lib_symbol_issues",
         "description": "Symbol 'Missing' not found in symbol library 'Ghost'",
         "items": [{"description": "Symbol U2 [Missing]"}]},
        {"type": "pin_not_connected", "description": "Pin not connected"},
    ]
    kept = verify_mod.drop_nonelectrical_erc_noise(violations, sch_text)
    kept_types = [(v["type"], v.get("description")) for v in kept]
    assert ("endpoint_off_grid", "off grid") not in kept_types
    assert not any(v["type"] == "lib_symbol_issues" and "Device" in v["description"] for v in kept)
    assert any(v["type"] == "lib_symbol_issues" and "Ghost" in v["description"] for v in kept)
    assert any(v["type"] == "pin_not_connected" for v in kept)
