"""Snap-fit lid in its closed position (reference solution for the eval self-test)."""
import importlib.util
from pathlib import Path

from build123d import Align, Box, Part, Pos

_spec = importlib.util.spec_from_file_location("_params", Path(__file__).with_name("_params.py"))
_m = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_m); p = _m.p
A = (Align.MIN, Align.MIN, Align.MIN)


def build() -> Part:
    t = p("enclosure.wall")
    y = p("enclosure.cavity_half_width")
    rim = p("enclosure.rim_z")
    L, h, hook = p("lid.latch_length"), p("lid.latch_thickness"), p("lid.latch_hook")
    lid = Pos(-26.0 - t, -y - t, rim) * Box(52.0 + 2 * t, 2 * y + 2 * t, t, align=A)
    for s in (-1, 1):
        y_in = y - 0.3                      # 0.3 mm gap to the wall
        ya = y_in - h if s > 0 else -y_in
        arm = Pos(-3.0, ya, rim - L) * Box(6.0, h, L, align=A)
        yh = y_in if s > 0 else -y_in - hook
        hk = Pos(-3.0, yh, rim - L) * Box(6.0, hook, 1.2, align=A)
        lid += arm + hk
    return lid


PART = build()
