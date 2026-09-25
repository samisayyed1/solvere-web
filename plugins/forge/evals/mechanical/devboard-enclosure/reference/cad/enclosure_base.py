"""Enclosure base (reference solution for the eval self-test)."""
import importlib.util
from pathlib import Path

from build123d import Align, Box, Cylinder, Part, Pos

_spec = importlib.util.spec_from_file_location("_params", Path(__file__).with_name("_params.py"))
_m = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_m); p = _m.p
A = (Align.MIN, Align.MIN, Align.MIN)


def build() -> Part:
    t = p("enclosure.wall")
    x0, x1 = -26.0, 26.0
    y = p("enclosure.cavity_half_width")
    floor_top, rim = -p("enclosure.standoff_height"), p("enclosure.rim_z")
    outer = Pos(x0 - t, -y - t, floor_top - t) * Box(x1 - x0 + 2 * t, 2 * y + 2 * t, rim - floor_top + t, align=A)
    cavity = Pos(x0, -y, floor_top) * Box(x1 - x0, 2 * y, rim - floor_top + 1, align=A)
    base = outer - cavity
    for sx, sy in ((-22.0, -7.0), (-22.0, 7.0), (22.0, -7.0), (22.0, 7.0)):
        base += Pos(sx, sy, floor_top) * Cylinder(2.25, p("enclosure.standoff_height"), align=(Align.CENTER, Align.CENTER, Align.MIN))
    zc = 1.6 + 3.16 / 2
    base -= Pos(x0 - t - 1, -6.6, zc - 3.65) * Box(t + 2, 13.2, rim - zc + 3.65 + 1, align=A)  # USB-C slot, open at the rim
    for s in (-1, 1):                                                                   # latch windows
        yw = y if s > 0 else -y - t
        base -= Pos(-3.3, yw - 0.01, -2.2) * Box(6.6, t + 0.02, 1.6, align=A)
    return base


PART = build()
