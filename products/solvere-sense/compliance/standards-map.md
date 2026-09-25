# Applicable standards map

**This is not a compliance determination.** It flags candidate standards and their sourced trigger reasons for a qualified human to review, scope and sign. Testing, certification and declarations of conformity always need an accredited lab, a notified body, or a named qualified person -- never Forge.

Data snapshot as of 2026-09-25 (`references/standards.toml`). Re-check any row older than ~180 days.

## ul94-flammability -- UL 94 flammability rating (+ IEC 60695-11-10/-20 equivalents)
- **Edition:** UL 94 7th ed. (2023-02-28, rev. 2026-07-02); IEC 60695-11-10 Ed.2.0 (2013); -11-20 Ed.2.0 (2015)
- **Body:** UL Standards & Engagement / IEC TC 89
- **Why it applies:** Enclosures, housings and internal plastic parts in electrical appliances and IT/AV equipment; called up by end-product standards such as 62368-1.
- **Source:** docs/research/R5a-*.md
- **Needs a qualified human for:** UL iQ Yellow Card lookup at actual wall thickness/colour; all testing and certification.

## ipc-2221c -- IPC-2221C -- generic PCB design rules
- **Edition:** Rev C (Dec 2023)
- **Body:** IPC (Global Electronics Association), task group D-31b
- **Why it applies:** Any PCB design package or fabrication note.
- **Source:** docs/research/R5a-*.md
- **Needs a qualified human for:** High-voltage creepage decisions, product class (1/2/3), impedance/thermal trade-offs.

## eu-rohs -- EU RoHS -- restricted substances in EEE
- **Edition:** Directive 2011/65/EU + 2015/863; 2025 lead-exemption resets apply from 2026-07-01
- **Body:** EP & Council / European Commission
- **Why it applies:** Any electrical/electronic equipment placed on the EU market.
- **Source:** docs/research/R5e-*.md
- **Needs a qualified human for:** Scope determination, exemption applicability, analytical test (XRF/ICP), signing the EU DoC.

## reach-scip -- REACH Candidate List (Art. 33) + SCIP notification
- **Edition:** 253 entries as of 2026-02-04 snapshot (treat as a floor; re-check before relying on it)
- **Body:** ECHA / EP & Council
- **Why it applies:** Any article placed on the EU market containing a Candidate-List SVHC above 0.1% w/w.
- **Source:** docs/research/R5e-*.md
- **Needs a qualified human for:** Supplier data quality, article-level calculation, ECHA submission.

## fcc-part15 -- FCC 47 CFR Part 15 -- unintentional/intentional radiators
- **Edition:** eCFR current, last amended 2026-04-27
- **Body:** FCC
- **Why it applies:** Any digital device (Subpart B) or licence-exempt intentional radiator (Subpart C) sold in the US.
- **Source:** docs/research/R5e-*.md
- **Needs a qualified human for:** FCC-recognised accredited test lab; TCB grant for Subpart C; the SDoC US responsible party.

## ised-rss -- ISED RSS-Gen + RSS-247 -- Canadian radio equipment certification
- **Edition:** RSS-Gen Issue 6 (2026-07-30, Amendment 1 2026-09-15); RSS-247 Issue 4 (2025-07-24)
- **Body:** ISED Canada
- **Why it applies:** Any licence-exempt radio sold in Canada (DTS/FHSS/LE-LAN or general Category I device).
- **Source:** docs/research/R5e-*.md
- **Needs a qualified human for:** Accredited lab, ISED-recognised certification body, ISED registration.

## eu-red-cyber -- EU RED cybersecurity (Delegated Reg. 2022/30 + EN 18031-1/-2/-3)
- **Edition:** 2022/30 applies 2025-08-01, repealed 2027-12-11 by 2026/339; EN 18031-1/-2/-3:2024 cited with restrictions by (EU) 2025/138
- **Body:** European Commission / CEN-CENELEC JTC 13
- **Why it applies:** Internet-connected radio equipment, or toy/childcare/wearable radio equipment processing personal data, placed on the EU market.
- **Source:** docs/research/R5e-*.md
- **Needs a qualified human for:** Risk assessment, notified-body route if a restricted clause is triggered, signing the DoC.

## cispr32-35-emc -- CISPR 32 / CISPR 35 (EN 55032 / EN 55035) -- multimedia equipment EMC
- **Edition:** CISPR 32 Ed. 2.1 (2019, consolidated); CISPR 35 Ed. 1.0 (2016); both at IEC stability date 2026, Ed.3 of 32 reported near FDIS
- **Body:** IEC CISPR/I / CENELEC
- **Why it applies:** IT/AV/broadcast-receiver multimedia equipment up to 600 V, typically via the EU EMC Directive harmonised route.
- **Source:** docs/research/R5e-*.md
- **Needs a qualified human for:** An accredited (ISO/IEC 17025) EMC lab and interpretation of results.

## etsi-en303645 -- ETSI EN 303 645 -- consumer IoT security baseline
- **Edition:** V3.1.3 (2024-09)
- **Body:** ETSI TC CYBER
- **Why it applies:** Consumer IoT devices; not itself mandatory but maps to EN 18031 and CRA Annex I.
- **Source:** docs/research/R5e-*.md
- **Needs a qualified human for:** Third-party assessment where a national scheme requires one.

## eu-cra -- EU Cyber Resilience Act (Regulation (EU) 2024/2847)
- **Edition:** In force since 2024-12-10; reporting duties from 2026-09-11; full application 2027-12-11
- **Body:** EP & Council
- **Why it applies:** Any 'product with digital elements' placed on the EU market (hardware or software, including remote data processing). Reporting duties (Art. 14) already apply to products placed on the market before full application.
- **Source:** docs/research/R5e-*.md
- **Needs a qualified human for:** Product classification (important/critical?), conformity-assessment module or notified body, the DoC, and the actual ENISA SRP submission.

## nist-ir8259 -- NIST IR 8259 series -- voluntary IoT cybersecurity capability baseline
- **Edition:** IR 8259 Rev. 1 (final, 2026-04-20); 8259A (2020-05); 8259B (2021-08-25)
- **Body:** NIST
- **Why it applies:** Not mandatory; relevant to US federal procurement (SP 800-213) and voluntary IoT labelling.
- **Source:** docs/research/R5e-*.md
- **Needs a qualified human for:** None strictly -- voluntary; still worth an internal checklist pass.


## EU Cyber Resilience Act reporting timeline (Regulation (EU) 2024/2847)

Source: docs/research/R5e-standards-materials-radio-security.md.

- **2024-12-10**: CRA in force.
- **2026-06-11**: rules for notified conformity-assessment bodies apply.
- **2026-09-11**: Article 14 reporting duties apply -- 24h early warning / 72h
  notification / final report within 14 days (vulnerability) or 1 month
  (incident), via ENISA's Single Reporting Platform. This covers products
  already on the market before full application.
- **2027-12-11**: full application (Annex I essential requirements, SBOM,
  CE marking, support-period declaration).

A named human submits every report. Forge only starts the clock and points
at the runbook -- it never files on anyone's behalf.

