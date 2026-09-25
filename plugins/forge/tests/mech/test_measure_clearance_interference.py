"""forge_cad.measure.clearance / interference -- hand-calc reference cases."""

from __future__ import annotations

import pytest

bd = pytest.importorskip("build123d")  # CAD env only (~/.forge/bin/forge-python)

from forge_cad import measure


def test_clearance_hand_calc_gap():
    a = bd.Box(10, 10, 10)  # spans x in [-5, 5]
    b = bd.Box(6, 6, 6).translate((13, 0, 0))  # spans x in [10, 16] -> gap 5.0
    m = measure.clearance(a, b)
    assert m["distance_mm"] == pytest.approx(5.0, abs=1e-6)


def test_clearance_zero_when_touching():
    a = bd.Box(10, 10, 10)
    b = bd.Box(6, 6, 6).translate((8, 0, 0))  # a right face x=5, b left face x=5 -> touching
    m = measure.clearance(a, b)
    assert m["distance_mm"] == pytest.approx(0.0, abs=1e-6)


def test_interference_hand_calc_overlap_volume():
    a = bd.Box(10, 10, 10)  # x in [-5, 5], y/z in [-5, 5]
    b = bd.Box(6, 6, 6).translate((7, 0, 0))  # x in [4, 10] -> overlap x in [4, 5] (1 mm) * 6 * 6
    m = measure.interference(a, b)
    assert m["interferes"] is True
    assert m["overlap_volume_mm3"] == pytest.approx(1.0 * 6.0 * 6.0, rel=1e-6)


def test_interference_none_when_apart():
    a = bd.Box(10, 10, 10)
    b = bd.Box(6, 6, 6).translate((20, 0, 0))
    m = measure.interference(a, b)
    assert m["interferes"] is False
    assert m["overlap_volume_mm3"] == 0.0


def test_seeded_interference_of_half_a_millimeter_is_detected():
    """A planted 0.5 mm interference (FORGE-BRIEF §6 seeded-defect list) must
    read as a real, non-zero, non-touching overlap."""
    a = bd.Box(20, 20, 10)  # x in [-10, 10]
    b = bd.Box(20, 20, 10).translate((19.5, 0, 0))  # x in [9.5, 29.5] -> overlap 0.5 mm in x
    m = measure.interference(a, b)
    assert m["interferes"] is True
    assert m["overlap_volume_mm3"] == pytest.approx(0.5 * 20.0 * 10.0, rel=1e-6)
