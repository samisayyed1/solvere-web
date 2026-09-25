---
name: checking-dfm
description: Apply process-specific design-for-manufacturability rules (FDM/SLA/SLS/MJF 3D printing, injection molding, CNC machining, sheet metal, and snap-fit strain) to a build123d part's forge_cad measurements, with every numeric rule sourced from docs/research/R5c/R5d. Use after verifying-geometry passes and a manufacturing process has been chosen, or whenever someone asks "will this print/mold/machine/bend", "is this wall thick enough for FDM/injection molding", "check draft for molding", "will this snap-fit break", or before a manufacturing-engineer handoff or a gate review. Do not use this for base geometric validity/dimensions (use verifying-geometry first) or for cost/tooling estimation (that is manufacturing-engineer's job, not a numeric check).
paths:
  - "cad/**"
  - "requirements/dfm/**"
allowed-tools: Read, Glob, Bash(~/.forge/bin/forge-python ${CLAUDE_SKILL_DIR}/scripts/verify.py:*), Bash(${CLAUDE_SKILL_DIR}/scripts/verify.py:*)
---

# Checking DFM

**Non-negotiable:** every rule number in `references/rules/*.toml` cites its
row in `docs/research/R5c-dfm-molding-cnc-sheetmetal.md` or
`R5d-dfm-additive-snapfit-pcb.md`. Never add or change a rule value without a
source line from those two files; never invent a number "from experience".
Where the sources disagreed, the table already picked the conservative
value and recorded the discarded one in `conflict` -- read it, don't
silently override it. A rule with `check_family = "unsupported"` has no
matching `forge_cad` measurement; referencing it in a spec is a hard error,
not something this skill fakes a check for.

## What this does

Reads every `requirements/dfm/<part>.toml` spec (schema:
`references/spec-schema.md`), applies the named process's rule table to that
part's `forge_cad` measurements (reusing the same measurement functions as
`verifying-geometry` -- see its `references/algorithms.md` for the
resolution limits, which apply here identically), and evaluates any
`[[snap_fit]]` entries with the root-strain formula from R5d
(`scripts/strain.py`) against per-material allowable strain
(`references/rules/snap_fit.toml`). Writes one `out/verify/dfm.<rule>.<part>.json`
or `out/verify/dfm.snap_fit.<name>.<part>.json` per check through
`forge.checkresult` (CONTRACTS §3).

## When to run it

- After `verifying-geometry` passes and a manufacturing process is chosen
  (`process = "..."` in the spec) -- DFM limits assume the base geometry is
  already valid and dimensionally correct; this skill does not re-check
  that.
- Before a `manufacturing-engineer` process-selection/costing pass.
- Before any gate review touching `cad/**` or `mfg/**`.

## How to run it

```
~/.forge/bin/forge-python plugins/forge/skills/checking-dfm/scripts/verify.py \
    --project <product-repo-root> [--changed cad/lid.py ...] [--fast]
```

Same exit-code and `--changed`/`--fast`/`[SKIP]` contract as
`verifying-geometry` (0/1/2; no `requirements/dfm/*.toml` prints `[SKIP]` and
exits 0).

## Picking a process

`[part].process` selects `references/rules/<process>.toml`:
`fdm`, `sla`, `sls`, `mjf`, `injection_molding`, `cnc`, `sheet_metal`.
Snap-fit strain (`[[snap_fit]]`) is independent of `process` and always
checked against `references/rules/snap_fit.toml`'s per-material allowable
strain -- pick the `material` id closest to the actual resin; if none
matches, say so and ask rather than guessing a similar-sounding material
(strain limits vary 2-10x between nominally similar plastics, R5d).

## Reading a failure

Every failing measurement's `remediation` names the rule id, the measured
vs. required value, and the fix. Cross-reference the rule's own `source` and
`conflict` fields (`references/rules/<process>.toml`) before pushing back on
a result -- a near-limit fail against the conservative figure may still be
fine against the discarded, less-conservative one, but that is an explicit
engineering judgement call to record (e.g. in `ASSUMPTIONS.md`), not
something to silently wave through.

## Snap-fit strain

`scripts/strain.py`'s `root_strain()` implements Covestro's cantilever
formula (R5d): `eps = h*y/(k*L^2)`, reported as `root_strain_pct` in **%**
(the material allowables in `references/rules/snap_fit.toml` are also
percent). It does **not** include BASF's short-arm
correction; `verify.py` adds a note (not a failure) whenever `length/thickness
< 10`, per R5d's caution that the plain formula under-predicts root strain
for short arms. Treat a passing result flagged this way with suspicion and
consider lengthening the arm or getting an FEA check (`running-fea`) instead
of trusting the hand formula alone.

## Unsupported rules

Several real DFM numbers (bend relief, K-factor, thread/pocket depth ratios,
tolerance bands, ...) have no `forge_cad` measurement yet -- their rule
entries are `check_family = "unsupported"` and exist only as sourced
reference data. If a requirement needs one of these, check it by hand
(caliper/drawing measurement) and record the finding directly rather than
adding it to a spec -- `verify.py` will refuse to run it.
