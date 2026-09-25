"""tracing-requirements/scripts/verify.py: the requirement -> design -> test
-> evidence graph (CONTRACTS.md §6, §9). FAILS on orphans, untested
requirements and dangling evidence ids; passes on a fully-wired fixture."""
from __future__ import annotations

import json

from .conftest import load_skill_module

verify = load_skill_module("tracing-requirements")

REQUIREMENTS_MD = """\
## REQ-MECH-004

The enclosure shall maintain a wall thickness of at least 2.0 mm.

Rationale: FDM min wall.
Verify: analysis

## REQ-MECH-005

The enclosure shall have a lid.

Rationale: keeps water out.
Verify: inspection
"""


def _base_project(tmp_path):
    (tmp_path / "requirements").mkdir(parents=True, exist_ok=True)
    (tmp_path / "requirements" / "requirements.md").write_text(REQUIREMENTS_MD)
    (tmp_path / "cad").mkdir(exist_ok=True)
    (tmp_path / "tests").mkdir(exist_ok=True)
    (tmp_path / "evidence").mkdir(exist_ok=True)
    (tmp_path / "cad" / "enclosure.py").write_text("# pretend cad\n")
    (tmp_path / "tests" / "test_wall.py").write_text("def test_wall(): pass\n")
    evidence = {
        "schema": "forge.evidence/1",
        "entries": [{
            "id": "EV-0001", "artifact": "cad/enclosure.py", "domain": "mech", "claim": "wall ok",
            "check_ids": [], "result": "pass", "level": "L1", "evidence_files": [],
            "inputs_sha256": "0" * 64, "tool_versions": {}, "git_sha": "nogit",
            "model": "test", "timestamp": "2026-01-01T00:00:00Z", "status": "VERIFIED",
        }],
    }
    (tmp_path / "evidence" / "manifest.json").write_text(json.dumps(evidence))
    return tmp_path


def _write_trace(project, requirements: dict):
    trace = {"schema": "forge.trace/1", "requirements": requirements}
    (project / "requirements" / "trace.json").write_text(json.dumps(trace))


def _measurement_names_failing(result: dict) -> list[str]:
    return [m["name"] for m in result["measurements"] if not m["pass"]]


def test_fully_wired_fixture_passes(tmp_path):
    project = _base_project(tmp_path)
    _write_trace(project, {
        "REQ-MECH-004": {"design": ["cad/enclosure.py"], "tests": ["tests/test_wall.py"],
                          "evidence": ["EV-0001"], "status": "verified"},
        "REQ-MECH-005": {"design": [], "tests": [], "evidence": [], "status": "waived"},
    })
    assert verify.run(project, None) == 0
    out = json.loads((project / "out/verify/requirements.trace_graph.json").read_text())
    assert out["status"] == "pass"
    graph = json.loads((project / "out/verify/trace.graph.json").read_text())
    assert {"REQ-MECH-004", "REQ-MECH-005"} <= {n["id"] for n in graph["nodes"]}
    assert (project / "out/verify/trace.graph.mmd").exists()


def test_orphan_design_file_fails(tmp_path):
    project = _base_project(tmp_path)
    (project / "cad" / "orphan_part.py").write_text("# never referenced\n")
    _write_trace(project, {
        "REQ-MECH-004": {"design": ["cad/enclosure.py"], "tests": ["tests/test_wall.py"],
                          "evidence": ["EV-0001"], "status": "verified"},
        "REQ-MECH-005": {"design": [], "tests": [], "evidence": [], "status": "waived"},
    })
    assert verify.run(project, None) == 1
    out = json.loads((project / "out/verify/requirements.trace_graph.json").read_text())
    failing = _measurement_names_failing(out)
    assert any(name == "orphan.design.cad/orphan_part.py" for name in failing)


def test_untested_requirement_fails(tmp_path):
    project = _base_project(tmp_path)
    _write_trace(project, {
        "REQ-MECH-004": {"design": ["cad/enclosure.py"], "tests": ["tests/test_wall.py"],
                          "evidence": ["EV-0001"], "status": "verified"},
        # REQ-MECH-005: no tests[], not waived -- untested
        "REQ-MECH-005": {"design": [], "tests": [], "evidence": [], "status": "open"},
    })
    assert verify.run(project, None) == 1
    out = json.loads((project / "out/verify/requirements.trace_graph.json").read_text())
    failing = _measurement_names_failing(out)
    assert any(name.startswith("REQ-MECH-005") and name.endswith(".tested") for name in failing)


def test_dangling_evidence_id_fails(tmp_path):
    project = _base_project(tmp_path)
    _write_trace(project, {
        "REQ-MECH-004": {"design": ["cad/enclosure.py"], "tests": ["tests/test_wall.py"],
                          "evidence": ["EV-9999"], "status": "verified"},  # does not exist
        "REQ-MECH-005": {"design": [], "tests": [], "evidence": [], "status": "waived"},
    })
    assert verify.run(project, None) == 1
    out = json.loads((project / "out/verify/requirements.trace_graph.json").read_text())
    failing = _measurement_names_failing(out)
    assert any("EV-9999" in name for name in failing)


def test_missing_trace_entry_fails(tmp_path):
    project = _base_project(tmp_path)
    _write_trace(project, {
        "REQ-MECH-004": {"design": ["cad/enclosure.py"], "tests": ["tests/test_wall.py"],
                          "evidence": ["EV-0001"], "status": "verified"},
        # REQ-MECH-005 entirely missing from trace.json
    })
    assert verify.run(project, None) == 1
    out = json.loads((project / "out/verify/requirements.trace_graph.json").read_text())
    failing = _measurement_names_failing(out)
    assert any(name.startswith("REQ-MECH-005") and name.endswith(".has_trace_entry") for name in failing)


def test_no_requirements_or_trace_is_skip(tmp_path):
    assert verify.run(tmp_path, None) == 0
    assert not (tmp_path / "out").exists()
