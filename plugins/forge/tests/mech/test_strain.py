"""checking-dfm/scripts/strain.py: the R5d cantilever snap-fit strain formula.

Imported directly by path since scripts/ is not a package (matches how
checking-dfm/scripts/verify.py imports its sibling module).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_STRAIN_PATH = Path(__file__).resolve().parents[2] / "skills" / "checking-dfm" / "scripts" / "strain.py"
_spec = importlib.util.spec_from_file_location("dfm_strain", _STRAIN_PATH)
strain = importlib.util.module_from_spec(_spec)
sys.modules["dfm_strain"] = strain
_spec.loader.exec_module(strain)


def test_root_strain_hand_calc_constant_section():
    # eps = h*y / (k*L^2); h=1.2, y=1.5, L=15, k=0.67
    eps = strain.root_strain(deflection_mm=1.5, length_mm=15.0, thickness_mm=1.2, taper="constant")
    expected = (1.2 * 1.5) / (0.67 * 15.0 ** 2)
    assert eps == pytest.approx(expected, rel=1e-9)
    assert eps * 100 == pytest.approx(1.194, abs=1e-3)


def test_tapered_half_thickness_allows_more_deflection_for_the_same_strain():
    # Higher k -> lower strain for the same y/L/h (R5d: tapering allows more
    # deflection at the same root strain).
    eps_constant = strain.root_strain(deflection_mm=2.0, length_mm=15.0, thickness_mm=1.2, taper="constant")
    eps_tapered = strain.root_strain(deflection_mm=2.0, length_mm=15.0, thickness_mm=1.2, taper="tapered_half_thickness")
    assert eps_tapered < eps_constant


def test_seeded_overstressed_latch_exceeds_pc_allowable():
    """8 mm deflection over a short 15 mm/1.2 mm arm (FORGE-BRIEF §6 seeded-
    defect list: 'snap-fit strain over allowable') must exceed PC's 4%
    Covestro-sourced allowable strain (references/rules/snap_fit.toml)."""
    eps_pct = strain.root_strain(deflection_mm=8.0, length_mm=15.0, thickness_mm=1.2, taper="constant") * 100
    assert eps_pct > 4.0


def test_invalid_length_raises():
    with pytest.raises(ValueError):
        strain.root_strain(deflection_mm=1.0, length_mm=0.0, thickness_mm=1.0)


def test_invalid_taper_raises():
    with pytest.raises(ValueError):
        strain.root_strain(deflection_mm=1.0, length_mm=10.0, thickness_mm=1.0, taper="bogus")


def test_short_arm_warning_triggers_below_threshold():
    assert strain.short_arm_warning(length_mm=5.0, thickness_mm=1.0) is not None


def test_short_arm_warning_silent_above_threshold():
    assert strain.short_arm_warning(length_mm=15.0, thickness_mm=1.0) is None
