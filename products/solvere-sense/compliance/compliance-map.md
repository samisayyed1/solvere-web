# Compliance map: addendum to the generated files (G0)

**This is not a compliance determination.** Nothing here or in the generated files says the pod complies with anything; a qualified human (compliance engineer, accredited lab or certification body) reviews, scopes and signs every line (Q-17). Evidence level L0.

## Primary artefacts (generated; do not edit by hand)

The Forge way is profile in, map out:

| File | What it is | How it is made |
|---|---|---|
| `compliance/product-profile.toml` | the product's facts, each cited to the owner answers, DS, MDS or XIAO | written by systems-engineer |
| `compliance/standards-map.md` | candidate standards, edition, trigger and source (11 matched at G0) | `~/.forge/bin/forge-python plugins/forge/skills/mapping-compliance/scripts/verify.py --project products/solvere-sense` |
| `compliance/test-plan.md`, `compliance/pre-scan-plan.md` | per-standard human tasks | same run |

Re-run the generator whenever the profile changes; never paraphrase the generated files. Editions, bodies and triggers live only there (from the skill's `references/standards.toml`, sourced from R5a/R5b/R5e).

Markets (Owner round 2, Q-03): US, EU, UK and Canada are **mapped, not sold**; no sale in any market until a qualified human confirms that market's route.

## Addendum: what the generated map does not cover

Each item below is either outside the skill's data file or a project-specific note on a generated row. **Every item needs a qualified human.**

| # | Topic | Why it is here | Source | Requirement / owner action |
|---|---|---|---|---|
| 1 | **United Kingdom** | The data file has no UK rows, so `UK` in `target_markets` matches nothing. UK radio, EMC, product-safety and connectable-product security rules are not in the Forge R5 files: **nothing is mapped for the UK**. | R5e (no UK coverage) | research needed before any UK plan |
| 2 | **IEC/UL 62368-1 product safety** | Not matched: the data row triggers only on `power_source` containing `"mains"`, and the pod has no mains (5 V USB-C from an external adapter). But the same row's trigger text names "sensors with a mains adapter" (R5b), which describes this pod. Kept as a candidate by REQ-SAFE-001 and REQ-SAFE-002 until a qualified human decides. | R5b; skill `standards.toml` row `iec-62368-1` | REQ-SAFE-001, -002; Q-17 |
| 3 | **EU RED core requirements** (Art. 3(1)(a) safety, 3(1)(b) EMC, 3(2) spectrum) | The data file carries only the RED cybersecurity row (`eu-red-cyber`). The core RED articles, the ETSI EN 301 489 radio-EMC series [U] and the harmonised spectrum standards for 60 GHz and 2.4 GHz are not in the data file. | R5e | REQ-EMC-003; research needed |
| 4 | **FCC intentional radiators** (on the generated `fcc-part15` row) | The pod carries a 60 GHz radar and a 2.4 GHz Wi-Fi/BLE/802.15.4 radio; DS p.8 shows a Part 15 statement and the co-location restriction (15.21) but no FCC ID, so it is unknown whether existing grants cover the kit inside the pod. | DS p.8; R5e | REQ-EMC-001, -002, -005 |
| 5 | **Two pods per room** | Whether the DS p.8 co-location statement applies to two separate pods in one room. | DS p.8; Owner round 2 (Q-12) | REQ-SYS-003 |
| 6 | **Canada, 60 GHz radar** (on the generated `ised-rss` row) | RSS-247 covers the 2.4 GHz radio; the RSS for the 60 GHz radar is not identified in R5e. Bilingual (EN/FR) labels and manual statements [U]. | R5e | REQ-EMC-004; research needed |
| 7 | **Internet connection** | The profile sets `connects_to_internet = true` conservatively although the owner chose local Wi-Fi to Home Assistant only; whether local-only use changes the RED-cyber, CRA and EN 303 645 rows is for a qualified human. | Owner round 2 (Q-02); R5e | REQ-FW-002, -003 |
| 8 | **PCB rows** (generated `ipc-2221c`) | Matched because the kit contains PCBs; Forge designs no PCB for v1 (kit bought assembled, Owner round 2 Q-01), so this row is expected to need no work unless the architecture changes. | DS p.7 | none at G0 |
| 9 | **Privacy** | Data stays on the local network (Owner round 2); whether GDPR or national privacy law applies is not in the R5 files. | gap | research needed |
| 10 | **Other EU product rules** | GPSR, WEEE, packaging rules: not in the R5 files. Battery rules do not apply (no battery). | R5e "Not found" | research needed |
| 11 | **Claims** | Home-automation use, strict neutral wording (Owner round 2, Q-15); a medical, safety or alarm claim would change the route (medical and functional-safety rows exist in the data file and are deliberately not triggered: `category = "consumer_iot"`, `has_safety_function = false`). | Owner round 2 | REQ-SAFE-003, -004; `compliance/claims-wording.md` |
| 12 | **IPX4** (bathroom variant, post-v1) | The IP-code test standard and edition are not in the R5 files or the data file. | Owner round 2 (Q-08) | REQ-MECH-018; research needed |

## Known limits of the generator at G0 (for the Forge maintainers)

Found while writing the profile; recorded in `docs/g0-check-log.md` §6. The check cannot fail on:

- **a market code typo**: a seeded profile with `"EUU"` for `"EU"` passes and silently drops 5 EU standards (11 matched become 6);
- **a radio removed**: a seeded profile with `has_radio = false` passes, even though REQ-EMC-002 and REQ-EMC-004 list radios (11 become 10).

It does fail on a missing required field and on an unmitigated EN 18031 blank-password tripwire. Until the skill validates market codes and cross-checks the profile against the requirements, a human reviews `product-profile.toml` against REQ-EMC-001..005 at each gate.

---

**Qualified-human review:** ____________  **Name:** ____________  **Date:** ____________  **Scope confirmed:** ____________

<!-- Leave the line above blank. Only a qualified human fills it in. -->
