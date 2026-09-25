---
paths:
  - "ecad/**"
  - "circuits/**"
---

# Electrical (ECAD)

- Circuits are code: tscircuit primary, SKiDL fallback (atopile deferred -- ADR-001 D11). Compile to KiCad; GUI is for inspection and last-resort operations only (advisory -- a GUI edit outside `ecad/` is not itself blocked, only writes under `ecad/**` by the wrong agent are, per the mechanical-engineer-only rule below).
- Every component value, tolerance and rating comes from `params/params.toml`, with a datasheet page reference or a caliper/DMM measurement procedure when the datasheet is silent (a verified value's edit is denied outside `forge params set --justification` by a PreToolUse hook, CONTRACTS §2).
- Run ERC before trusting a schematic change, and DRC plus the fab house's DFM rules before any layout is called done: `forge-python skills/checking-ecad/scripts/verify.py --project . --changed ecad/ --fast` (also runs via the PostToolUse `ecad/` hook, ERC only, fast).
- Critical nets (regulators, protection, timing) get an ngspice simulation with a stated result against spec, not just a schematic review -- `designing-circuits`'s verify entrypoint (check).
- ngspice always runs sandboxed (no network, writes only to `out/`) -- `-n` does not disable `.control shell`, so a netlist lint also rejects `shell` blocks.
- Component selection records lifecycle status and at least one alternate; flag single-source parts (advisory -- no automated check reads lifecycle-status fields yet; caught in review).
- kicad-mcp-pro is optional and read-only (`KICAD_MCP_OPERATING_MODE=readonly`); never call `lib_get_bom_with_pricing` (network, denied -- enforced by `forge-mcp-guard`'s server lock, CONTRACTS §13).
- Fabrication needs a human sign-off (`permissions.ask` on vendor-upload/quote/order commands) and, before release, ERC/DRC evidence plus `release/APPROVAL.toml` -- both gate the release bundle (`releasing-designs`).
- Standards and their current editions: `docs/standards/electrical.md`. Never reproduce IPC/ASME/ISO/UL text -- cite the clause (advisory -- no automated check for copied standards text).
