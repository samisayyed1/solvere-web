---
paths:
  - "requirements/**"
  - "model/**"
---

# Systems engineering

- Requirements are EARS sentences with an ID (`REQ-<AREA>-<NNN>`), a `Rationale:` and a `Verify:` method (inspection|analysis|demo|test) -- `requirements/requirements.md`. Lint: `forge-python skills/writing-requirements/scripts/verify.py`.
- Requirement **text and IDs belong to systems-engineer and humans**. Every other agent may change only `status`, `evidence` and `tests` in `requirements/trace.json` -- enforced by a diff lint (PostToolUse on `requirements/`).
- The traceability graph (`trace.json`) must have no orphans and no untested requirements before a gate: `forge-python skills/tracing-requirements/scripts/verify.py`.
- The systems model (`model/system.sysml`, SysML v2 textual notation) must parse with zero errors: `forge-python skills/modeling-systems/scripts/verify.py` (`spec42 check`).
- Interfaces and budgets (power, mass, thermal, cost, link) are drafted at G0 and carried forward -- keep them in the model or `params/params.toml`, not scattered in prose.
- An impossible or ambiguous requirement gets flagged and asked about, never silently reinterpreted.
- Standards: `docs/standards/systems.md` (INCOSE SEH, NASA SE Handbook, EARS paper).
