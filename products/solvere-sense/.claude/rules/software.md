---
paths:
  - "app/**"
  - "services/**"
---

# Software (apps, cloud, APIs)

- Covers on-device UI, companion apps, cloud services and APIs. Accessibility follows WCAG 2.2 (free standard, ISO/IEC 40500:2025) -- see `docs/standards/software.md` (advisory -- a citation pointer, not an enforced rule).
- If gstack is installed, delegate software sprints to it rather than duplicating its workflow; Forge owns requirements, evidence and the gate, gstack owns the build loop (advisory workflow guidance -- not itself checked).
- Every claim about a feature working needs a test that runs, not just code that compiles. Write the test from the requirement, not from the implementation (advisory -- caught by review and by `tracing-requirements`'s untested-requirement check, not a software-specific check).
- Security and observability are explicit: state what's logged, what's authenticated, and what secrets handling applies, rather than leaving them implicit in code (advisory -- no automated check parses app code for this).
- Data, security and privacy-by-design questions route to `safety-compliance-engineer`'s `analyzing-risk` and `compliance/` (`analyzing-risk`'s verify entrypoint, check_id `safety.dfmea_ap`, checks the risk rows this produces).
- No claim of "validated" or "production-ready" without the evidence level to back it (`plugins/forge/CONTRACTS.md` §4 in the Forge repo) -- enforced by the wording lint, `forge lint wording`.
