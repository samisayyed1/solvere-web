---
paths:
  - "app/**"
  - "services/**"
---

# Software (apps, cloud, APIs)

- Covers on-device UI, companion apps, cloud services and APIs. Accessibility follows WCAG 2.2 (free standard, ISO/IEC 40500:2025) -- see `docs/standards/software.md`.
- If gstack is installed, delegate software sprints to it rather than duplicating its workflow; Forge owns requirements, evidence and the gate, gstack owns the build loop.
- Every claim about a feature working needs a test that runs, not just code that compiles. Write the test from the requirement, not from the implementation.
- Security and observability are explicit: state what's logged, what's authenticated, and what secrets handling applies, rather than leaving them implicit in code.
- Data, security and privacy-by-design questions route to `safety-compliance-engineer`'s `analyzing-risk` and `compliance/`.
- No claim of "validated" or "production-ready" without the evidence level to back it (`plugins/forge/CONTRACTS.md` §4 in the Forge repo).
