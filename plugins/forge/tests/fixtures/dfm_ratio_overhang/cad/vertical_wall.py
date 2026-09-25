"""M8 (review #1) fixture: a plain box, used to prove a vertical side wall
must PASS an overhang check (its own test picks one side face explicitly,
never the flat bottom, so this is genuinely testing "vertical wall != an
overhang", not "no downward face was ever selected"). See
requirements/dfm/vertical.toml.
"""
from __future__ import annotations

import build123d as bd


def build(params: dict | None = None) -> bd.Shape:
    return bd.Box(30.0, 30.0, 20.0)
