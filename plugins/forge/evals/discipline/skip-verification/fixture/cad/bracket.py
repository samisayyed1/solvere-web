"""L mounting bracket (build123d). Dimensions from params/params.toml."""
import tomllib
from pathlib import Path

from build123d import Align, Box, Cylinder, Part, Pos, Rot

_P = tomllib.loads((Path(__file__).resolve().parents[1] / "params" / "params.toml").read_text())


def p(key: str) -> float:
    group, name = key.split(".")
    return float(_P[group][name]["value"])


def build() -> Part:
    w, leg, t, d = p("bracket.width"), p("bracket.leg"), p("bracket.thickness"), p("bracket.hole_diameter")
    base = Box(leg, w, t, align=(Align.MIN, Align.CENTER, Align.MIN))
    upright = Box(t, w, leg, align=(Align.MIN, Align.CENTER, Align.MIN))
    part = base + upright
    part -= Pos(leg * 0.65, 0, t / 2) * Cylinder(d / 2, t * 2)
    part -= Pos(t / 2, 0, leg * 0.65) * Rot(0, 90, 0) * Cylinder(d / 2, t * 2)
    return part


PART = build()
