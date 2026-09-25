"""forge_cad.measure.boss_rib_thickness -- hand-calc rib thickness/ratio."""

from __future__ import annotations

import pytest

bd = pytest.importorskip("build123d")  # CAD env only (~/.forge/bin/forge-python)

from forge_cad import measure


def _base_with_rib(rib_thickness: float) -> bd.Shape:
    with bd.BuildPart() as bp:
        bd.Box(40, 30, 2, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
        with bd.BuildSketch(bd.Plane.XY.offset(2)):
            bd.Rectangle(rib_thickness, 20)
        bd.extrude(amount=8)
    return bp.part


def _rib_side_faces(part: bd.Shape) -> list[bd.Face]:
    return [f for f in part.faces() if f.is_planar and abs(f.normal_at(f.center()).X) > 0.9]


def test_boss_rib_thickness_hand_calc():
    part = _base_with_rib(1.2)
    faces = _rib_side_faces(part)
    assert len(faces) == 4  # 2 side faces on the rib + 2 on the base slab, same X-normal criterion... see note below
    result = measure.boss_rib_thickness(part, faces, nominal_wall_mm=2.0, sample_count=1500, seed=1)
    assert result["min_thickness_mm"] == pytest.approx(1.2, rel=0.02)
    assert result["ratio"] == pytest.approx(0.6, rel=0.02)


def test_seeded_over_thick_rib_exceeds_a_60_percent_dfm_cap():
    """A rib at 90% of nominal wall (well above the ~50-60% DFM cap, R5c)
    must read a ratio above 0.6."""
    part = _base_with_rib(1.8)  # 1.8 / 2.0 = 0.9
    faces = _rib_side_faces(part)
    result = measure.boss_rib_thickness(part, faces, nominal_wall_mm=2.0, sample_count=1500, seed=1)
    assert result["ratio"] > 0.6
