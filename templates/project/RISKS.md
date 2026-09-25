# Risks

Open risks, tracked with an id so gate records and DFMEA/STPA output (`analyzing-risk`) can reference them. Severity and likelihood are qualitative (Low/Medium/High) until an analysis assigns S/O/D numbers.

| ID | Risk | Severity | Likelihood | Mitigation | Status | Owner |
|---|---|---|---|---|---|---|
| R-001 | Snap-fit lid retention force has not been measured on a printed prototype; the 15-40 N target (REQ-MECH-001) is a design assumption. | Medium | Medium | Measure on the first EVT prototype (`stacking-tolerances`, `verifying-geometry`); retire A-001 with the result. | open | mechanical-engineer |

## Status values

`open` -- not yet mitigated. `mitigating` -- mitigation in progress. `closed` -- mitigated, with evidence linked. `accepted` -- a human has explicitly accepted the residual risk (record who, and when, here).
