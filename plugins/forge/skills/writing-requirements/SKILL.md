---
name: writing-requirements
description: Write and lint product/system requirements in EARS (Easy Approach to Requirements Syntax) with IDs, rationale and a verification method. Use when the user needs requirements written, reviewed, tightened, or asks "write requirements for...", "turn this brief into requirements", "is this requirement testable", or when requirements/requirements.md needs a lint pass. Also fires from the systems.md path rule on requirements/**. Do NOT use for turning a fuzzy idea into a SPEC (see interviewing-stakeholders) or for the SysML structural model (see modeling-systems).
paths:
  - "requirements/**"
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(${CLAUDE_SKILL_DIR}/scripts/verify.py:*), Bash(forge-python ${CLAUDE_SKILL_DIR}/scripts/verify.py:*)
---

# Writing requirements

**Non-negotiable rules, read first:**
1. Every requirement is ONE EARS sentence, has an ID `REQ-<AREA>-<NNN>` (area = uppercase letters, e.g. MECH/ELEC/FW/SW/SYS/SIM/MFG/COMPLY; NNN >= 3 digits), a `Rationale:` line and a `Verify:` line (`inspection`, `analysis`, `demo` or `test`).
2. Never invent a requirement id someone else already owns. IDs and requirement text belong to systems-engineer and humans (CONTRACTS §6) — other agents may only change `status`, `evidence` and `tests` in `trace.json`, never here.
3. A number with no unit, or a vague word ("fast", "user-friendly", "approximately", "etc.", "and/or", "robust", "intuitive", ...) is not a requirement — it is a wish. Rewrite it as a measurable, falsifiable criterion.
4. Run `scripts/verify.py` after every edit to `requirements/requirements.md` and fix every finding before calling the requirement set done. Do not hand-wave a lint failure.

## File format

`requirements/requirements.md`, one block per requirement:

```markdown
## REQ-MECH-004

When the enclosure lid is closed, the enclosure shall maintain a minimum
wall thickness of 2.0 mm at the lid lip.

Rationale: FDM minimum wall per R5d DFM rules; extra margin for stiffness
under the 1.2 m drop-test load case.
Verify: analysis
```

The heading line is the ID alone (`## REQ-<AREA>-<NNN>`). The sentence follows on the next non-blank line(s), then `Rationale:` and `Verify:`, in that order. Blank line, then the next requirement.

## The six EARS patterns (Mavin et al., RE'09 — see `docs/research/R5b-standards-safety-risk-se.md`)

Pick exactly one pattern per requirement. Examples below are original, for a fictional battery-powered leak-detector puck called "DripGuard":

| Pattern | Shape | Example |
|---|---|---|
| Ubiquitous | `The <system> shall <response>.` | The DripGuard puck shall log every measurement with a UTC timestamp. |
| Event-driven | `When <trigger>, the <system> shall <response>.` | When the acoustic sensor detects a leak signature, the DripGuard puck shall sound its 85 dB alarm within 3 s. |
| State-driven | `While <state>, the <system> shall <response>.` | While the battery charge is below 15 %, the DripGuard puck shall disable the Wi-Fi radio. |
| Unwanted behaviour | `If <trigger>, then the <system> shall <response>.` | If the internal temperature exceeds 60 °C, then the DripGuard puck shall enter thermal shutdown and log a fault code. |
| Optional feature | `Where <feature is fitted>, the <system> shall <response>.` | Where the cellular module is fitted, the DripGuard puck shall send an alert SMS within 30 s of alarm. |
| Complex | Combine keywords. | While in pairing mode, when the pairing button is pressed for 3 s, the DripGuard puck shall broadcast a BLE advertisement for 60 s. |

Every requirement ends in exactly one `shall`. A requirement with zero or two+ `shall` clauses is not one requirement — split it.

## Verification methods

- `inspection` — visual check or measurement against a spec sheet, no test rig.
- `analysis` — calculation, simulation or model-based argument (hand-calc, FEA, tolerance stack, ...).
- `demo` — an end-to-end demonstration of the behaviour, not an instrumented test.
- `test` — an instrumented, repeatable test with a pass/fail acceptance criterion.

Prefer `test` wherever a measurement is practical; `demo` and `inspection` are weaker evidence and should not carry safety-relevant requirements alone.

## Workflow

1. Read the brief / SPEC.md / stakeholder interview notes.
2. Draft one EARS sentence per discrete, atomic need. When a need has multiple facets (e.g. "fast AND safe"), split into separate requirements — never join with "and/or".
3. Assign the next unused ID in that area (`grep -o 'REQ-MECH-[0-9]*' requirements/requirements.md | sort -V | tail -1`).
4. Write Rationale (why this exists — traces to a stakeholder need or a standard) and Verify.
5. Run:
   ```
   forge-python ${CLAUDE_SKILL_DIR}/scripts/verify.py --project <root>
   ```
   (or plain `python3` if `forge-python` isn't on PATH — the lint is stdlib-only).
6. Fix every failing measurement using its `remediation` string. Re-run until it exits 0.
7. Hand off to `tracing-requirements` to wire each new ID into `trace.json` with `design[]`, `tests[]` and `status: open`.

## What this skill refuses

- Writing requirements no one asked for ("gold-plating"). Every requirement traces to a stated need — if you can't say why, ask, don't invent.
- Marking a requirement `verified` or changing its `status` here — that belongs to `tracing-requirements` and the evidence chain, never a hand-edit.
- An impossible or self-contradictory requirement: flag it to the user and ask, per the brief's operating principles. Never silently soften it to make the lint pass.

See `references/ears-patterns.md` for more worked examples and common lint failures.
