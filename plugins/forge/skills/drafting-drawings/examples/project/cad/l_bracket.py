"""Example part: L mounting bracket with two base holes and one upright hole.

Frame: X along the base length (upright at X=0..t), Y across the width,
Z up (base bottom at Z=0). All dimensions come from params/params.toml.
"""
from __future__ import annotations

import sys
from pathlib import Path

import build123d as bd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _params import p  # noqa: E402


def build(params=None) -> bd.Shape:
    L = p(params, "bracket.base_length")
    W = p(params, "bracket.width")
    T = p(params, "bracket.thickness")
    H = p(params, "bracket.height")
    d1 = p(params, "bracket.base_hole_dia")
    x1 = p(params, "bracket.base_hole_x")
    pitch = p(params, "bracket.base_hole_pitch")
    d2 = p(params, "bracket.upright_hole_dia")
    z2 = p(params, "bracket.upright_hole_z")

    lo = (bd.Align.MIN, bd.Align.MIN, bd.Align.MIN)
    part = bd.Box(L, W, T, align=lo) + bd.Box(T, W, H, align=lo)
    for y in (W / 2 - pitch / 2, W / 2 + pitch / 2):
        part = part - bd.Pos(x1, y, T / 2) * bd.Cylinder(d1 / 2, 3 * T)
    part = part - bd.Pos(T / 2, W / 2, z2) * bd.Rot(0, 90, 0) * bd.Cylinder(d2 / 2, 3 * T)
    return part
