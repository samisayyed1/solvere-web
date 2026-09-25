"""forge_cad.measure.watertight_export (plugins/forge/lib/forge_cad/measure.py)."""

from __future__ import annotations

import pytest

bd = pytest.importorskip("build123d")  # CAD env only (~/.forge/bin/forge-python)

from forge_cad import measure


def test_closed_hollow_box_is_watertight(tmp_path):
    shell = bd.Box(40, 30, 20).hollow(faces=None, thickness=-2.0)
    result = measure.watertight_export(shell, tmp_path / "shell.stl", tolerance=0.05)
    assert result["export_ok"] is True
    assert result["watertight"] is True
    assert result["is_winding_consistent"] is True
    assert (tmp_path / "shell.stl").exists()


def test_open_top_shell_is_still_a_closed_manifold(tmp_path):
    """An open-top hollow box has finite wall thickness everywhere, so its
    boundary is still a closed 2-manifold (a bowl/tray) -- watertight=True is
    the physically correct answer here, not a bug."""
    box = bd.Box(40, 30, 20)
    top = box.faces().sort_by(bd.Axis.Z)[-1]
    shell = box.hollow(faces=[top], thickness=-2.0)
    result = measure.watertight_export(shell, tmp_path / "open.stl", tolerance=0.05)
    assert result["watertight"] is True


def test_seeded_non_watertight_mesh_from_a_bare_face(tmp_path):
    """A single 2D face (no thickness) tessellates to an open mesh with
    boundary edges -- must read as non-watertight."""
    face = bd.Rectangle(10, 10)
    result = measure.watertight_export(face, tmp_path / "face.stl", tolerance=0.05)
    assert result["watertight"] is False
