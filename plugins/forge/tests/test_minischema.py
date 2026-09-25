"""Tests for :mod:`forge.minischema` against all four Forge schemas
(check-result, evidence, params, verdict), each with a valid and an
invalid document, plus a few keyword-level unit tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from forge import minischema

SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas"


def _load(name: str) -> dict:
    return json.loads((SCHEMAS_DIR / name).read_text())


# ---------------------------------------------------------------------------
# forge.verdict/1
# ---------------------------------------------------------------------------

VERDICT_SCHEMA = _load("verdict.schema.json")

VALID_VERDICT = {
    "schema": "forge.verdict/1", "reviewer": "verification-evaluator", "gate": "G2",
    "subject": "enclosure rev B",
    "criteria": [{
        "id": "REQ-MECH-004", "verdict": "FAIL", "evidence": ["out/verify/geometry.min_wall.json"],
        "finding": "Lid lip wall 1.62 mm below 2.0 mm minimum.", "severity": "major",
        "affects": ["manufacturability", "function"],
    }],
    "overall": "FAIL", "summary": "1 major defect; 11 criteria PASS.",
    "not_checked": ["thermal (no analysis yet)"],
}


def test_verdict_valid():
    assert minischema.validate(VALID_VERDICT, VERDICT_SCHEMA) == []


def test_verdict_invalid_fail_without_severity_and_affects():
    bad = json.loads(json.dumps(VALID_VERDICT))
    bad["criteria"][0] = {"id": "REQ-MECH-004", "verdict": "FAIL", "evidence": [], "finding": "x"}
    errors = minischema.validate(bad, VERDICT_SCHEMA)
    assert any("severity" in e for e in errors)
    assert any("affects" in e for e in errors)


def test_verdict_invalid_bad_enum():
    bad = json.loads(json.dumps(VALID_VERDICT))
    bad["overall"] = "MAYBE"
    errors = minischema.validate(bad, VERDICT_SCHEMA)
    assert any("overall" not in e or "not in" in e for e in errors)  # sanity: some error reported
    assert errors


def test_verdict_invalid_additional_property_rejected():
    bad = json.loads(json.dumps(VALID_VERDICT))
    bad["unexpected_field"] = True
    errors = minischema.validate(bad, VERDICT_SCHEMA)
    assert any("unexpected" in e for e in errors)


# ---------------------------------------------------------------------------
# forge.check/1
# ---------------------------------------------------------------------------

CHECK_SCHEMA = _load("check-result.schema.json")

VALID_CHECK = {
    "schema": "forge.check/1", "check_id": "geometry.min_wall", "target": "cad/enclosure.py",
    "status": "fail", "level": "L1",
    "measurements": [{
        "name": "min_wall", "value": 1.62, "unit": "mm", "limit": {"min": 2.0}, "pass": False,
        "requirement": "REQ-MECH-004",
        "remediation": "Wall at lid lip is 1.62 mm < 2.0 mm; thicken the lip.",
    }],
    "tool_versions": {"build123d": "0.11.1"}, "git_sha": "abc123", "started": "2026-09-25T10:00:00Z",
    "duration_s": 1.4,
}


def test_check_result_valid():
    assert minischema.validate(VALID_CHECK, CHECK_SCHEMA) == []


def test_check_result_invalid_failing_measurement_without_remediation():
    bad = json.loads(json.dumps(VALID_CHECK))
    del bad["measurements"][0]["remediation"]
    errors = minischema.validate(bad, CHECK_SCHEMA)
    assert any("remediation" in e for e in errors)


def test_check_result_invalid_error_status_without_error_field():
    bad = json.loads(json.dumps(VALID_CHECK))
    bad["status"] = "error"
    errors = minischema.validate(bad, CHECK_SCHEMA)
    assert any("error" in e for e in errors)


# ---------------------------------------------------------------------------
# forge.evidence/1
# ---------------------------------------------------------------------------

EVIDENCE_SCHEMA = _load("evidence.schema.json")

VALID_ENTRY = {
    "id": "EV-0001", "artifact": "cad/enclosure.step", "domain": "mech", "claim": "walls meet minimum",
    "check_ids": ["geometry.min_wall"], "result": "pass", "level": "L1", "evidence_files": ["out/verify/geometry.min_wall.json"],
    "inputs_sha256": "a" * 64, "tool_versions": {"build123d": "0.11.1"}, "git_sha": "abc",
    "model": "claude-sonnet-5", "timestamp": "2026-09-25T10:00:00Z", "status": "VERIFIED",
}
VALID_EVIDENCE = {"schema": "forge.evidence/1", "entries": [VALID_ENTRY]}


def test_evidence_valid():
    assert minischema.validate(VALID_EVIDENCE, EVIDENCE_SCHEMA) == []


def test_evidence_invalid_l4_without_signed_by():
    bad = json.loads(json.dumps(VALID_EVIDENCE))
    bad["entries"][0]["level"] = "L4"
    errors = minischema.validate(bad, EVIDENCE_SCHEMA)
    assert any("signed_by" in e for e in errors)


def test_evidence_invalid_bad_id_pattern():
    bad = json.loads(json.dumps(VALID_EVIDENCE))
    bad["entries"][0]["id"] = "not-an-id"
    errors = minischema.validate(bad, EVIDENCE_SCHEMA)
    assert any("pattern" in e for e in errors)


# ---------------------------------------------------------------------------
# forge.params/1
# ---------------------------------------------------------------------------

PARAMS_SCHEMA = _load("params.schema.json")

VALID_PARAM = {"value": 2.0, "unit": "mm", "status": "assumed", "source": "R5d FDM min wall; chosen 2.0 for stiffness"}


def test_params_valid():
    assert minischema.validate(VALID_PARAM, PARAMS_SCHEMA) == []


def test_params_invalid_verified_without_verified_by_and_evidence():
    bad = dict(VALID_PARAM, status="verified")
    errors = minischema.validate(bad, PARAMS_SCHEMA)
    assert any("verified_by" in e for e in errors)
    assert any("evidence" in e for e in errors)


def test_params_valid_verified_with_evidence():
    good = dict(VALID_PARAM, status="verified", verified_by="Alice Chen", evidence=["EV-0001"])
    assert minischema.validate(good, PARAMS_SCHEMA) == []


# ---------------------------------------------------------------------------
# keyword-level unit tests
# ---------------------------------------------------------------------------

def test_type_union():
    schema = {"type": ["number", "string"]}
    assert minischema.validate(1, schema) == []
    assert minischema.validate("x", schema) == []
    assert minischema.validate(True, schema) != []  # bool is not "number" in JSON Schema


def test_ref_defs_resolution():
    schema = {
        "type": "object",
        "properties": {"item": {"$ref": "#/$defs/thing"}},
        "$defs": {"thing": {"type": "string", "minLength": 3}},
    }
    assert minischema.validate({"item": "abc"}, schema) == []
    assert minischema.validate({"item": "ab"}, schema) != []


def test_unsupported_type_raises_schema_error():
    with pytest.raises(minischema.SchemaError):
        minischema.validate(1, {"type": "widget"})
