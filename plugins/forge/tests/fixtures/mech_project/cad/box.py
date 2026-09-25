"""Dev-board-style enclosure base: an open-top hollow box with filleted
outer edges and four corner mounting holes. Fixture part for
verifying-geometry / checking-dfm (PASS case). All dimensions come from
params/params.toml -- see build().
"""

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
    wall = _p(params, "enclosure.wall_thickness", 2.0)
    fillet_r = _p(params, "enclosure.edge_fillet_radius", 2.0)
    hole_d = _p(params, "mounting.hole_diameter", 3.0)
    hole_inset = _p(params, "mounting.hole_inset", 6.0)

    box = bd.Box(length, width, height)
    top = box.faces().sort_by(bd.Axis.Z)[-1]
    shell = box.hollow(faces=[top], thickness=-wall)

    # Fillet only the four OUTER vertical edges (hollowing also creates four
    # inner vertical edges at the same Z-extent; select by XY corner extent).
    outer_verticals = []
    for e in shell.edges().filter_by(bd.Axis.Z):
        c = e.center()
        if abs(abs(c.X) - length / 2) < 1e-6 and abs(abs(c.Y) - width / 2) < 1e-6:
            outer_verticals.append(e)
    shell = shell.fillet(fillet_r, outer_verticals)

    # Four mounting holes through the base, inset from each corner.
    r = hole_d / 2.0
    cx, cy = length / 2 - hole_inset, width / 2 - hole_inset
    part = shell
    for sx in (-1, 1):
        for sy in (-1, 1):
            hole = bd.Pos(sx * cx, sy * cy, 0) * bd.Cylinder(r, height * 3)
            part = part - hole
    return part
