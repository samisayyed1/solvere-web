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
BLENDER = Path("/Applications/Blender.app/Contents/MacOS/Blender")

SPEC = """
[pack]
name = "bracket_pack"
length_mm = 80.0
width_mm = 40.0
height_mm = 10.0

[scale_bar]
length_mm = {scale_bar_mm}
"""


def _run_verify(project: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PY, str(VERIFY_PY), "--project", str(project)],
        capture_output=True, text=True, timeout=120,
    )


def _write_spec(project: Path, scale_bar_mm: float = 20.0) -> Path:
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
    specs_dir = tmp_path / "analysis" / "render_packs"
    specs_dir.mkdir(parents=True)
    (specs_dir / "bracket_pack.toml").write_text(SPEC.format(scale_bar_mm=20.0) + "\n[marketing]\nenabled = true\n")
    r = _run_verify(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    marketing_png = tmp_path / "out" / "renders" / "products" / "bracket_pack" / "marketing.png"
    assert marketing_png.exists() and marketing_png.stat().st_size > 1000


def test_verify_py_skips_cleanly_with_no_specs(tmp_path):
    r = _run_verify(tmp_path)
    assert r.returncode == 0
    assert "[SKIP]" in r.stdout
