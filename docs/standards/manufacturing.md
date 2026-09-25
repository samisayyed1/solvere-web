# Manufacturing -- standards and applicability

DFM numeric rules are sourced from manufacturer design-guideline pages, not a single formal standard, and often disagree between sources -- always cite the file and row, never restate from memory (`docs/research/R5c-dfm-molding-cnc-sheetmetal.md`, `docs/research/R5d-dfm-additive-snapfit-pcb.md`).

## When each process's rule set applies

| Process | Rule table | Applies when | Source |
|---|---|---|---|
| Injection molding | Wall thickness by resin, draft angle, rib/boss ratios, radii, tolerance | The part is injection molded. | R5c §1 |
| CNC machining | Default tolerance, internal corner radius, pocket depth, min wall, hole depth, thread depth, engraving | The part is CNC milled or turned. | R5c §2 |
| Sheet metal | Min bend radius, min flange, hole-to-bend/edge, K-factor, tolerances, hems | The part is sheet metal (laser/waterjet cut, stamped, or press-braked). | R5c §3 |
| FDM / SLA / SLS / MJF | Wall thickness, overhang, bridge, hole size, clearance, tolerance -- per process | The part is 3D printed; use the table for the *specific* process, never a different one. | R5d §"FDM"/"SLA"/"SLS"/"MJF" |
| Snap-fit permissible strain | Per-material strain values | Any snap-fit feature, in any process/material. | R5d §"Snap-fit permissible strain" |
| PCB fabrication (JLCPCB / PCBWay) | Trace/space, min hole, annular ring, stack-up | Any PCB order from that specific fab house -- rules are vendor-specific. | R5d §"PCB - JLCPCB"/"PCB - PCBWay" |

## What Forge automates

- Per-process DFM checks against the cited rule table (`checking-dfm`), with the specific source row named in the remediation string.
- Cost-driver and tooling-implication notes tied to the chosen process (`manufacturing-engineer`).
- BOM entries with MPN, alternates, lifecycle status and lead time, with single-source parts flagged (`supply-chain-engineer`, `costing-bom`).

## What needs a qualified human

- Final process selection when sources disagree (R5c notes PP/PS/acrylic wall-thickness figures differ even within one vendor's own pages) -- a human picks the conservative bound and records the choice.
- Any commitment of money: a quote, a purchase order, or a fab/vendor upload is `permissions.ask` -- Claude recommends, a human commits spend.
- Yield and process-capability claims at G5 (Pilot/PVT) need real production data, not a DFM-table pass.
