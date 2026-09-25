# Weighted Pugh matrix and sensitivity check

## Scoring

Each concept is scored against a **datum** (baseline) on every criterion, on
a -2..+2 scale:

| Score | Meaning |
|---|---|
| +2 | much better than the datum |
| +1 | better than the datum |
| 0 | same as the datum |
| -1 | worse than the datum |
| -2 | much worse than the datum |

Weighted total for a concept:

```
total = sum(normalized_weight[criterion] * score[concept][criterion] for criterion in criteria)
```

Weights are normalised to sum to 1 before scoring (`pugh.normalize_weights`), so the absolute numbers you enter (e.g. 30/40/30 or 3/4/3) don't need to sum to any particular total.

## Sensitivity check

A ranking that only holds because the weights happen to be exactly 30/40/30
is fragile — small, defensible disagreements about weighting ("is
manufacturability really worth more than cost here?") could flip the
decision. `pugh.sensitivity_check`:

1. For each criterion, perturb its weight by **+25%** and **-25%**,
   redistributing the difference proportionally across the other criteria
   (so weights still sum to 1).
2. Re-rank concepts under each perturbed weight set.
3. Compare the **top-N set** (default top 2) before and after. If it
   changes for *any* single perturbation, the ranking is flagged unstable.

This is deliberately a strict test — even one criterion moving 25% and
changing who's in the top 2 is enough to flag it. That's intentional: a
ranking a stakeholder trusts should survive a fairly loose disagreement
about the weights.

## Worked example: a fragile ranking

```json
{
  "criteria": [{"name": "cost", "weight": 0.34}, {"name": "mfg", "weight": 0.33}, {"name": "ergo", "weight": 0.33}],
  "concepts": [
    {"name": "datum", "datum": true, "scores": {"cost": 0, "mfg": 0, "ergo": 0}},
    {"name": "A", "scores": {"cost": 2, "mfg": 0, "ergo": -1}},
    {"name": "D", "scores": {"cost": -1, "mfg": 2, "ergo": 0}},
    {"name": "C", "scores": {"cost": -2, "mfg": -2, "ergo": -2}}
  ],
  "top_n": 1
}
```

At equal weights, A totals `0.34*2 + 0.33*0 + 0.33*-1 = 0.35`, D totals
`0.34*-1 + 0.33*2 + 0.33*0 = 0.32` — A wins, barely. Drop `cost`'s weight by
25% (redistributing to mfg/ergo) and D's `mfg` score of +2 pulls ahead. The
sensitivity check catches this and fails until a human sets
`sensitivity_reviewed_by`, or the team adds a criterion that discriminates
between A and D more clearly.

## Worked example: a robust ranking

```json
{
  "criteria": [{"name": "cost", "weight": 0.34}, {"name": "mfg", "weight": 0.33}, {"name": "ergo", "weight": 0.33}],
  "concepts": [
    {"name": "datum", "datum": true, "scores": {"cost": 0, "mfg": 0, "ergo": 0}},
    {"name": "A", "scores": {"cost": 1, "mfg": 1, "ergo": 1}},
    {"name": "B", "scores": {"cost": -1, "mfg": 0, "ergo": 0}},
    {"name": "C", "scores": {"cost": 0, "mfg": -1, "ergo": -1}}
  ]
}
```

A beats every other concept on every single criterion (a "dominant"
concept) — no weight perturbation can change that, so this ranking passes
without review.
