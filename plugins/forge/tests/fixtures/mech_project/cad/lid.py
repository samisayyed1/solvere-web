"""Flat lid for box.py's enclosure, sitting with a small clearance gap above
the box's open top rim (for geometry.clearance / geometry.interference
fixture checks)."""

from __future__ import annotations

import build123d as bd


def _p(params: dict | None, key: str, default: float) -> float:
    if not params:
        return default
    node = params
    for part in key.split("."):
        if not isinstance(node, dict) or part not in node:
            return default
        node = node[part]
    if isinstance(node, dict) and "value" in node:
        return float(node["value"])
    return float(node)


def build(params: dict | None = None) -> bd.Shape:
    length = _p(params, "enclosure.length", 60.0)
    width = _p(params, "enclosure.width", 40.0)
    height = _p(params, "enclosure.height", 20.0)
    lid_thickness = _p(params, "enclosure.lid_thickness", 2.0)
    clearance = _p(params, "enclosure.lid_clearance", 0.3)

    lid = bd.Box(length, width, lid_thickness)
    # box.py's top rim sits at z = height/2; leave `clearance` mm of air gap.
    z = height / 2 + clearance + lid_thickness / 2
    return lid.translate((0, 0, z))
