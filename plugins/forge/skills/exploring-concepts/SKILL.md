---
name: exploring-concepts
description: Run a design-exploration tournament -- generate N or more concepts in parallel, score them on a weighted Pugh matrix against a datum, check the ranking's sensitivity to the weights, and produce a top-2 report. Use when the user asks "what are our options", "explore concepts for...", "compare approaches", or before a G1/PDR gate. Always ends by asking the human to choose -- it never picks a winner for them. Do NOT use for a single already-chosen design's detailed verification (see the mechanical/electrical skills) or for an architecture decision with only one real option (see writing-adrs).
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(${CLAUDE_SKILL_DIR}/scripts/verify.py:*), Bash(forge-python ${CLAUDE_SKILL_DIR}/scripts/verify.py:*), Workflow(forge:concept-tournament)
---

# Exploring concepts

**Non-negotiable rules, read first:**
1. Generate **at least the minimum concept count** (default 3, configurable) before scoring anything — a Pugh matrix over two concepts (one of them the datum) isn't an exploration.
2. Score every concept against **every** criterion, relative to a stated **datum** (baseline). A concept with an incomplete score row is not comparable and the check fails.
3. Run the **sensitivity check** before trusting the ranking. If the top-N flips under a +/-25% change to any one criterion's weight, that is a close call, not noise — a human must look at it (`sensitivity_reviewed_by`) before the ranking is used to decide anything.
4. **This skill never picks the winner.** It produces a ranked report and a sensitivity finding; the human (or, in a workflow context, the owner via `AskUserQuestion`) makes the call. Do not phrase a report as "we should build concept A" — phrase it as "concept A ranks first; here is how sensitive that is."

## `concepts/pugh.json` format

```json
{
  "schema": "forge.pugh/1",
  "minimum_concepts": 3,
  "top_n": 2,
  "sensitivity_reviewed_by": "",
  "criteria": [
    {"name": "cost", "weight": 0.30},
    {"name": "manufacturability", "weight": 0.40},
    {"name": "ergonomics", "weight": 0.30}
  ],
  "concepts": [
    {"name": "datum-current-gen", "datum": true, "scores": {"cost": 0, "manufacturability": 0, "ergonomics": 0}},
    {"name": "concept-A-folded-sheet-metal", "scores": {"cost": 1, "manufacturability": -1, "ergonomics": 2}},
    {"name": "concept-B-injection-molded", "scores": {"cost": -1, "manufacturability": 2, "ergonomics": 0}},
    {"name": "concept-C-extruded", "scores": {"cost": 2, "manufacturability": 1, "ergonomics": -2}}
  ]
}
```

- Scores are **relative to the datum**, on a -2..+2 scale (much worse .. much better). The datum always scores 0 by construction and is excluded from the ranking used to pick a winner (it still appears in the report for context).
- `sensitivity_reviewed_by`: leave empty until a human has looked at an unstable ranking; then record who reviewed it.

## Workflow

1. **Generate concepts.** For real parallel generation with judges blind to authorship, invoke the `forge:concept-tournament` workflow (`plugins/forge/workflows/concept-tournament.js`) rather than writing concepts serially yourself — it fans out independent agents, scores with independent judges, and reconciles into the same `pugh.json` shape.
2. Agree the criteria and weights with the stakeholder/owner *before* scoring (weights baked in after seeing the scores is how a matrix gets gamed).
3. Score every concept, including the datum.
4. Run:
   ```
   forge-python ${CLAUDE_SKILL_DIR}/scripts/verify.py --project <root>
   ```
   It writes `out/verify/concepts.pugh_report.json` (full ranking + sensitivity detail) and fails if the concept count is short, a score row is incomplete, or the ranking is sensitivity-flagged and unreviewed.
5. If the ranking is stable (or reviewed), present the top-2 to the human/owner and **ask them to choose** — this skill's job ends here.

## What this skill refuses

- Auto-selecting a concept and presenting it as decided. Every report ends with a question, not a decision.
- Padding the concept count with trivial variations to hit the minimum. Each concept should reflect a genuinely different approach (different process, architecture or trade-off), not a color swap.
- Re-weighting criteria after scoring to make a preferred concept win. If the ranking surprises you, that's information — investigate the criteria, don't retune them to match a preconception.

See `references/pugh-matrix-guide.md` for the scoring method, the sensitivity-check math, and a worked example with a flipped ranking.
