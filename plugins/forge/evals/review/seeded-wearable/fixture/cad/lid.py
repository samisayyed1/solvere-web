"""PulseBand rev B lid with optical window (build123d)."""
from build123d import Box, Pos, Part
from forge_cad.params import P

W = P("housing.wall_thickness")
FRAME = P("lid.window_frame_wall")   # 0.35 mm around the 12 x 12 mm window


def build() -> Part:
    lid = Box(57.2, 42.2, W)
    window = Box(12 + 2 * FRAME, 12 + 2 * FRAME, 3.0)
    lid += Pos(0, 0, -1.5) * (window - Box(12, 12, 3.0))
    return lid
