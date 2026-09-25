---
name: stacking-tolerances
description: Compute worst-case and RSS (root-sum-square) tolerance stacks for a chain of dimensioned contributors, check the resultant gap against a requirement, and write GD&T intent notes per ASME Y14.5. Use when the user asks for a "tolerance stack", "stack-up", "worst-case analysis", "RSS tolerance", "will this gap close", "clearance analysis", or when analysis/stacks/*.toml changes. Also fires from the mechanical.md path rule on analysis/**. Do NOT use for CAD geometry checks (min wall, clearance in an assembly -- see verifying-geometry) or for per-process DFM rules (see checking-dfm).
paths:
  - "analysis/stacks/**"
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(${CLAUDE_SKILL_DIR}/scripts/verify.py:*), Bash(forge-python ${CLAUDE_SKILL_DIR}/scripts/verify.py:*)
---

# Stacking tolerances

**Non-negotiable rules, read first:**
1. Every stack lives at `analysis/stacks/<name>.toml` with a `[requirement]` table (`gap_min`, `gap_max`, `unit`) and at least one `[[contributor]]`. A stack file without a requirement cannot be checked and `verify.py` refuses it with `[ERROR]`, never a silent pass.
2. Every contributor states a `nominal`, `tol_plus`, `tol_minus` (both >= 0; use `tol_plus = tol_minus` for a symmetric tolerance) and a `direction` (`+1`/`-1`, its sensitivity sign in the stack loop). Tolerances come from `params/params.toml`, not invented numbers.
3. Both **worst-case** (extreme-condition, arithmetic) and **RSS** (statistical, root-sum-square) results are always computed and checked against the requirement. Worst-case failing is the design being wrong; RSS failing (while worst-case passes) is a process-capability risk worth flagging even though it is not an automatic block.
4. Run `scripts/verify.py` after every edit and fix every finding using its `remediation` string before calling a stack done.
5. Every geometric requirement gets a numeric check. A stack is not "probably fine" -- it is either inside the requirement or it is not.

## File format

`analysis/stacks/<name>.toml`:

```toml
[stack]
name = "lid_gap"
description = "gap between lid lip and housing shoulder, closed state"

[requirement]
unit = "mm"
gap_min = 0.20   # must stay open (no interference)
gap_max = 1.20   # must not be so loose the lid rattles

[[contributor]]
id = "A"
description = "housing depth (params.enclosure.housing_depth)"
nominal = 10.00
tol_plus = 0.05
tol_minus = 0.05
direction = 1          # +1: increasing A opens the gap
distribution = "normal"  # normal | uniform (uniform for e.g. as-machined stock tolerance)

[[contributor]]
id = "B"
description = "lid lip height (params.enclosure.lip_height)"
nominal = 7.00
tol_plus = 0.03
tol_minus = 0.03
direction = -1          # -1: increasing B closes the gap
distribution = "normal"

# optional: Monte Carlo cross-check at a fixed seed (reproducible, not required for a pass)
[monte_carlo]
n = 50000
seed = 12345
```

`direction` is the loop-diagram sensitivity: does increasing this dimension widen (+1) or narrow (-1) the resultant gap? Get this from the assembly loop diagram, not by guessing from the sign of the nominal.

## Running

```
forge-python ${CLAUDE_SKILL_DIR}/scripts/verify.py --project <root> [--changed analysis/stacks/lid_gap.toml] [--fast]
```

Writes `out/verify/mech.stack_<name>.json` (schema `forge.check/1`, CONTRACTS.md §3) with measurements `nominal_gap`, `worst_case_min/max`, `rss_min/max`, and `monte_carlo_min/max` when `[monte_carlo]` is present. No `analysis/stacks/*.toml` files means `[SKIP]` and exit 0 -- it never fakes a pass.

## Math (see `scripts/stack_math.py` for the reference implementation)

- **Nominal gap:** `sum(direction_i * nominal_i)`.
- **Worst case (extreme condition):** each contributor is walked independently to the tolerance-zone extreme that widens or narrows the gap: `nominal +/- sum(tol_i)` (accounting for `direction`). This is a bound, not a probability -- it is the gap if every part in the chain lands at its worst allowed dimension simultaneously.
- **RSS (statistical):** each contributor's tolerance is split into a symmetric half-width (combined in quadrature, `sqrt(sum(tol_i^2))`) plus a mean shift for any asymmetric tolerance (summed linearly, since a systematic offset does not average out). RSS assumes independent, roughly centred, roughly normal contributor distributions at the *same confidence band* the input tolerances were written at (commonly +/-3 sigma) -- state that assumption in the stack's `description` when it matters.
- **Monte Carlo (optional):** samples each contributor from its declared `distribution` (`normal`: tolerance treated as a 3-sigma half-width; `uniform`: exact bounds) at a fixed seed, sums per-draw, and reports the sampled min/max. Useful as an independent cross-check of the RSS closed-form result and for non-normal or heavily asymmetric chains where the closed-form RSS assumption is shaky. Not required for a pass; opt in via `[monte_carlo]`.

## GD&T intent (ASME Y14.5-2018 (R2024))

This skill computes the *linear* 1-D stack. It does not replace a feature-control-frame analysis for true position, profile or orientation tolerances stacked through a datum reference frame -- see `references/gdt-intent.md` for how to translate a 1-D loop diagram into GD&T callouts, when a stack needs bonus tolerance (MMC/LMC) accounted for, and citation conventions (cite the standard by edition, never quote its text).

## What this skill refuses

- Computing a stack with no requirement (`gap_min`/`gap_max`) -- there is nothing to check it against.
- Treating an RSS pass as a worst-case pass, or vice versa. Both are reported; neither substitutes for the other.
- Marking a stack "validated" -- a computed stack is L1 evidence (CONTRACTS §4). "Validated" needs L4 (physical measurement).
