---
name: modeling-cad-parts
description: Build a mechanical part or assembly in build123d through the build123d-mcp server, one small step at a time, with a numeric spec gate before any geometry and a build-measure-snapshot loop after every risky feature. Use when someone asks to model, design, or build a CAD part, enclosure, bracket, gear, fastener or assembly, or to change an existing cad/*.py part. Do not use this for measuring/checking an already-built part against requirements (use verifying-geometry) or for DFM/process limits (use checking-dfm) -- this skill only authors geometry.
paths:
  - "cad/**"
allowed-tools: mcp__build123d-mcp__execute, mcp__build123d-mcp__measure, mcp__build123d-mcp__validate, mcp__build123d-mcp__save_snapshot, mcp__build123d-mcp__restore_snapshot, mcp__build123d-mcp__compare, mcp__build123d-mcp__inspect_part, mcp__build123d-mcp__render_view, mcp__build123d-mcp__cross_sections, mcp__build123d-mcp__find_holes, mcp__build123d-mcp__find_hole_patterns, mcp__build123d-mcp__find_bosses, mcp__build123d-mcp__find_bored_bosses, mcp__build123d-mcp__find_countersinks, mcp__build123d-mcp__recognise_features, mcp__build123d-mcp__repair_hints, mcp__build123d-mcp__repair_advice, mcp__build123d-mcp__last_error, mcp__build123d-mcp__export, mcp__build123d-mcp__session_state, mcp__build123d-mcp__reset, mcp__build123d-mcp__health_check, mcp__build123d-mcp__version, Read, Write, Edit, Glob, Bash(~/.forge/bin/forge-python ${CLAUDE_PLUGIN_ROOT}/skills/verifying-geometry/scripts/verify.py:*), AskUserQuestion
---

# Modeling CAD parts

**Non-negotiable, in order:**
1. **Spec gate before any geometry.** Extract a numeric spec (dimensions,
   tolerances, interfaces, loads, material) from the request and
   `params/params.toml`. If a number is missing or two requirements
   conflict, use `AskUserQuestion` -- never guess silently (FORGE-BRIEF §0,
   R3 implication 3). Record every assumption you did make in
   `ASSUMPTIONS.md`, not just in your head.
2. **Params only.** Every dimension comes from `params/params.toml`
   (CONTRACTS §2) via the part module's `build(params=...)` argument. Never
   write a bare number into `cad/*.py` that also appears in params -- that
   is exactly the "looks right, dimensionally wrong" failure Forge exists to
   catch (R3).
3. **Part files export `build()`.** A zero-arg or `params=`-accepting
   callable returning a build123d `Shape`, so `forge_cad.load.load_part` and
   every downstream check can load it (CONTRACTS, `verifying-geometry`).
4. **Build -> measure -> compare -> snapshot, per feature, not per part.**
   After each feature: `execute`, `measure` it against the relevant spec
   slice, and only then continue. `save_snapshot` before any boolean, fillet
   or shell -- these are exactly the operations most likely to silently fail
   or produce a degenerate result (R3 implication 4). If the post-operation
   measurement regresses against the spec, `restore_snapshot` rather than
   pushing forward broken.
5. **Bounded repair.** At most 3 execution-repair attempts per step (syntax
   /API errors -- use `last_error` and `repair_hints`/`repair_advice`), and
   at most 2-3 geometric-refinement rounds per feature without new evidence
   (a fillet that won't take, a boolean that leaves a sliver). Keep the
   best-so-far result each round. After a repeated failure, stop and either
   try a different construction strategy or escalate to the user -- do not
   loop indefinitely (ADR-001 §13 rule 8, R3 implication 5).

## Workflow

See `references/workflow.md` for the full step-by-step (spec gate
questions, the build123d-mcp tool sequence, snapshot/restore mechanics, and
worked examples). In short:

1. Spec gate: read `params/params.toml` and `requirements/requirements.md`;
   ask what's missing; write `requirements/geometry/<part>.toml` (with
   `systems-engineer`/the user) so there is something to build *against*.
2. `execute` the first feature (base sketch/extrude); `measure` bbox/volume;
   compare to spec.
3. For each subsequent feature: `save_snapshot`, `execute`, `measure`,
   compare; `restore_snapshot` on regression instead of continuing.
4. When the part is feature-complete, run `verifying-geometry`'s
   `scripts/verify.py` against the whole spec (not just the last feature) --
   this skill's own `measure` calls are a per-step sanity check, not a
   substitute for the full numeric suite.
5. Hand off to `checking-dfm` once a process is chosen, and to
   `inspecting-renders` for the visual/identity pass -- never treat a clean
   `execute`/`measure` loop alone as "done".

## What this skill refuses

- Modeling from a spec with an unresolved conflict or a missing critical
  dimension (ask first).
- Hard-coding a dimension that has (or should have) a `params/params.toml`
  entry.
- Continuing past a failed `validate` or a `measure` regression without
  either fixing it or explicitly rolling back with `restore_snapshot`.
- Calling this skill to *check* an already-modeled part's requirements --
  that is `verifying-geometry`'s job, run independently so the same skill
  that built the part is never the one that clears it (FORGE-BRIEF §0, "the
  maker is never the checker").
