# Scope, headless limits and extension

Everything below was observed with FreeCAD 1.1.3 (`~/.forge/bin/freecadcmd`,
bundled Python 3.11), build123d 0.11.1 and ezdxf 1.4.4 on 2026-09-25. Re-test
after any of them changes.

## What works headlessly (proven by the tests)

- STEP import (`Part.read`) of any solid exported from build123d; principal,
  iso, full section (`DrawViewSection`) and detail (`DrawViewDetail`) views;
  several pages in one freecadcmd run; `TechDraw.writeDXFPage` per page.
- Each view lands on its own DXF layer named after the view object, and each
  dimension on its own layer -- this is what lets the check find "view X" and
  "dimension Y" in the output without guessing.
- `DrawViewDimension` of type DistanceX / DistanceY between projected vertices
  and Diameter / Radius on projected circle edges; `getRawValue()` returns
  TechDraw's own measurement, recorded per dimension in `layout.json`.
- `FormatSpec` accepts literal text around `%.Nf`, so tolerances go into the
  dimension text (`%.2f %%p0.10`). DXF control codes `%%c`/`%%p` survive; raw
  UTF-8 (`±`, `⌀`) is mangled because FreeCAD writes R2000 with a cp1252
  code page.

## Headless gaps and how this skill handles each

| Gap (FreeCAD 1.1.3 headless) | Handling |
|---|---|
| Page PDF/SVG export needs the GUI (issue #5710; ADR-001 §15.3). | DXF page export, PDF rendered from the DXF by ezdxf + matplotlib at the sheet size (1:1 print scale), plus an invisible standard-14 text layer so values are searchable and re-checked. |
| The SVG template (border, title block) is not exported. | Frame, title block, projection symbol and notes are drawn by `compose_sheet.py` on their own layers. |
| View captions, cutting-plane lines, detail circles and section hatching are GUI-side. | Drawn by `compose_sheet.py`; hatching comes from the build123d section of the solid, mapped with the projection TechDraw reported for that view. |
| Diameter/Radius dimension lines and arrows are exported collapsed onto the circle centre (text is placed correctly). | Leader and arrowhead rebuilt from the exported centre, radius and text box. |
| Vertical dimension text is exported unrotated and centred on its line. | Rotated 90 degrees and moved beside the line; the string and all dimension lines are untouched. |
| The dimension line sits 5 mm from the given text position, on a side set by the order of the two references. | References are ordered ascending and the text position is offset by 5 mm (`TD_LINE_OFFSET_MM`). |
| Native tolerance properties (`ArbitraryTolerances`, `OverTolerance`) crashed freecadcmd in the original skill. | Not used; tolerance is part of the dimension text. |
| Hidden edges are exported on the view layer with no line type, i.e. they would print as solid lines. | Hidden lines are not drawn. Internal features are shown with section views. |
| `getVertexByIndex` omits some edge ends in detail views; `makeCosmeticVertex3d` stores Y mirrored. | Missing ends get a 2-D `makeCosmeticVertex` at the projected point (which TechDraw takes as given); every attachment is self-checked (TechDraw value vs the projected span) before it is kept. Cosmetic ends are recorded as `snap: cosmetic` in `layout.json`. |
| With a detail view on the page, freecadcmd finishes all work and then never exits. | `techdraw_sheets.py` flushes and calls `os._exit`. |
| `__name__` is not `"__main__"` under freecadcmd; stdout needs line buffering and UTF-8. | Handled at the top/bottom of `techdraw_sheets.py`. |

When TechDraw cannot attach a dimension at all (e.g. a diameter asked for on
a view where the hole is hidden), the callout falls back to annotation text
with a leader (`DIMTXT_<id>`). It is still verified against the model; it just
has no independent TechDraw value (`dim_<id>_techdraw_vs_model` is absent).

## Not supported (real work, not config)

- Angular dimensions, chamfer / thread / counterbore depth callout symbols,
  surface texture and weld symbols, ordinate and baseline dimensioning.
- Offset, aligned, half and broken-out sections; hatching inside a detail of
  a section (the detail shows the cut outline only).
- Dimensions on pictorial (iso) views; oblique features (a cylinder axis
  neither along nor across the view) fall back to annotation.
- Selectors for cones, tori and free-form faces; dimension axes other than
  the model X/Y/Z.
- Automatic collision avoidance beyond stacking: dense views can overlap text;
  use `side`, `angle`, `offset` and `cell`, or split views over sheets.
- ISO 3098 lettering: text is ezdxf's default font.
- `count` counts coaxial-distinct cylinders of the same radius and direction;
  a fillet of the same radius would be counted too.

## Standards, and what is not claimed

Editions come from `docs/research/R5a-standards-drawings-ipc-accessibility.md`
(ASME Y14.5-2018 (R2024), ISO 1101:2017, ISO 8015:2011, ISO 14405-1:2025,
ISO 2768-1:1989, ISO 22081:2021). The projection symbol follows the usual
ISO 5456-2 / ASME Y14.3 truncated-cone convention, and sheet/lettering
practice follows ISO 128 / ISO 129 in outline only -- **the editions of ISO
5456-2, ASME Y14.3, ISO 128 and ISO 129 were not researched in R5a**; cite
them only after checking. No standard text is reproduced anywhere in this
skill. A passing check is L1 evidence ("computed in CAD"), not a compliance
determination and not release approval.

## The legacy single-view path

Specs without `schema = "forge.drawing/2"` still run `make_drawing.py`: one
top view of a `Part::Box` plate with an optional hole, dimensions found by
value-matching probed edges, title block as annotations. It is kept only so
older specs keep verifying; write new drawings in the v2 schema.

## Extending

- A new selector kind: add parsing in `drawspec.parse_ref`, resolution in
  `model_measure.resolve` (with a `snap` limit and an ambiguity rule), and a
  seeded-wrong test that a mis-aimed selector fails `dim_<id>_resolved`.
- A new annotation: draw it in `compose_sheet.py` on its own layer, read it
  back in `dxf_checks.check_drawing`, and add a test that deleting that layer
  fails the check. Never check an annotation by trusting the generator.
