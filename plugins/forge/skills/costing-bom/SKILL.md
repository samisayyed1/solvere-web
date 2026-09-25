---
name: costing-bom
description: Build and verify a bill of materials with MPNs, manufacturers, lifecycle status, lead time, volume-tier pricing and alternates, roll up cost at volume tiers, and flag single-source and NRND/EOL parts. Use when the user asks for a BOM, cost roll-up, "what does this cost at volume", supply-chain risk review, or when bom/bom.csv changes. Also fires from the manufacturing.md path rule on bom/. Do NOT use for DFM/process selection (see checking-dfm, owned by the mechanical builder) or for compliance/substance restrictions (RoHS/REACH — see mapping-compliance) — this skill is sourcing, lifecycle and cost, not manufacturability or regulatory scope.
paths:
  - "bom/**"
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(${CLAUDE_SKILL_DIR}/scripts/verify.py:*), Bash(forge-python ${CLAUDE_SKILL_DIR}/scripts/verify.py:*)
---

# Costing the BOM

**Non-negotiable rules, read first:**
1. Every line item needs a non-blank MPN, a manufacturer, a lifecycle status, a non-blank lead time and at least one volume-tier price — a BOM line with no price cannot be rolled up and is not done. No price may be negative. `ref_des` must be unique across lines (a duplicate double-counts cost/qty).
2. A part with no *real* alternate listed is single-sourced. Listing the part's own MPN as its `alternates` doesn't count — `verify.py` FAILs that as hiding the risk it's supposed to disclose (a genuinely different alternate, or an empty field covered by `risk_note`, are the only two honest states). A part not `Active` (NRND, EOL, Obsolete, Preview) carries lifecycle risk. Both are gate-blocking unless `risk_note` records the accepted mitigation (an alternate qualification plan, a last-time-buy, an owner and date) — this mirrors DFMEA action tracking (`analyzing-risk`): a flag with no owner is not a managed risk.
3. Never silently invent a price, MPN or lifecycle status. If the datasheet or distributor page is unread, say so and ask, or mark the field clearly incomplete — don't fabricate a plausible-looking number.
4. This skill never makes a compliance claim (RoHS/REACH/CE) about a part — that is `mapping-compliance`'s job, from the same BOM data.

## `bom/bom.csv` format

```
ref_des,description,mpn,manufacturer,qty_per_unit,lifecycle,lead_time_weeks,alternates,risk_note,price_1,price_100,price_1000,price_10000
R1,10k resistor 0402,RC0402FR-0710KL,Yageo,2,Active,4,RC0402JR-0710KL;ERJ-2RKF1002X,,0.02,0.01,0.005,0.003
U1,MCU,STM32F103C8T6,STMicro,1,NRND,26,,plan: migrate to STM32F103C8T7 by Q1 2027; owner J. Chen,3.10,2.40,1.90,1.60
```

- `alternates`: semicolon-separated alternate MPNs. Empty means single-source.
- `lifecycle`: `Active`, `NRND`, `EOL`, `Obsolete`, `Preview`, or a distributor-reported equivalent — anything other than `Active` is a lifecycle risk.
- `price_<qty>`: one column per volume tier your quotes cover (any integer quantity works as the column suffix — `price_1`, `price_100`, `price_1000`, ... are conventional but not fixed).
- `risk_note`: required whenever a line is single-source or not Active; the accepted-risk record.

## Workflow

1. For every part in `cad/`/`ecad/` params or the schematic netlist, add or update its `bom/bom.csv` line: MPN, manufacturer, qty per unit, lifecycle, lead time, at least one tier price, alternates.
2. Where a part is single-source or non-Active, either add a real alternate or write the mitigation into `risk_note` — don't leave it blank hoping no one asks.
3. Run:
   ```
   forge-python ${CLAUDE_SKILL_DIR}/scripts/verify.py --project <root>
   ```
   It writes `out/verify/bom.rollup.json` (extended cost per volume tier, single-source/lifecycle-risk counts) and fails on any unacknowledged single-source or lifecycle-risk line, or any unpriced line.
4. Report the roll-up in the check's `notes` (also mirrored in `bom.rollup.json`) at the next gate review.

## What this skill refuses

- Rolling up a cost from a price no one actually quoted. A missing price is a blocking finding, not a zero.
- Treating a "flag" as optional. Single-source and lifecycle risk are exactly the kind of thing a red-team review will ask about — an unacknowledged one is a real gap, not paperwork.
- Making the compliance call on a part (RoHS exemption, REACH SVHC) — flag substance data as a data field for `mapping-compliance` to consume, never assert compliance here.

See `references/bom-format.md` for the full column reference and worked examples of single-source/lifecycle acknowledgement.
