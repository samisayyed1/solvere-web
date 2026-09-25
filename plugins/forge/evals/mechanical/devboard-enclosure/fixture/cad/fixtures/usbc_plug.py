"""Mating USB-C plug overmold keep-out (fixed fixture; see docs/board.md)."""
from build123d import Align, Box, Part, Pos

A = (Align.MIN, Align.MIN, Align.MIN)
Z_CENTRE = 1.6 + 3.16 / 2


def build() -> Part:
    return Pos(-46.0, -6.2, Z_CENTRE - 3.25) * Box(20.0, 12.4, 6.5, align=A)
