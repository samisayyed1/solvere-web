"""SensorHub rev A lid (build123d)."""
from build123d import Box, Cylinder, Pos, Part
from forge_cad.params import P

T = P("enclosure.lid_wall")
HOLE_D = P("lid.screw_hole_diameter")
EDGE = P("lid.screw_hole_edge_offset")
L, Wd = 64.2, 48.0


def build() -> Part:
    lid = Box(L, Wd, T)
    for sx in (-1, 1):
        for sy in (-1, 1):
            lid -= Pos(sx * (L / 2 - EDGE), sy * (Wd / 2 - EDGE), 0) * Cylinder(HOLE_D / 2, T * 3)
    return lid
