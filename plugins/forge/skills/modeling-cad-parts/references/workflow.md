# modeling-cad-parts: step-by-step

## 1. Spec gate

Before calling any `build123d-mcp` tool:
- Read `params/params.toml` and `requirements/requirements.md`. List every
  `REQ-MECH-*` the part must satisfy.
- For each requirement, check it has a concrete number with a unit and a
  tolerance. If not, `AskUserQuestion` -- e.g. "the brief says 'fits in a
  pocket' with no dimension; what's the pocket size and required
  clearance?".
- Write (or update, with `systems-engineer`/the user)
  `requirements/geometry/<part>.toml` (schema:
  `verifying-geometry/references/spec-schema.md`) so the numeric target
  exists as a file, not just as conversation context that will be lost at
  compaction.
- Record every assumption in `ASSUMPTIONS.md` with a retirement condition
  ("assumed wall 2.0 mm pending datasheet; retire at EVT measurement").

## 2. First feature

- `execute` the base sketch/extrude (the outer envelope, usually).
- `measure` bounding box and volume.
- Compare against the spec slice for overall envelope
  (`requirements/geometry/<part>.toml`'s `geometry.bbox`/`geometry.volume`
  entries) by eye at this stage -- the full automated check comes later,
  but do not build ten more features on top of a wrong envelope.

## 3. Every subsequent feature

```
save_snapshot                      # before ANY boolean, fillet or shell
execute <feature>
measure <relevant quantity>
compare  vs. the spec slice / vs. the pre-feature snapshot
```

If the measurement regressed (wall got thinner than intended, volume jumped
unexpectedly, `validate` now fails) call `restore_snapshot` and try a
different construction order or parameter before re-attempting -- never
"fix it in the next feature" while leaving a known-bad state in place.

Use `find_holes` / `find_hole_patterns` / `find_bosses` / `find_bored_bosses`
/ `find_countersinks` / `recognise_features` after adding those features to
confirm the tool sees what you intended (these are also what
`verifying-geometry`'s `forge_cad.measure.find_holes` heuristic assumes is
present).

## 4. Repair budget

- **Execution errors** (build123d API mistakes, syntax): up to 3 attempts.
  Use `last_error` and `repair_hints`/`repair_advice` between attempts
  instead of guessing again blind.
- **Geometric refinement** (a fillet that won't take at the requested
  radius, a boolean leaving a sliver face, `validate` failing after a
  feature): up to 2-3 rounds. Keep the best-so-far snapshot each round
  (`save_snapshot` before trying a variant, `restore_snapshot` to the best
  one if the next attempt is worse, not just different).
- After exhausting the budget: stop. Either propose a different
  construction strategy (e.g. loft instead of a swept fillet) to the user,
  or escalate. Looping past the budget without new evidence is exactly the
  failure mode Forge's repair-budget rule exists to prevent (R3).

## 5. Handoff

- Feature-complete -> run `verifying-geometry/scripts/verify.py` against the
  full spec (not just this session's per-feature `measure` calls).
- Process chosen -> `checking-dfm/scripts/verify.py`.
- Visual/identity review -> `inspecting-renders` (separate from and never a
  substitute for the numeric checks above).
- `export` STEP once the above are green, for the evidence manifest and any
  mating-part work.

## Worked example (enclosure base, single-body)

```
1. AskUserQuestion: confirm outer envelope 40x30x20 mm (params: enclosure.length/width/height),
   wall 2.0 mm (params: enclosure.wall_thickness), material ABS (params: material.density_kg_m3).
2. execute: Box(length, width, height) from params.
   measure: bbox -> compare to 40x30x20 +-0.1 mm.
3. save_snapshot
   execute: hollow(faces=[top], thickness=wall_thickness)
   measure: min_wall via a quick forge_cad sanity check (or build123d-mcp's own wall-thickness tool if exposed)
   compare: ~2.0 mm -> ok, keep. If not, restore_snapshot and adjust the hollow call.
4. save_snapshot
   execute: 4x mounting-boss + hole features
   measure: hole positions/diameters
   compare vs. the PCB hole pattern spec
5. verifying-geometry: full requirements/geometry/enclosure_base.toml -> PASS
6. checking-dfm (process = "fdm"): wall/hole/draft rules -> PASS
7. export STEP -> evidence manifest entry
```
