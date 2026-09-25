#!/usr/bin/env python3
"""Verify entrypoint for drafting-drawings (CONTRACTS.md §9).

    forge-python skills/drafting-drawings/scripts/verify.py --project <root> [--changed <path> ...] [--recheck]

For each ``cad/drawings/<name>.toml`` (or just ``--changed`` ones):

* ``schema = "forge.drawing/2"`` specs (multi-view, any STEP/build123d part):
  measure every critical dimension on the model with build123d (independent
  of TechDraw), generate the sheets (freecadcmd TechDraw -> DXF -> ezdxf
  finishing -> PDF) into ``out/drawings/<name>/``, then read the output back
  and FAIL on: a missing critical dimension, a drawn value more than 0.01 mm
  from the model measurement (or TechDraw's own value, or params, off by more
  than that), a missing or wrong tolerance, a missing view or section/detail
  marker, a projection symbol that is missing or contradicts the declared
  method, a principal view on the wrong side, a missing title-block field, or
  a drawing that is not reproducible (the whole pipeline is re-run into a
  scratch directory and the DXF entity sets compared). ``--recheck`` checks
  the DXF/PDF already in ``out/drawings/<name>/`` instead of rewriting them
  (the reproducibility run still happens), so a hand-edited DXF is caught.
* Older specs without ``schema`` (single plate-with-hole view) keep the
  original path, unchanged.

Writes ``out/verify/mech.drawing_<name>.json`` (and, for v2,
``out/drawings/<name>/report.json`` with every value compared). Exit 0 pass,
1 fail, 2 error (bad spec, missing tool, generator crash).
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lib"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from forge.checkresult import Check, CheckContractError  # noqa: E402
from forge.tools import find_tool, forge_home  # noqa: E402
from dxf_to_pdf import dxf_to_pdf  # noqa: E402

_SAFE = re.compile(r"[^a-z0-9_]+")
DEFAULT_FREECADCMD = Path(find_tool("freecadcmd") or forge_home() / "bin" / "freecadcmd")
MAKE_DRAWING_PY = Path(__file__).resolve().parent / "make_drawing.py"
_NUMERIC = re.compile(r"[-+]?\d+\.?\d*")


def _safe_name(name: str) -> str:
    slug = _SAFE.sub("_", name.strip().lower()).strip("_")
    return slug or "drawing"


def _find_spec_files(project: Path, changed: list[str]) -> list[Path]:
    specs_dir = project / "cad" / "drawings"
    if changed:
        out = set()
        changed_abs = {(project / c).resolve() if not Path(c).is_absolute() else Path(c).resolve() for c in changed}
        for p in changed_abs:
            try:
                p.relative_to(specs_dir.resolve())
            except ValueError:
                continue
            if p.suffix == ".toml" and p.exists():
                out.add(p)
        # A drawing goes stale when its model or params change, not only its spec:
        # re-check every v2 spec whose [model] module/step/params is among the changed paths.
        for spec in (specs_dir.glob("*.toml") if specs_dir.is_dir() else []):
            try:
                model = tomllib.loads(spec.read_text()).get("model") or {}
            except (tomllib.TOMLDecodeError, OSError):
                out.add(spec)  # let the run report the broken spec
                continue
            deps = {model.get("module"), model.get("step"), model.get("params", "params/params.toml")} - {None}
            if any((project / d).resolve() in changed_abs for d in deps if isinstance(d, str)):
                out.add(spec.resolve())
        return sorted(out)
    if not specs_dir.is_dir():
        return []
    return sorted(specs_dir.glob("*.toml"))


def _extract_texts(dxf_path: Path) -> list[str]:
    import ezdxf
    doc = ezdxf.readfile(str(dxf_path))
    msp = doc.modelspace()
    out = []
    for e in msp.query("TEXT"):
        out.append(e.dxf.text)
    for e in msp.query("MTEXT"):
        out.append(e.text)
    return out


def _extract_dimension_values(dxf_path: Path) -> list[float]:
    import ezdxf
    doc = ezdxf.readfile(str(dxf_path))
    msp = doc.modelspace()
    values = []
    for e in msp.query("DIMENSION"):
        text = e.dxf.text if e.dxf.hasattr("text") else ""
        m = _NUMERIC.search(text or "")
        if m:
            values.append(float(m.group()))
    return values


def _run_one(spec_path: Path, project: Path, freecadcmd_bin: str, recheck: bool = False) -> int:
    try:
        spec = tomllib.loads(spec_path.read_text())
    except tomllib.TOMLDecodeError as exc:
        chk = Check(f"mech.drawing_{_safe_name(spec_path.stem)}", str(spec_path), level="L1", project=project)
        return chk.error(f"{spec_path}: invalid TOML: {exc}")
    import drawspec
    if drawspec.is_v2(spec):
        return _run_v2(spec_path, spec, project, freecadcmd_bin, recheck)

    drawing = spec.get("drawing", {})
    name = drawing.get("name", spec_path.stem)
    check_id = f"mech.drawing_{_safe_name(name)}"
    target = str(spec_path.relative_to(project)) if spec_path.is_relative_to(project) else str(spec_path)
    chk = Check(check_id, target, level="L1", project=project)

    for required in ("drawing", "part"):
        if required not in spec:
            return chk.error(f"{spec_path}: missing [{required}] table")
    for f in ("title", "dwg_no", "rev", "scale", "drawn_by"):
        if f not in drawing:
            return chk.error(f"{spec_path}: [drawing] missing required field {f!r}")
    dimensions = spec.get("dimension", [])
    if not dimensions:
        return chk.error(f"{spec_path}: no [[dimension]] entries -- a drawing with no critical dimensions cannot be checked")

    if not shutil.which(freecadcmd_bin) and not Path(freecadcmd_bin).exists():
        return chk.error(
            f"freecadcmd binary not found at {freecadcmd_bin!r}. Install it via "
            "plugins/forge/toolchain/install.sh or pass --freecadcmd-bin."
        )

    work_dir = project / "out" / "drawings" / _safe_name(name)
    work_dir.mkdir(parents=True, exist_ok=True)
    dxf_path = work_dir / "page.dxf"
    pdf_path = work_dir / "page.pdf"

    try:
        env = dict(os.environ)
        env["FORGE_DRAWING_SPEC"] = str(spec_path.resolve())
        env["FORGE_DRAWING_OUT_DXF"] = str(dxf_path.resolve())
        r = subprocess.run(
            [freecadcmd_bin, str(MAKE_DRAWING_PY)], env=env, capture_output=True, text=True, timeout=300,
        )
        if r.returncode != 0 or not dxf_path.exists():
            return chk.error(
                f"freecadcmd drawing generation failed (exit {r.returncode}) for {spec_path.name}. "
                f"stdout tail: {r.stdout[-800:]} stderr tail: {r.stderr[-800:]}"
            )
        drawing_warnings = [line for line in r.stdout.splitlines() if line.startswith("WARNING")]

        dxf_to_pdf(dxf_path, pdf_path)

        pdf_size = pdf_path.stat().st_size if pdf_path.exists() else 0
        chk.measure(
            "pdf_size_bytes", pdf_size, "bytes", min=1000,
            remediation=(
                f"{pdf_path} does not exist or is implausibly small ({pdf_size} bytes) -- the DXF -> PDF "
                "conversion likely failed. Re-run dxf_to_pdf.py directly on the DXF and inspect the error."
            ),
        )

        texts = _extract_texts(dxf_path)
        joined = "\n".join(texts)
        expected_fields = {
            "title": drawing["title"], "dwg_no": drawing["dwg_no"], "rev": drawing["rev"],
            "scale": drawing["scale"], "drawn_by": drawing["drawn_by"],
        }
        missing_fields = [k for k, v in expected_fields.items() if str(v) not in joined]
        chk.measure(
            "title_block_fields_present", len(expected_fields) - len(missing_fields), "1",
            min=len(expected_fields),
            remediation=(
                f"Title block field(s) {missing_fields} not found as DXF text in {dxf_path.name}. "
                "Check that make_drawing.py's title_fields list includes every field this spec sets, "
                "and that the value string matches exactly (it is a substring match)."
            ),
        )

        dim_values = _extract_dimension_values(dxf_path)
        matched = 0
        missing_dims = []
        for dim in dimensions:
            target_val = float(dim["value_mm"])
            tol = max(0.05, abs(target_val) * 0.01)
            if any(abs(v - target_val) <= tol for v in dim_values):
                matched += 1
            else:
                missing_dims.append(dim.get("id", "?"))
        chk.measure(
            "dimensions_present", matched, "1", min=len(dimensions),
            remediation=(
                f"Dimension(s) {missing_dims} from {spec_path.name} are not present in the exported DXF "
                f"{dxf_path.name} (found DIMENSION values {dim_values}). This usually means the projected "
                "geometry has no edge matching that nominal value (check part vs. spec dimensions), or "
                "make_drawing.py's edge probe missed it -- see the WARNING lines: "
                f"{drawing_warnings if drawing_warnings else '(none logged)'}"
            ),
        )

        chk.tool("freecad", "1.1.3")
        import ezdxf as _ezdxf
        chk.tool("ezdxf", _ezdxf.__version__)
        return chk.finish(notes=(
            f"DXF: {dxf_path.relative_to(project)}; PDF: {pdf_path.relative_to(project)}. "
            f"make_drawing.py warnings: {drawing_warnings or 'none'}. "
            "ADR-001 deviation #3: full-page PDF/SVG export from TechDraw needs a GUI (issue #5710); "
            "this pipeline exports DXF headlessly and renders the PDF with ezdxf+matplotlib instead."
        ))
    except CheckContractError as exc:
        return chk.error(str(exc))
    except Exception as exc:  # noqa: BLE001 -- fail closed, never a silent pass
        return chk.error(f"{type(exc).__name__}: {exc}")


def _model_extents(shape, spec) -> dict[str, tuple[float, float]]:
    """Expected sheet size (w, h) of each principal and section view, from the model (build123d)."""
    import build123d as bd
    import model_measure as mm
    out = {}
    for vid, v in spec["views"].items():
        if v["kind"] in ("front", "rear", "top", "bottom", "right", "left"):
            x0, x1, y0, y1 = mm.projected_extent(shape, v["direction"], v["x_direction"])
        elif v["kind"] == "section":
            # TechDraw keeps the material behind the plane as seen from the +normal side
            # (verified: a +X section of the L-bracket keeps the upright at x < origin).
            kept = shape.split(bd.Plane(origin=v["origin"], z_dir=v["direction"]), keep=bd.Keep.BOTTOM)
            x0, x1, y0, y1 = mm.projected_extent(kept, v["direction"], v["x_direction"])
        else:
            continue
        out[vid] = ((x1 - x0) * v["scale"], (y1 - y0) * v["scale"])
    return out


def _model_edges(shape, spec) -> dict[str, tuple]:
    """Principal views: every model edge projected on the view's paper axes (model mm), plus
    the projected bounding-box centre TechDraw centres the view on."""
    import model_measure as mm
    polys = mm.edge_polylines(shape)
    out = {}
    for vid, v in spec["views"].items():
        if v["kind"] not in ("front", "rear", "top", "bottom", "right", "left"):
            continue
        xa, ya = mm.paper_axes(v["direction"], v["x_direction"])
        segs = []
        for pl in polys:
            q = [(mm.dot(p, xa), mm.dot(p, ya)) for p in pl]
            segs += list(zip(q[:-1], q[1:]))
        x0, x1, y0, y1 = mm.projected_extent(shape, v["direction"], v["x_direction"])
        out[vid] = (segs, ((x0 + x1) / 2, (y0 + y1) / 2))
    return out


def _run_v2(spec_path: Path, raw: dict, project: Path, freecadcmd_bin: str, recheck: bool) -> int:
    import json as _json
    import tempfile

    import drawing_pipeline as dp
    import drawspec
    import dxf_checks
    import model_measure as mm

    stem = drawspec.spec_path_stem(spec_path)
    name = str(raw.get("drawing", {}).get("name", stem)) if isinstance(raw.get("drawing"), dict) else stem
    check_id = f"mech.drawing_{_safe_name(name)}"
    target = str(spec_path.relative_to(project)) if spec_path.is_relative_to(project) else str(spec_path)
    chk = Check(check_id, target, level="L1", project=project)
    params_rel = (raw.get("model") or {}).get("params", "params/params.toml") if isinstance(raw.get("model"), dict) else "params/params.toml"
    params_path = project / params_rel
    try:
        params = tomllib.loads(params_path.read_text()) if params_path.exists() else {}
        spec = drawspec.load_spec(raw, params, stem=stem)
    except (drawspec.SpecError, tomllib.TOMLDecodeError) as exc:
        return chk.error(f"{spec_path}: spec error: {exc}")
    except Exception as exc:  # noqa: BLE001 -- e.g. decimals = "x": malformed spec, fail closed with a result file
        return chk.error(f"{spec_path}: spec error: {type(exc).__name__}: {exc}")
    if not shutil.which(freecadcmd_bin) and not Path(freecadcmd_bin).exists():
        return chk.error(f"freecadcmd binary not found at {freecadcmd_bin!r}. Install it via "
                         "plugins/forge/toolchain/install.sh or pass --freecadcmd-bin.")
    try:
        shape = mm.load_model(project, spec["model"], params)
    except Exception as exc:  # noqa: BLE001
        return chk.error(f"cannot load model {spec['model']}: {type(exc).__name__}: {exc}")
    out_dir = project / "out" / "drawings" / _safe_name(spec["name"])
    try:
        measures = mm.measure_all(shape, spec)
        anchors = {k: mm.datum_anchor(shape, d) for k, d in spec["datums"].items()}
        gen = None
        if not recheck:
            gen = dp.generate(project, spec, shape, measures, anchors, out_dir, freecadcmd_bin)
        sheet_files = {s["index"]: {"dxf": out_dir / f"sheet{s['index']}.dxf", "pdf": out_dir / f"sheet{s['index']}.pdf"}
                       for s in spec["sheets"]}
        missing = [str(f["dxf"]) for f in sheet_files.values() if not f["dxf"].exists()]
        if missing:
            return chk.error(f"sheet DXF(s) not found: {missing} (run without --recheck to generate them)")
        if not (out_dir / "layout.json").exists():
            return chk.error(f"{out_dir / 'layout.json'} not found: TechDraw's own dimension values cannot be checked "
                             "(run without --recheck to regenerate)")
        layout = _json.loads((out_dir / "layout.json").read_text())
        with tempfile.TemporaryDirectory(prefix="forge_drawing_repro_") as tmp:
            again = dp.generate(project, spec, shape, measures, anchors, Path(tmp), freecadcmd_bin)
            repro = {i: dxf_checks.entity_set_diff(f["dxf"], Path(tmp) / f"sheet{i}.dxf") for i, f in sheet_files.items()}
            if gen is None:
                gen = {"sheets": again["sheets"], "issues": again["issues"]}
        extents = _model_extents(shape, spec)
        dxf_checks.check_drawing(chk, spec=spec, sheet_files=sheet_files, layout=layout, measures=measures,
                                 model_extents=extents, gen=gen, repro=repro, model_edges=_model_edges(shape, spec))
        import build123d as _bd
        import ezdxf as _ezdxf
        chk.tool("freecad", layout.get("freecad", "1.1.3"))
        chk.tool("build123d", _bd.__version__)
        chk.tool("ezdxf", _ezdxf.__version__)
        report = {"spec": target, "sheets": {i: {"dxf": str(f["dxf"].relative_to(project)), "pdf": str(f["pdf"].relative_to(project)),
                                                 "dxf_entity_set_sha256": dxf_checks.entity_set_sha(f["dxf"])}
                                             for i, f in sheet_files.items()},
                  "dimensions": {d["id"]: {"param": d["param"], "param_value_mm": d["param_nominal"], "requirement": d["requirement"],
                                           "model_mm": measures[d["id"]].get("value"), "error": measures[d["id"]].get("error"),
                                           "techdraw": layout.get("dims", {}).get(d["id"])} for d in spec["dimensions"]}}
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "report.json").write_text(_json.dumps(report, indent=2, sort_keys=True, default=str) + "\n")
        n_td = sum(1 for r in layout.get("dims", {}).values() if r.get("method") == "techdraw")
        return chk.finish(notes=(
            f"{len(sheet_files)} sheet(s) in {out_dir.relative_to(project)}; {n_td}/{len(spec['dimensions'])} critical "
            "dimensions attached as TechDraw dimensions, the rest as verified annotation text. Values compared with a "
            "build123d measurement of the model (tolerance 0.01 mm). Headless route: TechDraw.writeDXFPage + ezdxf "
            "finishing + ezdxf/matplotlib PDF (ADR-001 §15.3). NOT FOR MANUFACTURE until a qualified human signs the "
            "title block -- this check is L1 evidence, not approval."))
    except CheckContractError as exc:
        return chk.error(str(exc))
    except dp.GenerationError as exc:
        return chk.error(str(exc))
    except drawspec.SpecError as exc:
        return chk.error(f"{spec_path}: spec error: {exc}")
    except Exception as exc:  # noqa: BLE001 -- fail closed, never a silent pass
        import traceback
        return chk.error(f"{type(exc).__name__}: {exc} :: {traceback.format_exc()[-1500:]}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", type=Path, default=Path.cwd())
    ap.add_argument("--changed", action="append", default=[])
    ap.add_argument("--fast", action="store_true", help="accepted for interface compatibility; FreeCAD runs are not fast")
    ap.add_argument("--freecadcmd-bin", default=str(DEFAULT_FREECADCMD))
    ap.add_argument("--recheck", action="store_true",
                    help="v2 specs: check the DXF/PDF already in out/drawings/<name>/ instead of regenerating them")
    ns = ap.parse_args()
    project = ns.project.resolve()

    spec_files = _find_spec_files(project, ns.changed)
    if not spec_files:
        print("[SKIP] no cad/drawings/*.toml files to check")
        return 0

    worst = 0
    for path in spec_files:
        rc = _run_one(path, project, ns.freecadcmd_bin, ns.recheck)
        worst = max(worst, rc)
    return worst


if __name__ == "__main__":
    sys.exit(main())
