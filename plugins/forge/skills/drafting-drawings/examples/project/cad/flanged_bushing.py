"""Example part: flanged bushing -- a flange disc with four bolt holes, a
cylindrical boss on top, a through bore and a counterbore from the boss end.

Frame: axis along Z, flange bottom at Z=0, bolt holes on the X and Y axes.
"""
from __future__ import annotations

import sys
from pathlib import Path

import build123d as bd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _params import p  # noqa: E402


def build(params=None) -> bd.Shape:
    fd = p(params, "bushing.flange_dia")
    ft = p(params, "bushing.flange_thickness")
    bd_ = p(params, "bushing.boss_dia")
    bh = p(params, "bushing.boss_height")
    bore = p(params, "bushing.bore_dia")
    cb_d = p(params, "bushing.cbore_dia")
    cb_depth = p(params, "bushing.cbore_depth")
    pcd = p(params, "bushing.bolt_pcd")
    hole = p(params, "bushing.bolt_hole_dia")

    lo = (bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)
    part = bd.Cylinder(fd / 2, ft, align=lo) + bd.Pos(0, 0, ft) * bd.Cylinder(bd_ / 2, bh, align=lo)
    top = ft + bh
    part = part - bd.Cylinder(bore / 2, 3 * top)
    part = part - bd.Pos(0, 0, top - cb_depth) * bd.Cylinder(cb_d / 2, 2 * cb_depth, align=lo)
    for x, y in ((pcd / 2, 0), (-pcd / 2, 0), (0, pcd / 2), (0, -pcd / 2)):
        part = part - bd.Pos(x, y, 0) * bd.Cylinder(hole / 2, 3 * ft)
    return part
