---
paths:
  - "cad/**"
---

# Mechanical (CAD)

- Only the `mechanical-engineer` agent writes `cad/`. Enforced by a PreToolUse hook keyed on `agent_type`.
- CAD is code: build123d, stepwise, parametric. Never write a whole part blind -- model a feature, measure it, snapshot before risky boolean/fillet operations.
- Every dimension comes from `params/params.toml`. Never hard-code a value that belongs there.
- Every geometric requirement gets a numeric check before a render is trusted. Renders are a second layer, never the only one.
- Before a boolean or fillet operation that could fail, save a snapshot so a repair loop can roll back instead of restarting.
- Run `forge-python skills/verifying-geometry/scripts/verify.py --project . --changed cad/ --fast` after any change (also runs automatically via the PostToolUse `cad/` hook: rebuild, validity check, params lint).
- DFM rules are process-specific (FDM, SLA, SLS, MJF, CNC, injection molding, sheet metal) -- see `docs/standards/mechanical.md` and `checking-dfm`. Cite the rule, never invent a number.
- Tolerance stacks use worst-case and RSS, with GD&T intent per ASME Y14.5 -- see `docs/standards/mechanical.md`.
- Claim mass/volume/bbox only from `out/<part>/metrics.json`, never from a screenshot.
