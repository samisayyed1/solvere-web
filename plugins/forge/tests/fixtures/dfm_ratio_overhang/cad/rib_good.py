"""M8 (review #1) fixture: a flat slab 0.8 mm thick against a 2.0 mm nominal
wall (params dfm_test.nominal_wall_mm) -- ratio 0.8/2.0 = 0.4, which must
PASS a 0.5x rib/boss cap. See requirements/dfm/rib_good.toml.
"""
from __future__ import annotations

import build123d as bd

THICKNESS_MM = 0.8


def build(params: dict | None = None) -> bd.Shape:
    return bd.Box(30.0, 30.0, THICKNESS_MM)
