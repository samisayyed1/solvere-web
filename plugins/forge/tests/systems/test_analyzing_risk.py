"""analyzing-risk: ap.action_priority (a sourced approximation of the AIAG &
VDA Action Priority method -- see skills/analyzing-risk/references/dfmea-ap.md
for the sourcing gap) and scripts/verify.py's DFMEA check."""
from __future__ import annotations

import csv
import json

import pytest

from .conftest import load_skill_module

ap = load_skill_module("analyzing-risk", "ap.py")
verify = load_skill_module("analyzing-risk", "verify.py")


# Known S/O/D triples and the AP band this module's documented, sourced rule
# implies (severity dominates, then occurrence, then detection -- R5b). See
# ap.py's module docstring: this is NOT the licensed handbook's table.
@pytest.mark.parametrize("severity,occurrence,detection,expected", [
    (10, 8, 8, "High"),    # critical severity, real occurrence -> always High
    (9, 5, 5, "High"),
    (10, 1, 2, "Medium"),  # critical severity but cause designed out + good detection
    (8, 6, 5, "High"),     # high severity, moderate-high occurrence -> High
    (8, 2, 5, "Medium"),   # high severity, low occurrence -> Medium
    (8, 1, 2, "Low"),      # high severity, occurrence designed out, good detection -> Low
    (6, 8, 5, "Medium"),   # moderate severity, high occurrence -> Medium
    (6, 5, 8, "Medium"),   # moderate severity, moderate occurrence, poor detection -> Medium
    (6, 5, 2, "Low"),      # moderate severity, moderate occurrence, good detection -> Low
    (3, 9, 9, "Low"),      # low severity dominates regardless of O/D
    (1, 10, 10, "Low"),    # severity 1 always Low
])
def test_known_sod_triples(severity, occurrence, detection, expected):
    result = ap.action_priority(severity, occurrence, detection)
    assert result.ap == expected
    assert result.approximate is True
    assert "AIAG & VDA" in result.note


def test_critical_severity_never_low():
    """R5b: top severities are reserved for safety/health/regulatory effects
    -- this approximation must never let S>=9 read as Low, for any O/D."""
    for o in range(1, 11):
        for d in range(1, 11):
            assert ap.action_priority(9, o, d).ap != "Low"
            assert ap.action_priority(10, o, d).ap != "Low"


@pytest.mark.parametrize("bad", [0, 11, -1, 3.5])
def test_out_of_range_sod_raises(bad):
    with pytest.raises(ValueError):
        ap.action_priority(bad, 5, 5)


DFMEA_HEADER = (
    "id,item,function,failure_mode,effect,severity,cause,occurrence,"
    "current_controls,detection,action,owner,due_date\n"
)


def _write_dfmea(tmp_path, rows: str):
    d = tmp_path / "analysis"
    d.mkdir(parents=True, exist_ok=True)
    (d / "dfmea.csv").write_text(DFMEA_HEADER + rows)
    return tmp_path


def test_high_ap_with_tracked_action_passes(tmp_path):
    rows = (
        "DFMEA-001,enclosure lid,retain water seal,gasket compresses unevenly,"
        "water ingress damages PCB,9,gasket groove tolerance stack,5,"
        "visual inspection at assembly,6,add compression test to line QC,"
        "J. Rivera,2026-11-01\n"
    )
    project = _write_dfmea(tmp_path, rows)
    assert verify.run(project, None) == 0
    out = json.loads((project / "out/verify/safety.dfmea_ap.json").read_text())
    assert out["status"] == "pass"


def test_high_ap_without_tracked_action_fails(tmp_path):
    rows = (
        "DFMEA-002,battery connector,deliver power,connector backs out under vibration,"
        "device loses power,8,no strain relief on wire,6,none,7,,,\n"
    )
    project = _write_dfmea(tmp_path, rows)
    assert verify.run(project, None) == 1
    out = json.loads((project / "out/verify/safety.dfmea_ap.json").read_text())
    assert out["status"] == "fail"
    failing = [m["name"] for m in out["measurements"] if not m["pass"]]
    assert any("high_ap_has_action" in name for name in failing)


def test_low_severity_never_blocks_even_unmitigated(tmp_path):
    rows = (
        "DFMEA-003,cosmetic label,brand identity,label slightly misaligned,"
        "minor cosmetic defect,2,print registration drift,8,none,8,,,\n"
    )
    project = _write_dfmea(tmp_path, rows)
    assert verify.run(project, None) == 0


def test_invalid_sod_range_fails(tmp_path):
    rows = (
        "DFMEA-004,widget,do thing,breaks,stops working,15,x,5,none,5,,,\n"
    )
    project = _write_dfmea(tmp_path, rows)
    assert verify.run(project, None) == 1
    out = json.loads((project / "out/verify/safety.dfmea_ap.json").read_text())
    failing = [m["name"] for m in out["measurements"] if not m["pass"]]
    assert any("sod_valid" in name for name in failing)


def test_no_dfmea_file_is_skip(tmp_path):
    assert verify.run(tmp_path, None) == 0
    assert not (tmp_path / "out").exists()
