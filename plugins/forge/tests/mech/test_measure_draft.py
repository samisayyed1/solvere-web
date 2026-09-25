"""forge_cad.measure.draft_angles / select_side_faces -- hand-calc via a
frustum built with a known taper (plugins/forge/lib/forge_cad/measure.py)."""

from __future__ import annotations

import math

import pytest

bd = pytest.importorskip("build123d")  # CAD env only (~/.forge/bin/forge-python)

from forge_cad import measure


def _frustum(draft_deg: float, height: float = 20.0, base: float = 20.0) -> bd.Shape:
    dx = height * math.tan(math.radians(draft_deg))
    with bd.BuildPart() as bp:
        with bd.BuildSketch(bd.Plane.XY):
            bd.Rectangle(base, base)
        with bd.BuildSketch(bd.Plane.XY.offset(height)):
            bd.Rectangle(base - 2 * dx, base - 2 * dx)
        bd.loft()
    return bp.part


def test_draft_angle_matches_hand_calc():
    part = _frustum(3.0)
    faces = measure.select_side_faces(part, pull_direction=(0, 0, 1))
    assert len(faces) == 4
    results = measure.draft_angles(part, faces, pull_direction=(0, 0, 1))
    for r in results:
        assert r["draft_deg"] == pytest.approx(3.0, abs=1e-6)


def test_zero_draft_wall_reads_zero():
    box = bd.Box(20, 20, 20)
    faces = measure.select_side_faces(box, pull_direction=(0, 0, 1))
    assert len(faces) == 4
    results = measure.draft_angles(box, faces, pull_direction=(0, 0, 1))
    for r in results:
        assert r["draft_deg"] == pytest.approx(0.0, abs=1e-6)


def test_seeded_zero_draft_molded_face_fails_a_typical_2deg_minimum():
    """A vertical (0 deg draft) molded wall (FORGE-BRIEF §6 seeded-defect
    list) must read below any realistic injection-molding draft minimum."""
    box = bd.Box(20, 20, 20)
    faces = measure.select_side_faces(box, pull_direction=(0, 0, 1))
    results = measure.draft_angles(box, faces, pull_direction=(0, 0, 1))
    assert all(r["draft_deg"] < 2.0 for r in results)


def test_select_side_faces_excludes_top_and_bottom():
    box = bd.Box(20, 20, 20)
    faces = measure.select_side_faces(box, pull_direction=(0, 0, 1))
    normals = {tuple(round(c, 3) for c in tuple(f.normal_at(f.center()))) for f in faces}
    assert (0.0, 0.0, 1.0) not in normals and (0.0, 0.0, -1.0) not in normals
