# Drawing spec schema -- `forge.drawing/2`

A drawing spec lives at `cad/drawings/<name>.toml`. It says **what** the sheet
must show and **which model feature** each critical dimension belongs to. It
never holds a dimension value: values come from the model (measured) and from
`params/params.toml` (the nominal the model is built from). The executable
form of this page is `scripts/drawspec.py`; if they ever disagree, the code
wins and this page is the bug.

Worked examples (all verified): `examples/project/cad/drawings/{l_bracket,flanged_bushing,enclosure}.toml`.

Units: millimetres everywhere. Any length may be a number or a string
expression over params keys (`"bracket.width/2 - bracket.base_hole_pitch/2"`;
numbers, dotted params keys, `+ - * /`, parentheses -- nothing else is
evaluated). Text fields must be ASCII (FreeCAD writes DXF R2000).

## Top level

```toml
schema = "forge.drawing/2"      # required; without it the old single-view plate path runs
```

## `[drawing]` -- title block (every field required unless marked)

| Key | Meaning |
|---|---|
| `title` | Part name. |
| `number` | Part / drawing number. |
| `rev` | Revision. |
| `material` | Material callout (free text). |
| `units` | Must be `"mm"`. |
| `general_tolerance` | `"ISO 2768-f"`, `-m`, `-c` or `-v` (ISO 2768-1:1989, R5a §1). A geometric class letter (`-mK`) is accepted by the parser but **fails** the check: ISO 2768-2 was withdrawn in 2021 and replaced by ISO 22081 (R5a §1-2). R5a also records that a new single-part ISO 2768 was at stage 60.00 on 2026-06-02 -- recheck before release. |
| `tolerancing_standard` | Optional; **required** when any `[[datum]]`/`[[gdt]]` exists, because a frame's meaning depends on it. Cite the edition, e.g. `"ASME Y14.5-2018"` or `"ISO 1101:2017, ISO 8015:2011"` (R5a §1). Do not mix ASME and ISO conventions on one sheet (R5a §2). |
| `author` | Drawn by. |
| `date` | `YYYY-MM-DD`, fixed in the spec (so output is reproducible; no clock is read). |
| `projection` | `"first"` or `"third"`. Drawn as the truncated-cone symbol in the title block and used to arrange the principal views. |
| `sheet_size` | `A4`, `A3`, `A2`, `A1`, `A0` (ISO), `ANSI-A`, `ANSI-B`, `ANSI-C`; landscape. |
| `signoff` | Optional; default `"NOT FOR MANUFACTURE UNTIL SIGNED"`. Must keep the words `NOT FOR MANUFACTURE`. An empty `APPROVED (SIGN + DATE)` box is always drawn. |
| `name` | Optional output name (default: file stem). Output goes to `out/drawings/<name>/`. |

## `[model]`

```toml
[model]
module = "cad/l_bracket.py"     # build123d module exposing build(params=...)   -- or --
# step = "cad/l_bracket.step"   # a STEP file (released or supplied part)
params = "params/params.toml"   # optional, this is the default
```

The module is loaded with `forge_cad.load.load_part(..., params=...)`, so the
part is built from the same params the drawing is checked against.

## `[[sheet]]`

```toml
[[sheet]]
scale = "1:1"                   # "2:1", "1:2", ... ; printed in the title block
views = ["front", "top", "right", "iso"]
```

Every declared view must be on exactly one sheet. Sheets are numbered in
file order (`SHEET 1 OF 2`, ...). Notes print on sheet 1.

## `[[view]]`

| Key | For | Meaning |
|---|---|---|
| `id` | all | Lower-case identifier; the DXF layer is `View_<id>`. |
| `kind` | all | `front`, `rear`, `top`, `bottom`, `right`, `left` (principal), `iso`, `section`, `detail`. |
| `scale` | optional | Overrides the sheet scale for this view (required for `detail`). |
| `cell` | iso/section/detail | Optional `[column, row]` on the view grid (front = `[0, 0]`, row up). Principal views are always placed by the projection method. |
| `direction`, `x_direction` | iso | Optional other pictorial direction (default iso: `[1,-1,1]` / `[1,1,0]`). |
| `base` | section, detail | View the cutting-plane line / detail circle is drawn on. |
| `label` | section, detail | One capital letter (not I, O, Q). |
| `origin`, `normal` | section | A point on the cutting plane and its normal (`"-Y"` or a 3-vector). The view looks along `-normal`; the material on the `+normal` side is removed (verified against TechDraw); arrows on the cutting line point along `-normal`. The plane must be seen edge-on in the base view. |
| `center`, `radius` | detail | Model point (3-D) at the centre of the detail circle, and its radius in model mm. |

Principal-view directions (TechDraw `Direction` = towards the viewer; paper up = direction x x_direction):
front `(0,-1,0)/(1,0,0)`, rear `(0,1,0)/(-1,0,0)`, top `(0,0,1)/(1,0,0)`,
bottom `(0,0,-1)/(1,0,0)`, right `(1,0,0)/(0,1,0)`, left `(-1,0,0)/(0,-1,0)`.
Third angle puts the top view above the front view and the right view to its
right; first angle puts them below / to the left. The check reads the view
positions back from the DXF and fails a sheet whose arrangement contradicts
the declared method.

## Selectors

A selector names a model feature by geometry, resolved on the exact B-rep in
build123d (`scripts/model_measure.py`), never by TechDraw's edge numbering.

| Selector | Picks | Position used by a linear dimension |
|---|---|---|
| `{ plane = "X", at = "min" }` | Planar faces with outward normal along +/-X (`"+X"`/`"-X"` restrict the sense); `at` = `"min"`, `"max"` or a coordinate (nearest within `snap`, default 0.5 mm). | The plane's coordinate. |
| `{ cylinder = "Z", near = [x, y, z] }` | The cylindrical face whose axis is parallel to Z and is nearest to the point (a point **on** the hole/boss wall). Fails if nothing is within `snap`, or if two different cylinders are equally near (ambiguous). | The axis position (e.g. a hole centre). |
| `{ vertex = [x, y, z] }` | The model vertex nearest to the point (within `snap`). | The vertex coordinate. |

A selector that matches nothing is not a spec error -- it is a **failing
measurement** (`dim_<id>_resolved`): the model no longer has the feature the
drawing calls out.

## `[[dimension]]` -- critical dimensions

```toml
[[dimension]]
id = "base_hole_dia"                 # layer Dim_<id> in the DXF
param = "bracket.base_hole_dia"      # params key holding the nominal (required)
requirement = "REQ-MECH-006"         # requirement id (required)
view = "top"                         # principal, section or detail view (not iso)
type = "diameter"                    # linear | diameter | radius
count = 2                            # optional "2X" callout; checked against the model
of = { cylinder = "Z", near = ["bracket.base_hole_x + bracket.base_hole_dia/2", 12, 3] }
tol = { plus = 0.1, minus = 0.0 }    # required; number = +/-, or {plus, minus[, style = "limits"]}
decimals = 2                         # optional, 2..4 (>= 2 keeps display rounding <= 0.005 mm)
side = "below"                       # optional: below/above (horizontal), left/right (vertical)
angle = 45                           # optional: leader angle for circle callouts, degrees
offset = [0, 0]                      # optional nudge of the text, sheet mm
allow_annotation = false             # optional; see below
```

Linear dimensions take `axis` (`"X"`, `"Y"`, `"Z"`) plus `from` and `to`
selectors; the axis must lie in the view's plane (spec error otherwise). A
diameter on a view that looks along the cylinder axis is attached to the
projected circle; on a view that sees the cylinder side-on it is drawn across
the two silhouette lines with a diameter symbol.

Tolerance display (DXF control codes: `%%c` diameter, `%%p` plus/minus):
`60.00 %%p0.20`, `2X %%c6.60 +0.10/0`, and limits `%%c12.018/12.000`.

If TechDraw cannot attach the dimension (feature hidden or oblique in that
view) the callout is written as annotation text with a leader. That text has
no independent TechDraw measurement, so it **fails** (`dim_<id>_annotation_fallback`)
unless the dimension sets `allow_annotation = true`; even then the leader tip
must sit on the feature's projection and the value is still compared with the
model. Prefer choosing a better view.

If `params/params.toml` gives the key a `tol`, it must equal the drawing
tolerance (`dim_<id>_tolerance_vs_params`); params is the single source of
truth (CONTRACTS §2).

## `[[datum]]` and `[[gdt]]` -- datum features and feature control frames

```toml
[[datum]]
id = "A"                              # capital letter, not I/O/Q
view = "front"                        # the face must be seen edge-on in this view
on = { plane = "-Z", at = "min" }     # plane or cylinder selector
along = 0.1                           # optional: where on the face (fraction of its visible length)

[[gdt]]
id = "base_holes_position"
characteristic = "position"           # see list below
tolerance = 0.2                       # mm
diameter_zone = true                  # prefix the tolerance with a diameter symbol
modifier = "M"                        # optional: M (MMC) or L (LMC)
datums = ["A", "B"]                   # primary, secondary, tertiary; each must be a declared [[datum]]
dimension = "base_hole_dia"           # the frame is placed at, and belongs to, this dimension's feature
requirement = "REQ-MECH-006"          # optional
```

Characteristics: form (`straightness`, `flatness`, `circularity`,
`cylindricity`) take **no** datum; orientation (`perpendicularity`,
`parallelism`, `angularity`) and runout (`circular_runout`, `total_runout`)
need **at least one**; `position`, `profile_line`, `profile_surface` take
zero or more. These are the general rules common to ASME Y14.5 and ISO 1101
(R5a §2 lists "feature-control frames well-formed, datum references resolve"
as what a tool can check). Choosing datums and tolerances that fit the part's
function needs a qualified human (R5a §2) -- Forge only checks that the frame
is well formed, drawn, and references declared datums.

## `[[note]]`

```toml
[[note]]
text = "BREAK SHARP EDGES 0.2 MAX."
```

Two notes are always added first: the units and general-tolerance statement,
and that critical dimensions are verified against the 3-D model.

## What the output contains (layers the check reads)

`View_<id>` (TechDraw projected geometry), `Dim_<id>` (TechDraw DIMENSION),
`DIMTXT_<id>` (annotation fallback), `TITLE_BLOCK`, `PROJECTION_SYMBOL`,
`FRAME`, `NOTES`, `CENTERLINES`, `SECTION_LINE_<id>`, `HATCH_<id>`,
`DETAIL_CIRCLE_<id>`, `VIEW_LABEL_<id>`, `DATUM_<letter>`, `FCF_<gdt id>`
(frame polyline carries XDATA `FORGE: gdt:<characteristic>`).
