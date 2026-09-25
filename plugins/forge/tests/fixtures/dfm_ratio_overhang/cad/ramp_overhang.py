"""M8 (review #1) fixture: a wedge whose single sloped underside is exactly
30 deg from horizontal, facing downward -- a genuine unsupported overhang
that must FAIL a 45 deg "max overhang without support" limit (fdm.toml
overhang_max_deg). Every other face (front/back/left/right/top) is flat and
not downward-facing, so ``geometry.overhang``'s auto face selection must
find exactly this one face. See requirements/dfm/ramp.toml.
"""
from __future__ import annotations

import math

import build123d as bd

DX, DY, DZ = 30.0, 30.0, 40.0
ANGLE_FROM_HORIZONTAL_DEG = 30.0
_Z1 = DY * math.tan(math.radians(ANGLE_FROM_HORIZONTAL_DEG))


def build(params: dict | None = None) -> bd.Shape:
    return bd.Solid.make_wedge(delta_x=DX, delta_y=DY, delta_z=DZ,
                                min_x=0.0, min_z=_Z1, max_x=DX, max_z=DZ)
