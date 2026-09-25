# {{PROJECT_NAME}}

A Forge product-engineering project. This file is a table of contents, not a manual -- see `AGENTS.md` for the cross-tool twin (imported below), and `plugins/forge/CONTRACTS.md` in the Forge repo for the binding interfaces.

@AGENTS.md

## Commands

- `make verify` -- run every automatable verification rung (`forge verify --all`).
- `make doctor` -- `forge doctor`: toolchain, MCP lock and file-integrity checks.
- `make test` -- pytest for scripts with logic.
- `make lint` -- `forge lint` (agents, skills, claudemd, wording, manifest).
- `make evidence` -- print the current `evidence/manifest.json` summary.

## Current gate

See `forge.toml` `[project].gate`. Only a human advances it (record in `reviews/Gx.md`); see `docs/standards/gates.md` in the Forge repo for G0-G6 pass criteria.

## Where things live

| What | Where |
|---|---|
| Requirements (EARS) + traceability | `requirements/requirements.md`, `requirements/trace.json` |
| Systems model (SysML v2) | `model/system.sysml` |
| Single source of truth for every dimension/value | `params/params.toml` |
| CAD (build123d, only mechanical-engineer writes here) | `cad/` |
| Circuits as code, KiCad outputs | `ecad/` |
| Firmware | `firmware/` |
| App / cloud / software | `app/` |
| Simulation and analysis | `analysis/` |
| Manufacturing process, DFM, fixtures | `mfg/`, `bom/` |
| Compliance mapping | `compliance/` |
| Tests | `tests/` |
| Evidence ledger (append-only) | `evidence/manifest.json` |
| Gate records, blank human sign-off | `reviews/Gx.md` (see `reviews/_gate-template.md`) |
| Architecture decisions | `docs/decisions/` (see `ADR-template.md`) |
| Open assumptions / risks | `ASSUMPTIONS.md`, `RISKS.md` |
| Release bundles | `release/` |
| Build + check outputs (gitignored, except promoted evidence) | `out/` |

## Pointers

- **Rules** (`.claude/rules/*.md`, path-scoped, load lazily): `mechanical.md`, `electrical.md`, `firmware.md`, `software.md`, `systems.md`, `simulation.md`, `manufacturing.md`, `compliance.md`.
- **Skills**: `/forge:new-project`, `/forge:init` (scaffolding); domain skills load by trigger -- see the Forge plugin's `skills/`.
- **Permissions and sandbox**: `.claude/settings.json` (deny/ask/allow, sandbox baseline -- do not weaken without an ADR).
- **MCP servers**: `.mcp.json` (build123d-mcp, kicad-mcp-pro, both launched only via `forge-mcp-guard`).
- **Verify entrypoints and domain-to-check mapping**: `forge.toml`.
- **Standards**: `docs/standards/` in the Forge repo (gates, per-domain applicability). Never reproduced here verbatim.

## Rules for this file

Keep this file under 100 lines. Encyclopedic content belongs in `docs/`, rules or skills, not here.
