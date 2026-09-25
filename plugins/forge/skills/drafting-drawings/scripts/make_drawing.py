"""FreeCAD TechDraw drawing generator -- runs under ``freecadcmd`` (bundled Python 3.11,
a *separate* interpreter from ``forge-python``; do not import build123d/OCP/ezdxf here).

Builds a simple plate-with-a-hole part from a drawing spec TOML, lays out a
TechDraw page (ASME ANSI-A landscape template), adds a top view, critical
dimensions, and title-block text, then exports the page as a full-page DXF
(ADR-001 deviation #3: headless TechDraw PDF/SVG export is not possible --
issue #5710 -- but headless full-page DXF export is, and works here).

Invocation (env vars, not argv -- ``freecadcmd`` swallows unrecognised CLI
flags into its own ``--help``, see SKILL.md):

    FORGE_DRAWING_SPEC=<abs path to spec.toml> \\
    FORGE_DRAWING_OUT_DXF=<abs path to write .dxf> \\
    freecadcmd make_drawing.py

Prints ``OK <dxf path>`` and exits 0 on success. A spec dimension that does
not match any projected edge within tolerance is *not* a fatal error here
(this script only builds the drawing) -- it is skipped with a WARNING line,
and it is ``verify.py`` (a different check, at the next rung of the
verification ladder) that fails the build for a missing dimension. Any
other problem (bad spec, FreeCAD/TechDraw failure) exits 2 with an ERROR
line.
"""
from __future__ import annotations

import os
import sys
import tomllib
from pathlib import Path

TEMPLATE = (
    "/Applications/FreeCAD.app/Contents/Resources/share/Mod/TechDraw/Templates/"
    "ASME/ANSIA_Landscape.svg"
)
MATCH_ABS_MM = 0.05
MATCH_REL = 0.01


def _match_tol(value_mm: float) -> float:
    return max(MATCH_ABS_MM, abs(value_mm) * MATCH_REL)


def main() -> int:
    # freecadcmd's embedded interpreter does not reliably flush block-buffered stdio on
    # exit (observed empirically: a final print() was silently dropped without this).
    try:
        sys.stdout.reconfigure(line_buffering=True)
        sys.stderr.reconfigure(line_buffering=True)
    except Exception:
        pass

    spec_path = os.environ.get("FORGE_DRAWING_SPEC")
    out_dxf = os.environ.get("FORGE_DRAWING_OUT_DXF")
    if not spec_path or not out_dxf:
        print("ERROR: FORGE_DRAWING_SPEC and FORGE_DRAWING_OUT_DXF must be set", file=sys.stderr)
        return 2

    spec_path = Path(spec_path)
    out_dxf = Path(out_dxf)
    try:
        spec = tomllib.loads(spec_path.read_text())
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: cannot read spec {spec_path}: {exc}", file=sys.stderr)
        return 2

    try:
        drawing = spec["drawing"]
        part = spec["part"]
        dimensions = spec.get("dimension", [])
    except KeyError as exc:
        print(f"ERROR: spec missing required table {exc}", file=sys.stderr)
        return 2

    import FreeCAD
    import TechDraw  # noqa: F401 -- imported for its side effect of registering DrawPage etc.

    doc = FreeCAD.newDocument("forge_drawing")

    box = doc.addObject("Part::Box", "Plate")
    box.Length = float(part["length_mm"])
    box.Width = float(part["width_mm"])
    box.Height = float(part["height_mm"])

    part_obj = box
    if "hole_diameter_mm" in part:
        cyl = doc.addObject("Part::Cylinder", "Hole")
        cyl.Radius = float(part["hole_diameter_mm"]) / 2.0
        cyl.Height = float(part["height_mm"]) * 3.0
        cyl.Placement.Base = FreeCAD.Vector(
            float(part.get("hole_x_mm", box.Length.Value / 2)),
            float(part.get("hole_y_mm", box.Width.Value / 2)),
            -float(part["height_mm"]),
        )
        cut = doc.addObject("Part::Cut", "Part")
        cut.Base = box
        cut.Tool = cyl
        part_obj = cut
    doc.recompute()

    page = doc.addObject("TechDraw::DrawPage", "Page")
    tmpl = doc.addObject("TechDraw::DrawSVGTemplate", "Template")
    tmpl.Template = TEMPLATE
    page.Template = tmpl
    doc.recompute()

    view = doc.addObject("TechDraw::DrawViewPart", "View")
    view.Source = [part_obj]
    view.Direction = FreeCAD.Vector(0, 0, 1)
    view.X = 220
    view.Y = 150
    view.Scale = 1.0
    page.addView(view)
    doc.recompute()

    # -- title block: one DrawViewAnnotation per field, so each lands as its own DXF TEXT
    # entity (writeDXFPage exports page *views*, not the SVG template's cosmetic text --
    # see SKILL.md "Why title-block text is drawn, not templated").
    title_fields = [
        ("TITLE", drawing.get("title", "")),
        ("DWG NO", drawing.get("dwg_no", "")),
        ("REV", drawing.get("rev", "")),
        ("SCALE", drawing.get("scale", "")),
        ("DRAWN BY", drawing.get("drawn_by", "")),
        ("DATE", drawing.get("date", "")),
    ]
    for i, (label, value) in enumerate(title_fields):
        ann = doc.addObject("TechDraw::DrawViewAnnotation", f"TitleField{i}")
        ann.Text = [f"{label}: {value}"]
        ann.X = 300
        ann.Y = 30 + i * 8
        page.addView(ann)
    doc.recompute()

    # -- probe projected edges (Distance for lines, Diameter for circles) to find which
    # edge index corresponds to each spec dimension's nominal value. See SKILL.md
    # "Edge selection" for why this is done by value-matching rather than a fixed index.
    #
    # Both dimension types are always tried for every edge index (never short-circuited
    # after the first non-raising attempt): empirically, asking for the wrong type on an
    # edge sometimes raises ("2d reference is a Circle") and sometimes just silently
    # returns 0.0 depending on document state, so 0.0 is not a reliable "wrong type"
    # signal either -- only a genuine value match against the spec's target decides.
    # The probe range is a fixed, generous cap (not an early-exit heuristic) because an
    # out-of-range edge index reliably logs a "2D references are corrupt" C++ warning but
    # does not reliably raise a catchable Python exception, so there is no safe stop signal.
    PROBE_MAX_EDGES = 16
    probed: list[tuple[int, str, float]] = []
    for i in range(1, PROBE_MAX_EDGES + 1):
        for dim_type in ("Distance", "Diameter"):
            d = None
            try:
                d = doc.addObject("TechDraw::DrawViewDimension", f"__Probe_{i}_{dim_type}")
                d.Type = dim_type
                d.References2D = [(view, f"Edge{i}")]
                page.addView(d)
                doc.recompute()
                raw = float(d.getRawValue())
                if raw > 1e-6:  # a genuine 0.0-valued real dimension is not a case this skill handles
                    probed.append((i, dim_type, raw))
            except Exception:
                pass
            finally:
                if d is not None and d.Name in [o.Name for o in doc.Objects]:
                    try:
                        page.removeView(d)
                    except Exception:
                        pass
                    doc.removeObject(d.Name)
        doc.recompute()
    used_edges: set[int] = set()
    n_placed = 0
    for j, dim in enumerate(dimensions):
        dim_id = dim.get("id", f"dim{j}")
        target = float(dim["value_mm"])
        tol = _match_tol(target)
        best = None
        for edge_i, dim_type, raw in probed:
            if edge_i in used_edges:
                continue
            if abs(raw - target) <= tol:
                best = (edge_i, dim_type, raw)
                break
        if best is None:
            print(
                f"WARNING: no projected edge matches dimension {dim_id!r} "
                f"(target {target} mm, tol +/-{tol:.3f} mm) -- skipped, drawing is incomplete",
                file=sys.stderr,
            )
            continue
        edge_i, dim_type, raw = best
        used_edges.add(edge_i)
        d = doc.addObject("TechDraw::DrawViewDimension", f"Dim_{dim_id}")
        d.Type = dim_type
        d.References2D = [(view, f"Edge{edge_i}")]
        page.addView(d)
        n_placed += 1

        tol_plus = dim.get("tol_plus_mm")
        tol_minus = dim.get("tol_minus_mm")
        if tol_plus is not None and tol_minus is not None:
            ann = doc.addObject("TechDraw::DrawViewAnnotation", f"TolAnn_{dim_id}")
            ann.Text = [f"{dim_id}: {target:.3f} +{float(tol_plus):.3f}/-{float(tol_minus):.3f} mm"]
            ann.X = 20
            ann.Y = 20 + n_placed * 8
            page.addView(ann)
    doc.recompute()

    out_dxf.parent.mkdir(parents=True, exist_ok=True)
    TechDraw.writeDXFPage(page, str(out_dxf))
    if not out_dxf.exists() or out_dxf.stat().st_size == 0:
        print(f"ERROR: TechDraw.writeDXFPage did not produce {out_dxf}", file=sys.stderr)
        return 2

    print(f"OK {out_dxf} ({n_placed}/{len(dimensions)} spec dimensions placed)")
    sys.stdout.flush()
    return 0


# freecadcmd runs a script with __name__ set to its filename stem, not "__main__"
# (verified empirically) -- so this file always calls main() unconditionally rather
# than relying on the usual `if __name__ == "__main__":` guard. It is not meant to be
# imported anywhere else.
sys.exit(main())
