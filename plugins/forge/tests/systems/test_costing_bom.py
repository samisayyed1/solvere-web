"""costing-bom/scripts/verify.py: BOM roll-up and single-source/lifecycle
(NRND/EOL) risk flags (CONTRACTS-style check-result contract)."""
from __future__ import annotations

import json

from .conftest import load_skill_module

verify = load_skill_module("costing-bom")

BOM_HEADER = (
    "ref_des,description,mpn,manufacturer,qty_per_unit,lifecycle,lead_time_weeks,"
    "alternates,risk_note,price_1,price_100,price_1000\n"
)


def _write_bom(tmp_path, rows: str):
    d = tmp_path / "bom"
    d.mkdir(parents=True, exist_ok=True)
    (d / "bom.csv").write_text(BOM_HEADER + rows)
    return tmp_path


def _failing_names(out: dict) -> list[str]:
    return [m["name"] for m in out["measurements"] if not m["pass"]]


def test_fully_covered_bom_passes(tmp_path):
    rows = (
        "R1,10k resistor,RC0402FR-0710KL,Yageo,2,Active,4,"
        "RC0402JR-0710KL;ERJ-2RKF1002X,,0.02,0.01,0.005\n"
        "U1,MCU,STM32F103C8T6,STMicro,1,NRND,26,,"
        "\"plan: migrate to STM32F103C8T7 by Q1; owner J. Chen\",3.10,2.40,1.90\n"
    )
    project = _write_bom(tmp_path, rows)
    assert verify.run(project, None) == 0
    out = json.loads((project / "out/verify/supply.bom_rollup.json").read_text())
    assert out["status"] == "pass"
    rollup = json.loads((project / "out/verify/bom.rollup.json").read_text())
    assert rollup["single_source_count"] == 1  # U1 has no alternates
    assert rollup["lifecycle_risk_count"] == 1  # U1 is NRND
    assert rollup["tier_totals_usd"]["1"] == 3.14  # 2*0.02 + 1*3.10


def test_unacknowledged_single_source_fails(tmp_path):
    rows = "U2,Regulator,LM317T,TI,1,Active,8,,,0.55,0.40,0.35\n"
    project = _write_bom(tmp_path, rows)
    assert verify.run(project, None) == 1
    out = json.loads((project / "out/verify/supply.bom_rollup.json").read_text())
    assert any("single_source_acknowledged" in n for n in _failing_names(out))


def test_unacknowledged_eol_fails(tmp_path):
    rows = (
        "U3,Legacy driver,XYZ123,Acme,1,EOL,52,ALT-XYZ123;ALT2-XYZ123,,1.00,0.80,0.60\n"
    )
    project = _write_bom(tmp_path, rows)
    assert verify.run(project, None) == 1
    out = json.loads((project / "out/verify/supply.bom_rollup.json").read_text())
    assert any("lifecycle_risk_acknowledged" in n for n in _failing_names(out))


def test_acknowledged_eol_with_risk_note_passes(tmp_path):
    rows = (
        "U3,Legacy driver,XYZ123,Acme,1,EOL,52,ALT-XYZ123,"
        "\"last-time-buy placed 2026-10-01; owner P. Singh\",1.00,0.80,0.60\n"
    )
    project = _write_bom(tmp_path, rows)
    assert verify.run(project, None) == 0


def test_unpriced_line_fails(tmp_path):
    rows = "R9,resistor,ABC,Yageo,1,Active,4,ALT-ABC,,,,\n"
    project = _write_bom(tmp_path, rows)
    assert verify.run(project, None) == 1
    out = json.loads((project / "out/verify/supply.bom_rollup.json").read_text())
    assert any(n == "bom.all_lines_priced" for n in _failing_names(out))


def test_no_bom_file_is_skip(tmp_path):
    assert verify.run(tmp_path, None) == 0
    assert not (tmp_path / "out").exists()
