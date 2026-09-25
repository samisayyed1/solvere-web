"""Example part: open-top enclosure shell with two internal screw bosses.

Frame: centred on X/Y, floor bottom at Z=0, open at Z=height. Bosses sit on
the X axis at +/- boss_x, rising from the floor.
"""
from __future__ import annotations

import sys
from pathlib import Path

import build123d as bd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _params import p  # noqa: E402


def build(params=None) -> bd.Shape:
    L = p(params, "enclosure.length")
    W = p(params, "enclosure.width")
    H = p(params, "enclosure.height")
    wall = p(params, "enclosure.wall")
    floor = p(params, "enclosure.floor")
    boss_d = p(params, "enclosure.boss_dia")
    boss_h = p(params, "enclosure.boss_height")
    boss_x = p(params, "enclosure.boss_x")
    pilot = p(params, "enclosure.pilot_dia")

    lo = (bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)
    outer = bd.Box(L, W, H, align=lo)
    cavity = bd.Pos(0, 0, floor) * bd.Box(L - 2 * wall, W - 2 * wall, H, align=lo)
    part = outer - cavity
    for x in (-boss_x, boss_x):
        part = part + bd.Pos(x, 0, floor) * bd.Cylinder(boss_d / 2, boss_h, align=lo)
        part = part - bd.Pos(x, 0, floor) * bd.Cylinder(pilot / 2, boss_h + 1, align=lo)
    return part
