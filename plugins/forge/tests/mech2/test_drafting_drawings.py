"""End-to-end + seeded-wrong tests for drafting-drawings (CONTRACTS.md §3, §9).

These run the real headless pipeline: freecadcmd -> TechDraw -> DXF ->
ezdxf/matplotlib -> PDF. Proves the ADR-001 §15.3 deviation (headless
TechDraw PDF/SVG export is impossible, DXF export is not) actually works
end to end, not just in principle.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parents[2] / "skills" / "drafting-drawings"
SCRIPTS_DIR = SKILL_DIR / "scripts"
VERIFY_PY = SCRIPTS_DIR / "verify.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "bracket_rev_a.toml"
FORGE_PYTHON = Path.home() / ".forge" / "bin" / "forge-python"
PY = str(FORGE_PYTHON) if FORGE_PYTHON.exists() else sys.executable
FREECADCMD = Path.home() / ".forge" / "bin" / "freecadcmd"

pytestmark = pytest.mark.skipif(not FREECADCMD.exists(), reason="freecadcmd not installed")


def _run_verify(project: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PY, str(VERIFY_PY), "--project", str(project)],
        capture_output=True, text=True, timeout=180,
    )


def _dump_toml(data: dict) -> str:
    lines = []
    for section, val in data.items():
        if isinstance(val, list):  # [[dimension]] array of tables
            for item in val:
                lines.append(f"[[{section}]]")
                for k, v in item.items():
                    lines.append(f'{k} = "{v}"' if isinstance(v, str) else f"{k} = {v}")
                lines.append("")
        else:
            lines.append(f"[{section}]")
            for k, v in val.items():
                lines.append(f'{k} = "{v}"' if isinstance(v, str) else f"{k} = {v}")
            lines.append("")
    return "\n".join(lines)


def _write_spec(project: Path, filename: str = "bracket_rev_a.toml", mutate=None) -> Path:
    data = tomllib.loads(FIXTURE.read_text())
    if mutate:
        mutate(data)
    specs_dir = project / "cad" / "drawings"
    specs_dir.mkdir(parents=True, exist_ok=True)
    path = specs_dir / filename
    path.write_text(_dump_toml(data))
    return path


@pytest.mark.slow
def test_verify_py_passes_and_produces_pdf_and_dxf_with_title_block_and_dimensions(tmp_path):
    _write_spec(tmp_path)
    r = _run_verify(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr

    out = json.loads((tmp_path / "out" / "verify" / "mech.drawing_bracket_rev_a.json").read_text())
    assert out["status"] == "pass"
    by_name = {m["name"]: m for m in out["measurements"]}
    assert by_name["title_block_fields_present"]["value"] == 5
    assert by_name["dimensions_present"]["value"] == 3
    assert by_name["pdf_size_bytes"]["value"] > 1000

    pdf = tmp_path / "out" / "drawings" / "bracket_rev_a" / "page.pdf"
    dxf = tmp_path / "out" / "drawings" / "bracket_rev_a" / "page.dxf"
    assert pdf.exists() and pdf.stat().st_size > 1000
    assert dxf.exists()

    # independently re-parse the DXF (not just trust verify.py's own measurement)
    ezdxf = pytest.importorskip("ezdxf")  # CAD-env only
    doc = ezdxf.readfile(str(dxf))
    msp = doc.modelspace()
    texts = [e.dxf.text for e in msp.query("TEXT")]
    joined = "\n".join(texts)
    for expected in ("MOUNTING BRACKET", "DWG-1001", "1:1", "forge"):
        assert expected in joined, f"{expected!r} missing from DXF title-block text: {texts}"
    dim_texts = [e.dxf.text for e in msp.query("DIMENSION")]
    assert len(dim_texts) == 3


@pytest.mark.slow
def test_verify_py_FAILS_when_spec_dimension_missing_from_dxf(tmp_path):
    """Seeded-wrong: a spec dimension with no matching part edge must FAIL, not pass."""
    def mutate(data):
        data["dimension"][0]["value_mm"] = 99.0  # no edge on this part measures 99 mm

    _write_spec(tmp_path, mutate=mutate)
    r = _run_verify(tmp_path)
    assert r.returncode == 1, r.stdout + r.stderr
    out = json.loads((tmp_path / "out" / "verify" / "mech.drawing_bracket_rev_a.json").read_text())
    assert out["status"] == "fail"
    by_name = {m["name"]: m for m in out["measurements"]}
    assert by_name["dimensions_present"]["pass"] is False
    assert by_name["dimensions_present"]["value"] < 3
    assert len(by_name["dimensions_present"]["remediation"]) >= 10
    # title block should still be fine -- only the dimension check should fail
    assert by_name["title_block_fields_present"]["pass"] is True


def test_verify_py_ERRORS_on_spec_missing_title_block_field(tmp_path):
    def mutate(data):
        del data["drawing"]["scale"]

    _write_spec(tmp_path, mutate=mutate)
    r = _run_verify(tmp_path)
    assert r.returncode == 2, r.stdout + r.stderr


def test_verify_py_ERRORS_on_spec_with_no_dimensions(tmp_path):
    def mutate(data):
        data["dimension"] = []

    _write_spec(tmp_path, mutate=mutate)
    r = _run_verify(tmp_path)
    assert r.returncode == 2, r.stdout + r.stderr


def test_verify_py_skips_cleanly_with_no_specs(tmp_path):
    r = _run_verify(tmp_path)
    assert r.returncode == 0
    assert "[SKIP]" in r.stdout
