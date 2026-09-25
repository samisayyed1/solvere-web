---
paths:
  - "compliance/**"
---

# Compliance

- Forge output here is a **standards map and test-plan draft, never a compliance determination**. Every compliance document says so explicitly, and carries a blank human sign-off line (only a human may fill it in -- enforced by a PreToolUse hook, CONTRACTS §7).
- `mapping-compliance` goes: product profile -> applicable standards (with current edition and citation) -> test plan -> pre-scan plan. Cite `docs/standards/compliance.md` (sourced from `docs/research/R5b`, `R5e`) for edition numbers -- never invent one (`mapping-compliance`'s verify entrypoint, check_id `compliance.standards_map`, fails on an uncited standard).
- No accidental medical, safety or regulatory claims: `safety-compliance-engineer`'s claims review checks report and marketing language before it ships.
- Standards text (IPC, ASME, ISO, UL) is copyrighted and must not be reproduced -- cite clause numbers and hold only user-supplied or licensed values (advisory -- no automated check reads reproduced standards text; caught only in review).
- "Certified" or "production-ready" wording requires L5 evidence (accredited body or qualified human sign-off) -- the wording lint (`forge lint wording`) enforces this on everything under `compliance/`, `reviews/`, `release/`.
- Hazard analysis (STPA) and DFMEA/PFMEA live alongside compliance mapping in `analyzing-risk`'s output; S/O/D ratings and action tracking are never left implicit (`analyzing-risk`'s verify entrypoint, check_id `safety.dfmea_ap`, checks every row has an S/O/D rating).
