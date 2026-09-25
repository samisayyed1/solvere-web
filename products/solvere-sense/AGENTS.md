# Solvere Sense ceiling pod -- agent instructions

Cross-tool twin of `CLAUDE.md` (imported there via `@AGENTS.md` per ADR-001 §4, for AI coding tools that read `AGENTS.md` natively). Keep both files consistent; this one carries the substance, `CLAUDE.md` is the pointer.

## What this project is

A Forge product-engineering project. Forge's operating principle: **verification is the product**. Work is done only when a check that can fail has passed and its evidence is saved (`evidence/manifest.json`). Nothing is called "validated" without L4 physical-test evidence, or "certified"/"production-ready" without L5 sign-off from a qualified human or accredited body.

## Ground rules for any agent working here

1. **Every claim needs a check that can fail.** Before writing "this meets the requirement," run the relevant `forge verify` entrypoint (see `forge.toml`) and cite `out/verify/<check_id>.json`.
2. **The maker is never the checker.** Don't grade your own CAD, circuit, firmware or requirement. Independent review runs in a fresh context with read-only tools.
3. **Params are the single source of truth.** Every dimension, tolerance and value used in CAD, ECAD, firmware or analysis comes from `params/params.toml`. Never hard-code a value that belongs there. Changing a `status = "verified"` param requires a sourced justification (`forge params set --justification "..."`); direct edits are blocked by a hook.
4. **Requirements are EARS, with an ID and a verification method.** `requirements/requirements.md` format: `REQ-<AREA>-<NNN>`, an EARS sentence, `Rationale:`, `Verify:` (inspection|analysis|demo|test). Outside the systems-engineer role, agents may change only `status`, `evidence` and `tests` in `requirements/trace.json` -- never requirement text or IDs.
5. **Only mechanical-engineer writes `cad/`.** Enforced by a PreToolUse hook keyed on `agent_type`.
6. **Gates are human-only.** `reviews/Gx.md` always ships with a blank sign-off line. Never fill it in, and never mark a gate as passed on request -- decline and explain what evidence is missing.
7. **Nothing below L4 is "validated," nothing below L5 is "certified" or "production-ready."** State the evidence level on every design claim (L0 claimed ... L5 certified -- see `plugins/forge/CONTRACTS.md` §4 in the Forge repo).
8. **Ask when a requirement is ambiguous, conflicting, or missing a number.** Never guess a dimension, tolerance, rating or standard silently.
9. **Safety, money and fabrication decisions need a human sign-off.** Fab/quote/flash commands are gated by `permissions.ask` in `.claude/settings.json` and by `release/APPROVAL.toml` for release-type actions.
10. **MCP servers only via the guard.** `build123d-mcp` and `kicad-mcp-pro` run only through `/home/user/solvere-web/plugins/forge/bin/forge-mcp-guard`, never launched directly -- see `.mcp.json`.

## Where things live

See `CLAUDE.md` for the full table. In short: requirements and the systems model under `requirements/` and `model/`; every dimension in `params/params.toml`; domain work under `cad/`, `ecad/`, `firmware/`, `app/`, `analysis/`, `mfg/`, `bom/`, `compliance/`; evidence in `evidence/manifest.json`; gate records in `reviews/`; decisions in `docs/decisions/`.

## Verification ladder

Syntax -> build -> validity -> numeric requirement checks -> physics (analysis/simulation/HIL) -> visual inspection (question-first) -> independent evaluator -> red-team -> human -> physical test. `make verify` runs every automatable rung; each result lands in `evidence/manifest.json`.
