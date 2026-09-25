"""Mounting plate: a flat rectangular plate with four corner mounting holes.
Ladder fixture part (plugins/forge/tests/ladder). Every dimension comes from
params/params.toml (CONTRACTS.md §2) -- see build().
"""

from __future__ import annotations

import build123d as bd


def _p(params: dict | None, key: str) -> float:
    node = params or {}
    for part in key.split("."):
        node = node[part]
    return float(node["value"] if isinstance(node, dict) else node)


def build(params: dict | None = None) -> bd.Shape:
    length = _p(params, "plate.length")
    width = _p(params, "plate.width")
    thickness = _p(params, "plate.thickness")
    hole_d = _p(params, "plate.hole_diameter")
    inset = _p(params, "plate.hole_inset")

    part = bd.Box(length, width, thickness)
    cx, cy = length / 2 - inset, width / 2 - inset
    for sx in (-1, 1):
        for sy in (-1, 1):
            part = part - bd.Pos(sx * cx, sy * cy, 0) * bd.Cylinder(hole_d / 2, thickness * 3)
    return part
