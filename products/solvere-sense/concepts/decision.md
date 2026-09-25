# G1 concept decision

- **Decision:** the owner chose **Concept D (cost/mfg-first, Revision 1)** in chat on 2026-09-25, from the top 2 offered (D and A).
- **Tournament:**
  - 4 independent concept generators (Opus), each with a different lens.
  - 3 pass/fail safety gates applied first (`concepts/gates.md`).
  - 3 blind Opus judges. Round-1 verdicts are in `judging/J1..J3.md`. B, C and D failed a gate in round 1, were revised once, and were re-gated in `judging/*-rev1.md`.
  - Weights were agreed with the owner before any scoring (`criteria.json`).
- **Result** (`pugh.json`, judges' mean, weighted, against the datum): D +0.85, A +0.65, C +0.47, B +0.10.
  - `exploring-concepts` verify: PASS.
  - Sensitivity at ±25 % per weight: stable, no flips of the top 2.
- **Not done, to save budget:** the workflow's optional pairwise head-to-head step.
- **Scope:** this records the concept choice only. It does not pass the G1 gate. The gate record is `reviews/G1.md`, and only a human signs it.

## Carried into G2, from the judges' watch items

1. The antenna gap d = N × 2.5 mm crosses the bayonet joint (P2 seat → flat land → P1 lug → floor). The tolerance stack on d is a G2 check.
2. FDM sag on the hidden flat seat lands (bridges up to 10 mm) is checked on the first fit print.
3. Whether the skirt-groove glow is bright enough through a wall of at least 2.5 mm is untested (TP-UX-004). Fallbacks, in order: a clear light guide outside the cone, then a Grove-port LED.
4. The LED position on the kit is not yet measured (A-005). It must be measured before the skirt-groove location is final.
5. Radome εr at 60 GHz is unmeasured for FR resin and PA 12 FR (coupon plan TP-SYS-002). T is computed at G2 once the measured value exists.
6. The warm-white finish over the UL 94-listed grey materials is not covered by any listing. This is for a qualified human (Q-17).
7. The $30 production BOM is not reachable with the $28.99 kit (R-002). The G2 BOM reports the real number.
