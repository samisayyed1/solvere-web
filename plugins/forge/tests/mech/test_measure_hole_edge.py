"""forge_cad.measure.find_holes / hole_edge_distance -- hand-calc reference
cases (plugins/forge/lib/forge_cad/measure.py)."""

from __future__ import annotations

import pytest

bd = pytest.importorskip("build123d")  # CAD env only (~/.forge/bin/forge-python)

from forge_cad import measure


def test_centered_hole_edge_distance_hand_calc():
    box = bd.Box(40, 40, 10)
    holed = box - bd.Cylinder(4, 20)  # centered, radius 4 mm
    holes = measure.find_holes(holed)
    assert len(holes) == 1
    assert holes[0]["radius_mm"] == pytest.approx(4.0)
    top = holed.faces().sort_by(bd.Axis.Z)[-1]
    hole_face = holed.faces()[holes[0]["face_index"]]
    m = measure.hole_edge_distance(holed, hole_face, top)
    assert m["axis_to_edge_mm"] == pytest.approx(20.0, abs=1e-6)  # 40/2, centered
    assert m["wall_to_edge_mm"] == pytest.approx(16.0, abs=1e-6)  # 20 - radius 4


def test_off_center_hole_edge_distance_hand_calc():
    box = bd.Box(40, 40, 10)
    holed = box - bd.Pos(10, 0, 0) * bd.Cylinder(3, 20)
    holes = measure.find_holes(holed)
    assert len(holes) == 1
    top = holed.faces().sort_by(bd.Axis.Z)[-1]
    hole_face = holed.faces()[holes[0]["face_index"]]
    m = measure.hole_edge_distance(holed, hole_face, top)
    assert m["axis_to_edge_mm"] == pytest.approx(10.0, abs=1e-6)  # 20 - 10 to the +x edge
    assert m["wall_to_edge_mm"] == pytest.approx(7.0, abs=1e-6)  # 10 - radius 3


def test_seeded_hole_too_close_to_edge_reads_below_a_typical_3mm_minimum():
    """A hole drilled 2 mm from the edge (FORGE-BRIEF §6 seeded-defect list:
    'hole too close to edge') must read below a representative 3 mm DFM
    hole-to-edge minimum."""
    box = bd.Box(40, 40, 10)
    # radius 1 mm hole, center 3 mm from the +x edge (20 - 3 = 17) -> wall_to_edge = 2 mm
    holed = box - bd.Pos(17, 0, 0) * bd.Cylinder(1, 20)
    holes = measure.find_holes(holed)
    top = holed.faces().sort_by(bd.Axis.Z)[-1]
    hole_face = holed.faces()[holes[0]["face_index"]]
    m = measure.hole_edge_distance(holed, hole_face, top)
    assert m["wall_to_edge_mm"] == pytest.approx(2.0, abs=1e-6)
    assert m["wall_to_edge_mm"] < 3.0


def test_find_holes_ignores_a_fillet_face():
    box = bd.Box(30, 30, 10)
    vertical_edges = box.edges().filter_by(bd.Axis.Z)
    filleted = box.fillet(3.0, vertical_edges)
    holes = measure.find_holes(filleted)
    assert holes == []
