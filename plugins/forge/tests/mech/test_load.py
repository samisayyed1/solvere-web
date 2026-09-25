"""forge_cad.load: part-module and STEP loading (plugins/forge/lib/forge_cad/load.py)."""

from __future__ import annotations

import pytest

bd = pytest.importorskip("build123d")  # CAD env only (~/.forge/bin/forge-python)

from forge_cad import load


def test_load_part_with_build_function(tmp_path):
    mod = tmp_path / "part.py"
    mod.write_text("import build123d as bd\ndef build():\n    return bd.Box(10, 10, 10)\n")
    shape = load.load_part(mod)
    assert isinstance(shape, bd.Shape)
    assert shape.volume == pytest.approx(1000.0)


def test_load_part_passes_params_when_accepted(tmp_path):
    mod = tmp_path / "part.py"
    mod.write_text(
        "import build123d as bd\n"
        "def build(params=None):\n"
        "    s = (params or {}).get('side', 10.0)\n"
        "    return bd.Box(s, s, s)\n"
    )
    shape = load.load_part(mod, params={"side": 4.0})
    assert shape.volume == pytest.approx(64.0)


def test_load_part_with_bare_PART_constant(tmp_path):
    mod = tmp_path / "part.py"
    mod.write_text("import build123d as bd\nPART = bd.Box(2, 2, 2)\n")
    shape = load.load_part(mod)
    assert shape.volume == pytest.approx(8.0)


def test_load_part_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load.load_part(tmp_path / "nope.py")


def test_load_part_without_build_or_PART_raises(tmp_path):
    mod = tmp_path / "part.py"
    mod.write_text("x = 1\n")
    with pytest.raises(load.PartLoadError):
        load.load_part(mod)


def test_load_part_build_returning_non_shape_raises(tmp_path):
    mod = tmp_path / "part.py"
    mod.write_text("def build():\n    return 42\n")
    with pytest.raises(load.PartLoadError):
        load.load_part(mod)


def test_load_step_round_trip(tmp_path):
    box = bd.Box(5, 6, 7)
    step_path = tmp_path / "box.step"
    bd.export_step(box, str(step_path))
    shape = load.load_step(step_path)
    assert shape.volume == pytest.approx(5 * 6 * 7, rel=1e-3)


def test_load_step_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load.load_step(tmp_path / "nope.step")
