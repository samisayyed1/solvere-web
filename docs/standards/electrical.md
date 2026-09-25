# Electrical -- standards and applicability

No IPC/UL/IEC text is reproduced (IPC's own front matter forbids feeding its standards into AI systems -- `docs/research/R5a-standards-drawings-ipc-accessibility.md` §2). This page cites which standard applies when and its current edition as researched on 2026-09-25.

## When each standard applies

| Standard | Current edition (2026-09-25) | Applies when | Source |
|---|---|---|---|
| IPC-2221 | Rev C, Dec 2023 | Generic PCB design (trace width/spacing, current capacity). | R5a §1 |
| IPC-2222 | Rev B, Oct 2020 | Rigid PCB sectional design standard. | R5a §1 |
| IPC-7351 / IPC-7352 | 7351 Rev B (no longer maintained); 7352 is its de facto successor, Jul 2023 | Land pattern / footprint generation. | R5a §1 |
| IPC-A-610 | Rev J, Mar 2024 (Rev K in final draft) | Acceptability of electronic assemblies (post-assembly inspection). | R5a §1 |
| J-STD-001 | Rev J, Apr 2024 (Rev K in final draft) | Soldering requirements for electronic assemblies. | R5a §1 |
| UL 94 | 7th edition, 28 Feb 2023 (revised 2 Jul 2026) | Flammability classification of enclosure/PCB materials. | R5a §1 |
| IEC 60695-11-10 / -11-20 | Ed. 2.0 (2013 / 2015) | The IEC-side flame test method matching UL 94 HB/V and 5VA/5VB. | R5a §1 |
| CISPR 32 / EN 55032 | CISPR 32 Ed. 2.1 (2019, stability date 2026); EN 55032:2015+A11+A1:2020 | Multimedia equipment emissions (EMC). | R5e §"Standards table" |
| CISPR 35 / EN 55035 | CISPR 35 Ed. 1.0 (2016, stability date 2026); EN 55035:2017+A11:2020 | Multimedia equipment immunity (EMC). | R5e §"Standards table" |

Electronics standards applicability for regulatory purposes (RED, FCC, ISED, RoHS, REACH) is a compliance question -- see `docs/standards/compliance.md`, not this page.

## What Forge automates

- ERC and DRC via `kicad-cli`, plus the fab house's DFM rules, in `checking-ecad`.
- ngspice simulation of critical nets (regulators, protection, timing) against the stated spec, with a sanity check, in `designing-circuits`.
- PCB fabrication DFM checks (trace/space, min hole, annular ring) against `docs/research/R5d-dfm-additive-snapfit-pcb.md`'s JLCPCB/PCBWay tables.
- Component lifecycle and single-source flags in the BOM (`supply-chain-engineer`).

## What needs a qualified human

- Any footprint or land pattern that departs from IPC-7351/7352 guidance needs an engineer's sign-off, not just a CAD-tool default.
- EMC pre-compliance is a *risk estimate*, not a test: CISPR 32/35 pass/fail needs an accredited lab (see `docs/standards/compliance.md`).
- Fabrication release (Gerber export, vendor upload) is `permissions.ask` -- a human confirms every fab order.
- kicad-mcp-pro's `lib_get_bom_with_pricing` tool is denied by policy (network call to a pricing API); pricing lookups are a human or a separate, explicitly-approved step.
