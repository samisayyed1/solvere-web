---
name: mapping-compliance
description: Map a product's facts (market, power source, radio, connectivity, PCB, plastics, UI) against a sourced standards data file to a candidate list of applicable standards with edition, trigger reason and source, then a test plan and pre-scan plan. Use when the user asks "what standards apply", "compliance checklist", "do we need FCC/CE/UL", or before a G1/G4 gate involving safety, EMC, radio or cybersecurity regulation. Also fires from the compliance.md path rule. Do NOT use this for hazard/failure analysis (see analyzing-risk) or BOM substance sourcing detail (see costing-bom) — this skill only maps regulatory applicability, and it never determines compliance.
paths:
  - "compliance/**"
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(${CLAUDE_SKILL_DIR}/scripts/verify.py:*), Bash(forge-python ${CLAUDE_SKILL_DIR}/scripts/verify.py:*)
---

# Mapping compliance

**Non-negotiable rules, read first:**
1. **This is never a compliance determination.** Every generated file — `compliance/standards-map.md`, `test-plan.md`, `pre-scan-plan.md` — carries the fixed disclaimer, and a qualified human always signs before anything ships. Never write "this product is compliant" or "this product meets X" anywhere.
2. Every standard listed must trace to `references/standards.toml`, whose `edition`, `year` and `trigger` fields trace to a specific Forge research file (R5a/R5b/R5e). Never add a standard, edition or claim that isn't in that data file — if a new one is needed, add a sourced row to `standards.toml` first (with its `source_file`), don't improvise in the output.
3. **EN 18031 restricted-clause tripwires are gate blockers, not notes**: a no-password mode, or toy/childcare radio equipment without parental control, gives *no* presumption of conformity under the EU RED cyber delegated act (R5e). Either fix the design or record an explicit mitigation note — an unmitigated tripwire fails the check.
4. Standards text itself is copyrighted (IPC's front matter explicitly forbids feeding its text to AI systems — R5a). Cite clause numbers and standard names only; never paste or reconstruct standard body text.

## `compliance/product-profile.toml`

The product's own facts, used to match against `references/standards.toml`'s `applies_if` predicates:

```toml
category = "consumer_iot"        # consumer_iot | medical | automotive | industrial | ...
power_source = "battery"         # "battery" | "mains" | "battery_and_mains"
has_radio = true
has_pcb = true
has_plastic_enclosure = true
has_web_or_app_ui = true
connects_to_internet = true
contract_manufactured = true
has_safety_function = false
is_toy_or_childcare = false
allows_blank_password = false          # EN 18031 tripwire -- set true only if real, and mitigate
has_parental_control = false           # relevant only if is_toy_or_childcare
target_markets = ["US", "EU", "CA"]
# password_mitigation_note / toy_control_mitigation_note: required if the
# corresponding tripwire fires.
```

## Workflow

1. Fill in `compliance/product-profile.toml` from the actual product facts — ask `interviewing-stakeholders`'/`writing-requirements`'s SPEC.md and requirements if a field is unclear; never guess a market or a radio claim.
2. Run:
   ```
   forge-python ${CLAUDE_SKILL_DIR}/scripts/verify.py --project <root>
   ```
   It writes `compliance/standards-map.md`, `compliance/test-plan.md`, `compliance/pre-scan-plan.md` and fails on a missing required profile field or an unmitigated EN 18031 tripwire.
3. Hand the standards map to `analyzing-risk` for anything with a safety dimension, and to `costing-bom` for substance-restriction (RoHS/REACH) BOM flags.
4. At a gate review, attach the three generated files as-is — never paraphrase away the disclaimer.

## What this skill refuses

- Declaring or implying compliance, certification, or "production-ready" status (CONTRACTS §4's wording rule: those words need L5, a human sign-off, never this skill alone).
- Inventing a standard, edition or applicability rule not in `references/standards.toml`. If the data file is wrong or stale, fix the data file (with a source), don't patch around it in the generated report.
- Silently ignoring a restricted-clause tripwire because "it's probably fine" — that judgement belongs to a human, recorded in a mitigation note.
