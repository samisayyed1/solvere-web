# Stage gates

Source: `docs/brief/FORGE-BRIEF.md` §4, ADR-001 §14. **Only a human passes a gate.** Claude may recommend PASS/FAIL/BLOCKED (via `verification-evaluator`'s verdict and the `gate-review` workflow), but the sign-off line in `reviews/Gx.md` is always left blank by every agent, and a PreToolUse hook blocks agent edits to a filled sign-off line.

## G0-G6

| Gate | Name | What passes it |
|---|---|---|
| G0 | Discovery & requirements freeze | Every requirement has a verification method (inspection/analysis/demo/test); interfaces and budgets (power, mass, thermal, cost, link) are drafted. |
| G1 | Concept / PDR | Concept tournament done (`exploring-concepts`); architecture chosen; top risks identified with mitigations in `RISKS.md`. |
| G2 | Detailed design / CDR | All automated checks green (`make verify`); DFMEA done; tolerance stacks and key simulations done. |
| G3 | EVT | Prototypes built and measured; `params/params.toml` values updated from measurements (`status = "measured"` or `"verified"`); assumptions in `ASSUMPTIONS.md` retired against real data. |
| G4 | DVT | Every requirement verified at L4 (physically tested, with data); compliance pre-scans done; reliability tests done. |
| G5 | PVT | Pilot production; yield and process capability measured; fixtures built; final BOM and cost roll-up. |
| G6 | Launch | Release bundle assembled (STEP/STL/drawings, Gerbers/fab outputs, BOM, firmware binaries with hashes, test reports, evidence manifest, changelog, git SHA) and any applicable certifications attached. |

## Exact pass criteria (expand per project in the gate record)

A gate record is never "PASS" merely because every automated check is green -- automated checks are necessary, not sufficient. The record must also carry the reviewer verdict and an explicit human decision.

- **G0:** `forge lint ears` and `forge trace` both pass with zero orphans and zero untested requirements; every `REQ-*` has a `Verify:` method; a drafted budget line exists for every quantity the brief calls out (power, mass, thermal, cost, link where applicable).
- **G1:** at least the target concept count was generated and scored in a Pugh matrix (`exploring-concepts`); a top-2 report exists; the owner has chosen one; `RISKS.md` lists the top risks for the chosen concept with a mitigation each.
- **G2:** `make verify` (every domain's ladder up to `numeric`/`validity`) is green; DFMEA exists in `analysis/` or `compliance/` with S/O/D ratings; `stacking-tolerances` has run on every toleranced interface; key simulations (`running-fea`, `designing-circuits`) have hand-calc cross-checks and convergence studies attached.
- **G3:** at least one prototype exists per major subsystem; `params/params.toml` shows `status = "measured"` (with `evidence`) for every value that was previously `"assumed"` and is now measurable; `ASSUMPTIONS.md` "Retired" table is non-trivial.
- **G4:** every `REQ-*` in `requirements/trace.json` has `status = "verified"` with `evidence` pointing at L4 entries in `evidence/manifest.json`; `compliance/` has a pre-scan plan per `mapping-compliance`, explicitly marked "not a compliance determination" where applicable.
- **G5:** a documented pilot run with yield and process-capability data; fixtures exist and are referenced; `bom/` reflects the final, costed BOM at the pilot volume tier.
- **G6:** `releasing-designs` has produced the versioned bundle in `release/`, with a checksum manifest and `release/APPROVAL.toml` signed by a human; wording lint (`forge lint wording`) passes on every `validated`/`certified`/`production-ready` claim in the bundle.

## Each gate record contains

Per CONTRACTS.md §7 and `reviews/_gate-template.md`:

1. **Criteria** -- the pass criteria above, expanded for this project.
2. **Evidence links** -- `evidence/manifest.json` entry ids and `out/verify/*.json` paths, one row per criterion.
3. **The evaluator verdict** -- the `forge.verdict/1` JSON block from `verification-evaluator`, pasted unedited.
4. **Red-team findings** -- the `forge.verdict/1` JSON block from `red-team`, pasted unedited.
5. **Open risks** -- cross-referenced from `RISKS.md` by id.
6. **A blank human sign-off line** -- `Human sign-off: ____ Name: ____ Date: ____ Decision: PASS / FAIL`.

## Wording discipline

"Validated" needs L4 evidence or higher; "certified" or "production-ready" needs L5 (CONTRACTS.md §4). This applies inside every gate record, not only in `release/`.
