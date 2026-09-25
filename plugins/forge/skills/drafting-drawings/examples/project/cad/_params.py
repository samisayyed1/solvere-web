"""Tiny params accessor shared by the example parts (CONTRACTS §2: every
dimension comes from params/params.toml; a missing key is an error, never a
silent default)."""
from __future__ import annotations

from typing import Any, Mapping


def p(params: Mapping[str, Any] | None, key: str) -> float:
    if params is None:
        raise KeyError(f"params not supplied; {key!r} must come from params/params.toml")
    node: Any = params
    for part in key.split("."):
        if not isinstance(node, Mapping) or part not in node:
            raise KeyError(f"params/params.toml has no {key!r}")
        node = node[part]
    if isinstance(node, Mapping):
        node = node["value"]
    return float(node)
