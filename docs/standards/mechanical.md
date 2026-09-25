# Mechanical -- standards and applicability

No standard's text is reproduced here (IPC, ASME, ISO and UL texts are copyrighted -- `docs/research/R5a-standards-drawings-ipc-accessibility.md` §2). This page cites which standard applies when, its current edition as researched on 2026-09-25, and the source file for the exact citation. Design values (draft angles, wall minimums, radii) live in `checking-dfm`'s rule tables, sourced from `docs/research/R5c-dfm-molding-cnc-sheetmetal.md` and `docs/research/R5d-dfm-additive-snapfit-pcb.md` -- cite those files, never invent a number.

## When each standard applies

| Standard | Current edition (2026-09-25) | Applies when | Source |
|---|---|---|---|
| ASME Y14.5 | Y14.5-2018 (R2024); revision in progress | Any drawing or GD&T intent carries geometric tolerances. | R5a §1 |
| ASME Y14.5.1 | Y14.5.1-2019 | A tolerance needs a mathematical (not graphical) definition. | R5a §1 |
| ISO 8015 | ISO 8015:2011 | The project follows ISO tolerancing (GPS) rather than ASME. | R5a §1 |
| ISO 1101 | ISO 1101:2017 | Geometrical tolerancing under the ISO GPS system. | R5a §1 |
| ISO 14405-1 | ISO 14405-1:2025 (replaces the withdrawn 2016 edition) | Linear size tolerancing under ISO GPS. | R5a §1 |
| ISO 2768-1 / ISO 22081 | ISO 2768-1:1989 (revision pending, stage 60.00 as of research date); ISO 22081:2021 replaces ISO 2768-2 | General (un-toleranced) linear/angular tolerances. | R5a §1 |
| DFM rule tables (injection molding, CNC, sheet metal) | Manufacturer design-guideline pages, dated per-row | Any part destined for that process; process-specific, never mixed. | R5c |
| DFM rule tables (FDM, SLA, SLS, MJF, snap-fit strain) | Manufacturer design-guideline pages, dated per-row | Any part destined for that additive process, or a snap-fit feature in any material. | R5d |

## What Forge automates

- Numeric DFM checks against the process-specific rule tables (`checking-dfm`), with the source row cited.
- Wall thickness, clearance, draft, and hole/boss ratio checks against `params/params.toml`, scripted (`verifying-geometry`).
- Worst-case and RSS tolerance stacks (`stacking-tolerances`), with GD&T intent stated per ASME Y14.5 conventions.
- Solid validity, watertightness, mass properties, and bounding-box/volume range checks.

## What needs a qualified human

- Any GD&T scheme that will appear on a released drawing: a qualified mechanical engineer signs it. Forge states intent; it does not certify a drawing.
- Choosing which tolerance standard (ASME vs. ISO GPS) governs the project -- record the choice in an ADR.
- Reconciling disagreeing DFM sources (R5c/R5d note several: e.g. PP wall thickness ranges differ between Protolabs' own pages) -- a human picks the conservative bound and records why.
- Any claim that a part is "validated" (needs L4 physical measurement) or "production-ready"/"certified" (needs L5 human or accredited sign-off).
