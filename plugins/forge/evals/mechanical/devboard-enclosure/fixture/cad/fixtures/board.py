"""Dev-board keep-out volume (fixed fixture; see docs/board.md)."""
from build123d import Align, Box, Part, Pos

A = (Align.MIN, Align.MIN, Align.MIN)


def build() -> Part:
    pcb = Pos(-25.5, -10.5, 0.0) * Box(51.0, 21.0, 1.6, align=A)
    usb = Pos(-26.0, -4.47, 1.6) * Box(7.35, 8.94, 3.16, align=A)
    parts = Pos(-18.0, -9.5, 1.6) * Box(43.5, 19.0, 2.5, align=A)
    return pcb + usb + parts
