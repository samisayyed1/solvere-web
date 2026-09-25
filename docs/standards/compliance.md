# Compliance -- standards and applicability

**Everything on this page is a standards map, not a compliance determination.** Every compliance artifact Forge produces says so explicitly and carries a blank human sign-off line (CONTRACTS.md §4, ADR-001 Risk #9). Standards text is never reproduced -- cite the clause number and the source file below.

## Safety and functional-safety standards

| Standard | Current edition (2026-09-25) | Applies when | Source |
|---|---|---|---|
| IEC 62368-1 / EN IEC 62368-1 / UL 62368-1 | IEC Ed. 4.0 (2023, corrected 2025-08); EN 2024 edition's OJ citation is uncertain (see R5b) | Audio/video, IT and communication equipment safety. | R5b §1 |
| IEC 60601-1 (+ -1-2) | Ed. 3.2 consolidated (2020); EN under MDR cites 2006 + amendments | Medical electrical equipment (only if the product is a medical device). | R5b §1 |
| IEC 61508 | Ed. 2.0, 2010 (Ed.3 at CDV) | Functional safety of programmable electronic systems generally. | R5b §1 |
| ISO 26262 | 2nd edition, 2018 (3rd-edition DIS 2026-08-04) | Automotive functional safety. | R5b §1 |
| DO-178C / DO-254 | 2011 / Apr 2000 | Airborne software / complex electronic hardware. | R5b §1 |

## EU / US / Canada market-access and substance rules

| Rule | Current status (2026-09-25) | Applies when | Source |
|---|---|---|---|
| EU RoHS (2011/65/EU + amendments) | Lead exemptions 6(a)-6(c) apply from 2026-07-01 (Del. Dir. (EU) 2025/2364); ECHA takeover from 2027-08-13 | Any electrical/electronic product placed on the EU market. | R5e §"Standards table" |
| EU REACH / SCIP | Candidate List ~253 entries as of 2026-02-04 (unconfirmed count, ECHA site blocked our check) | Any article containing a Candidate-List SVHC above 0.1% w/w placed on the EU market. | R5e §"Standards table" |
| FCC 47 CFR Part 15 | eCFR current, last amended 2026-04-27 | Any product with a radio or that is an unintentional radiator, placed on the US market. | R5e §"Standards table" |
| ISED RSS-Gen / RSS-247 | RSS-Gen Issue 6 + Amendment 1 (2026); RSS-247 Issue 4 (2025-07-24) | Radio equipment placed on the Canadian market. | R5e §"Standards table" |
| EU RED (2014/53/EU) + cybersecurity delegated act | Del. Reg. (EU) 2022/30 applies from 2025-08-01, repealed 2027-12-11 by (EU) 2026/339 | Radio equipment placed on the EU market. | R5e §"Standards table" |
| EN 18031-1/-2/-3 | :2024, restricted presumption of conformity (Impl. Dec. (EU) 2025/138) | RED cybersecurity presumption route -- restrictions apply, see `docs/standards/firmware.md`. | R5e §Summary |
| EU Cyber Resilience Act (2024/2847) | In force since 2024-12-10; Article 14 reporting live since 2026-09-11; full application 2027-12-11 | Any product with digital elements placed on the EU market. **Reporting duty already active**, including for products placed before 2027-12-11. | R5e §Summary |
| CISPR 32 / 35, EN 55032 / 55035 | See `docs/standards/electrical.md` | EMC emissions/immunity, multimedia equipment. | R5e §"Standards table" |
| ETSI EN 303 645 | V3.1.3, 2024-09 | Consumer IoT baseline cybersecurity (not RED-harmonised). | R5e §"Standards table" |
| NIST IR 8259 series | Rev. 1 (2026-04-20) | IoT cybersecurity capability baseline (US, voluntary unless referenced by a buyer/regulator). | R5e §"Standards table" |
| OWASP ASVS | 5.0.0, 2025-05-30 | Application security verification. | R5e §"Standards table" |

## What Forge automates

- `mapping-compliance`: product profile -> applicable-standards list (with edition and citation) -> draft test plan -> pre-scan plan.
- Wording lint (`forge lint wording`) rejecting `validated`/`certified`/`production-ready` claims below the required evidence level, everywhere under `compliance/`, `reviews/`, `release/`.
- Flagging BOM line items against RoHS exemption codes/expiry and SVHC hits, at the level of "flag for review" -- never a compliance verdict.

## What needs a qualified human

- **All of it, ultimately.** Every table above ends in "a qualified human or accredited body confirms." Forge's output is a starting map and a draft test plan.
- CRA Article 14 reporting (24h/72h/14-day or 1-month clocks) is filed by a named human through ENISA's Single Reporting Platform -- Forge can draft the report content, never submit it.
- Any EMC, safety, or radio test result (CISPR, IEC 62368-1, RED Article 3, FCC/ISED certification) comes from an accredited lab, not from Forge's pre-scan.
- Standards whose dates or counts are known to be volatile during 2026-2027 (RoHS exemption expiries, REACH Candidate List count, CISPR 32 Ed. 3 status) should be re-checked against the source before being relied on -- see the "Not found / discrepancies" sections of R5b and R5e.
