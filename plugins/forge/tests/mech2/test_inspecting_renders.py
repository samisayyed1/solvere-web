"""Tests for inspecting-renders (CONTRACTS.md §3, §9): question-first render inspection.

The core seeded-wrong case CONTRACTS.md calls out by name is "render run
without a questions file" -- it must never pass. These tests render once
(real PyVista offscreen renders, ~5-10s) into a session-scoped project and
then exercise several ``verify.py`` scenarios against that fixed render
output, to avoid re-rendering for every case.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parents[2] / "skills" / "inspecting-renders"
SCRIPTS_DIR = SKILL_DIR / "scripts"
RENDER_PY = SCRIPTS_DIR / "render.py"
VERIFY_PY = SCRIPTS_DIR / "verify.py"
FORGE_PYTHON = Path.home() / ".forge" / "bin" / "forge-python"
PY = str(FORGE_PYTHON) if FORGE_PYTHON.exists() else sys.executable

BRACKET_PY = """
from build123d import BuildPart, Box, Align

def build(params=None):
    with BuildPart() as bp:
        Box(80, 40, 10, align=(Align.CENTER, Align.CENTER, Align.CENTER))
    return bp.part
"""

QUESTIONS_PART = '[part]\nmodule = "cad/bracket.py"\n\n'
QUESTIONS = QUESTIONS_PART + "\n".join(
    f'[[question]]\nid = "q{i}"\ntext = "Question {i} about the part?"\n' for i in range(1, 11)
)
QUESTIONS_NO_PART = "\n".join(
    f'[[question]]\nid = "q{i}"\ntext = "Question {i} about the part?"\n' for i in range(1, 11)
)


def _run(args: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run([PY, *args], capture_output=True, text=True, timeout=120, **kw)


@pytest.fixture(scope="module")
def rendered_project(tmp_path_factory) -> Path:
    project = tmp_path_factory.mktemp("inspecting_renders_project")
    (project / "cad").mkdir(parents=True)
    (project / "cad" / "bracket.py").write_text(BRACKET_PY)
    (project / "analysis" / "renders").mkdir(parents=True)
    (project / "analysis" / "renders" / "bracket-questions.toml").write_text(QUESTIONS)
    r = _run([str(RENDER_PY), "--project", str(project), "--part", "bracket"])
    assert r.returncode == 0, r.stdout + r.stderr
    return project


def _answers_toml(*, all_yes_no: bool = True, all_evidence_valid: bool = True, with_deviations: bool = True,
                   all_no: bool = False, no_deviation_notes: bool = True) -> str:
    lines = ['part = "bracket"', ""]
    for i in range(1, 11):
        answer = "no" if all_no else ("yes" if all_yes_no else "")
        evidence = "out/renders/bracket/iso.png" if all_evidence_valid else "out/renders/bracket/does_not_exist.png"
        dev_note = ('deviation_note = "front view shows a visible gap between the lid and housing here"'
                    if (answer == "no" and no_deviation_notes) else 'deviation_note = ""')
        lines += [
            "[[answer]]", f'question_id = "q{i}"', f'question_text = "Question {i} about the part?"',
            f'answer = "{answer}"', f'evidence_file = "{evidence}"', 'numeric_check = ""', dev_note, "",
        ]
    if with_deviations:
        lines += ["[deviations]", 'notes = "none found"']
    return "\n".join(lines)


@pytest.mark.slow
def test_render_py_refuses_without_questions_file(tmp_path):
    project = tmp_path
    (project / "analysis" / "renders").mkdir(parents=True)
    r = _run([str(RENDER_PY), "--project", str(project), "--part", "widget"])
    assert r.returncode == 2, r.stdout + r.stderr
    assert not (project / "out" / "renders" / "widget").exists()


def test_verify_py_ERRORS_when_run_without_questions_file(tmp_path):
    """The named seeded-wrong case: render (or claim to inspect) without a questions file must FAIL."""
    project = tmp_path
    render_dir = project / "out" / "renders" / "bracket"
    render_dir.mkdir(parents=True)
    (render_dir / "front.png").write_bytes(b"\x89PNG" + b"0" * 2000)
    (project / "analysis" / "renders").mkdir(parents=True)
    (project / "analysis" / "renders" / "bracket-answers.toml").write_text('part = "bracket"\n[[answer]]\nquestion_id = "q1"\nanswer = "yes"\n')
    r = _run([str(VERIFY_PY), "--project", str(project)])
    assert r.returncode == 2, r.stdout + r.stderr


def test_verify_py_ERRORS_on_too_few_questions(tmp_path):
    (tmp_path / "analysis" / "renders").mkdir(parents=True)
    few = "\n".join(f'[[question]]\nid = "q{i}"\ntext = "t{i}"\n' for i in range(1, 4))
    (tmp_path / "analysis" / "renders" / "bracket-questions.toml").write_text(few)
    r = _run([str(VERIFY_PY), "--project", str(tmp_path)])
    assert r.returncode == 2, r.stdout + r.stderr


@pytest.mark.slow
def test_verify_py_passes_with_complete_answers(rendered_project):
    a_path = rendered_project / "analysis" / "renders" / "bracket-answers.toml"
    a_path.write_text(_answers_toml())
    r = _run([str(VERIFY_PY), "--project", str(rendered_project)])
    assert r.returncode == 0, r.stdout + r.stderr
    out = json.loads((rendered_project / "out" / "verify" / "mech.render_inspection_bracket.json").read_text())
    assert out["status"] == "pass"
    by_name = {m["name"]: m for m in out["measurements"]}
    assert by_name["required_views_present"]["value"] == 6
    assert by_name["views_non_blank"]["value"] == 6
    assert by_name["questions_answered"]["value"] == 10


@pytest.mark.slow
def test_verify_py_FAILS_on_blank_answers(rendered_project):
    """Seeded-wrong: an answers template that was never filled in must FAIL, not pass."""
    a_path = rendered_project / "analysis" / "renders" / "bracket-answers.toml"
    a_path.write_text(_answers_toml(all_yes_no=False))
    r = _run([str(VERIFY_PY), "--project", str(rendered_project)])
    assert r.returncode == 1, r.stdout + r.stderr
    out = json.loads((rendered_project / "out" / "verify" / "mech.render_inspection_bracket.json").read_text())
    assert out["status"] == "fail"
    by_name = {m["name"]: m for m in out["measurements"]}
    assert by_name["answers_have_yes_no"]["pass"] is False


@pytest.mark.slow
def test_verify_py_FAILS_on_answer_citing_nonexistent_evidence(rendered_project):
    """Seeded-wrong: an answer citing a render file that doesn't exist must FAIL."""
    a_path = rendered_project / "analysis" / "renders" / "bracket-answers.toml"
    a_path.write_text(_answers_toml(all_evidence_valid=False))
    r = _run([str(VERIFY_PY), "--project", str(rendered_project)])
    assert r.returncode == 1, r.stdout + r.stderr
    out = json.loads((rendered_project / "out" / "verify" / "mech.render_inspection_bracket.json").read_text())
    by_name = {m["name"]: m for m in out["measurements"]}
    assert by_name["answers_cite_existing_evidence"]["pass"] is False


@pytest.mark.slow
def test_verify_py_ERRORS_when_deviations_section_missing(rendered_project):
    a_path = rendered_project / "analysis" / "renders" / "bracket-answers.toml"
    a_path.write_text(_answers_toml(with_deviations=False))
    r = _run([str(VERIFY_PY), "--project", str(rendered_project)])
    assert r.returncode == 2, r.stdout + r.stderr


@pytest.mark.slow
def test_verify_py_FAILS_when_no_answers_have_no_deviation_note(rendered_project):
    """S11: the review's exact seeded-wrong case -- all 10 answers "no", with
    only the generic [deviations] "none found" -- must FAIL, not PASS."""
    a_path = rendered_project / "analysis" / "renders" / "bracket-answers.toml"
    a_path.write_text(_answers_toml(all_no=True, no_deviation_notes=False))
    r = _run([str(VERIFY_PY), "--project", str(rendered_project)])
    assert r.returncode == 1, r.stdout + r.stderr
    out = json.loads((rendered_project / "out" / "verify" / "mech.render_inspection_bracket.json").read_text())
    assert out["status"] == "fail"
    by_name = {m["name"]: m for m in out["measurements"]}
    assert by_name["no_answers_have_deviation_notes"]["pass"] is False
    assert len(by_name["no_answers_have_deviation_notes"]["remediation"]) >= 10


@pytest.mark.slow
def test_verify_py_passes_when_no_answers_have_real_deviation_notes(rendered_project):
    """Positive case: "no" answers with an actual, specific deviation_note pass."""
    a_path = rendered_project / "analysis" / "renders" / "bracket-answers.toml"
    a_path.write_text(_answers_toml(all_no=True, no_deviation_notes=True))
    r = _run([str(VERIFY_PY), "--project", str(rendered_project)])
    assert r.returncode == 0, r.stdout + r.stderr
    out = json.loads((rendered_project / "out" / "verify" / "mech.render_inspection_bracket.json").read_text())
    by_name = {m["name"]: m for m in out["measurements"]}
    assert by_name["no_answers_have_deviation_notes"]["pass"] is True


def test_verify_py_ERRORS_when_questions_file_has_no_part_table(tmp_path):
    """S11: a questions file that never names real geometry to render must be
    refused, not silently allowed to (mis)inspect nothing in particular."""
    (tmp_path / "analysis" / "renders").mkdir(parents=True)
    (tmp_path / "analysis" / "renders" / "widget-questions.toml").write_text(QUESTIONS_NO_PART)
    r = _run([str(VERIFY_PY), "--project", str(tmp_path)])
    assert r.returncode == 2, r.stdout + r.stderr


@pytest.mark.slow
def test_render_py_refuses_without_a_part_table(tmp_path):
    """S11: render.py must never fall back to placeholder/demo geometry when
    [part] is missing -- it refuses instead."""
    (tmp_path / "analysis" / "renders").mkdir(parents=True)
    (tmp_path / "analysis" / "renders" / "widget-questions.toml").write_text(QUESTIONS_NO_PART)
    r = _run([str(RENDER_PY), "--project", str(tmp_path), "--part", "widget"])
    assert r.returncode == 2, r.stdout + r.stderr
    assert "[part]" in (r.stdout + r.stderr)
    assert not (tmp_path / "out" / "renders" / "widget").exists()


@pytest.mark.slow
def test_render_py_renders_the_named_part_not_a_fixed_size(tmp_path):
    """S11 positive case: render.py must actually load and render the
    module [part] names -- proven here by using a part with different
    dimensions than any hard-coded demo default and checking the bounding
    box shows up in a real (non-blank) front-view render."""
    (tmp_path / "cad").mkdir(parents=True)
    (tmp_path / "cad" / "odd_part.py").write_text(
        "from build123d import BuildPart, Box, Align\n"
        "def build(params=None):\n"
        "    with BuildPart() as bp:\n"
        "        Box(123, 7, 55, align=(Align.CENTER, Align.CENTER, Align.CENTER))\n"
        "    return bp.part\n"
    )
    (tmp_path / "analysis" / "renders").mkdir(parents=True)
    (tmp_path / "analysis" / "renders" / "odd-questions.toml").write_text(
        '[part]\nmodule = "cad/odd_part.py"\n\n' + QUESTIONS_NO_PART
    )
    r = _run([str(RENDER_PY), "--project", str(tmp_path), "--part", "odd"])
    assert r.returncode == 0, r.stdout + r.stderr
    front = tmp_path / "out" / "renders" / "odd" / "front.png"
    assert front.exists() and front.stat().st_size > 1000


def test_verify_py_skips_cleanly_with_nothing_to_check(tmp_path):
    r = _run([str(VERIFY_PY), "--project", str(tmp_path)])
    assert r.returncode == 0
    assert "[SKIP]" in r.stdout
