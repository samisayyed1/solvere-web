---
paths:
  - "ecad/**"
  - "circuits/**"
---

# Electrical (ECAD)

- Circuits are code: tscircuit primary, SKiDL fallback (atopile deferred -- ADR-001 D11). Compile to KiCad; GUI is for inspection and last-resort operations only.
- Every component value, tolerance and rating comes from `params/params.toml`, with a datasheet page reference or a caliper/DMM measurement procedure when the datasheet is silent.
- Run ERC before trusting a schematic change, and DRC plus the fab house's DFM rules before any layout is called done: `forge-python skills/checking-ecad/scripts/verify.py --project . --changed ecad/ --fast` (also runs via the PostToolUse `ecad/` hook, ERC only, fast).
- Critical nets (regulators, protection, timing) get an ngspice simulation with a stated result against spec, not just a schematic review -- `designing-circuits`'s verify entrypoint.
- ngspice always runs sandboxed (no network, writes only to `out/`) -- `-n` does not disable `.control shell`, so a netlist lint also rejects `shell` blocks.
- Component selection records lifecycle status and at least one alternate; flag single-source parts.
- kicad-mcp-pro is optional and read-only (`KICAD_MCP_OPERATING_MODE=readonly`); never call `lib_get_bom_with_pricing` (network, denied).
- Fabrication needs a human sign-off (`permissions.ask` on vendor-upload/quote/order commands) and, before release, ERC/DRC evidence plus `release/APPROVAL.toml`.
- Standards and their current editions: `docs/standards/electrical.md`. Never reproduce IPC/ASME/ISO/UL text -- cite the clause.
