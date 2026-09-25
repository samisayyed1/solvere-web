---
name: verifying-geometry
description: Run Forge's scripted numeric geometry check suite (solid validity, watertight export, bounding box/volume/mass, min wall thickness, clearance/interference, draft angle, min fillet radius, hole-to-edge distance, boss/rib ratio) against a build123d part or assembly and record pass/fail evidence with remediation. Use after modeling-cad-parts changes cad/**, before checking-dfm or a gate review, or whenever someone asks "does this part meet its geometric requirements" / "measure this part" / "is the wall thick enough" / "check clearance/interference". Do not use this for visual/aesthetic review (use inspecting-renders) or for process-specific DFM limits (use checking-dfm) -- this skill only checks requirements/geometry/*.toml against forge_cad measurements, nothing about manufacturability.
paths:
  - "cad/**"
  - "requirements/geometry/**"
allowed-tools: Read, Glob, Bash(~/.forge/bin/forge-python ${CLAUDE_SKILL_DIR}/scripts/verify.py:*), Bash(${CLAUDE_SKILL_DIR}/scripts/verify.py:*)
---

# Verifying geometry

**Non-negotiable:** a check with no spec entry is not "assumed fine" -- it is
unchecked. Never report a part as verified beyond what
`requirements/geometry/<part>.toml` actually lists. Never hand-edit an
`out/verify/*.json` result file; only `scripts/verify.py` writes them.
Numbers beat pictures (FORGE-BRIEF §0) -- this skill's output is the
dimensional truth; `inspecting-renders` is a second, separate layer, never a
substitute.

## What this does

Reads every `requirements/geometry/<part>.toml` spec (schema:
`references/spec-schema.md`), loads that part's current build123d geometry
(never a stale STEP or a cached mental model), runs the listed check
families through `forge_cad.measure` (algorithms and their resolution
limits: `references/algorithms.md`), and writes one
`out/verify/<check_id>.<part>.json` per check through `forge.checkresult`
(CONTRACTS §3) -- each failing measurement carries the rule, the measured
vs. required value with units, and how to fix it.

## When to run it

- After `modeling-cad-parts` finishes a feature or a whole part (its
  build-measure-snapshot loop calls this after every risky step, not just at
  the end).
- Before `checking-dfm` -- DFM rules assume the base geometry is already
  valid, watertight and dimensionally in spec; garbage in, garbage out.
- Before any gate review (`reviewing-designs`) touching `cad/**`.
- As the PostToolUse hook's `cad/**` entrypoint, with `--fast --changed <path>`.

## How to run it

```
~/.forge/bin/forge-python plugins/forge/skills/verifying-geometry/scripts/verify.py \
    --project <product-repo-root> [--changed cad/enclosure_base.py ...] [--fast]
```

Exit code: 0 all checks in all specs passed, 1 something failed, 2 an
internal error (missing spec field, module doesn't build, tool missing --
never a silent pass). No `requirements/geometry/*.toml` in the project (or
no `[[check]]` entries in a spec) prints `[SKIP] <reason>` and exits 0 -- it
never fakes a pass on an empty suite.

## If there is no spec yet

Do not invent one silently. A geometry spec's numeric limits must come from
`requirements/requirements.md` (via `requirement = "REQ-..."`) and
`params/params.toml` -- writing a spec is a `systems-engineer`/
`mechanical-engineer` decision, not something this skill improvises. If a
part has no spec, say so and ask which requirements it should be checked
against before creating `requirements/geometry/<part>.toml`.

## Reading a failure

Every failing measurement's `remediation` string names the rule, the
measured vs. required value with units, and the fix -- read it before
re-running. A `geometry.min_wall`/`geometry.boss_rib` failure/pass close to
the limit should be re-run with a higher `sample_count`
(`references/algorithms.md`): it is a Monte Carlo estimate, not exhaustive.
A `geometry.watertight` failure with `geometry.validity` passing is often a
tessellation-resolution artifact, not a real gap -- tighten `tolerance_mm`
and re-check before treating it as a design defect.

## Face indices

`geometry.draft`, `geometry.min_radius` (implicitly, via its own face scan),
`geometry.hole_edge` and `geometry.boss_rib` reference faces by their
position in `shape.faces()`, which is stable for one loaded part but not a
persistent ID across a redesign. When a spec's face-index checks start
failing after unrelated changes, re-derive the indices (build123d-mcp
`inspect_part`, or a short `forge-python` snippet) rather than guessing.
