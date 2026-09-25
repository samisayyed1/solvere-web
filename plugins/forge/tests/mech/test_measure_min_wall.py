"""forge_cad.measure.min_wall_thickness -- hand-calc accuracy and a seeded
thin-wall failure (plugins/forge/lib/forge_cad/measure.py)."""

from __future__ import annotations

import pytest

bd = pytest.importorskip("build123d")  # CAD env only (~/.forge/bin/forge-python)

from forge_cad import measure


def _closed_shell(wall_mm: float) -> bd.Shape:
    return bd.Box(40, 30, 20).hollow(faces=None, thickness=-wall_mm)


def test_min_wall_matches_hand_calc_within_sampling_tolerance():
    shell = _closed_shell(2.0)
    result = measure.min_wall_thickness(shell, sample_count=3000, tessellate_tolerance=0.05, seed=1)
    # Hand calc: uniform 2.0 mm wall on all six faces of a rectangular shell.
    assert result["min_thickness_mm"] == pytest.approx(2.0, rel=0.01)
    assert result["hit_count"] == 3000


def test_min_wall_seeded_thin_wall_reads_thin():
    thin = _closed_shell(0.5)
    result = measure.min_wall_thickness(thin, sample_count=1500, tessellate_tolerance=0.05, seed=1)
    assert result["min_thickness_mm"] == pytest.approx(0.5, rel=0.02)
    assert result["min_thickness_mm"] < 0.8  # below the FDM DFM minimum -- would fail a real check


def test_min_wall_restricted_to_a_face_subset():
    shell = _closed_shell(2.0)
    one_face = [shell.faces().sort_by(bd.Axis.Z)[-1]]
    result = measure.min_wall_thickness(shell, sample_count=500, faces=one_face, seed=1)
    assert result["min_thickness_mm"] == pytest.approx(2.0, rel=0.02)


def test_min_wall_on_empty_face_selection_reports_no_samples():
    shell = _closed_shell(2.0)
    result = measure.min_wall_thickness(shell, sample_count=100, faces=[])
    assert result["sample_count"] == 0
    assert result["min_thickness_mm"] is None


def test_min_wall_is_reproducible_with_a_fixed_seed():
    shell = _closed_shell(2.0)
    a = measure.min_wall_thickness(shell, sample_count=500, seed=42)
    b = measure.min_wall_thickness(shell, sample_count=500, seed=42)
    assert a["min_thickness_mm"] == b["min_thickness_mm"]
