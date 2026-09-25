# Compliance map (G0 draft)

**This is a standards map for planning, not a compliance determination.** Every line needs confirmation by a qualified human (a compliance engineer, test lab or certification body); none has been confirmed. Evidence level L0. Editions and dates come from the Forge research files `docs/research/R5e-standards-materials-radio-security.md` (R5e), `R5b-standards-safety-risk-se.md` (R5b) and `R5a-standards-drawings-ipc-accessibility.md` (R5a), all accessed 2026-09-25; their [V]/[R]/[U] tags are kept. Standards text is not reproduced.

Markets (Owner round 2, Q-03): map US, EU, UK and Canada, and **sell in none of them until a qualified human confirms** the route for that market.

## Product profile used for the mapping

| Attribute | Value | Source |
|---|---|---|
| Function | ceiling-mounted home-automation presence sensor with a fall-event output, for bedrooms and living rooms; one person per covered area; up to two pods per room | Owner; Owner round 2 |
| Power | 5 V USB-C from an external wall adapter; no battery; no mains inside | Owner; REQ-PWR-003, REQ-ELEC-001 |
| Intentional radiators | 60 GHz FMCW radar (58-62 GHz, 12 dBm, MDS p.4); XIAO ESP32C6 2.4 GHz Wi-Fi 6, Bluetooth LE, IEEE 802.15.4 (XIAO). Kit as-is, no other radio (Owner round 2) | IF-07 |
| Network connection | Wi-Fi to a local Home Assistant only (ESPHome, DS p.2); no cloud | Owner round 2 (Q-02) |
| Personal data | presence and fall events about occupants of a home | inferred from function |
| Claims | home-automation use; no medical, safety or alarm claims, strict; deny-list in `compliance/claims-wording.md` | REQ-SAFE-003, REQ-SAFE-004; Owner round 2 (Q-15) |
| Environment | 0 °C to 40 °C ambient; v1 indoor dry rooms; bathroom variant IPX4 later | Owner round 2 |
| Vendor statements | DS p.8: FCC Part 15 statement, co-location restriction (15.21), Class B digital-device limits; no FCC ID shown | DS p.8 |

## Per market

Every row: **needs a qualified human** to confirm applicability, edition and route, and to sign.

### United States

| Topic | What may apply | Source | Requirement |
|---|---|---|---|
| Unintentional emissions | FCC 47 CFR Part 15 Subpart B, Class B (residential); SDoC or Certification | R5e [V] | REQ-EMC-001 |
| Intentional radiators | FCC Part 15 Subpart C; Certification through a TCB by default. Whether the kit's existing grants (if any) cover the pod as built is unknown: DS p.8 shows no FCC ID | R5e [V]; DS p.8 | REQ-EMC-002, REQ-EMC-005 |
| Product safety | UL 62368-1 Ed. 4 (joint with CSA) for AV/ICT equipment, if a qualified human decides it applies to a 5 V USB sensor | R5b [V] | REQ-SAFE-001, -002 |
| Enclosure flammability | UL 94 (7th ed., revised 2 Jul 2026), class called up by the end-product standard | R5a [V] | REQ-SAFE-001 |
| IoT security | NIST IR 8259 Rev. 1 / 8259A / 8259B: voluntary | R5e [V] | REQ-FW-002, -003 |
| Gaps | FCC "Cyber Trust Mark", module/host labelling rules: not covered or not re-read in R5e | R5e "Not found" | research needed |

### European Union

| Topic | What may apply | Source | Requirement |
|---|---|---|---|
| Radio | RED 2014/53/EU (Art. 3(1)(a) safety, 3(1)(b) EMC, 3(2) spectrum) | R5e [V] | REQ-EMC-003 |
| EMC | EN 55032 / EN 55035 (CISPR 32 Ed. 2.1 / CISPR 35 Ed. 1.0); radio products also use ETSI EN 301 489 series | R5e [V]/[R]; EN 301 489 [U] | REQ-EMC-003 |
| Radio spectrum (60 GHz, 2.4 GHz) | harmonised radio standards for each radio: not covered in R5e | gap | research needed |
| RED cybersecurity | Delegated Regulation 2022/30, applied from 1 Aug 2025 until 11 Dec 2027; EN 18031-1/-2/-3:2024 give no presumption if the user can skip setting a password | R5e [V] | REQ-FW-002 |
| Cyber Resilience Act | Regulation (EU) 2024/2847: vulnerability and incident reporting from 11 Sep 2026; full application 11 Dec 2027 (Annex I, SBOM, CE marking, support period) | R5e [V] | REQ-FW-002, -003; SBOM at G5 |
| Consumer IoT baseline | ETSI EN 303 645 V3.1.3: no universal default passwords (maps to EN 18031 and CRA Annex I) | R5e [V] | REQ-FW-003 |
| Product safety | EN IEC 62368-1:2024: OJ citation status unsettled (only the 2014 edition appears cited under LVD) | R5b [R] | REQ-SAFE-001, -002 |
| Substances | RoHS 2011/65/EU + 2015/863 (lead exemptions changed 1 Jul 2026); REACH Candidate List (253 entries, 4 Feb 2026) and SCIP | R5e [V]/[R]/[U] | BOM declarations at G2/G5 |
| Privacy | data stays on the local network (Owner round 2); whether GDPR or national privacy law still applies is not covered in R5 files | gap | research needed |
| Gaps | GPSR, WEEE, packaging rules, battery rules (not applicable: no battery): not covered in R5e | R5e "Not found" | research needed |

### United Kingdom

The Forge R5 research files do not cover UK-specific law (UKCA marking, the UK radio, EMC and product-safety regimes, or UK product-security rules for connectable products). **Nothing is mapped for the UK yet.** Research is needed before the UK can be planned, and a qualified human must confirm the result.

### Canada

| Topic | What may apply | Source | Requirement |
|---|---|---|---|
| Licence-exempt radio | ISED RSS-Gen Issue 6 (30 Jul 2026, Amendment 1 15 Sep 2026; Issue 5 accepted until about 30 Jul 2027) | R5e [V] | REQ-EMC-004 |
| 2.4 GHz radios | RSS-247 Issue 4 (24 Jul 2025) | R5e [V] | REQ-EMC-004 |
| 60 GHz radar | the applicable RSS is not identified in R5e | gap | research needed |
| Labels and manuals | bilingual (EN/FR) labelling and manual statements | R5e [U] | instructions at G4 |
| Product safety | CSA C22.2 No. 62368-1-2025 (enforcement from 2026-04-30) | R5b [R] | REQ-SAFE-001, -002 |

## Across all markets

- **Medical, safety or alarm claims** change the route entirely (R-008). The owner chose home-automation use with strict wording (Owner round 2): REQ-SAFE-003, REQ-SAFE-004 and `compliance/claims-wording.md` apply to every user-facing text, including Home Assistant entity names.
- **IPX4 (bathroom variant, post-v1)**: the IP-code test standard and edition are not in the Forge R5 files; research and a qualified human are needed before REQ-MECH-018 is tested.
- **Two pods per room**: whether the DS p.8 co-location statement applies to two separate pods in one room is for a qualified human (REQ-SYS-003).
- **Adding any radio** beyond the kit needs a new authorisation assessment (DS p.8 co-location statement; REQ-EMC-005). Owner round 2: kit as-is.
- **Pre-scan plan**: `compliance/pre-scan-plan.md` is written at G3 by `mapping-compliance`, after markets and radios are fixed.

---

**Qualified-human review:** ____________  **Name:** ____________  **Date:** ____________  **Scope confirmed:** ____________

<!-- Leave the line above blank. Only a qualified human fills it in. -->
