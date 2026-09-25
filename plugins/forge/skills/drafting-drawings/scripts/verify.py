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
import re
import shutil
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lib"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from forge.checkresult import Check, CheckContractError  # noqa: E402
from forge.tools import find_tool, forge_home  # noqa: E402

_SAFE = re.compile(r"[^a-z0-9_]+")
DEFAULT_FREECADCMD = Path(find_tool("freecadcmd") or forge_home() / "bin" / "freecadcmd")


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


def _run_one(spec_path: Path, project: Path, freecadcmd_bin: str, recheck: bool = False) -> int:
    try:
        spec = tomllib.loads(spec_path.read_text())
    except tomllib.TOMLDecodeError as exc:
        chk = Check(f"mech.drawing_{_safe_name(spec_path.stem)}", str(spec_path), level="L1", project=project)
        return chk.error(f"{spec_path}: invalid TOML: {exc}")
    import drawspec
    if drawspec.is_v2(spec):
        return _run_v2(spec_path, spec, project, freecadcmd_bin, recheck)

    # S14: the legacy single-view [part] schema (no `schema` key) is refused,
    # not silently run through its own weaker path -- it predates [model],
    # the tolerance >= 0 check, and the scale validation the v2 schema has,
    # and letting it keep passing would let a spec dodge all three simply by
    # never adding `schema = "forge.drawing/2"`.
    drawing = spec.get("drawing", {})
    name = drawing.get("name", spec_path.stem)
    check_id = f"mech.drawing_{_safe_name(name)}"
    target = str(spec_path.relative_to(project)) if spec_path.is_relative_to(project) else str(spec_path)
    chk = Check(check_id, target, level="L1", project=project)
    return chk.error(
        f"{spec_path.name}: this is the legacy single-view [part] drawing spec, which is refused -- "
        "it has no [model] (a real build123d module or STEP file to measure against, CONTRACTS SS10) "
        "and none of the v2 schema's checks (tolerance >= 0, a valid scale, GD&T, reproducibility). "
        "Migrate it to schema = \"forge.drawing/2\": add [drawing].projection/sheet_size/general_tolerance, "
        "[model].module (or .step), one or more [[view]] and [[sheet]] entries, and rewrite each "
        "[[dimension]] with view/type/tol/param instead of value_mm -- see "
        "references/spec-schema.md and examples/project/cad/drawings/*.toml for a worked v2 example."
    )


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
