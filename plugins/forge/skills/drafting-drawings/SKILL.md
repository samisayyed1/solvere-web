---
name: drafting-drawings
description: Produce dimensioned engineering drawings (multi-view, multi-sheet DXF + PDF with section and detail views, critical dimensions with tolerances, GD&T frames, title block, projection symbol) of any STEP or build123d part, headlessly via FreeCAD TechDraw, and verify every critical dimension against an independent build123d measurement of the model. Use when the user asks for a "drawing", "dwg", "print", "PDF drawing", "title block", "dimensioned drawing", "section view", "GD&T on the drawing", or when cad/drawings/*.toml changes. Do NOT use to create or change the 3-D model (modeling-cad-parts), to check the model itself against requirements (verifying-geometry), for tolerance stack-ups (stacking-tolerances), or for renders (rendering-products) -- a render is never a substitute for a dimensioned drawing, and a drawing never changes the model.
paths:
  - "cad/drawings/**"
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(forge-python ${CLAUDE_SKILL_DIR}/scripts/verify.py:*), Bash(~/.forge/bin/forge-python ${CLAUDE_SKILL_DIR}/scripts/verify.py:*), Bash(freecadcmd ${CLAUDE_SKILL_DIR}/scripts/techdraw_sheets.py:*), Bash(freecadcmd ${CLAUDE_SKILL_DIR}/scripts/make_drawing.py:*)
---

# Drafting drawings

**Non-negotiable rules, read first:**

1. **The drawing is derived from the model and params, never the other way.**
   No number on a sheet is typed by hand: every critical dimension names a
   `params/params.toml` key and a geometric selector, the value shown is what
   TechDraw measures on the projected model, and `verify.py` fails the drawing
   if it disagrees with the params nominal or with the model. If a drawing is
   "wrong", fix the model or params and regenerate -- never edit the DXF.
2. **A drawing is a communication artifact; its dimensions are verified
   against the model.** `verify.py` re-measures each critical dimension on the
   exact B-rep with build123d (independent of TechDraw), reads the output DXF
   (and the PDF text layer) back, and fails if a dimension is missing, differs
   by more than **0.01 mm**, lacks its tolerance, or a declared view, marker,
   title-block field or the projection symbol is missing or contradicts the
   spec -- or if regenerating from the same inputs gives a different DXF
   entity set. A PDF that "looks right" is not evidence; the check JSON is.
3. **Human sign-off before release.** Every sheet carries `NOT FOR MANUFACTURE
   UNTIL SIGNED` and an empty approval box. A passing check is L1 evidence
   ("computed in CAD", CONTRACTS §4), not approval, not a compliance
   determination. Datums, GD&T and the general tolerance class are design
   decisions a qualified engineer signs (R5a §2); Forge checks they are well
   formed and drawn, not that they are right for the function.
4. **Headless route only.** FreeCAD's TechDraw page PDF/SVG export needs the
   GUI (issue #5710) -- do not try. The pipeline is TechDraw views + dimensions
   -> `TechDraw.writeDXFPage` -> ezdxf finishing (title block, symbol,
   section/detail markers, hatching, frames) -> ezdxf/matplotlib PDF at sheet
   size (ADR-001 §15.3). Say so when you report: the PDF is a faithful render
   of the DXF, not FreeCAD's own PDF.
5. **Ask, don't guess.** If a critical dimension, its tolerance, the
   projection method or the general tolerance class is not stated, ask. Do
   not invent tolerances to make a drawing look complete.
6. **Cite standards by edition from R5a, never reproduce their text.** ASME
   Y14.5-2018 (R2024), ISO 1101:2017, ISO 8015:2011, ISO 14405-1:2025,
   ISO 2768-1:1989 (revision pending), ISO 22081:2021. ISO 2768-2 (`-mK`
   style classes) is withdrawn -- the check fails it. Editions of ISO 128,
   ISO 129, ISO 5456-2 and ASME Y14.3 were not researched; do not cite a year
   for them until someone checks.

## Workflow

1. Confirm the model builds from params (`verifying-geometry` passes) --
   drawing a wrong model only documents the error.
2. Write `cad/drawings/<name>.toml` (`schema = "forge.drawing/2"`). Full
   schema: `references/spec-schema.md`. Start from the closest worked example
   in `examples/project/cad/drawings/` (L bracket; flanged bushing with a
   counterbore and section A-A; two-sheet enclosure with section and 4:1
   detail).
3. Run the check (it generates the sheets, then verifies them):

   ```
   ~/.forge/bin/forge-python ${CLAUDE_SKILL_DIR}/scripts/verify.py --project <root> [--changed cad/drawings/<name>.toml]
   ```

4. Fix every failing measurement using its `remediation`. Re-run until it
   passes. Read the PDF once for layout (overlapping text is a layout issue
   the check does not catch -- adjust `side`, `angle`, `offset`, `cell` or
   split views across `[[sheet]]`s).
5. Record evidence (`forge evidence add`, domain `mech`) pointing at
   `out/verify/mech.drawing_<name>.json`, `out/drawings/<name>/report.json`
   and the sheet PDFs. Hand the PDF to a human for sign-off.

`--recheck` verifies the DXF/PDF already in `out/drawings/<name>/` without
rewriting them (the reproducibility run still happens) -- use it when a
drawing was touched outside Forge. No `cad/drawings/*.toml` means `[SKIP]`,
exit 0. `--changed` also picks up every drawing whose `[model]` module, STEP
or params file is among the changed paths (a model change makes a drawing
stale). Exit 1 = a drawing failed; exit 2 = bad spec, missing tool or a
generator crash (never a pass).

## Minimal spec

```toml
schema = "forge.drawing/2"

[drawing]
title = "L MOUNTING BRACKET"
number = "FX-1001"
rev = "A"
material = "EN AW-6061-T6"
units = "mm"
general_tolerance = "ISO 2768-m"
author = "forge"
date = "2026-09-25"
projection = "third"            # or "first"; drawn as the symbol, drives view placement
sheet_size = "A3"

[model]
module = "cad/l_bracket.py"     # build(params=...) ; or step = "cad/part.step"

[[sheet]]
scale = "1:1"
views = ["front", "top", "right", "iso"]

[[view]]
id = "front"
kind = "front"
# ... top, right, iso; sections: kind = "section", base, label, origin, normal
# details: kind = "detail", base, label, center, radius, scale

[[dimension]]
id = "base_length"
param = "bracket.base_length"   # the nominal lives in params, not here
requirement = "REQ-MECH-001"
view = "front"
type = "linear"                 # linear | diameter | radius
axis = "X"
from = { plane = "X", at = "min" }
to = { plane = "X", at = "max" }
tol = 0.2                       # required: +/-, or { plus, minus[, style = "limits"] }
```

Selectors pick model features by geometry: `plane` (normal axis + min/max/
coordinate), `cylinder` (axis + a point on its wall), `vertex`. Coordinates
may be params expressions (`"bracket.width/2"`). See the schema reference for
datums, feature control frames, notes, sides/angles and grid cells.

## Output

`out/drawings/<name>/`:

| File | What |
|---|---|
| `sheet<N>.dxf` | The drawing, one per sheet (layers listed in the schema reference). |
| `sheet<N>.pdf` | Same sheet, page = sheet size, prints at the stated scale; searchable text layer. |
| `sheet<N>.techdraw.dxf` | Raw `writeDXFPage` output before finishing (for debugging). |
| `layout.json` | Per view: placement and TechDraw's 3-D -> 2-D projection; per dimension: how it was attached and TechDraw's own value. |
| `report.json` | Per dimension: params value, build123d value, TechDraw value; entity-set hash per sheet. |
| `job.json`, `model.step`, `freecadcmd.log` | The exact freecadcmd input and its log. |

`out/verify/mech.drawing_<name>.json` holds the measurements (`forge.check/1`).

## What the check measures (all fail closed)

| Measurement | Fails when |
|---|---|
| `dim_<id>_present` | The callout is missing, unparseable, duplicated, or has the wrong symbol / count prefix. |
| `dim_<id>_drawing_vs_model` | Drawn nominal differs from the build123d measurement by > 0.01 mm. |
| `dim_<id>_techdraw_vs_model`, `_dxf_geometry_vs_model` | TechDraw's value (from `layout.json`, and re-read from the DXF extension-line origins / view scale) differs from build123d by > 0.01 mm -- attached to the wrong geometry, or the DXF was edited. |
| `dim_<id>_annotation_fallback` | TechDraw could not attach it and the spec did not opt in with `allow_annotation = true`, or the leader does not touch the feature. |
| `dim_<id>_params_vs_model` | The model does not match its params nominal (model not built from params, or wrong key bound). |
| `dim_<id>_tolerance`, `_tolerance_vs_params` | Tolerance missing/wrong on the sheet, or differs from params `tol`. |
| `dim_<id>_feature_count`, `_resolved`, `_in_pdf` | "NX" count wrong; selector matches no feature; value missing from the PDF text. |
| `view_<id>_present`, `_extent_error`, `_orientation`, `_markers` | View not drawn; outline != model extents x scale (wrong scale or section side); line ends off the model's edges projected in the declared direction (mirrored / wrong view); section line / detail circle / label / hatch missing. |
| `sheet<N>_title_block_fields`, `_projection_symbol`, `_view_arrangement` | A title-block field missing; symbol missing or its geometry contradicts the declared method; principal views on the wrong side or misaligned. |
| `sheet<N>_reproducible`, `_layout_overflow`, `_pdf_*` | Regenerated DXF entity set (entities + layer states) differs; views do not fit the sheet; PDF missing or lacks the exact strings. |
| `gdt_<id>_frame`, `datum_<X>_symbol`, `notes_present`, `general_tolerance_class_current` | Frame/datum/notes missing; a withdrawn ISO 2768-2 class. |

## When TechDraw cannot attach a dimension

A dimension is normally a real `TechDraw::DrawViewDimension` on the view's
projected (hidden-line-removed) vertices or circle. If a reference point has
no projected vertex, a cosmetic vertex is placed at its projection
(`snap: cosmetic` in `layout.json`; the attachment is self-checked). If no
attachment is possible (feature hidden in that view, or oblique), the callout
becomes annotation text with a leader on layer `DIMTXT_<id>`. That fails the
check unless the dimension sets `allow_annotation = true` (it has no
independent TechDraw value); with the opt-in it is still compared with the
model and its leader must touch the feature. Prefer a view where the feature
is seen edge-on or as a circle.

## Limits you must state when reporting

- No hidden lines (TechDraw exports them without a line type); use sections.
- Only full planar sections; the detail of a section is not hatched.
- No angular, thread, chamfer or surface-texture callouts; no dimensions on
  the iso view; selectors for planes, cylinders and vertices only.
- Dimension placement is stacking, not collision-free layout -- read the PDF.
- Default ezdxf font, not ISO 3098 lettering.
- Full list and the headless workarounds behind them: `references/scope-and-extension.md`.

## Legacy specs

Specs without `schema = "forge.drawing/2"` (the original single top view of a
plate with one hole, `[part]` + `[[dimension]] value_mm`) are **refused**
(exit 2, `verify.py`'s `_run_one`) with a migration message: they predate
`[model]` (a real part to measure the drawing against) and the v2 checks
(tolerance >= 0, a valid scale, GD&T, reproducibility), so they are never
silently run through their own weaker path (S14). Migrate them to v2 --
see "File format" above and `references/spec-schema.md`. `scripts/make_drawing.py`
(the old FreeCAD generator for this schema) is unused dead code, kept only
so the migration message's history is easy to find; do not write new legacy specs.
