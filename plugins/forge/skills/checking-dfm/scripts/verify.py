#!/usr/bin/env python3
"""checking-dfm entrypoint (CONTRACTS.md §9, forge.toml domain "mech").

    forge-python skills/checking-dfm/scripts/verify.py --project <root> \
        [--changed <path> ...] [--fast]

Reads every ``requirements/dfm/<part>.toml`` spec, applies the named process's
rule table (``references/rules/<process>.toml``, numbers sourced from R5c/R5d
-- see each table's header) to ``forge_cad`` measurements of that part, and
computes snap-fit root strain against per-material allowable strain
(``references/rules/snap_fit.toml``). Writes one ``out/verify/<check_id>.json``
per check through ``forge.checkresult`` (CONTRACTS §3). Exit codes and the
"nothing to check" contract match ``verifying-geometry/scripts/verify.py``
exactly (0 pass / 1 fail / 2 error, ``[SKIP]`` on an empty suite).

Runs on ``~/.forge/bin/forge-python``. Assumes the part already passed
``verifying-geometry`` -- this checks manufacturability limits, not base
geometric validity/dimensions.
"""

from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path
from typing import Any

_LIB_DIR = Path(__file__).resolve().parents[3] / "lib"
_RULES_DIR = Path(__file__).resolve().parent.parent / "references" / "rules"
sys.path.insert(0, str(_LIB_DIR))

import build123d as bd  # noqa: E402
from forge import checkresult  # noqa: E402
from forge_cad import load, measure  # noqa: E402

import strain as strain_mod  # noqa: E402  (sibling module, scripts/strain.py)

RATIO_COMPARISONS = {"min_ratio_of_wall", "max_ratio_of_wall"}


class SpecError(ValueError):
    """The requirements/dfm/*.toml spec, or the rule it names, is malformed
    or cannot be checked with the measurements available."""


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


def _load_rule_table(process: str) -> dict[str, dict[str, Any]]:
    path = _RULES_DIR / f"{process}.toml"
    if not path.is_file():
        available = sorted(p.stem for p in _RULES_DIR.glob("*.toml"))
        raise SpecError(f"no rule table for process {process!r}; available: {available}")
    doc = tomllib.loads(path.read_text())
    return {r["id"]: r for r in doc.get("rule", [])}


def _load_material_table() -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    doc = tomllib.loads((_RULES_DIR / "snap_fit.toml").read_text())
    return doc.get("meta", {}), {m["id"]: m for m in doc.get("material", [])}


def _resolve_limit(rule: dict[str, Any], nominal_wall_mm: float | None, *,
                    as_ratio: bool = False) -> tuple[str, float]:
    """Returns (comparison, resolved numeric limit) for a rule.

    By default a ratio-of-wall rule (``min_ratio_of_wall`` / ``max_ratio_of_wall``)
    is converted to an absolute mm/deg value (``value_ratio * nominal_wall_mm``),
    because most families (min_wall, min_radius, ...) measure an absolute mm/deg
    quantity and a ratio rule is just a convenient way to author that limit.

    ``as_ratio=True`` is for families whose *measurement itself* is already a
    dimensionless ratio (currently only ``geometry.boss_rib``, whose
    ``measure.boss_rib_thickness`` returns ``thickness / nominal_wall_mm``).
    There the limit must stay a bare ratio (``value_ratio``, never multiplied
    by the wall) -- multiplying it turned a ratio-vs-ratio comparison into a
    ratio-vs-millimetres one, so a rule capping ribs at 0.5x the wall let a
    0.8-ratio rib pass on a 2 mm wall (limit became 0.5*2 = 1.0 mm, and
    0.8 <= 1.0) (M8, review #1). A rule that mixes ``as_ratio=True`` with a
    non-ratio comparison is a spec error, not a silent unit mismatch.
    """
    comparison = rule["comparison"]
    if as_ratio:
        if comparison not in RATIO_COMPARISONS:
            raise SpecError(
                f"rule {rule['id']!r} measures a dimensionless ratio (check_family requires "
                f"as_ratio limits) but comparison is {comparison!r}, not one of {sorted(RATIO_COMPARISONS)}"
            )
        if "value_ratio" not in rule:
            raise SpecError(f"rule {rule['id']!r} is ratio-based; it needs value_ratio")
        return comparison, float(rule["value_ratio"])
    if comparison in RATIO_COMPARISONS:
        if nominal_wall_mm is None:
            raise SpecError(f"rule {rule['id']!r} is ratio-based; the spec needs [part].nominal_wall_param")
        return comparison, float(rule["value_ratio"]) * nominal_wall_mm
    if "value_mm" in rule:
        return comparison, float(rule["value_mm"])
    if "value_deg" in rule:
        return comparison, float(rule["value_deg"])
    raise SpecError(f"rule {rule['id']!r} has no value_mm/value_deg/value_ratio")


def _apply_dfm_check(entry: dict[str, Any], *, rule: dict[str, Any], part_name: str, shape: bd.Shape,
                      project: Path, target: str, nominal_wall_mm: float | None, pull_direction: tuple,
                      params: dict[str, Any], fast: bool) -> int:
    family = rule["check_family"]
    if family == "unsupported":
        raise SpecError(
            f"rule {rule['id']!r} has no forge_cad measurement mapped to it yet ({rule.get('conflict') or rule.get('source')}); "
            "remove it from the spec or check it manually."
        )
    requirement = entry.get("requirement")
    # geometry.boss_rib measures a dimensionless ratio (rib/boss thickness
    # over nominal wall) -- its limit must stay a ratio too, never be
    # multiplied into millimetres (see _resolve_limit's as_ratio docstring,
    # M8 review #1).
    comparison, limit = _resolve_limit(rule, nominal_wall_mm, as_ratio=(family == "geometry.boss_rib"))
    check_id = f"dfm.{rule['id']}.{part_name}"

    with checkresult.run_check(check_id, target, project=project) as chk:
        chk.tool("build123d", bd.__version__)

        if family == "geometry.min_wall":
            samples = int(entry.get("sample_count", 1500))
            if fast:
                samples = min(samples, 300)
            faces = [shape.faces()[i] for i in entry["faces"]] if "faces" in entry else None
            m = measure.min_wall_thickness(shape, sample_count=samples, faces=faces)
            val = m["min_thickness_mm"]
            if val is None:
                chk.measure("min_wall", -1.0, "mm", min=limit, requirement=requirement,
                            remediation=f"{rule['id']}: no opposite-wall hit found ({m['resolution_note']}).")
            else:
                chk.measure("min_wall", val, "mm", min=limit, location=str(m["location_mm"]), requirement=requirement,
                            remediation=f"{rule['id']}: wall {val:.4f} mm at {m['location_mm']} is below the "
                                        f"{limit:.4f} mm {rule['source']}. Thicken the wall there.")

        elif family == "geometry.hole_diameter":
            holes = measure.find_holes(shape)
            if not holes:
                raise SpecError(f"{rule['id']}: find_holes() found no holes to check (see its heuristic limits)")
            for h in holes:
                dia = 2.0 * h["radius_mm"]
                chk.measure(f"hole_{h['face_index']}_diameter", dia, "mm", min=limit, requirement=requirement,
                            remediation=f"{rule['id']}: hole at face {h['face_index']} is Ø{dia:.3f} mm, below the "
                                        f"{limit:.4f} mm minimum ({rule['source']}). Enlarge the hole.")

        elif family == "geometry.clearance":
            other_mod = entry.get("other_module")
            if not other_mod:
                raise SpecError(f"{rule['id']}: geometry.clearance needs 'other_module'")
            other = load.load_part(project / other_mod, params=params)
            m = measure.clearance(shape, other)
            chk.measure("clearance", m["distance_mm"], "mm", min=limit, requirement=requirement,
                        remediation=f"{rule['id']}: clearance to {other_mod} is {m['distance_mm']:.4f} mm, below "
                                    f"the {limit:.4f} mm minimum ({rule['source']}).")

        elif family == "geometry.draft":
            faces_spec = entry.get("faces", "auto")
            all_faces = shape.faces()
            faces = measure.select_side_faces(shape, pull_direction=pull_direction) if faces_spec == "auto" \
                else [all_faces[i] for i in faces_spec]
            if not faces:
                raise SpecError(f"{rule['id']}: no faces selected for the draft check")
            results = measure.draft_angles(shape, faces, pull_direction=pull_direction)
            for r in results:
                chk.measure(f"draft_face_{r['face_index']}", r["draft_deg"], "deg", min=limit, requirement=requirement,
                            remediation=f"{rule['id']}: face {r['face_index']} draft {r['draft_deg']:.3f} deg is "
                                        f"below the {limit:.3f} deg minimum ({rule['source']}). Add draft.")

        elif family == "geometry.overhang":
            # FDM/SLA "maximum overhang without support": distinct from mold
            # draft (geometry.draft above). Mold draft measures a side
            # wall's angle from *vertical*; overhang measures a *downward-
            # facing* face's angle from *horizontal*. Reusing geometry.draft
            # here made every vertical wall (0 deg from vertical) fail a
            # "min 45 deg" overhang limit, since it isn't the same angle at
            # all (M8, review #1).
            faces_spec = entry.get("faces", "auto")
            all_faces = shape.faces()
            candidates = measure.select_downward_faces(shape, pull_direction=pull_direction) if faces_spec == "auto" \
                else [all_faces[i] for i in faces_spec]
            # Only genuinely downward-facing faces are overhangs -- a
            # vertical (or upward) face named explicitly is filtered out
            # here too, never evaluated as an overhang.
            down_faces = measure.filter_downward_faces(candidates, pull_direction=pull_direction)
            if not down_faces:
                # Nothing downward-facing was selected (e.g. an all-vertical
                # part, or an explicit face list that named only side
                # walls): there is no overhang to check, and that is a
                # clean pass, not an error or a silent no-op.
                chk.measure("overhang_none_found", True, "1", equals=True, requirement=requirement)
            else:
                results = measure.overhang_angles(shape, down_faces, pull_direction=pull_direction)
                for r in results:
                    angle = r["overhang_angle_from_horizontal_deg"]
                    chk.measure(f"overhang_face_{r['face_index']}", angle, "deg", min=limit, requirement=requirement,
                                remediation=f"{rule['id']}: face {r['face_index']} overhangs at {angle:.3f} deg "
                                            f"from horizontal, below the {limit:.3f} deg minimum ({rule['source']}). "
                                            "Add support material, add a chamfer/fillet, or reorient the part.")

        elif family == "geometry.min_radius":
            concave_only = bool(rule.get("concave_only", True))
            results = measure.min_radius(shape, concave_only=concave_only)
            if not results:
                raise SpecError(f"{rule['id']}: min_radius() found no matching cylindrical faces")
            for r in results:
                chk.measure(f"radius_face_{r['face_index']}", r["radius_mm"], "mm", min=limit, requirement=requirement,
                            remediation=f"{rule['id']}: face {r['face_index']} radius {r['radius_mm']:.3f} mm is "
                                        f"below the {limit:.3f} mm minimum ({rule['source']}). Increase the radius.")

        elif family == "geometry.hole_edge":
            boundary = shape.faces().sort_by(bd.Axis.Z)[-1 if entry.get("boundary_face", "top") == "top" else 0]
            holes = measure.find_holes(shape)
            if not holes:
                raise SpecError(f"{rule['id']}: find_holes() found no holes to check")
            all_faces = shape.faces()
            for h in holes:
                m = measure.hole_edge_distance(shape, all_faces[h["face_index"]], boundary)
                chk.measure(f"hole_{h['face_index']}_wall_to_edge", m["wall_to_edge_mm"], "mm", min=limit,
                            requirement=requirement,
                            remediation=f"{rule['id']}: hole at face {h['face_index']} is "
                                        f"{m['wall_to_edge_mm']:.3f} mm from the edge, below the {limit:.3f} mm "
                                        f"minimum ({rule['source']}). Move the hole inward or shrink it.")

        elif family == "geometry.boss_rib":
            faces = [shape.faces()[i] for i in entry["faces"]]
            samples = int(entry.get("sample_count", 400))
            if fast:
                samples = min(samples, 150)
            m = measure.boss_rib_thickness(shape, faces, nominal_wall_mm=nominal_wall_mm, sample_count=samples)
            ratio = m.get("ratio")
            if ratio is None:
                raise SpecError(f"{rule['id']}: boss_rib_thickness found no opposite-wall hit: {m['resolution_note']}")
            kw = {"max": limit} if comparison == "max_ratio_of_wall" else {"min": limit}
            chk.measure("boss_rib_ratio", ratio, "1", requirement=requirement,
                        remediation=f"{rule['id']}: ratio {ratio:.3f} violates the {limit:.3f} limit ({rule['source']}). "
                                    "Adjust the rib/boss thickness.", **kw)

        else:
            raise SpecError(f"rule {rule['id']!r} names an unhandled check_family {family!r}")

    return 0


def _apply_snap_fit(entry: dict[str, Any], *, part_name: str, project: Path, target: str,
                     materials: dict[str, dict[str, Any]], meta: dict[str, Any]) -> int:
    name = entry.get("name")
    if not name:
        raise SpecError("a [[snap_fit]] entry needs 'name'")
    material_id = entry.get("material")
    material = materials.get(material_id)
    if material is None:
        raise SpecError(f"snap_fit {name!r}: unknown material {material_id!r}; see references/rules/snap_fit.toml")
    requirement = entry.get("requirement")
    taper = entry.get("taper", "constant")
    eps = strain_mod.root_strain(deflection_mm=float(entry["deflection_mm"]), length_mm=float(entry["length_mm"]),
                                  thickness_mm=float(entry["thickness_mm"]), taper=taper)
    eps_pct = eps * 100.0
    frequent = bool(entry.get("frequent", False))
    if frequent:
        allowable = material.get("allowable_strain_frequent_pct")
        note = ""
        if allowable is None:
            allowable = material["allowable_strain_once_pct"] * float(meta.get("frequent_use_factor", 0.6))
            note = f" (no material-specific frequent value; applied the default {meta.get('frequent_use_factor', 0.6)}x factor)"
        source_note = material["source"] + note
    else:
        allowable = material["allowable_strain_once_pct"]
        source_note = material["source"]

    warn = strain_mod.short_arm_warning(length_mm=float(entry["length_mm"]), thickness_mm=float(entry["thickness_mm"]))
    check_id = f"dfm.snap_fit.{name}.{part_name}"
    with checkresult.run_check(check_id, target, project=project) as chk:
        chk.tool("forge_cad.strain", "1")
        notes = warn or None
        chk.measure("root_strain_pct", eps_pct, "1", max=allowable, requirement=requirement,
                    remediation=f"Root strain {eps_pct:.3f}% exceeds the {material['name']} allowable "
                                f"{allowable:.3f}% ({source_note}). Increase length, reduce deflection, "
                                "thicken the root, or switch to a tapered arm (higher k).")
    return 0


def _iter_specs(project: Path, changed: list[str]) -> list[Path]:
    spec_dir = project / "requirements" / "dfm"
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
            kept.append(spec_path)
    return kept


def _run_one(fn, *args: Any, **kwargs: Any) -> int:
    try:
        fn(*args, **kwargs)
    except SystemExit as exc:
        return int(exc.code or 0)
    return 0


def main(argv: list[str]) -> int:
    # Declares this entrypoint's check_id namespace so PostToolUse can bind a
    # fix message to the check that owns it, by check_id rather than which
    # out/verify/*.json file happens to have the newest mtime (M7, review #1).
    print("[FORGE_CHECK_ID_PREFIX] dfm.")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", default=".", type=Path)
    ap.add_argument("--changed", action="append", default=[])
    ap.add_argument("--fast", action="store_true")
    ns = ap.parse_args(argv)
    project = ns.project.resolve()

    specs = _iter_specs(project, ns.changed)
    if not specs:
        print("[SKIP] no requirements/dfm/*.toml specs to check")
        return 0

    params = _load_params(project)
    snap_meta, materials = _load_material_table()
    worst = 0

    for spec_path in specs:
        try:
            doc = tomllib.loads(spec_path.read_text())
        except tomllib.TOMLDecodeError as exc:
            print(f"[ERROR] {spec_path}: malformed TOML: {exc}", file=sys.stderr)
            return 2
        part_doc = doc.get("part", {})
        checks = doc.get("check", [])
        snap_fits = doc.get("snap_fit", [])
        if not checks and not snap_fits:
            print(f"[SKIP] {spec_path}: no [[check]] or [[snap_fit]] entries")
            continue

        part_name = part_doc.get("name")
        shape = None
        rules: dict[str, dict[str, Any]] = {}
        nominal_wall_mm = None
        pull_direction = tuple(part_doc.get("pull_direction", (0.0, 0.0, 1.0)))

        if checks:
            if not part_name or "module" not in part_doc or "process" not in part_doc:
                print(f"[ERROR] {spec_path}: [part] needs 'name', 'module' and 'process' for [[check]] entries",
                      file=sys.stderr)
                return 2
            try:
                shape = load.load_part(project / part_doc["module"], params=params)
                rules = _load_rule_table(part_doc["process"])
            except SpecError as exc:
                print(f"[ERROR] {spec_path}: {exc}", file=sys.stderr)
                return 2
            except Exception as exc:  # noqa: BLE001 -- fail closed: a build error is never a silent pass
                print(f"[ERROR] {spec_path}: part module failed to build: {type(exc).__name__}: {exc}", file=sys.stderr)
                return 2
            if "nominal_wall_param" in part_doc:
                try:
                    nominal_wall_mm = _param_value(params, part_doc["nominal_wall_param"])
                except SpecError as exc:
                    print(f"[ERROR] {spec_path}: {exc}", file=sys.stderr)
                    return 2

        for entry in checks:
            rule = rules.get(entry.get("rule"))
            if rule is None:
                print(f"[ERROR] {spec_path}: unknown rule {entry.get('rule')!r} for process {part_doc['process']!r}",
                      file=sys.stderr)
                return 2
            try:
                code = _run_one(_apply_dfm_check, entry, rule=rule, part_name=part_name, shape=shape,
                                 project=project, target=part_doc["module"], nominal_wall_mm=nominal_wall_mm,
                                 pull_direction=pull_direction, params=params, fast=ns.fast)
            except SpecError as exc:
                print(f"[ERROR] {spec_path}: {exc}", file=sys.stderr)
                return 2
            worst = max(worst, code)

        for entry in snap_fits:
            target = part_doc.get("module", str(spec_path))
            try:
                code = _run_one(_apply_snap_fit, entry, part_name=part_name or spec_path.stem, project=project,
                                 target=target, materials=materials, meta=snap_meta)
            except (SpecError, KeyError, ValueError) as exc:
                print(f"[ERROR] {spec_path}: {exc}", file=sys.stderr)
                return 2
            worst = max(worst, code)

    return worst


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
