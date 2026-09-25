---
name: analyzing-risk
description: Run a systems-theoretic hazard analysis (STPA) and a Design/Process FMEA (AIAG & VDA style, S/O/D 1-10, Action Priority) with tracked actions. Use when the user asks "what could go wrong", "hazard analysis", "FMEA", "safety analysis", "risk assessment" for a product, or before a gate review on anything with a safety, health or regulatory dimension. Also fires from the compliance.md path rule. Do NOT use for compliance-standard mapping (see mapping-compliance) or for BOM/supply-chain risk (see costing-bom) — this skill is hazard causation and failure-mode analysis, not regulatory scope or sourcing.
paths:
  - "compliance/**"
  - "analysis/**"
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(${CLAUDE_SKILL_DIR}/scripts/verify.py:*), Bash(forge-python ${CLAUDE_SKILL_DIR}/scripts/verify.py:*)
---

# Analyzing risk

**Non-negotiable rules, read first:**
1. This skill never calls anything "validated" or "certified" — hazard analysis is engineering judgement, not physical test (CONTRACTS §4). It also never asserts a product "is safe"; it lists hazards, unsafe control actions, loss scenarios and failure modes for a human to act on.
2. The Action Priority (AP) computation (`scripts/ap.py`) is a **sourced approximation**, not the real AIAG & VDA lookup table — that table is in a paywalled handbook the research session (`docs/research/R5b-standards-safety-risk-se.md`) could not read. Every AP result says so. Treat a Low or Medium from this script as "needs a human check against the handbook", never as clearance.
3. Every row with Action Priority **High** needs a tracked action: what, who (`owner`), and by when (`due_date`). A High-AP row with no action is a gate blocker, not a note for later.
4. A cross-functional team and a trained facilitator judge S/O/D — this skill drafts the structure and does the arithmetic; it does not invent severity or occurrence numbers no one on the team agreed to.

## STPA (systems-theoretic hazard analysis)

Four steps, from the MIT PSASS STPA Handbook (Leveson & Thomas, March 2018 — see `docs/research/R5b`, and `references/stpa-steps.md` for the full walkthrough):

1. **Define the purpose.** Name the losses stakeholders won't accept, set the system boundary, derive system-level hazards and constraints.
2. **Model the control structure.** A hierarchical diagram of controllers, the control actions they issue, and the feedback they receive. Start abstract, refine as the design firms up.
3. **Identify unsafe control actions (UCAs).** For each control action: hazardous if not given / given / given too early, too late or out of order / stopped too soon or applied too long. Turn each UCA into a controller constraint.
4. **Identify loss scenarios.** Why could a UCA arise (bad feedback, wrong process model, flawed logic)? Why might a correct command not be carried out (actuator/process faults)? Scenarios drive requirements (`writing-requirements`) and tests (`tracing-requirements`).

Write STPA output as `analysis/stpa.md`: control-structure description, a UCA table, and a loss-scenario table with a `derived requirement` column pointing at `REQ-<AREA>-<NNN>` ids. There is no automated checker for STPA content itself (it's structured judgement) — the requirement IDs it derives get checked by `writing-requirements`/`tracing-requirements` as normal.

## DFMEA (Design FMEA, AIAG & VDA style)

Data file: `analysis/dfmea.csv`, columns:

```
id,item,function,failure_mode,effect,severity,cause,occurrence,current_controls,detection,action,owner,due_date
```

- `severity`, `occurrence`, `detection`: integers 1–10.
  - **Severity**: how bad the worst effect of the failure mode is. 1 = no noticeable effect; the top of the scale (9–10) is reserved for effects on safe operation, health or regulatory compliance.
  - **Occurrence**: how likely the failure *cause* is to happen, judged by how effective prevention controls are and how proven the design is. 1 = the cause has effectively been designed out.
  - **Detection**: how well current controls would catch the cause/failure mode before release/ship. 10 = no detection method; 1 = always caught.
- `action`, `owner`, `due_date`: required whenever the computed Action Priority is High.

Run:
```
forge-python ${CLAUDE_SKILL_DIR}/scripts/verify.py --project <root>
```
It validates S/O/D ranges, computes Action Priority per row (`ap.action_priority`), and fails any High-AP row with no tracked action. See `references/dfmea-ap.md` for the sourcing gap and the exact banding logic used.

## Workflow

1. Run STPA first (or alongside DFMEA) to find systemic/interaction hazards a component-level FMEA misses.
2. Draft the DFMEA structure: item -> function -> failure mode -> effect -> cause -> current controls, one row per cause.
3. As a team, agree S/O/D for each row (this skill does not choose these numbers unattended for anything above trivial severity — ask).
4. Run `scripts/verify.py`; fix every High-AP row with no action.
5. Feed derived requirements into `writing-requirements`, and hazards/failure modes worth a standards cross-check into `mapping-compliance`.

## What this skill refuses

- Computing or asserting a final AP classification as if it were the licensed AIAG & VDA table. It states the approximation and the gap every time.
- Silently lowering a severity rating to make a High-AP row disappear. If a rating looks wrong, flag it to the team — don't edit around the check.
- Certifying, validating, or signing anything. STPA/DFMEA output feeds a gate review; only a human signs the gate (CONTRACTS §7).
