"""Weighted Pugh matrix scoring and a weight-sensitivity check.

Pure functions, no I/O, so they're easy to unit-test and to reuse from both
``scripts/verify.py`` and ``workflows/concept-tournament.js`` (via a judge
agent that calls this module, or via the verify entrypoint on its JSON
output).

**Pugh matrix method** (datum/baseline comparison, standard engineering-design
technique -- Stuart Pugh, "Total Design", 1991; the scoring convention below
-- a signed -2..+2 scale relative to a datum, rather than the classic
+/S/- -- is a common weighted variant and is Forge's own choice, not a
verbatim reproduction of any single source):

    total(concept) = sum(weight[c] * score[concept][c] for c in criteria)

The datum itself always totals 0 by construction (every score against
itself is 0).
"""
from __future__ import annotations

from typing import Any, NamedTuple

DEFAULT_PERTURBATION = 0.25  # +/-25% relative change to one criterion's weight


class RankedConcept(NamedTuple):
    name: str
    total: float


def normalize_weights(criteria: list[dict[str, Any]]) -> dict[str, float]:
    """Return {criterion_name: weight} normalised to sum to 1.0."""
    total_w = sum(float(c["weight"]) for c in criteria)
    if total_w <= 0:
        raise ValueError("criteria weights must sum to a positive number")
    return {c["name"]: float(c["weight"]) / total_w for c in criteria}


def weighted_score(scores: dict[str, float], weights: dict[str, float]) -> float:
    return sum(weights[name] * float(scores.get(name, 0.0)) for name in weights)


def rank(concepts: list[dict[str, Any]], weights: dict[str, float], *, exclude_datum: bool = False) -> list[RankedConcept]:
    """Score and sort concepts, highest total first.

    A concept with ``"datum": true`` is the Pugh baseline (always totals 0
    by construction) -- pass ``exclude_datum=True`` to leave it out of the
    ranking used for concept *selection* (it still makes sense to show it in
    a report, just not to crown it "the winner")."""
    candidates = [c for c in concepts if not (exclude_datum and c.get("datum"))]
    ranked = [RankedConcept(c["name"], weighted_score(c.get("scores", {}), weights)) for c in candidates]
    return sorted(ranked, key=lambda r: r.total, reverse=True)


def top_n_names(ranked: list[RankedConcept], n: int = 2) -> tuple[str, ...]:
    return tuple(r.name for r in ranked[:n])


def _perturb(weights: dict[str, float], criterion: str, factor: float) -> dict[str, float]:
    """Scale ``criterion``'s weight by ``factor`` and redistribute the delta
    proportionally across the remaining criteria, keeping the total at 1.0."""
    others = [k for k in weights if k != criterion]
    new_w = dict(weights)
    old = weights[criterion]
    new = max(0.0, old * factor)
    delta = old - new
    new_w[criterion] = new
    others_total = sum(weights[k] for k in others)
    if others_total > 0:
        for k in others:
            new_w[k] = weights[k] + delta * (weights[k] / others_total)
    return new_w


def sensitivity_check(
    criteria: list[dict[str, Any]],
    concepts: list[dict[str, Any]],
    *,
    top_n: int = 2,
    perturbation: float = DEFAULT_PERTURBATION,
) -> dict[str, Any]:
    """Perturb each criterion's weight by +/-``perturbation`` (redistributing
    the rest proportionally) and check whether the top-``top_n`` concept
    *set* changes. Returns a report dict with ``stable`` and ``flips``."""
    weights = normalize_weights(criteria)
    base_ranked = rank(concepts, weights, exclude_datum=True)
    base_top = set(top_n_names(base_ranked, top_n))

    flips: list[dict[str, Any]] = []
    for c in criteria:
        name = c["name"]
        for direction, factor in (("+", 1 + perturbation), ("-", 1 - perturbation)):
            perturbed_weights = _perturb(weights, name, factor)
            perturbed_ranked = rank(concepts, perturbed_weights, exclude_datum=True)
            perturbed_top = set(top_n_names(perturbed_ranked, top_n))
            if perturbed_top != base_top:
                flips.append({
                    "criterion": name,
                    "direction": direction,
                    "base_top": sorted(base_top),
                    "perturbed_top": sorted(perturbed_top),
                })

    return {
        "stable": not flips,
        "base_ranking": [{"name": r.name, "total": round(r.total, 4)} for r in base_ranked],
        "base_top": sorted(base_top),
        "flips": flips,
        "perturbation": perturbation,
    }
