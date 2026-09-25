"""Tolerance-stack math: worst-case, RSS and (optional) Monte Carlo.

Pure computation, no I/O beyond reading the stack TOML, so it can be unit
tested directly (``plugins/forge/tests/mech2/test_stacking_tolerances.py``)
without going through ``verify.py`` or the check-result machinery.

Stack file format (``analysis/stacks/<name>.toml``)::

    [stack]
    name = "lid_gap"
    description = "gap between lid lip and housing shoulder"

    [requirement]
    unit = "mm"
    gap_min = 0.20
    gap_max = 1.20

    [[contributor]]
    id = "A"
    description = "housing depth"
    nominal = 10.00
    tol_plus = 0.05
    tol_minus = 0.05
    direction = 1          # +1 adds to the gap, -1 subtracts
    distribution = "normal"  # normal | uniform; tol is treated as a 3-sigma half-width for normal

    [[contributor]]
    id = "B"
    description = "lid lip height"
    nominal = 7.00
    tol_plus = 0.03
    tol_minus = 0.03
    direction = -1
    distribution = "normal"

A contributor's ``direction`` is its GD&T sensitivity sign in the stack
equation (ASME Y14.5-2018 (R2024) treats this as the loop-diagram
sensitivity of each contributor to the resultant gap). Asymmetric
tolerances (``tol_plus`` != ``tol_minus``) are decomposed into a symmetric
half-width plus a mean shift, per standard tolerance-stack practice.
"""

from __future__ import annotations

import math
import random
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class StackFileError(ValueError):
    """The stack TOML is missing a required field or is otherwise malformed."""


# S7: geometry stacks are SI-mm only (CONTRACTS SS10); "deg" is the one
# non-length unit a GD&T loop diagram legitimately uses (an angular stack-up,
# e.g. a cumulative orientation tolerance). Anything else -- a typo like
# "mn", or "in"/"cm"/other non-SI units -- is refused rather than silently
# trusted, since nothing here converts units.
UNIT_VOCAB = ("mm", "deg")


@dataclass
class Contributor:
    id: str
    nominal: float
    tol_plus: float
    tol_minus: float
    direction: int
    distribution: str = "normal"
    description: str = ""
    param: str | None = None  # optional "a.b" binding into params/params.toml (S7)

    @property
    def sym_tol(self) -> float:
        """Symmetric half-width, average of the (possibly asymmetric) plus/minus tolerances."""
        return (self.tol_plus + self.tol_minus) / 2.0

    @property
    def mean_shift(self) -> float:
        """Offset of the tolerance zone's midpoint from nominal (0 for symmetric tolerances)."""
        return (self.tol_plus - self.tol_minus) / 2.0


@dataclass
class Stack:
    name: str
    description: str
    unit: str
    contributors: list[Contributor]
    gap_min: float | None = None
    gap_max: float | None = None
    source_path: Path | None = None


def load_stack(path: Path) -> Stack:
    try:
        data = tomllib.loads(Path(path).read_text())
    except tomllib.TOMLDecodeError as exc:
        raise StackFileError(f"{path}: invalid TOML: {exc}") from exc

    stack_tbl = data.get("stack")
    if not stack_tbl or "name" not in stack_tbl:
        raise StackFileError(f"{path}: missing [stack] table or [stack].name")
    req = data.get("requirement", {})
    unit = str(req.get("unit", "mm"))
    if unit not in UNIT_VOCAB:
        raise StackFileError(
            f"{path}: [requirement].unit {unit!r} is not in the supported unit vocabulary "
            f"{list(UNIT_VOCAB)} -- geometry stacks are SI mm (CONTRACTS.md SS10); nothing here "
            "converts units, so a stack written in another unit would silently mis-check."
        )
    contribs_raw = data.get("contributor")
    if not contribs_raw:
        raise StackFileError(f"{path}: no [[contributor]] entries")

    contributors: list[Contributor] = []
    for i, c in enumerate(contribs_raw):
        for field_name in ("id", "nominal", "tol_plus", "tol_minus", "direction"):
            if field_name not in c:
                raise StackFileError(f"{path}: contributor #{i + 1} missing '{field_name}'")
        if c["direction"] not in (1, -1):
            raise StackFileError(f"{path}: contributor {c['id']!r} direction must be +1 or -1, got {c['direction']!r}")
        if c["tol_plus"] < 0 or c["tol_minus"] < 0:
            raise StackFileError(f"{path}: contributor {c['id']!r} tolerances must be >= 0")
        dist = c.get("distribution", "normal")
        if dist not in ("normal", "uniform"):
            raise StackFileError(f"{path}: contributor {c['id']!r} distribution must be 'normal' or 'uniform', got {dist!r}")
        contributors.append(Contributor(
            id=str(c["id"]), nominal=float(c["nominal"]), tol_plus=float(c["tol_plus"]),
            tol_minus=float(c["tol_minus"]), direction=int(c["direction"]), distribution=dist,
            description=str(c.get("description", "")),
            param=str(c["param"]) if c.get("param") is not None else None,
        ))

    return Stack(
        name=str(stack_tbl["name"]), description=str(stack_tbl.get("description", "")),
        unit=unit, contributors=contributors,
        gap_min=req.get("gap_min"), gap_max=req.get("gap_max"), source_path=Path(path),
    )


@dataclass
class StackResult:
    nominal_gap: float
    wc_min: float
    wc_max: float
    rss_min: float
    rss_max: float
    mc_min: float | None = None
    mc_max: float | None = None
    mc_mean: float | None = None
    mc_std: float | None = None
    mc_n: int | None = None
    mc_seed: int | None = None


def nominal_gap(stack: Stack) -> float:
    return sum(c.direction * c.nominal for c in stack.contributors)


def worst_case(stack: Stack) -> tuple[float, float]:
    """Extreme-condition (arithmetic) worst-case stack, ASME Y14.5 Rule of the stack equation.

    Each contributor's tolerance zone is walked to its extreme in the
    direction that widens (max) or narrows (min) the resultant gap,
    independent of the others -- this is the classical worst-case bound,
    not a probability statement.
    """
    nominal = nominal_gap(stack)
    plus_sum = sum(c.tol_plus if c.direction > 0 else c.tol_minus for c in stack.contributors)
    minus_sum = sum(c.tol_minus if c.direction > 0 else c.tol_plus for c in stack.contributors)
    return nominal - minus_sum, nominal + plus_sum


def rss(stack: Stack) -> tuple[float, float]:
    """Root-sum-square (statistical) stack at the same confidence band as the input tolerances.

    Each contributor's tolerance is decomposed into a symmetric half-width
    (RSS-combined in quadrature) plus a mean shift (summed linearly, since
    a systematic offset does not average out). Treats each ``tol_plus`` /
    ``tol_minus`` as a fixed-confidence half-width (e.g. all specified at
    +/-3 sigma) -- the RSS result is reported at that same band.
    """
    nominal = nominal_gap(stack)
    mean_shift = sum(c.direction * c.mean_shift for c in stack.contributors)
    combined_tol = math.sqrt(sum(c.sym_tol ** 2 for c in stack.contributors))
    center = nominal + mean_shift
    return center - combined_tol, center + combined_tol


def monte_carlo(stack: Stack, n: int = 100_000, seed: int = 12345) -> tuple[float, float, float, float]:
    """Sample each contributor independently and sum; returns (min, max, mean, std) of the resultant gap.

    ``tol`` is treated as a 3-sigma half-width for ``normal`` contributors
    (``std = sym_tol / 3``) and as the exact half-width of a uniform
    distribution for ``uniform`` contributors. Fixed seed for
    reproducibility -- rerunning with the same stack file reproduces the
    same sample statistics bit-for-bit.
    """
    rng = random.Random(seed)
    samples = [0.0] * n
    for c in stack.contributors:
        center = c.nominal + c.mean_shift
        if c.distribution == "normal":
            std = c.sym_tol / 3.0
            draws = [rng.gauss(center, std) if std > 0 else center for _ in range(n)]
        else:  # uniform
            lo, hi = c.nominal - c.tol_minus, c.nominal + c.tol_plus
            draws = [rng.uniform(lo, hi) for _ in range(n)]
        for i, d in enumerate(draws):
            samples[i] += c.direction * d
    mean = sum(samples) / n
    var = sum((s - mean) ** 2 for s in samples) / n
    return min(samples), max(samples), mean, math.sqrt(var)


def evaluate(stack: Stack, *, monte_carlo_n: int = 0, monte_carlo_seed: int = 12345) -> StackResult:
    wc_min, wc_max = worst_case(stack)
    rss_min, rss_max = rss(stack)
    result = StackResult(
        nominal_gap=nominal_gap(stack), wc_min=wc_min, wc_max=wc_max, rss_min=rss_min, rss_max=rss_max,
    )
    if monte_carlo_n > 0:
        mc_min, mc_max, mc_mean, mc_std = monte_carlo(stack, n=monte_carlo_n, seed=monte_carlo_seed)
        result.mc_min, result.mc_max, result.mc_mean, result.mc_std = mc_min, mc_max, mc_mean, mc_std
        result.mc_n, result.mc_seed = monte_carlo_n, monte_carlo_seed
    return result


@dataclass
class ParamMismatch:
    """A contributor's ``nominal`` disagrees with the params/params.toml key
    it claims to bind (``param = "a.b"``)."""
    contributor_id: str
    param_key: str
    stack_nominal: float
    params_value: float


def load_params(project: Path) -> dict[str, Any]:
    """params/params.toml as a nested dict, or ``{}`` if the project has none."""
    path = Path(project) / "params" / "params.toml"
    if not path.is_file():
        return {}
    return tomllib.loads(path.read_text())


def _param_value(params: dict[str, Any], dotted_key: str) -> float:
    node: Any = params
    for part in dotted_key.split("."):
        if not isinstance(node, dict) or part not in node:
            raise StackFileError(f"params key {dotted_key!r} not found in params/params.toml")
        node = node[part]
    if not isinstance(node, dict) or "value" not in node:
        raise StackFileError(f"params key {dotted_key!r} is not a leaf parameter table")
    return float(node["value"])


def param_mismatches(stack: Stack, params: dict[str, Any], *, tol: float = 1e-9) -> list[ParamMismatch]:
    """S7: SKILL.md says "tolerances come from params/params.toml, not
    invented numbers" -- for every contributor that names a ``param``
    binding, check its ``nominal`` actually equals that key's params.toml
    value. Raises :class:`StackFileError` (fail-closed, like every other
    malformed-spec case here) if a bound key doesn't exist or isn't a leaf
    parameter table; returns the list of (contributor, params_value)
    mismatches for the ones that exist but disagree."""
    mismatches = []
    for c in stack.contributors:
        if c.param is None:
            continue
        params_value = _param_value(params, c.param)
        if abs(c.nominal - params_value) > tol:
            mismatches.append(ParamMismatch(c.id, c.param, c.nominal, params_value))
    return mismatches
