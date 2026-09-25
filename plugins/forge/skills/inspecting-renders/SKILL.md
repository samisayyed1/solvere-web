---
name: inspecting-renders
description: Question-first render inspection (CADCodeVerify-style, docs/research/R3 §1) -- write 10-20 yes/no validation questions from the requirements BEFORE rendering, render standard/section/exploded views with PyVista offscreen, then answer every question citing a render file and, where dimensional, a numeric check. Use when the user asks to "check the renders", "inspect the model visually", "does this look right", or when analysis/renders/*.toml changes. Also fires from the mechanical.md path rule on analysis/**. Do NOT use for the engineering/marketing render pack itself (see rendering-products) or as a substitute for a numeric geometry check (see verifying-geometry, stacking-tolerances) -- renders are a second layer, never the only evidence.
paths:
  - "analysis/renders/**"
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(${CLAUDE_SKILL_DIR}/scripts/render.py:*), Bash(${CLAUDE_SKILL_DIR}/scripts/verify.py:*), Bash(forge-python ${CLAUDE_SKILL_DIR}/scripts/render.py:*), Bash(forge-python ${CLAUDE_SKILL_DIR}/scripts/verify.py:*)
---

# Inspecting renders

**Non-negotiable rules, read first:**
1. **Write the questions before you render anything.** `analysis/renders/<part>-questions.toml` must exist with 10-20 yes/no questions derived from the requirements before `render.py` will produce a single image. This is CADCodeVerify's finding turned into a hard gate (docs/research/R3: "use questions as a checklist generator, not as a judge" -- and the checklist has to predate the evidence it will be checked against, or it silently becomes a judge that rationalizes whatever the render shows).
2. `render.py` refuses (exit 2, no images written) without a valid questions file. `verify.py` does the same, and this is the seeded-wrong case this skill is built to catch: rendering, or claiming to have inspected renders, with no prior questions file must never pass.
3. Every answer cites an `evidence_file` that actually exists, and a `numeric_check` id when the question is dimensional. **Renders are never dimensional acceptance** (docs/brief/FORGE-BRIEF.md §0) -- a "yes" to "is the wall thick enough" needs a `numeric_check` pointing at a real `out/verify/geometry.min_wall.json`, not just a picture that looks fine.
4. Every answer set ends with a `[deviations]` section, even when nothing was found -- "no deviations" is a claim that must be written down, not implied by silence. **Every `answer = "no"` also needs its own `deviation_note`** (>= 10 characters, on that `[[answer]]` block) -- a "no" answer *is* a deviation, and `verify.py` FAILs it if the note is missing or the global `[deviations]` section just says "none found" while an answer is "no".
5. `verify.py` checks structure (views present and non-blank, every question answered yes/no, evidence exists, deviations recorded) -- it cannot judge whether an answer is *correct*. That judgement is the point of doing the inspection; `verify.py` only catches an inspection that was skipped, faked, or left incomplete.

## Workflow

1. Read the part's requirements. Write `analysis/renders/<part>-questions.toml`, naming the **real geometry to render** in `[part]` -- `render.py` never renders placeholder/demo geometry in place of the part being inspected:
   ```toml
   [part]
   module = "cad/enclosure_base.py"   # or: step = "cad/out/enclosure_base.step"
   # mate_module = "cad/lid.py"       # optional: a second body for a meaningful exploded view

   [[question]]
   id = "q1"
   text = "Does the lid seat flush against the housing with no visible gap in the front view?"
   [[question]]
   id = "q2"
   text = "Is exactly one USB-C cutout visible on the right-side view?"
   # ... 8-18 more
   ```
2. Render:
   ```
   forge-python ${CLAUDE_SKILL_DIR}/scripts/render.py --project <root> --part <name>
   ```
   Loads `[part]`'s geometry with `forge_cad.load` (the same loader `verifying-geometry`/`checking-dfm` use) and writes `out/renders/<part>/{front,top,right,iso,section,exploded}.png`, plus, if it doesn't already exist, a blank `analysis/renders/<part>-answers.toml` template (never overwritten once it exists, so in-progress answers are safe to re-run render.py over).
3. Fill in the answers template: `answer = "yes"|"no"`, `evidence_file` pointing at a render (or a different existing file if the answer needs something render.py didn't produce), `numeric_check` for anything dimensional, `deviation_note` (required, >= 10 chars, whenever `answer = "no"`), and the `[deviations]` section.
4. Verify:
   ```
   forge-python ${CLAUDE_SKILL_DIR}/scripts/verify.py --project <root> [--changed analysis/renders/<part>-answers.toml]
   ```
   Writes `out/verify/mech.render_inspection_<part>.json` with measurements `required_views_present`, `views_non_blank`, and (once an answers file exists) `questions_answered`, `answers_have_yes_no`, `answers_cite_existing_evidence`.

## What this skill refuses

- Rendering, or scoring an inspection, with no questions file, too few (< 10) or too many (> 20) questions -- exit 2 in both `render.py` and `verify.py`.
- Rendering without a `[part]` table naming real geometry (`module` or `step`) -- `render.py` refuses rather than falling back to placeholder/demo geometry that has nothing to do with the part being inspected.
- An answers file missing a `[deviations]` section, or any `answer = "no"` with no (or a too-short) `deviation_note`.
- Calling an inspection "done" because the images "look fine" -- every question needs a definite yes/no plus a citation, and `verify.py` fails (not merely warns) if any answer is blank or its evidence file doesn't exist.
- Standing in for a numeric geometry check. A render can show that a wall is *obviously* too thin, but only `verifying-geometry`'s `geometry.min_wall` check is evidence that it passes.
