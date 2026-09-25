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


def test_dfm_fails_when_board_trace_width_below_fab_floor(verify_mod, tmp_path):
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
    rc = verify_mod.main(["--project", str(tmp_path)])
    result_files = list((tmp_path / "out/verify").glob("ecad.*.json"))
    result = json.loads(result_files[0].read_text())
    dfm_width = next((m for m in result["measurements"] if m["name"] == "dfm_min_track_width"), None)
    assert dfm_width is not None
    # the demo board's measured min track width (0.4318 mm) is well above both fabs'
    # 0.10 mm floor, so this measurement itself should pass regardless of overall status
    assert dfm_width["pass"] is True
    assert dfm_width["value"] == pytest.approx(0.4318, abs=1e-3)
