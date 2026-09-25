# Software -- standards and applicability

## When each standard applies

| Standard | Current edition (2026-09-25) | Applies when | Source |
|---|---|---|---|
| WCAG 2.2 | W3C Recommendation, updated 2024-12-12 | Any user-facing UI (app, web, on-device screen). Free to use. | R5a §1 |
| ISO/IEC 40500 | :2025 (2nd ed.) = WCAG 2.2 (Oct 2023 text) | Where an ISO-numbered accessibility citation is required instead of a W3C one. Free from ISO. | R5a §1 |
| ISO 9241-11 / -110 / -210 | :2018 / :2020 / :2019 | Usability definition, dialogue principles, and human-centred design process, respectively. | R5a §1 |
| OWASP ASVS | 5.0.0, 2025-05-30 | Application security verification, any web/app software component. | R5e §"Standards table" |
| NIST IR 8259 series | Rev. 1 (2026-04-20), 8259A/8259B unchanged | If the software controls or pairs with an IoT device. | R5e §"Standards table" |

## What Forge automates

- Nothing here is automatically checked against WCAG/ASVS clause-by-clause today -- `ux-designer` and `software-architect` apply these standards by reference during design and review; a future skill may add scripted axe-core/ASVS-style scans.
- Requirement-to-test traceability for every software feature claim, same as any other domain (`tracing-requirements`).
- If gstack is installed, software build/test loops delegate to it; Forge still owns the requirement, evidence and gate layer.

## What needs a qualified human

- An accessibility conformance claim ("WCAG 2.2 AA") needs a human audit, not just an automated scanner pass -- automated tools catch a minority of WCAG success criteria.
- An ASVS level claim (L1/L2/L3) needs a human security review against the verification requirements; Forge does not self-certify.
- Any claim of "validated" or "production-ready" software needs the evidence level to match (L4/L5, CONTRACTS.md §4) -- a green test suite alone is L1-L2, not more.
