"""M8 (review #1) fixture: a flat slab 1.6 mm thick, meant to stand in for a
rib/boss feature checked against a 2.0 mm nominal wall (params
dfm_test.nominal_wall_mm) -- ratio 1.6/2.0 = 0.8, which must FAIL a 0.5x
("at most half the wall") rib/boss cap. See requirements/dfm/rib_bad.toml.
"""
from __future__ import annotations

import build123d as bd

THICKNESS_MM = 1.6


def build(params: dict | None = None) -> bd.Shape:
    return bd.Box(30.0, 30.0, THICKNESS_MM)
