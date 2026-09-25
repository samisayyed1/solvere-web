# Systems engineering -- standards and applicability

## When each reference applies

| Reference | Current edition (2026-09-25) | Applies when | Source |
|---|---|---|---|
| INCOSE Systems Engineering Handbook | 5th edition, Jun 2023 (aligned to ISO/IEC/IEEE 15288:2023) | General systems-engineering process guidance -- requirements, architecture, V&V planning. | R5b §1 |
| NASA SE Handbook | NASA/SP-2016-6105 Rev2 (web-updated 2024-03-27) | Systems-engineering process reference, especially for staged/gated programs. | R5b §1 |
| NASA NPR 7123.1 | Rev D + Change 2, effective 2023-07-05 | NASA-governed programs specifically; otherwise reference only. | R5b §1 |
| EARS (Mavin et al., RE'09, DOI 10.1109/RE.2009.9) | 2009 paper, no newer edition | Requirement sentence structure -- Forge's `writing-requirements` lint enforces this form. | R5b §1 |
| STPA Handbook (Leveson & Thomas) | Mar 2018, free PDF | System-theoretic hazard analysis, used by `analyzing-risk`. | R5b §1 |
| AIAG & VDA FMEA Handbook | 1st edition, Jun 2019 (Jun 2020 errata) | DFMEA/PFMEA structure and S/O/D scoring, used by `analyzing-risk`. | R5b §1 |

## What Forge automates

- EARS-form linting of every requirement (`writing-requirements`) -- syntax only, not whether the requirement is *correct* or complete.
- Requirement-to-design-to-test-to-evidence traceability with orphan and untested-requirement detection (`tracing-requirements`).
- SysML v2 textual model parsing against zero errors and zero warnings (`modeling-systems`, via `spec42 check`).

## What needs a qualified human

- Whether a requirement set is *complete* for the product's mission -- Forge checks form and traceability, not completeness or correctness of intent.
- Architecture trade studies and budget allocation (power, mass, thermal, cost, link) -- Forge records the budget in `params/params.toml`/the model; a systems engineer sets the numbers and their rationale.
- STPA/DFMEA severity, occurrence and detection ratings are a team judgment call, not a computed value.
- An impossible or self-contradictory requirement is flagged and asked about, never silently reinterpreted or dropped.
