"""Core contract libs: check results and evidence (CONTRACTS.md §3-4). Each protection has a failing case."""
from __future__ import annotations

import json

import pytest

from forge import checkresult, evidence
from forge.checkresult import Check, CheckContractError


def test_passing_check_writes_schema_result(tmp_path):
    chk = Check("geometry.volume", "cad/box.py", project=tmp_path)
    chk.measure("volume", 964.66, "mm3", equals=964.6571, tol=0.01)
    assert chk.finish() == 0
    out = json.loads((tmp_path / "out/verify/geometry.volume.json").read_text())
    assert out["schema"] == "forge.check/1" and out["status"] == "pass"


def test_failing_measurement_FAILS_and_carries_remediation(tmp_path):
    chk = Check("geometry.min_wall", "cad/box.py", project=tmp_path)
    chk.measure("min_wall", 1.62, "mm", min=2.0, remediation="Thicken the lip to >= 2.0 mm.")
    assert chk.finish() == 1
    out = json.loads((tmp_path / "out/verify/geometry.min_wall.json").read_text())
    assert out["status"] == "fail" and out["measurements"][0]["remediation"]


def test_failure_without_remediation_is_a_contract_error(tmp_path):
    chk = Check("geometry.min_wall", "cad/box.py", project=tmp_path)
    with pytest.raises(CheckContractError):
        chk.measure("min_wall", 1.0, "mm", min=2.0)


def test_limitless_or_unitless_measurement_rejected(tmp_path):
    chk = Check("geometry.x", "t", project=tmp_path)
    with pytest.raises(CheckContractError):
        chk.measure("x", 1.0, "mm")
    with pytest.raises(CheckContractError):
        chk.measure("x", 1.0, "", min=0)


def test_empty_check_is_error_not_pass(tmp_path):
    assert Check("geometry.none", "t", project=tmp_path).finish() == 2


def test_nan_never_passes(tmp_path):
    chk = Check("geometry.nan", "t", project=tmp_path)
    assert chk.measure("v", float("nan"), "mm", min=0, remediation="value is NaN; fix the model") is False


def test_run_check_turns_exceptions_into_exit_2(tmp_path):
    with pytest.raises(SystemExit) as exc:
        with checkresult.run_check("geometry.boom", "t", project=tmp_path):
            raise RuntimeError("kernel crashed")
    assert exc.value.code == 2


def test_evidence_append_only_ids_and_levels(tmp_path):
    a = evidence.add_entry(tmp_path, artifact="cad/box.py", domain="mech", claim="volume within 0.01 mm3",
                           check_ids=["geometry.volume"], result="pass", level="L1", evidence_files=[])
    b = evidence.add_entry(tmp_path, artifact="cad/box.py", domain="mech", claim="second claim here",
                           check_ids=[], result="fail", level="L1", evidence_files=[])
    assert (a, b) == ("EV-0001", "EV-0002")
    assert len(evidence.load(tmp_path)["entries"]) == 2


def test_L4_without_signature_REJECTED(tmp_path):
    with pytest.raises(evidence.EvidenceError):
        evidence.add_entry(tmp_path, artifact="x", domain="mech", claim="drop test passed",
                           check_ids=[], result="pass", level="L4", evidence_files=[])


def test_from_checks_fails_if_any_check_failed_and_error_is_unverified(tmp_path):
    ok = Check("geometry.a", "t", project=tmp_path); ok.measure("a", 1, "mm", min=0); ok.finish()
    bad = Check("geometry.b", "t", project=tmp_path)
    bad.measure("b", -1, "mm", min=0, remediation="b must be non-negative"); bad.finish()
    err = Check("geometry.c", "t", project=tmp_path); err.error("tool missing")
    files = sorted((tmp_path / "out/verify").glob("*.json"))
    evidence.add_from_checks(tmp_path, files, artifact="t", domain="mech", claim="all geometry checks")
    entry = evidence.load(tmp_path)["entries"][-1]
    assert entry["result"] == "fail" and entry["status"] == "UNVERIFIED"
