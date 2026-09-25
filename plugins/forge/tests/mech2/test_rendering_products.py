"""Tests for rendering-products: engineering render pack (PyVista, orthographic,
numerically consistent scale) + optional Blender marketing render.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parents[2] / "skills" / "rendering-products"
SCRIPTS_DIR = SKILL_DIR / "scripts"
VERIFY_PY = SCRIPTS_DIR / "verify.py"
FORGE_PYTHON = Path.home() / ".forge" / "bin" / "forge-python"
PY = str(FORGE_PYTHON) if FORGE_PYTHON.exists() else sys.executable
BLENDER = next((p for p in (Path("/Applications/Blender.app/Contents/MacOS/Blender"),
                            Path.home() / ".forge" / "opt" / "blender" / "blender") if p.exists()),
               Path("/Applications/Blender.app/Contents/MacOS/Blender"))

BRACKET_PY = """
from build123d import BuildPart, Box, Align

def build(params=None):
    with BuildPart() as bp:
        Box(80.0, 40.0, 10.0, align=(Align.CENTER, Align.CENTER, Align.CENTER))
    return bp.part
"""

SPEC = """
[pack]
name = "bracket_pack"
module = "cad/bracket.py"

[scale_bar]
length_mm = {scale_bar_mm}
"""


def _run_verify(project: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PY, str(VERIFY_PY), "--project", str(project)],
        capture_output=True, text=True, timeout=120,
    )


def _write_spec(project: Path, scale_bar_mm: float = 20.0) -> Path:
    (project / "cad").mkdir(parents=True, exist_ok=True)
    (project / "cad" / "bracket.py").write_text(BRACKET_PY)
    specs_dir = project / "analysis" / "render_packs"
    specs_dir.mkdir(parents=True, exist_ok=True)
    path = specs_dir / "bracket_pack.toml"
    path.write_text(SPEC.format(scale_bar_mm=scale_bar_mm))
    return path


@pytest.mark.slow
def test_verify_py_passes_with_consistent_orthographic_pack(tmp_path):
    _write_spec(tmp_path)
    r = _run_verify(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    out = json.loads((tmp_path / "out" / "verify" / "mech.render_pack_bracket_pack.json").read_text())
    assert out["status"] == "pass"
    by_name = {m["name"]: m for m in out["measurements"]}
    assert by_name["views_present"]["value"] == 4
    assert by_name["consistent_window_size"]["value"] == 1
    assert by_name["consistent_camera_scale"]["value"] == 1
    assert by_name["scale_mm_per_pixel_correct"]["value"] == 4

    manifest = json.loads((tmp_path / "out" / "renders" / "products" / "bracket_pack" / "manifest.json").read_text())
    scales = {v["parallel_scale_mm"] for v in manifest["views"]}
    sizes = {(v["width_px"], v["height_px"]) for v in manifest["views"]}
    assert len(scales) == 1 and len(sizes) == 1, "every view must share one camera scale and window size"
    for v in manifest["views"]:
        expected = (2.0 * v["parallel_scale_mm"]) / v["height_px"]
        assert v["scale_mm_per_pixel"] == pytest.approx(expected, rel=1e-9)


@pytest.mark.slow
def test_verify_py_FAILS_when_scale_bar_does_not_fit_in_frame(tmp_path):
    """Seeded-wrong: a scale bar far larger than the part/frame must FAIL, not pass."""
    _write_spec(tmp_path, scale_bar_mm=100_000.0)
    r = _run_verify(tmp_path)
    assert r.returncode == 1, r.stdout + r.stderr
    out = json.loads((tmp_path / "out" / "verify" / "mech.render_pack_bracket_pack.json").read_text())
    assert out["status"] == "fail"
    by_name = {m["name"]: m for m in out["measurements"]}
    assert by_name["scale_bar_fits_in_frame"]["pass"] is False
    assert len(by_name["scale_bar_fits_in_frame"]["remediation"]) >= 10


def test_verify_py_ERRORS_on_spec_missing_pack_name(tmp_path):
    specs_dir = tmp_path / "analysis" / "render_packs"
    specs_dir.mkdir(parents=True)
    (specs_dir / "broken.toml").write_text("[pack]\nlength_mm = 1.0\n")
    r = _run_verify(tmp_path)
    assert r.returncode == 2, r.stdout + r.stderr


@pytest.mark.slow
@pytest.mark.skipif(not BLENDER.exists(), reason="Blender not installed")
def test_verify_py_produces_marketing_render_when_enabled(tmp_path):
    (tmp_path / "cad").mkdir(parents=True, exist_ok=True)
    (tmp_path / "cad" / "bracket.py").write_text(BRACKET_PY)
    specs_dir = tmp_path / "analysis" / "render_packs"
    specs_dir.mkdir(parents=True)
    (specs_dir / "bracket_pack.toml").write_text(SPEC.format(scale_bar_mm=20.0) + "\n[marketing]\nenabled = true\n")
    r = _run_verify(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    marketing_png = tmp_path / "out" / "renders" / "products" / "bracket_pack" / "marketing.png"
    assert marketing_png.exists() and marketing_png.stat().st_size > 1000


def test_verify_py_ERRORS_when_pack_has_no_module_or_step(tmp_path):
    """S12: a spec that names no real geometry must be refused, not
    silently rendered as a placeholder box."""
    specs_dir = tmp_path / "analysis" / "render_packs"
    specs_dir.mkdir(parents=True)
    (specs_dir / "bracket_pack.toml").write_text('[pack]\nname = "bracket_pack"\n')
    r = _run_verify(tmp_path)
    assert r.returncode == 2, r.stdout + r.stderr


def test_verify_py_ERRORS_when_pack_has_both_module_and_step(tmp_path):
    specs_dir = tmp_path / "analysis" / "render_packs"
    specs_dir.mkdir(parents=True)
    (specs_dir / "bracket_pack.toml").write_text(
        '[pack]\nname = "bracket_pack"\nmodule = "cad/a.py"\nstep = "cad/a.step"\n'
    )
    r = _run_verify(tmp_path)
    assert r.returncode == 2, r.stdout + r.stderr


@pytest.mark.slow
def test_render_pack_renders_the_named_part_geometry(tmp_path):
    """S12 positive case: render_pack.py must actually load and use the
    module [pack] names -- proven by a part whose bounding box differs
    from any hard-coded demo default, checked via the manifest's derived
    scale (which depends on the real geometry's diagonal)."""
    (tmp_path / "cad").mkdir(parents=True)
    (tmp_path / "cad" / "odd.py").write_text(
        "from build123d import BuildPart, Box, Align\n"
        "def build(params=None):\n"
        "    with BuildPart() as bp:\n"
        "        Box(200.0, 5.0, 5.0, align=(Align.CENTER, Align.CENTER, Align.CENTER))\n"
        "    return bp.part\n"
    )
    specs_dir = tmp_path / "analysis" / "render_packs"
    specs_dir.mkdir(parents=True)
    (specs_dir / "odd_pack.toml").write_text('[pack]\nname = "odd_pack"\nmodule = "cad/odd.py"\n')
    r = _run_verify(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    manifest = json.loads((tmp_path / "out" / "renders" / "products" / "odd_pack" / "manifest.json").read_text())
    # diag = sqrt(200^2+5^2+5^2) ~= 200.12; parallel_scale_mm = diag*0.65 ~= 130.1 --
    # very different from the old fixed 80x40x10 demo's ~68.7, so this proves the
    # real 200x5x5 geometry drove the render, not a hard-coded box.
    scale = manifest["views"][0]["parallel_scale_mm"]
    assert scale == pytest.approx(((200.0 ** 2 + 5.0 ** 2 + 5.0 ** 2) ** 0.5) * 0.65, rel=1e-6)


def test_verify_py_skips_cleanly_with_no_specs(tmp_path):
    r = _run_verify(tmp_path)
    assert r.returncode == 0
    assert "[SKIP]" in r.stdout
