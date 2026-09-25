"""Camera clip body (build123d). Jaw opening 26 mm (REQ-MECH-002), mass target 45 g (REQ-SYS-001)."""
from build123d import Box, Part


def build() -> Part:
    return Box(40, 30, 12) - Box(26, 30, 8)
