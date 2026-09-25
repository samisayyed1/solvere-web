---
name: writing-adrs
description: Write an architecture decision record (ADR) for a Forge project -- a numbered, evidence-linked record of a choice between real options with stated consequences. Use when the user makes or asks about a non-trivial architecture/tooling/process choice ("should we use X or Y", "document why we picked..."), or when a decision needs to be revisited later. Do NOT use for routine implementation details that have only one sane option, and do NOT use to record a safety/gate decision (see reviewing-designs' Gx.md records instead).
allowed-tools: Read, Write, Edit, Glob, Bash(${CLAUDE_SKILL_DIR}/scripts/new_adr.py:*)
---

# Writing ADRs

**Non-negotiable rules, read first:**
1. An ADR records a **real choice between at least two options** with stated pros/cons — not a single option dressed up as a decision. If there was really only one viable option, say so plainly in Context; don't pad an Options table to look rigorous.
2. Every claim in Context and Rationale is evidence-linked: a research file, a measured result, or an explicit owner approval — never "generally considered best practice" with nothing behind it.
3. ADRs are numbered sequentially and never renumbered or deleted. A superseded decision gets a new ADR that says so and updates the old one's Status to "Superseded by ADR-NNN", never a silent overwrite.
4. Where this brief's ADR-001 already made a decision (packaging, models, toolchain pins, ...), a project ADR that touches the same area must say explicitly whether it follows or deviates from ADR-001, and why (CONTRACTS.md's own front matter: "Where this brief and ADR-001 disagree, the ADR wins" — a project ADR needs the same discipline about its own precedence).

## Workflow

1. Confirm this is a real decision (≥2 genuine options) worth recording, not routine work.
2. Gather the evidence for each option — research files, prior art in this repo, a quick spike, or ask the user for missing facts. Never fabricate a pro/con no one checked.
3. Scaffold the file:
   ```
   ${CLAUDE_SKILL_DIR}/scripts/new_adr.py --project <root> --title "<short title>" --date <YYYY-MM-DD> [--status Proposed]
   ```
   This numbers it automatically from the highest existing `docs/decisions/ADR-*.md` and never overwrites an existing file.
4. Fill in Context, Options considered, Decision, Rationale, Consequences from `references/adr-template.md`.
5. If the decision needs owner sign-off (safety, money, fabrication, or a free-first-policy exception per ADR-001 §17), leave the sign-off line blank — never fill it in on the human's behalf.

## What this skill refuses

- Backfilling a plausible-sounding "Options considered" table after the fact for a decision that was actually made for one reason someone typed in chat. Write down the real reason, even if it's "the owner asked for X."
- Filling in a human sign-off line. That is always left blank (CONTRACTS §7's rule for gate records applies here too: only a human signs).
