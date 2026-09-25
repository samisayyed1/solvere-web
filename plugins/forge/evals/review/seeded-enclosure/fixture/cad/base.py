"""SensorHub rev A base (build123d). Dimensions from params/params.toml."""
from build123d import Box, Cylinder, Pos, Part
from forge_cad.params import P

W = P("enclosure.base_wall")
SLOT = P("base.pcb_slot_width")
STANDOFF = P("pcb.standoff_height")
CABLE_D = P("base.cable_exit_diameter")


def build() -> Part:
    outer = Box(SLOT + 2 * W, 44 + 2 * W, 10 + W)
    base = outer - Pos(0, 0, W) * Box(SLOT, 44, 10)
    for x in (-26, 26):
        for y in (-16, 16):
            base += Pos(x, y, W + STANDOFF / 2) * Cylinder(2.5, STANDOFF)
    # DC cable enters through the -X wall and lands on the J3 screw terminal
    base -= Pos(-SLOT / 2 - W / 2, 0, W + 2.5) * Cylinder(CABLE_D / 2, W * 3, rotation=(0, 90, 0))
    return base
