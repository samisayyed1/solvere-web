"""forge_cad.measure.min_radius -- hand-calc fillet radii (plugins/forge/lib/forge_cad/measure.py)."""

from __future__ import annotations

import pytest

bd = pytest.importorskip("build123d")  # CAD env only (~/.forge/bin/forge-python)

from forge_cad import measure


def test_convex_fillet_radius_hand_calc():
    box = bd.Box(30, 30, 10)
    vertical_edges = box.edges().filter_by(bd.Axis.Z)
    filleted = box.fillet(3.0, vertical_edges)
    results = measure.min_radius(filleted, concave_only=False)
    assert len(results) == 4
    for r in results:
        assert r["radius_mm"] == pytest.approx(3.0, abs=1e-6)
        assert r["is_concave"] is False


def test_concave_only_excludes_convex_fillets_by_default():
    box = bd.Box(30, 30, 10)
    vertical_edges = box.edges().filter_by(bd.Axis.Z)
    filleted = box.fillet(3.0, vertical_edges)
    results = measure.min_radius(filleted)  # concave_only=True default
    assert results == []


def test_concave_internal_fillet_detected():
    # A pocket cut INTO the box (not a boss added on top) has genuinely
    # concave internal vertical edges at its four corners.
    with bd.BuildPart() as bp:
        bd.Box(30, 30, 10)
        with bd.BuildSketch(bd.Plane.XY.offset(5)):
            bd.Rectangle(10, 10)
        bd.extrude(amount=-6, mode=bd.Mode.SUBTRACT)
    part = bp.part
    pocket_bottom_z = 5 - 6
    vertical_edges = [e for e in part.edges().filter_by(bd.Axis.Z)
                       if e.length == pytest.approx(6.0) and e.center().Z == pytest.approx((5 + pocket_bottom_z) / 2)]
    assert len(vertical_edges) == 4
    filleted = part.fillet(1.5, vertical_edges)
    results = measure.min_radius(filleted, concave_only=True)
    assert len(results) >= 1
    assert all(r["radius_mm"] == pytest.approx(1.5, abs=1e-6) for r in results)
    assert all(r["is_concave"] is True for r in results)


def test_seeded_missing_fillet_sharp_corner_is_not_found_as_a_radius():
    """A sharp internal corner (FORGE-BRIEF §6 seeded-defect list: 'missing
    fillet, sharp internal corner below min radius') has no cylindrical face
    at all -- min_radius must report nothing to measure there, which a
    verifying-geometry spec then treats as an error (no fillet exists to
    check), not a silent pass."""
    with bd.BuildPart() as bp:
        bd.Box(30, 30, 10)
        with bd.BuildSketch(bd.Plane.XY.offset(5)):
            bd.Rectangle(10, 10)
        bd.extrude(amount=-6, mode=bd.Mode.SUBTRACT)
    part = bp.part  # no fillet applied -- sharp internal pocket corners only
    results = measure.min_radius(part, concave_only=True)
    assert results == []
