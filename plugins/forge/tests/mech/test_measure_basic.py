"""forge_cad.measure: validity, bbox, volume, area, mass -- hand-calculated
reference shapes (plugins/forge/lib/forge_cad/measure.py)."""

from __future__ import annotations

import pytest

bd = pytest.importorskip("build123d")  # CAD env only (~/.forge/bin/forge-python)

from forge_cad import measure


def test_validity_on_a_clean_box():
    box = bd.Box(10, 20, 30)
    v = measure.validity(box)
    assert v == {"is_valid": True, "is_manifold": True, "solid_count": 1}


def test_bounding_box_hand_calc():
    box = bd.Box(20, 15, 2.0)
    bb = measure.bounding_box(box)
    assert bb["size_mm"] == pytest.approx((20.0, 15.0, 2.0))
    assert bb["min_mm"] == pytest.approx((-10.0, -7.5, -1.0))
    assert bb["max_mm"] == pytest.approx((10.0, 7.5, 1.0))


def test_volume_hand_calc():
    box = bd.Box(20, 15, 2.0)
    assert measure.volume(box) == pytest.approx(20 * 15 * 2.0, rel=1e-6)


def test_area_hand_calc():
    box = bd.Box(10, 10, 10)
    assert measure.area(box) == pytest.approx(6 * 10 * 10, rel=1e-6)


def test_mass_properties_hand_calc():
    box = bd.Box(20, 15, 2.0)  # 600 mm^3
    m = measure.mass_properties(box, density_kg_m3=1200.0)
    expected_mass_g = 600.0 * 1200.0 * 1e-6  # 0.72 g
    assert m["mass_g"] == pytest.approx(expected_mass_g, rel=1e-6)
    assert m["center_of_mass_mm"] == pytest.approx((0.0, 0.0, 0.0), abs=1e-6)


def test_validity_seeded_wrong_null_shape_fails():
    empty = bd.Compound(children=[])
    v = measure.validity(empty)
    assert v["is_valid"] is False
    assert v["solid_count"] == 0
