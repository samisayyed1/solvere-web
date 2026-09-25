#!/usr/bin/env python3
"""verifying-geometry entrypoint (CONTRACTS.md §9, forge.toml domain "mech").

    forge-python skills/verifying-geometry/scripts/verify.py --project <root> \
        [--changed <path> ...] [--fast]

Reads every ``requirements/geometry/<part>.toml`` spec in the project (see
``references/spec-schema.md`` for the format), loads that part's build123d
geometry (``forge_cad.load``), runs the check families it lists
(``forge_cad.measure``), and writes one ``out/verify/<check_id>.json`` per
check through ``forge.checkresult`` (CONTRACTS §3). Exits 0 if every check in
every spec passed, 1 if any failed, 2 on an internal error. Prints
``[SKIP] <reason>`` and exits 0 if there is nothing to check -- it never
fakes a pass.

Runs on ``~/.forge/bin/forge-python`` (build123d/OCP/trimesh/numpy;
CONTRACTS §10). Not stdlib -- do not import this from a hook or the ``forge``
CLI.
"""

from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path
from typing import Any

# CONTRACTS §10: skills/<skill>/scripts/x.py -> plugins/forge/lib
_LIB_DIR = Path(__file__).resolve().parents[3] / "lib"
sys.path.insert(0, str(_LIB_DIR))

import build123d as bd  # noqa: E402
from forge import checkresult  # noqa: E402
from forge_cad import load, measure  # noqa: E402

FAMILIES = (
    "geometry.validity", "geometry.watertight", "geometry.bbox", "geometry.volume",
    "geometry.mass", "geometry.min_wall", "geometry.clearance", "geometry.interference",
    "geometry.draft", "geometry.min_radius", "geometry.hole_edge", "geometry.boss_rib",
)


class SpecError(ValueError):
    """The requirements/geometry/*.toml spec itself is malformed."""


def _load_params(project: Path) -> dict[str, Any]:
    path = project / "params" / "params.toml"
    if not path.is_file():
        return {}
    return tomllib.loads(path.read_text())


def _param_value(params: dict[str, Any], dotted_key: str) -> float:
    node: Any = params
    for part in dotted_key.split("."):
        if not isinstance(node, dict) or part not in node:
            raise SpecError(f"params key {dotted_key!r} not found in params/params.toml")
        node = node[part]
    if not isinstance(node, dict) or "value" not in node:
        raise SpecError(f"params key {dotted_key!r} is not a leaf parameter table")
    return float(node["value"])


def _num(entry: dict[str, Any], key: str, params: dict[str, Any], *, required: bool = False) -> float | None:
    """Read a numeric field, or its ``<key>_param`` params.toml alternative."""
    if key in entry:
        return float(entry[key])
    param_key = f"{key}_param"
    if param_key in entry:
        return _param_value(params, entry[param_key])
    if required:
        raise SpecError(f"check {entry.get('family')!r} needs {key!r} or {param_key!r}")
    return None


def _face_by_axis(shape: bd.Shape, which: str) -> bd.Face:
    faces = shape.faces().sort_by(bd.Axis.Z)
    if which == "top":
        return faces[-1]
    if which == "bottom":
        return faces[0]
    raise SpecError(f"unknown boundary_face selector {which!r} (use 'top' or 'bottom')")


def _select_faces(shape: bd.Shape, spec: Any, pull_direction: tuple[float, float, float]) -> list[bd.Face]:
    all_faces = shape.faces()
    if spec is None or spec == "auto":
        return measure.select_side_faces(shape, pull_direction=pull_direction)
    if isinstance(spec, list):
        return [all_faces[i] for i in spec]
    raise SpecError(f"unsupported face selector {spec!r}")


def run_check_family(entry: dict[str, Any], *, part_name: str, shape: bd.Shape, project: Path,
                      target: str, params: dict[str, Any], pull_direction: tuple[float, float, float],
                      fast: bool) -> int:
    family = entry.get("family")
    if family not in FAMILIES:
        raise SpecError(f"unknown check family {family!r} (expected one of {FAMILIES})")
    requirement = entry.get("requirement")
    check_id = f"{family}.{part_name}"

    with checkresult.run_check(check_id, target, project=project) as chk:
        chk.tool("build123d", bd.__version__)

        if family == "geometry.validity":
            m = measure.validity(shape)
            chk.measure("is_valid", m["is_valid"], "1", equals=True, requirement=requirement,
                        remediation="Shape fails OCP BRepCheck_Analyzer; inspect self-intersections or open wires "
                                    "with the modeling-cad-parts repair-hints tool and rebuild.")
            chk.measure("is_manifold", m["is_manifold"], "1", equals=True, requirement=requirement,
                        remediation="Shape is not a manifold solid; check for coincident/duplicate faces.")

        elif family == "geometry.watertight":
            tol = float(entry.get("tolerance_mm", 0.05))
            out_stl = project / "out" / "verify" / f"{part_name}.stl"
            m = measure.watertight_export(shape, out_stl, tolerance=tol)
            chk.measure("watertight", m.get("watertight", False), "1", equals=True, requirement=requirement,
                        remediation=f"STL export of {part_name} is not watertight at tolerance {tol} mm "
                                    "(gap/non-manifold edge in the tessellation or the BREP). Tighten the "
                                    "tessellation tolerance and re-check, then inspect for real gaps.")

        elif family == "geometry.bbox":
            axis = entry.get("axis", "x")
            bb = measure.bounding_box(shape)
            idx = {"x": 0, "y": 1, "z": 2}[axis]
            size = bb["size_mm"][idx]
            min_v = _num(entry, "min_mm", params)
            max_v = _num(entry, "max_mm", params)
            chk.measure(f"bbox_{axis}", size, "mm", min=min_v, max=max_v, requirement=requirement,
                        remediation=f"Bounding box {axis}={size:.4f} mm is outside [{min_v}, {max_v}] mm; "
                                    "check the driving params/params.toml dimension.")

        elif family == "geometry.volume":
            v = measure.volume(shape)
            min_v = _num(entry, "min_mm3", params)
            max_v = _num(entry, "max_mm3", params)
            chk.measure("volume", v, "mm3", min=min_v, max=max_v, requirement=requirement,
                        remediation=f"Volume {v:.4f} mm3 is outside [{min_v}, {max_v}] mm3; a feature is "
                                    "missing, oversized, or a boolean operation didn't apply.")

        elif family == "geometry.mass":
            density = _num(entry, "density_kg_m3", params, required=True)
            m = measure.mass_properties(shape, density_kg_m3=density)
            max_g = _num(entry, "max_g", params)
            min_g = _num(entry, "min_g", params)
            chk.measure("mass", m["mass_g"], "g", min=min_g, max=max_g, requirement=requirement,
                        remediation=f"Mass {m['mass_g']:.4f} g (density {density} kg/m3) is outside "
                                    f"[{min_g}, {max_g}] g; check volume or the params density value.")

        elif family == "geometry.min_wall":
            min_v = _num(entry, "min_mm", params, required=True)
            samples = int(entry.get("sample_count", 1500))
            if fast:
                samples = min(samples, 300)
            faces = None
            if "faces" in entry:
                faces = [shape.faces()[i] for i in entry["faces"]]
            m = measure.min_wall_thickness(shape, sample_count=samples, faces=faces)
            val = m["min_thickness_mm"]
            if val is None:
                chk.measure("min_wall", -1.0, "mm", min=min_v, requirement=requirement,
                            remediation=f"min_wall_thickness found no opposite-wall hit ({m['resolution_note']}); "
                                        "the shape may be open/convex where sampled -- fix the geometry or narrow "
                                        "the 'faces' selector.")
            else:
                chk.measure("min_wall", val, "mm", min=min_v, location=str(m["location_mm"]), requirement=requirement,
                            remediation=f"Minimum wall {val:.4f} mm at {m['location_mm']} is below the "
                                        f"{min_v} mm requirement (params: check the wall-thickness key). Thicken "
                                        "the wall there or reduce an intersecting offset/fillet.")

        elif family == "geometry.clearance":
            other_mod = entry.get("other_module")
            if not other_mod:
                raise SpecError("geometry.clearance needs 'other_module'")
            other = load.load_part(project / other_mod, params=params)
            min_v = _num(entry, "min_mm", params, required=True)
            m = measure.clearance(shape, other)
            chk.measure("clearance", m["distance_mm"], "mm", min=min_v, requirement=requirement,
                        remediation=f"Clearance to {other_mod} is {m['distance_mm']:.4f} mm, below the "
                                    f"{min_v} mm requirement; move or trim the interfering feature.")

        elif family == "geometry.interference":
            other_mod = entry.get("other_module")
            if not other_mod:
                raise SpecError("geometry.interference needs 'other_module'")
            other = load.load_part(project / other_mod, params=params)
            m = measure.interference(shape, other)
            chk.measure("overlap_volume", m["overlap_volume_mm3"], "mm3", equals=0.0, tol=1e-6,
                        requirement=requirement,
                        remediation=f"{part_name} interferes with {other_mod} by "
                                    f"{m['overlap_volume_mm3']:.4f} mm3; move or trim the overlapping feature.")

        elif family == "geometry.draft":
            min_v = _num(entry, "min_deg", params, required=True)
            faces = _select_faces(shape, entry.get("faces"), pull_direction)
            results = measure.draft_angles(shape, faces, pull_direction=pull_direction)
            if not results:
                raise SpecError("geometry.draft selected no faces to check")
            for r in results:
                chk.measure(f"draft_face_{r['face_index']}", r["draft_deg"], "deg", min=min_v,
                            requirement=requirement,
                            remediation=f"Face {r['face_index']} draft is {r['draft_deg']:.3f} deg, below the "
                                        f"{min_v} deg minimum for pull direction {pull_direction}; add draft in "
                                        "the CAD feature that built this face.")

        elif family == "geometry.min_radius":
            min_v = _num(entry, "min_mm", params, required=True)
            results = measure.min_radius(shape, concave_only=bool(entry.get("concave_only", True)))
            if not results:
                raise SpecError("geometry.min_radius found no cylindrical (fillet) faces to check; "
                                 "add fillets or set concave_only=false")
            for r in results:
                chk.measure(f"radius_face_{r['face_index']}", r["radius_mm"], "mm", min=min_v,
                            requirement=requirement,
                            remediation=f"Face {r['face_index']} internal radius is {r['radius_mm']:.3f} mm, "
                                        f"below the {min_v} mm minimum; increase that fillet's radius.")

        elif family == "geometry.hole_edge":
            min_v = _num(entry, "min_mm", params, required=True)
            boundary = _face_by_axis(shape, entry.get("boundary_face", "top"))
            holes = measure.find_holes(shape)
            if not holes:
                raise SpecError("geometry.hole_edge found no holes (see find_holes' heuristic limits)")
            all_faces = shape.faces()
            for h in holes:
                hole_face = all_faces[h["face_index"]]
                m = measure.hole_edge_distance(shape, hole_face, boundary)
                chk.measure(f"hole_{h['face_index']}_wall_to_edge", m["wall_to_edge_mm"], "mm", min=min_v,
                            requirement=requirement,
                            remediation=f"Hole at face {h['face_index']} is {m['wall_to_edge_mm']:.3f} mm from the "
                                        f"boundary edge, below the {min_v} mm minimum; move the hole inward or "
                                        "shrink it.")

        elif family == "geometry.boss_rib":
            nominal = _num(entry, "nominal_wall_mm", params, required=True)
            max_ratio = _num(entry, "max_ratio", params, required=True)
            faces = [shape.faces()[i] for i in entry.get("faces", [])]
            if not faces:
                raise SpecError("geometry.boss_rib needs an explicit 'faces' list")
            samples = int(entry.get("sample_count", 400))
            if fast:
                samples = min(samples, 150)
            m = measure.boss_rib_thickness(shape, faces, nominal_wall_mm=nominal, sample_count=samples)
            ratio = m.get("ratio")
            if ratio is None:
                raise SpecError(f"geometry.boss_rib on {part_name} found no opposite-wall hit: {m['resolution_note']}")
            chk.measure("boss_rib_ratio", ratio, "1", max=max_ratio, requirement=requirement,
                        remediation=f"Boss/rib thickness {m['min_thickness_mm']:.4f} mm is {ratio:.2f}x the "
                                    f"{nominal} mm nominal wall, above the {max_ratio}x DFM limit; thin the "
                                    "rib/boss to control sink marks (checking-dfm rib_thickness rule).")

    return 0  # run_check() calls sys.exit; unreachable, kept for clarity/lint


def _iter_specs(project: Path, changed: list[str]) -> list[Path]:
    spec_dir = project / "requirements" / "geometry"
    if not spec_dir.is_dir():
        return []
    specs = sorted(spec_dir.glob("*.toml"))
    if not changed:
        return specs
    changed_abs = {str((project / c).resolve()) for c in changed}
    kept = []
    for spec_path in specs:
        if str(spec_path.resolve()) in changed_abs:
            kept.append(spec_path)
            continue
        try:
            doc = tomllib.loads(spec_path.read_text())
            module = doc.get("part", {}).get("module")
            if module and str((project / module).resolve()) in changed_abs:
                kept.append(spec_path)
        except tomllib.TOMLDecodeError:
            kept.append(spec_path)  # let the real run below report the parse error
    return kept


def main(argv: list[str]) -> int:
    # Declares this entrypoint's check_id namespace so PostToolUse can bind a
    # fix message to the check that owns it, by check_id rather than which
    # out/verify/*.json file happens to have the newest mtime (M7, review #1).
    # Every check_id this script writes starts with "geometry." (see FAMILIES).
    print("[FORGE_CHECK_ID_PREFIX] geometry.")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", default=".", type=Path)
    ap.add_argument("--changed", action="append", default=[])
    ap.add_argument("--fast", action="store_true")
    ns = ap.parse_args(argv)
    project = ns.project.resolve()

    specs = _iter_specs(project, ns.changed)
    if not specs:
        print("[SKIP] no requirements/geometry/*.toml specs to check")
        return 0

    params = _load_params(project)
    worst = 0
    for spec_path in specs:
        try:
            doc = tomllib.loads(spec_path.read_text())
        except tomllib.TOMLDecodeError as exc:
            print(f"[ERROR] {spec_path}: malformed TOML: {exc}", file=sys.stderr)
            return 2
        part_doc = doc.get("part")
        if not part_doc or "module" not in part_doc or "name" not in part_doc:
            print(f"[ERROR] {spec_path}: [part] needs 'name' and 'module'", file=sys.stderr)
            return 2
        part_name = part_doc["name"]
        module_path = project / part_doc["module"]
        pull_direction = tuple(part_doc.get("pull_direction", (0.0, 0.0, 1.0)))

        try:
            shape = load.load_part(module_path, params=params)
        except Exception as exc:  # noqa: BLE001 -- fail closed: a build error is never a silent pass
            print(f"[ERROR] {spec_path}: part module failed to build: {type(exc).__name__}: {exc}", file=sys.stderr)
            return 2

        checks = doc.get("check", [])
        if not checks:
            print(f"[SKIP] {spec_path}: no [[check]] entries")
            continue

        for entry in checks:
            try:
                code = _run_one(entry, part_name=part_name, shape=shape, project=project,
                                 target=part_doc["module"], params=params, pull_direction=pull_direction,
                                 fast=ns.fast)
            except SpecError as exc:
                print(f"[ERROR] {spec_path}: {exc}", file=sys.stderr)
                return 2
            worst = max(worst, code)
    return worst


def _run_one(entry: dict[str, Any], **kwargs: Any) -> int:
    """Wraps run_check_family's sys.exit(...) (from checkresult.run_check) back into a return code."""
    try:
        run_check_family(entry, **kwargs)
    except SystemExit as exc:
        return int(exc.code or 0)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
