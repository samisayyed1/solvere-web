"""Seeded-defect variant of box.py: the wall thickness is hard-coded to
0.6 mm instead of read from params/params.toml's enclosure.wall_thickness
(2.0 mm) -- exactly the "hard-coded dimension diverges from params" failure
verifying-geometry and checking-dfm exist to catch (CONTRACTS §2,
FORGE-BRIEF §0). Used only by tests/fixtures to prove the checks FAIL.
"""

from __future__ import annotations

import build123d as bd


def build(params: dict | None = None) -> bd.Shape:
    length = 60.0
    width = 40.0
    height = 20.0
    wall = 0.6  # SEEDED DEFECT: should be params["enclosure"]["wall_thickness"]["value"] (2.0 mm)
    fillet_r = 2.0
    hole_d = 3.0
    hole_inset = 6.0

    box = bd.Box(length, width, height)
    top = box.faces().sort_by(bd.Axis.Z)[-1]
    shell = box.hollow(faces=[top], thickness=-wall)

    outer_verticals = []
    for e in shell.edges().filter_by(bd.Axis.Z):
        c = e.center()
        if abs(abs(c.X) - length / 2) < 1e-6 and abs(abs(c.Y) - width / 2) < 1e-6:
            outer_verticals.append(e)
    shell = shell.fillet(fillet_r, outer_verticals)

    r = hole_d / 2.0
    cx, cy = length / 2 - hole_inset, width / 2 - hole_inset
    part = shell
    for sx in (-1, 1):
        for sy in (-1, 1):
            hole = bd.Pos(sx * cx, sy * cy, 0) * bd.Cylinder(r, height * 3)
            part = part - hole
    return part
