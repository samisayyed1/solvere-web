"""exploring-concepts: pugh.sensitivity_check (weighted Pugh matrix ranking
stability under a +/-25% weight perturbation) and scripts/verify.py."""
from __future__ import annotations

import json

from .conftest import load_skill_module

pugh = load_skill_module("exploring-concepts", "pugh.py")
verify = load_skill_module("exploring-concepts", "verify.py")

CRITERIA = [{"name": "cost", "weight": 0.34}, {"name": "mfg", "weight": 0.33}, {"name": "ergo", "weight": 0.33}]


def test_dominant_concept_ranking_is_stable():
    """A concept that beats every rival on every criterion can't be flipped
    by any single-criterion weight perturbation."""
    concepts = [
        {"name": "datum", "datum": True, "scores": {"cost": 0, "mfg": 0, "ergo": 0}},
        {"name": "A", "scores": {"cost": 1, "mfg": 1, "ergo": 1}},
        {"name": "B", "scores": {"cost": -1, "mfg": 0, "ergo": 0}},
        {"name": "C", "scores": {"cost": 0, "mfg": -1, "ergo": -1}},
    ]
    report = pugh.sensitivity_check(CRITERIA, concepts, top_n=1)
    assert report["stable"] is True
    assert report["flips"] == []
    assert report["base_top"] == ["A"]


def test_close_call_ranking_change_is_detected():
    """A near-tie between two concepts must flip under a +/-25% weight
    perturbation -- this is exactly what the sensitivity check exists to
    catch (seeded-wrong input: a fragile ranking)."""
    concepts = [
        {"name": "datum", "datum": True, "scores": {"cost": 0, "mfg": 0, "ergo": 0}},
        {"name": "A", "scores": {"cost": 2, "mfg": 0, "ergo": -1}},
        {"name": "D", "scores": {"cost": -1, "mfg": 2, "ergo": 0}},
        {"name": "C", "scores": {"cost": -2, "mfg": -2, "ergo": -2}},
    ]
    report = pugh.sensitivity_check(CRITERIA, concepts, top_n=1)
    assert report["stable"] is False
    assert report["flips"], "expected at least one weight perturbation to flip the top-1 ranking"
    assert report["base_top"] == ["A"]
    assert any(f["perturbed_top"] == ["D"] for f in report["flips"])


def test_datum_excluded_from_ranking():
    concepts = [
        {"name": "datum", "datum": True, "scores": {"cost": 0, "mfg": 0, "ergo": 0}},
        {"name": "A", "scores": {"cost": -1, "mfg": -1, "ergo": -1}},  # worse than datum on everything
    ]
    ranked = pugh.rank(concepts, pugh.normalize_weights(CRITERIA), exclude_datum=True)
    assert [r.name for r in ranked] == ["A"]  # datum isn't a rankable candidate


def _write_pugh(tmp_path, data: dict):
    d = tmp_path / "concepts"
    d.mkdir(parents=True, exist_ok=True)
    (d / "pugh.json").write_text(json.dumps(data))
    return tmp_path


ROBUST_DATA = {
    "schema": "forge.pugh/1",
    "top_n": 1,
    "criteria": CRITERIA,
    "concepts": [
        {"name": "datum", "datum": True, "scores": {"cost": 0, "mfg": 0, "ergo": 0}},
        {"name": "A", "scores": {"cost": 1, "mfg": 1, "ergo": 1}},
        {"name": "B", "scores": {"cost": -1, "mfg": 0, "ergo": 0}},
        {"name": "C", "scores": {"cost": 0, "mfg": -1, "ergo": -1}},
    ],
}

FRAGILE_DATA = {
    "schema": "forge.pugh/1",
    "top_n": 1,
    "criteria": CRITERIA,
    "sensitivity_reviewed_by": "",
    "concepts": [
        {"name": "datum", "datum": True, "scores": {"cost": 0, "mfg": 0, "ergo": 0}},
        {"name": "A", "scores": {"cost": 2, "mfg": 0, "ergo": -1}},
        {"name": "D", "scores": {"cost": -1, "mfg": 2, "ergo": 0}},
        {"name": "C", "scores": {"cost": -2, "mfg": -2, "ergo": -2}},
    ],
}


def test_verify_passes_on_robust_ranking(tmp_path):
    project = _write_pugh(tmp_path, ROBUST_DATA)
    assert verify.run(project, None) == 0
    out = json.loads((project / "out/verify/concepts.pugh_sensitivity.json").read_text())
    assert out["status"] == "pass"


def test_verify_fails_on_unreviewed_fragile_ranking(tmp_path):
    project = _write_pugh(tmp_path, FRAGILE_DATA)
    assert verify.run(project, None) == 1
    out = json.loads((project / "out/verify/concepts.pugh_sensitivity.json").read_text())
    assert any(m["name"] == "ranking.sensitivity_acknowledged" and not m["pass"] for m in out["measurements"])


def test_verify_passes_once_reviewed(tmp_path):
    data = dict(FRAGILE_DATA)
    data["sensitivity_reviewed_by"] = "J. Doe, 2026-09-25"
    project = _write_pugh(tmp_path, data)
    assert verify.run(project, None) == 0


def test_verify_fails_below_minimum_concept_count(tmp_path):
    data = {
        "schema": "forge.pugh/1",
        "minimum_concepts": 3,
        "criteria": CRITERIA,
        "concepts": [
            {"name": "datum", "datum": True, "scores": {"cost": 0, "mfg": 0, "ergo": 0}},
            {"name": "A", "scores": {"cost": 1, "mfg": 1, "ergo": 1}},
        ],
    }
    project = _write_pugh(tmp_path, data)
    assert verify.run(project, None) == 1
    out = json.loads((project / "out/verify/concepts.pugh_sensitivity.json").read_text())
    assert any(m["name"] == "concepts.count" and not m["pass"] for m in out["measurements"])


def test_no_pugh_file_is_skip(tmp_path):
    assert verify.run(tmp_path, None) == 0
    assert not (tmp_path / "out").exists()


# --- S15 ---------------------------------------------------------------

def test_minimum_concepts_cannot_be_lowered_below_the_floor(tmp_path):
    """A maker cannot set minimum_concepts=1 in the file it wrote to let its
    own single concept pass -- the floor is enforced regardless."""
    data = {
        "schema": "forge.pugh/1",
        "minimum_concepts": 1,
        "criteria": CRITERIA,
        "concepts": [
            {"name": "datum", "datum": True, "scores": {"cost": 0, "mfg": 0, "ergo": 0}},
            {"name": "A", "scores": {"cost": 1, "mfg": 1, "ergo": 1}},
        ],
    }
    project = _write_pugh(tmp_path, data)
    assert verify.run(project, None) == 1
    out = json.loads((project / "out/verify/concepts.pugh_sensitivity.json").read_text())
    m = next(m for m in out["measurements"] if m["name"] == "concepts.count")
    assert not m["pass"]
    assert m["limit"]["min"] == 3


def test_score_out_of_pugh_range_fails(tmp_path):
    data = {
        "schema": "forge.pugh/1",
        "criteria": CRITERIA,
        "concepts": [
            {"name": "datum", "datum": True, "scores": {"cost": 0, "mfg": 0, "ergo": 0}},
            {"name": "A", "scores": {"cost": 50, "mfg": 1, "ergo": 1}},
            {"name": "B", "scores": {"cost": -1, "mfg": 0, "ergo": 0}},
            {"name": "C", "scores": {"cost": 0, "mfg": -1, "ergo": -1}},
        ],
    }
    project = _write_pugh(tmp_path, data)
    assert verify.run(project, None) == 1
    out = json.loads((project / "out/verify/concepts.pugh_sensitivity.json").read_text())
    m = next(m for m in out["measurements"] if m["name"] == "A.scores_in_range")
    assert not m["pass"]


def test_missing_datum_fails(tmp_path):
    data = {
        "schema": "forge.pugh/1",
        "criteria": CRITERIA,
        "concepts": [
            {"name": "A", "scores": {"cost": 1, "mfg": 1, "ergo": 1}},
            {"name": "B", "scores": {"cost": -1, "mfg": 0, "ergo": 0}},
            {"name": "C", "scores": {"cost": 0, "mfg": -1, "ergo": -1}},
        ],
    }
    project = _write_pugh(tmp_path, data)
    assert verify.run(project, None) == 1
    out = json.loads((project / "out/verify/concepts.pugh_sensitivity.json").read_text())
    m = next(m for m in out["measurements"] if m["name"] == "concepts.has_datum")
    assert not m["pass"]


def test_duplicate_concept_names_fail(tmp_path):
    data = {
        "schema": "forge.pugh/1",
        "criteria": CRITERIA,
        "concepts": [
            {"name": "datum", "datum": True, "scores": {"cost": 0, "mfg": 0, "ergo": 0}},
            {"name": "A", "scores": {"cost": 1, "mfg": 1, "ergo": 1}},
            {"name": "A", "scores": {"cost": -1, "mfg": 0, "ergo": 0}},
            {"name": "C", "scores": {"cost": 0, "mfg": -1, "ergo": -1}},
        ],
    }
    project = _write_pugh(tmp_path, data)
    assert verify.run(project, None) == 1
    out = json.loads((project / "out/verify/concepts.pugh_sensitivity.json").read_text())
    m = next(m for m in out["measurements"] if m["name"] == "concepts.unique_names")
    assert not m["pass"]
    assert "A" in m["remediation"]
