"""PulseBand rev B housing (build123d). All dimensions from params/params.toml."""
from build123d import Box, Cylinder, Pos, Part
from forge_cad.params import P  # reads params/params.toml

W = P("housing.wall_thickness")          # 1.6 mm
POCKET = P("housing.battery_pocket")      # [41.0, 26.0, 6.0], centred, floor z=0
BOSS_D, BOSS_H = P("housing.pcb_boss")    # 3.0, 6.0
BOSSES = P("housing.pcb_boss_positions")
CABLE_D = P("housing.cable_exit_diameter")


def build() -> Part:
    outer = Box(POCKET[0] + 2 * W + 8, POCKET[1] + 2 * W + 8, POCKET[2] + W + 4)
    shell = outer - Pos(0, 0, W) * Box(POCKET[0] + 8, POCKET[1] + 8, POCKET[2] + 4)
    # PCB standoffs rise from the pocket floor
    for x, y in BOSSES:
        shell += Pos(x, y, BOSS_H / 2) * Cylinder(BOSS_D / 2, BOSS_H)
    # tether exits through the +X end wall; cable is soldered straight to the PCB pads
    shell -= Pos(POCKET[0] / 2 + 4 + W / 2, 0, 3.0) * Cylinder(CABLE_D / 2, 10, rotation=(0, 90, 0))
    return shell


PART = build()
