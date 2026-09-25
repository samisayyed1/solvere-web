import tomllib
from pathlib import Path

_P = tomllib.loads((Path(__file__).resolve().parents[1] / "params" / "params.toml").read_text())


def p(key: str) -> float:
    group, name = key.split(".", 1)
    return float(_P[group][name]["value"])
