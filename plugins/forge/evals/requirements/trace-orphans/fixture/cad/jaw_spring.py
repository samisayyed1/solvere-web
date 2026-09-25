"""Jaw return spring seat (build123d). Keeps the jaw closed on the strap (REQ-MECH-001)."""
from build123d import Cylinder, Part


def build() -> Part:
    return Cylinder(3, 8)
