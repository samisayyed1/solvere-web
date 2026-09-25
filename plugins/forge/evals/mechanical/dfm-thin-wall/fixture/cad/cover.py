"""Sensor cover: open-bottom shell with vent slots (build123d). Dimensions from params/params.toml."""
import tomllib
from pathlib import Path

from build123d import Align, Box, Part, Pos

_P = tomllib.loads((Path(__file__).resolve().parents[1] / "params" / "params.toml").read_text())
A = (Align.CENTER, Align.CENTER, Align.MIN)


def p(key: str) -> float:
    group, name = key.split(".")
    return float(_P[group][name]["value"])


def build() -> Part:
    L, W, H, t, v = p("cover.length"), p("cover.width"), p("cover.height"), p("cover.wall"), p("cover.vent_width")
    shell = Box(L, W, H, align=A) - Box(L - 2 * t, W - 2 * t, H - t, align=A)
    for i in range(-2, 3):
        shell -= Pos(i * 8.0, 0, H - t / 2) * Box(v, W * 0.6, t * 3)
    return shell


PART = build()
