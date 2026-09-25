"""General solid linear-static FEA: STEP / build123d part -> gmsh tet10 -> CalculiX C3D10.

Pipeline for one ``analysis/fea/<case>.toml`` (schema: SKILL.md "General case file"):

1. Geometry: a STEP file, or a build123d script whose ``object`` (a Part or a zero-argument
   function returning one) is exported to STEP. Exactly one solid; assemblies/contact refused.
2. Faces: boundary conditions, loads, refinement zones, stress-exclusion zones and hand-calc
   probes name CAD faces through geometric selectors (face_select.py) -- never mesh node ids.
3. Mesh: gmsh unstructured 2nd-order tetrahedra at each of >= 3 global sizes, with distance
   threshold size fields around declared ``[[refine]]`` faces that scale with the level.
   gmsh tet10 -> CalculiX C3D10 node permutation from tet10.py, re-proved on every mesh.
4. Loads: consistent nodal forces from tri6 surface quadrature (uniform force, normal
   pressure, torque with Saint-Venant tau ~ r distribution) or a (singular) point force.
5. Constraints: a rigid-body-mode rank check BEFORE solving -- ccx 2.23 + SPOOLES was
   observed to finish an unconstrained model with "Job finished" and |u| ~ 1e10 mm.
6. Solve with CalculiX (*STATIC, linear geometry), read nodal U, RF and extrapolated S from
   the .frd; refuse any *ERROR, non-finite or absurd result.
7. Post: peak von Mises / max principal with location (optionally outside declared,
   justified exclusion zones), max displacement with location, face-mean displacement,
   face rotation, reaction force + moment balance.
8. Study: hand-calc comparison at the finest level, % change between the two finest levels
   for every quantity of interest, observed order / Richardson estimate, and a divergence
   test that flags stress singularities instead of trusting them.

Limits of validity: linear elastic isotropic, small deflection/strain, static, one solid,
no contact, no preload, no thermal load.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import runpy
import subprocess
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

import face_select
import handcalc
import material_bands
import tet10


class FeaError(RuntimeError):
    """Meshing, solving or post-processing failed; never produces a partial pass."""


class CaseError(ValueError):
    """The case file is malformed or incomplete (reported as exit 2)."""


# --------------------------------------------------------------------------- case schema

# S8: a maker agent could otherwise set its own acceptance bounds with no
# floor or ceiling (a safety factor requirement of 0.5, a 500% hand-calc
# tolerance, a 100% convergence tolerance all used to pass silently). The
# safety-factor floor is never waivable -- SF < 1 means the part is
# predicted to yield under the stated load. The hand-calc and convergence
# ceilings loosen a check meant to catch a bad mesh or a bad model, so they
# may be waived, but only by a signed [waiver] naming a human and a reason.
HARD_MIN_SAFETY_FACTOR = 1.0
CEILING_HAND_CALC_TOL_PCT = 10.0
CEILING_CONVERGENCE_TOL_PCT = 5.0

_TOP = {"case", "geometry", "material", "bc", "load", "refine", "stress", "mesh", "hand_calc",
        "requirement", "validity", "waiver"}
_SUB = {
    "case": {"name", "description"},
    "geometry": {"step", "build123d", "object"},
    "material": {"params", "name", "E_MPa", "nu", "yield_MPa", "density_kg_m3", "source"},
    "bc": {"name", "type", "faces", "dofs", "value_mm"},
    "load": {"name", "type", "faces", "vector_n", "pressure_mpa", "torque_nmm", "axis", "center_mm", "at_mm"},
    "refine": {"name", "faces", "size_factor", "dist_min_mm", "dist_max_mm"},
    "stress": {"exclude"},
    "exclude": {"faces", "distance_mm", "reason"},
    "mesh": {"sizes_mm", "convergence_tol_pct", "stress_convergence_tol_pct", "max_nodes", "high_order_optimize"},
    "hand_calc": {"name", "formula", "inputs", "fea", "tolerance_pct"},
    "fea": {"quantity", "faces", "component", "axis", "center_mm"},
    "requirement": {"min_safety_factor", "max_reaction_imbalance_pct"},
    "validity": {"max_displacement_ratio"},
    "waiver": {"signed_by", "reason", "date"},
}
QUANTITIES = {"face_mean_displacement": "mm", "face_rotation": "rad", "max_displacement": "mm",
              "peak_von_mises": "MPa", "peak_principal": "MPa"}
MAX_REACTION_IMBALANCE_PCT = 0.5     # brief: reactions must balance applied loads within 0.5 %
MIN_REFINEMENT_RATIO = 1.2           # a 1 % size change "converges" anything; refuse it
DIVERGENCE_ORDER = 0.25              # observed order below this while growing = singularity suspected


def _keys(table: dict, allowed: set[str], where: str) -> None:
    if not isinstance(table, dict):
        raise CaseError(f"{where} must be a table")
    unknown = set(table) - allowed
    if unknown:
        raise CaseError(f"{where}: unknown key(s) {sorted(unknown)} (allowed: {sorted(allowed)}) -- "
                        "typos are refused rather than silently ignored")


def _req(table: dict, where: str, *keys: str) -> None:
    missing = [k for k in keys if k not in table]
    if missing:
        raise CaseError(f"{where}: missing required key(s) {', '.join(missing)}")


_UNIT_MPA = {"Pa": 1e-6, "kPa": 1e-3, "MPa": 1.0, "N/mm2": 1.0, "N/mm^2": 1.0, "GPa": 1e3}
_UNIT_DENS = {"kg/m3": 1.0, "kg/m^3": 1.0, "g/cm3": 1e3, "g/cm^3": 1e3}


def _check_e_plausibility(name: str, e_mpa: float, source_note: str) -> None:
    """S8: catches a mistyped/unit-slipped E (see material_bands.py) for a
    material family we recognise by name. Never invents a value -- a name
    that matches no known family is simply not checked."""
    band = material_bands.implausible_e(name, e_mpa)
    if band is not None:
        keyword, lo, hi = band
        raise CaseError(
            f"[material] E = {e_mpa} MPa is implausible for a material named {name!r} (matched family "
            f"{keyword!r}, typical published range [{lo:,.0f}, {hi:,.0f}] MPa -- {source_note}). This usually "
            "means a GPa value was entered where MPa was expected (e.g. 210 instead of 210000 for steel). "
            "Fix the value, or rename [material].name if this genuinely isn't that family."
        )


def load_material(mat: dict, project: Path) -> dict:
    """E [MPa], nu, yield [MPa], density [kg/m3] + provenance, from params.toml or inline."""
    if "params" in mat:
        path = project / "params" / "params.toml"
        if not path.is_file():
            raise CaseError(f"[material].params = {mat['params']!r} but {path} does not exist")
        node = tomllib.loads(path.read_text())
        for part in str(mat["params"]).split("."):
            if not isinstance(node, dict) or part not in node:
                raise CaseError(f"params key {mat['params']!r} not found in params/params.toml")
            node = node[part]
        out, prov = {}, []
        for key, conv in (("E", _UNIT_MPA), ("nu", {"1": 1.0}), ("yield", _UNIT_MPA), ("density", _UNIT_DENS)):
            leaf = node.get(key) if isinstance(node, dict) else None
            if not isinstance(leaf, dict) or "value" not in leaf:
                raise CaseError(f"params {mat['params']}.{key} missing (need E, nu, yield, density leaves "
                                "each with value/unit/source -- CONTRACTS.md §2)")
            unit = str(leaf.get("unit", ""))
            if unit not in conv:
                raise CaseError(f"params {mat['params']}.{key} unit {unit!r} not one of {sorted(conv)}")
            if not str(leaf.get("source", "")).strip():
                raise CaseError(f"params {mat['params']}.{key} has no source -- no invented material properties")
            out[key] = float(leaf["value"]) * conv[unit]
            prov.append(f"{key}={leaf['value']} {unit} [{leaf.get('status', '?')}] ({leaf['source']})")
        name = mat.get("name", mat["params"])
        _check_e_plausibility(str(name), out["E"], f"params {mat['params']}.E")
        return {"name": name, "E": out["E"], "nu": out["nu"], "yield": out["yield"],
                "density": out["density"], "source": f"params {mat['params']}: " + "; ".join(prov)}
    _req(mat, "[material]", "E_MPa", "nu", "yield_MPa", "source")
    if not str(mat["source"]).strip():
        raise CaseError("[material].source is empty -- no invented material properties")
    name = mat.get("name", "?")
    e_mpa = float(mat["E_MPa"])
    _check_e_plausibility(str(name), e_mpa, "[material].E_MPa")
    return {"name": name, "E": e_mpa, "nu": float(mat["nu"]),
            "yield": float(mat["yield_MPa"]), "density": float(mat.get("density_kg_m3", float("nan"))),
            "source": str(mat["source"])}


def _check_waiver(data: dict, where: str) -> dict | None:
    """S8: a [waiver] table lets a human accept a hand-calc/convergence
    ceiling above the default -- but only when it actually names a human
    and says why. Returns the waiver table, or None if there isn't one."""
    w = data.get("waiver")
    if w is None:
        return None
    _keys(w, _SUB["waiver"], "[waiver]")
    _req(w, "[waiver]", "signed_by", "reason")
    if not str(w["signed_by"]).strip():
        raise CaseError(f"{where}: [waiver].signed_by must name a human -- an empty waiver waives nothing")
    if len(str(w["reason"]).strip()) < 10:
        raise CaseError(f"{where}: [waiver].reason must explain why the ceiling is being waived")
    return w


def load_case(path: Path, project: Path) -> dict:
    try:
        data = tomllib.loads(path.read_text())
    except tomllib.TOMLDecodeError as exc:
        raise CaseError(f"{path.name}: {exc}") from exc
    _keys(data, _TOP, path.name)
    for sect in ("case", "geometry", "material", "mesh", "requirement"):
        if sect not in data:
            raise CaseError(f"{path.name}: missing [{sect}] table")
    for sect in ("case", "geometry", "material", "mesh", "requirement", "stress", "validity"):
        if sect in data:
            _keys(data[sect], _SUB[sect], f"[{sect}]")
    _req(data["case"], "[case]", "name")
    geo = data["geometry"]
    if ("step" in geo) == ("build123d" in geo):
        raise CaseError("[geometry] needs exactly one of step = <path> or build123d = <script.py>")
    for arr, need in (("bc", ("name", "type", "faces")), ("load", ("name", "type")),
                      ("refine", ("faces", "size_factor", "dist_min_mm", "dist_max_mm")),
                      ("hand_calc", ("name", "formula", "fea", "tolerance_pct"))):
        items = data.get(arr, [])
        if not isinstance(items, list):
            raise CaseError(f"[[{arr}]] must be an array of tables")
        for i, it in enumerate(items):
            _keys(it, _SUB[arr], f"[[{arr}]] #{i}")
            _req(it, f"[[{arr}]] #{i}", *need)
    if not data.get("bc"):
        raise CaseError("at least one [[bc]] is required (an unsupported body has no static solution)")
    if not data.get("load") and not any(float(b.get("value_mm", 0.0)) != 0.0 for b in data["bc"]):
        raise CaseError("at least one [[load]] (or a non-zero prescribed displacement) is required")
    if not data.get("hand_calc"):
        raise CaseError("at least one [[hand_calc]] is required -- the hand-calc cross-check is mandatory. "
                        "If no closed form exists, the case is out of this skill's scope (SKILL.md).")
    names = [b["name"] for b in data["bc"]] + [ld["name"] for ld in data.get("load", [])] + [h["name"] for h in data["hand_calc"]]
    if len(names) != len(set(names)):
        raise CaseError("bc / load / hand_calc names must be unique")
    for i, hc in enumerate(data["hand_calc"]):
        _keys(hc["fea"], _SUB["fea"], f"[[hand_calc]] #{i} fea")
        _req(hc["fea"], f"[[hand_calc]] #{i} fea", "quantity")
        if hc["fea"]["quantity"] not in QUANTITIES:
            raise CaseError(f"[[hand_calc]] {hc['name']}: fea.quantity must be one of {sorted(QUANTITIES)}")
        if hc["fea"]["quantity"] in ("face_mean_displacement", "face_rotation") and "faces" not in hc["fea"]:
            raise CaseError(f"[[hand_calc]] {hc['name']}: {hc['fea']['quantity']} needs fea.faces")
        if float(hc["tolerance_pct"]) <= 0:
            raise CaseError(f"[[hand_calc]] {hc['name']}: tolerance_pct must be > 0")
    waiver = _check_waiver(data, path.name)
    for i, hc in enumerate(data["hand_calc"]):
        tol = float(hc["tolerance_pct"])
        if tol > CEILING_HAND_CALC_TOL_PCT and waiver is None:
            raise CaseError(
                f"[[hand_calc]] {hc['name']}: tolerance_pct = {tol} exceeds the {CEILING_HAND_CALC_TOL_PCT}% "
                "ceiling (S8) -- a looser tolerance stops the hand calc from actually cross-checking the FEA. "
                "Tighten it, or add a [waiver] with signed_by and reason naming a human who accepts the wider bound."
            )
    for i, ex in enumerate(data.get("stress", {}).get("exclude", [])):
        _keys(ex, _SUB["exclude"], f"[stress].exclude #{i}")
        _req(ex, f"[stress].exclude #{i}", "faces", "distance_mm", "reason")
        if len(str(ex["reason"]).strip()) < 10:
            raise CaseError(f"[stress].exclude #{i}: reason must say why the excluded stress is not physical")
    mesh = data["mesh"]
    _req(mesh, "[mesh]", "sizes_mm", "convergence_tol_pct")
    conv_tol = float(mesh["convergence_tol_pct"])
    if conv_tol > CEILING_CONVERGENCE_TOL_PCT and waiver is None:
        raise CaseError(
            f"[mesh].convergence_tol_pct = {conv_tol} exceeds the {CEILING_CONVERGENCE_TOL_PCT}% ceiling (S8) "
            "-- a looser tolerance calls an unconverged mesh converged. Tighten it, or add a [waiver] with "
            "signed_by and reason naming a human who accepts the wider bound."
        )
    stress_conv_tol = mesh.get("stress_convergence_tol_pct")
    if stress_conv_tol is not None and float(stress_conv_tol) > CEILING_CONVERGENCE_TOL_PCT and waiver is None:
        raise CaseError(
            f"[mesh].stress_convergence_tol_pct = {stress_conv_tol} exceeds the {CEILING_CONVERGENCE_TOL_PCT}% "
            "ceiling (S8). Tighten it, or add a [waiver] with signed_by and reason."
        )
    sizes = mesh["sizes_mm"]
    if not isinstance(sizes, list) or len(sizes) < 3:
        raise CaseError(f"[mesh].sizes_mm must list >= 3 refinement levels for a convergence study, got {sizes!r}")
    sizes = [float(s) for s in sizes]
    for a, b in zip(sizes, sizes[1:]):
        if b <= 0 or a / b < MIN_REFINEMENT_RATIO:
            raise CaseError(f"[mesh].sizes_mm must decrease by a ratio >= {MIN_REFINEMENT_RATIO} per level "
                            f"(got {a} -> {b}); tiny steps make any quantity look converged")
    req = data["requirement"]
    _req(req, "[requirement]", "min_safety_factor")
    min_sf = float(req["min_safety_factor"])
    if min_sf < HARD_MIN_SAFETY_FACTOR:
        raise CaseError(
            f"[requirement].min_safety_factor = {min_sf} is below the hard floor of {HARD_MIN_SAFETY_FACTOR} "
            "(S8) -- a safety factor requirement below 1.0 accepts a part predicted to yield under the stated "
            "load. This floor is never waivable; fix the requirement or the design."
        )
    if float(req.get("max_reaction_imbalance_pct", MAX_REACTION_IMBALANCE_PCT)) > MAX_REACTION_IMBALANCE_PCT:
        raise CaseError(f"[requirement].max_reaction_imbalance_pct may tighten but not exceed {MAX_REACTION_IMBALANCE_PCT} %")
    data["_material"] = load_material(data["material"], project)
    return data


# --------------------------------------------------------------------------- geometry

def prepare_step(case: dict, project: Path, work_root: Path) -> Path:
    geo = case["geometry"]
    if "step" in geo:
        p = (project / geo["step"]).resolve()
        if not p.is_file():
            raise CaseError(f"[geometry].step {geo['step']!r} not found under {project}")
        return p
    script = (project / geo["build123d"]).resolve()
    if not script.is_file():
        raise CaseError(f"[geometry].build123d {geo['build123d']!r} not found under {project}")
    obj_name = geo.get("object", "part")
    ns = runpy.run_path(str(script), run_name="forge_fea_geometry")
    if obj_name not in ns:
        raise CaseError(f"{script.name} defines no {obj_name!r} (set [geometry].object)")
    obj = ns[obj_name]
    if callable(obj):
        obj = obj()
    obj = getattr(obj, "part", obj)      # accept a BuildPart context too
    from build123d import export_step
    work_root.mkdir(parents=True, exist_ok=True)
    out = work_root / "geometry.step"
    export_step(obj, str(out))
    return out


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# --------------------------------------------------------------------------- mesh

@dataclass
class FaceSet:
    tags: list[int]
    tris: np.ndarray          # (k,6) node rows, gmsh tri6 order
    nodes: np.ndarray         # unique node rows


@dataclass
class Mesh:
    xyz: np.ndarray           # (n,3) mm; node id in CalculiX = row + 1
    tets: np.ndarray          # (m,10) node rows, CalculiX C3D10 order
    faces: dict[str, FaceSet]
    face_desc: dict[str, list[str]]
    h: float
    min_sj: float
    volume_mm3: float
    bbox: list[float]
    ordering: dict = field(default_factory=dict)


def refine_key(i: int, r: dict) -> str:
    return f"refine:{r.get('name', i)}"


def mesh_part(step: Path, *, h: float, selections: dict[str, object], refine: list[dict], max_nodes: int,
              high_order_optimize: int, msh_out: Path | None = None, permutation=tet10.GMSH_TO_CCX_TET10) -> Mesh:
    import gmsh
    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.option.setString("Geometry.OCCTargetUnit", "MM")
        gmsh.model.add("forge_fea")
        gmsh.model.occ.importShapes(str(step))
        gmsh.model.occ.synchronize()
        vols = gmsh.model.getEntities(3)
        if len(vols) != 1:
            raise FeaError(f"{step.name}: {len(vols)} solids found; running-fea handles exactly one solid "
                           "(no assemblies / contact). Fuse the part or analyse bodies separately.")
        vtag = vols[0][1]
        part_bb = list(gmsh.model.getBoundingBox(3, vtag))
        volume = gmsh.model.occ.getMass(3, vtag)
        infos = {t: face_select.face_info(t, vtag) for _, t in gmsh.model.getBoundary([(3, vtag)], oriented=False)}
        resolved: dict[str, list[int]] = {}
        for name, spec in selections.items():
            try:
                resolved[name] = face_select.select_faces(spec, vtag, part_bb, infos, name)
            except face_select.SelectorError as exc:
                raise CaseError(str(exc)) from exc

        fields = []
        for i, r in enumerate(refine):
            f_dist = gmsh.model.mesh.field.add("Distance")
            gmsh.model.mesh.field.setNumbers(f_dist, "SurfacesList", resolved[refine_key(i, r)])
            gmsh.model.mesh.field.setNumber(f_dist, "Sampling", 100)
            f_thr = gmsh.model.mesh.field.add("Threshold")
            gmsh.model.mesh.field.setNumber(f_thr, "InField", f_dist)
            gmsh.model.mesh.field.setNumber(f_thr, "SizeMin", float(r["size_factor"]) * h)
            gmsh.model.mesh.field.setNumber(f_thr, "SizeMax", h)
            gmsh.model.mesh.field.setNumber(f_thr, "DistMin", float(r["dist_min_mm"]))
            gmsh.model.mesh.field.setNumber(f_thr, "DistMax", float(r["dist_max_mm"]))
            fields.append(f_thr)
        if fields:
            f_min = gmsh.model.mesh.field.add("Min")
            gmsh.model.mesh.field.setNumbers(f_min, "FieldsList", fields)
            gmsh.model.mesh.field.setAsBackgroundMesh(f_min)
            gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
            gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
        gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
        gmsh.option.setNumber("Mesh.MeshSizeMax", h)
        gmsh.option.setNumber("Mesh.MeshSizeMin", min([h] + [float(r["size_factor"]) * h for r in refine]) * 0.5)
        gmsh.option.setNumber("Mesh.Algorithm3D", 1)
        gmsh.option.setNumber("Mesh.ElementOrder", 2)
        gmsh.option.setNumber("Mesh.HighOrderOptimize", int(high_order_optimize))
        gmsh.model.mesh.generate(3)

        ntags, ncoords, _ = gmsh.model.mesh.getNodes()
        ntags = np.asarray(ntags, dtype=np.int64)
        if ntags.size > max_nodes:
            raise FeaError(f"mesh at h={h} mm has {ntags.size} nodes > [mesh].max_nodes={max_nodes}; "
                           "coarsen sizes_mm or raise max_nodes knowingly")
        row = np.full(int(ntags.max()) + 1, -1, dtype=np.int64)
        row[ntags] = np.arange(ntags.size)
        xyz = np.asarray(ncoords, dtype=float).reshape(-1, 3)
        etypes, etags, enodes = gmsh.model.mesh.getElements(3)
        if list(etypes) != [11]:
            raise FeaError(f"expected only 10-node tetrahedra (gmsh type 11), got element types {list(etypes)}")
        gm = row[np.asarray(enodes[0], dtype=np.int64).reshape(-1, 10)]
        qual = gmsh.model.mesh.getElementQualities(list(etags[0]), "minSJ")
        min_sj = float(np.min(qual))
        faces: dict[str, FaceSet] = {}
        for name, tags in resolved.items():
            tris, nodes = [], []
            for t in tags:
                st, _, sn = gmsh.model.mesh.getElements(2, t)
                if list(st) != [9]:
                    raise FeaError(f"face #{t}: expected 6-node triangles (gmsh type 9), got {list(st)}")
                tris.append(row[np.asarray(sn[0], dtype=np.int64).reshape(-1, 6)])
                nodes.append(row[np.asarray(gmsh.model.mesh.getNodes(2, t, includeBoundary=True)[0], dtype=np.int64)])
            faces[name] = FaceSet(tags, np.vstack(tris), np.unique(np.concatenate(nodes)))
        if msh_out is not None:
            msh_out.parent.mkdir(parents=True, exist_ok=True)
            gmsh.write(str(msh_out))
    finally:
        gmsh.finalize()

    tets = gm[:, list(permutation)]
    mesh = Mesh(xyz=xyz, tets=tets, faces=faces,
                face_desc={n: [face_select.describe(infos[t]) for t in tags] for n, tags in resolved.items()},
                h=h, min_sj=min_sj, volume_mm3=volume, bbox=part_bb)
    mesh.ordering = tet10.ordering_report(xyz, tets)
    return mesh


# --------------------------------------------------------------------------- loads and constraints

def _outward_normals(mesh: Mesh, fs: FaceSet, nrm: np.ndarray) -> np.ndarray:
    """Flip each tri's quadrature normals so they point out of the solid (away from its tet)."""
    corners = np.sort(mesh.tets[:, :4], axis=1)
    lookup = {}
    for combo in ((0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3)):
        opp = [i for i in range(4) if i not in combo][0]
        keys = corners[:, combo]
        for e, k in enumerate(map(tuple, keys)):
            lookup[k] = (e, corners[e, opp])
    sign = np.empty(fs.tris.shape[0])
    for i, tri in enumerate(fs.tris):
        k = tuple(sorted(tri[:3]))
        if k not in lookup:
            raise FeaError("surface triangle not found on any tetrahedron face (non-conforming mesh)")
        _, opp = lookup[k]
        cen = mesh.xyz[tri[:3]].mean(axis=0)
        sign[i] = 1.0 if np.dot(nrm[i, 0], cen - mesh.xyz[opp]) > 0 else -1.0
    return nrm * sign[:, None, None]


def build_loads(case: dict, mesh: Mesh) -> tuple[np.ndarray, list[dict]]:
    """Nodal force array (n,3) in N and a per-load summary."""
    total = np.zeros_like(mesh.xyz)
    summary = []
    for ld in case.get("load", []):
        name, typ = ld["name"], ld["type"]
        if typ in ("force", "pressure", "torque"):
            if "faces" not in ld:
                raise CaseError(f"load {name}: type {typ} needs faces")
            fs = mesh.faces[f"load:{name}"]
            area, cen, _, pts, wj = tet10.face_integrals(mesh.xyz, fs.tris)
        if typ == "force":
            vec = np.asarray(ld.get("vector_n"), dtype=float)
            if vec.shape != (3,):
                raise CaseError(f"load {name}: vector_n must be [Fx, Fy, Fz] in N")
            f = tet10.consistent_nodal_forces(mesh.xyz, fs.tris, lambda p, n: np.broadcast_to(vec / area, p.shape))
            desc = f"uniform traction {vec / area} MPa over {area:.4g} mm2"
        elif typ == "pressure":
            if "pressure_mpa" not in ld:
                raise CaseError(f"load {name}: pressure needs pressure_mpa")
            p0 = float(ld["pressure_mpa"])
            _, _, nrm = tet10.tri6_quadrature(mesh.xyz, fs.tris)
            out_n = _outward_normals(mesh, fs, nrm)
            # traction = -p * outward normal (positive pressure pushes into the surface)
            f = tet10.consistent_nodal_forces(mesh.xyz, fs.tris, lambda p, n: -p0 * out_n)
            desc = f"pressure {p0} MPa (into surface) over {area:.4g} mm2"
        elif typ == "torque":
            t0 = float(ld["torque_nmm"])
            axis = np.asarray(ld.get("axis"), dtype=float)
            if axis.shape != (3,) or np.linalg.norm(axis) == 0:
                raise CaseError(f"load {name}: torque needs axis = [ax, ay, az]")
            axis = axis / np.linalg.norm(axis)
            c = np.asarray(ld.get("center_mm", cen), dtype=float)
            r = pts - c
            ar = np.cross(axis, r)
            jf = float(np.einsum("kq,kqd,kqd->", wj, ar, ar))
            f = tet10.consistent_nodal_forces(mesh.xyz, fs.tris, lambda p, n: (t0 / jf) * np.cross(axis, p - c))
            desc = f"torque {t0} N.mm about {axis} through {np.round(c, 4)} (tau ~ r, J_face={jf:.5g} mm4)"
        elif typ == "point_force":
            vec = np.asarray(ld.get("vector_n"), dtype=float)
            at = np.asarray(ld.get("at_mm"), dtype=float)
            if vec.shape != (3,) or at.shape != (3,):
                raise CaseError(f"load {name}: point_force needs vector_n and at_mm 3-vectors")
            node = int(np.argmin(np.linalg.norm(mesh.xyz - at, axis=1)))
            f = np.zeros_like(mesh.xyz)
            f[node] = vec
            mesh.faces[f"load:{name}"] = FaceSet([], np.zeros((0, 6), dtype=np.int64), np.array([node]))
            desc = (f"POINT force {vec} N at node nearest {at.tolist()} (dist "
                    f"{np.linalg.norm(mesh.xyz[node] - at):.3g} mm) -- singular by construction")
        else:
            raise CaseError(f"load {name}: type {typ!r} not in force | pressure | torque | point_force")
        total += f
        summary.append({"name": name, "type": typ, "resultant_n": f.sum(axis=0).tolist(), "desc": desc})
    return total, summary


def build_constraints(case: dict, mesh: Mesh) -> list[dict]:
    out = []
    for bc in case["bc"]:
        name, typ = bc["name"], bc["type"]
        fs = mesh.faces[f"bc:{name}"]
        value = float(bc.get("value_mm", 0.0))
        if typ == "fixed":
            dofs = [1, 2, 3]
            value = 0.0
        elif typ == "symmetry":
            spec = bc["faces"]
            if not isinstance(spec, dict) or "plane" not in spec:
                raise CaseError(f"bc {name}: symmetry needs a single axis-aligned plane selector (plane = x|y|z)")
            dofs = [{"x": 1, "y": 2, "z": 3}[spec["plane"]]]
            value = 0.0
        elif typ == "displacement":
            dofs = [int(d) for d in bc.get("dofs", [])]
            if not dofs or any(d not in (1, 2, 3) for d in dofs):
                raise CaseError(f"bc {name}: displacement needs dofs = subset of [1, 2, 3] (global x, y, z)")
        else:
            raise CaseError(f"bc {name}: type {typ!r} not in fixed | symmetry | displacement")
        out.append({"name": name, "nset": f"BC_{_safe(name)}", "nodes": fs.nodes, "dofs": dofs, "value": value})
    return out


def drop_constrained_loads(case: dict, mesh: Mesh, forces: np.ndarray, constraints: list[dict],
                           loads: list[dict]) -> np.ndarray:
    """Remove load components on constrained dofs (the support takes them directly).

    Legitimate on shared edges -- e.g. a pressure face meeting a symmetry plane, where the mirror
    half would supply that component. A CAD face that is itself both loaded and supported is a
    modelling error and is refused.
    """
    bc_tags = {t for bc in case["bc"] for t in mesh.faces[f"bc:{bc['name']}"].tags}
    for ld in case.get("load", []):
        shared = bc_tags.intersection(mesh.faces[f"load:{ld['name']}"].tags)
        if shared:
            raise CaseError(f"load {ld['name']} is applied to face(s) {sorted(shared)} that are also supported by a "
                            "[[bc]]; the support would absorb the load. Separate the loaded and supported faces.")
    mask = np.zeros_like(forces, dtype=bool)
    for con in constraints:
        for d in con["dofs"]:
            mask[con["nodes"], d - 1] = True
    dropped = np.where(mask, forces, 0.0)
    if np.any(dropped):
        tot = float(np.abs(forces).sum())
        frac = float(np.abs(dropped).sum()) / tot if tot else 0.0
        loads.append({"name": "(absorbed by supports)", "type": "info",
                      "resultant_n": dropped.sum(axis=0).tolist(),
                      "desc": f"load components on constrained dofs removed (shared edges with supports): "
                              f"{100 * frac:.3g} % of the summed |nodal load|, resultant {np.round(dropped.sum(axis=0), 6).tolist()} N"})
        if any(ld["type"] == "point_force" for ld in case.get("load", [])) and frac > 0.5:
            raise CaseError("a point load sits on a supported node; move it off the support")
    return np.where(mask, 0.0, forces)


_RB_NAMES = ["translation x", "translation y", "translation z", "rotation about x", "rotation about y",
             "rotation about z"]


def rigid_body_check(mesh: Mesh, constraints: list[dict]) -> list[str]:
    """Names of rigid-body modes the constraints leave free (empty = statically supported)."""
    c = mesh.xyz.mean(axis=0)
    scale = float(np.linalg.norm(np.ptp(mesh.xyz, axis=0))) or 1.0
    rows = []
    for con in constraints:
        r = (mesh.xyz[con["nodes"]] - c) / scale
        for d in con["dofs"]:
            e = np.zeros(3)
            e[d - 1] = 1.0
            blk = np.zeros((r.shape[0], 6))
            blk[:, d - 1] = 1.0
            # rotation mode k: u = e_k x r ; component d of that
            for k in range(3):
                ek = np.zeros(3)
                ek[k] = 1.0
                blk[:, 3 + k] = np.cross(ek, r)[:, d - 1]
            rows.append(blk)
    if not rows:
        return list(_RB_NAMES)
    a = np.vstack(rows)
    _, s, vt = np.linalg.svd(a, full_matrices=True)
    s_full = np.zeros(6)
    s_full[: s.size] = s
    null = vt[s_full < 1e-8 * max(s_full.max(), 1e-300)] if s_full.max() > 0 else vt
    free = []
    for v in null:
        free.append(" + ".join(f"{abs(v[i]):.2f}*{_RB_NAMES[i]}" for i in np.argsort(-np.abs(v))[:2] if abs(v[i]) > 0.1))
    return free


def _safe(name: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in name).upper()[:60]


# --------------------------------------------------------------------------- CalculiX I/O

def write_inp(path: Path, mesh: Mesh, mat: dict, constraints: list[dict], forces: np.ndarray) -> Path:
    lines = ["*HEADING", "forge running-fea general (C3D10)", "*NODE"]
    lines += [f"{i + 1}, {x:.10g}, {y:.10g}, {z:.10g}" for i, (x, y, z) in enumerate(mesh.xyz)]
    lines.append("*ELEMENT, TYPE=C3D10, ELSET=EALL")
    ids = mesh.tets + 1
    lines += [f"{e + 1}, " + ", ".join(map(str, ids[e, :8])) + ",\n" + ", ".join(map(str, ids[e, 8:]))
              for e in range(ids.shape[0])]
    for con in constraints:
        lines.append(f"*NSET, NSET={con['nset']}")
        n = con["nodes"] + 1
        lines += [", ".join(map(str, n[i:i + 10])) for i in range(0, n.size, 10)]
    lines += ["*MATERIAL, NAME=MAT1", "*ELASTIC", f"{mat['E']:.10g}, {mat['nu']:.10g}",
              "*SOLID SECTION, ELSET=EALL, MATERIAL=MAT1", "*STEP", "*STATIC", "*BOUNDARY"]
    for con in constraints:
        for d in con["dofs"]:
            lines.append(f"{con['nset']}, {d}, {d}, {con['value']:.10g}")
    fmax = float(np.abs(forces).max()) if forces.size else 0.0
    loaded = np.argwhere(np.abs(forces) > 1e-14 * max(fmax, 1e-300))
    if loaded.size:
        lines.append("*CLOAD")
        lines += [f"{n + 1}, {d + 1}, {forces[n, d]:.12g}" for n, d in loaded]
    lines += ["*NODE FILE", "U, RF", "*EL FILE", "S", "*END STEP"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")
    return path


def run_ccx(inp: Path, ccx_bin: str, timeout_s: int = 1800) -> str:
    env = dict(os.environ)
    nproc = str(min(8, os.cpu_count() or 1))
    env.update(OMP_NUM_THREADS=nproc, CCX_NPROC_EQUATION_SOLVER=nproc, CCX_NPROC_STIFFNESS=nproc,
               CCX_NPROC_RESULTS=nproc)
    try:
        r = subprocess.run([ccx_bin, "-i", inp.stem], cwd=inp.parent, capture_output=True, text=True,
                           timeout=timeout_s, env=env)
    except subprocess.TimeoutExpired as exc:
        raise FeaError(f"CalculiX timed out after {timeout_s} s on {inp.name}") from exc
    (inp.parent / f"{inp.stem}.ccx.log").write_text(r.stdout + r.stderr)
    dat = inp.with_suffix(".dat")
    text = r.stdout + (dat.read_text() if dat.exists() else "")
    bad = [ln.strip() for ln in text.splitlines()
           if "*ERROR" in ln or "singular" in ln.lower() or "zero pivot" in ln.lower()]
    if r.returncode != 0 or bad or "Job finished" not in r.stdout:
        raise FeaError(f"CalculiX failed on {inp.name} (exit {r.returncode}): "
                       + ("; ".join(bad[:5]) if bad else r.stdout[-800:]))
    return r.stdout


def read_frd(frd: Path, n_nodes: int) -> dict[str, np.ndarray]:
    """Nodal result blocks (DISP, FORC, STRESS) from a CalculiX ASCII .frd file."""
    want = {"DISP": 3, "FORC": 3, "STRESS": 6}
    out: dict[str, np.ndarray] = {}
    cur, arr = None, None
    with frd.open() as fh:
        for ln in fh:
            if ln.startswith(" -4"):
                name = ln.split()[1]
                if name in want:
                    cur, arr = name, np.full((n_nodes, want[name]), np.nan)
                else:
                    cur = None
            elif cur and ln.startswith(" -1"):
                nid = int(ln[3:13])
                arr[nid - 1] = [float(ln[13 + 12 * j: 25 + 12 * j]) for j in range(want[cur])]
            elif cur and ln.startswith(" -3"):
                out[cur] = arr
                cur = None
    missing = [k for k in want if k not in out]
    if missing:
        raise FeaError(f"{frd.name}: result block(s) {missing} missing -- solve incomplete")
    for k, v in out.items():
        if not np.all(np.isfinite(v)):
            raise FeaError(f"{frd.name}: non-finite values in {k} (singular or failed solve)")
    return out


# --------------------------------------------------------------------------- post-processing

def von_mises(s: np.ndarray) -> np.ndarray:
    sxx, syy, szz, sxy, syz, szx = s.T
    return np.sqrt(0.5 * ((sxx - syy) ** 2 + (syy - szz) ** 2 + (szz - sxx) ** 2)
                   + 3.0 * (sxy ** 2 + syz ** 2 + szx ** 2))


def principal(s: np.ndarray) -> np.ndarray:
    sxx, syy, szz, sxy, syz, szx = s.T
    t = np.stack([np.stack([sxx, sxy, szx], -1), np.stack([sxy, syy, syz], -1), np.stack([szx, syz, szz], -1)], -2)
    return np.linalg.eigvalsh(t)[:, ::-1]      # (n,3) s1 >= s2 >= s3


def _near(mesh: Mesh, name_nodes: np.ndarray, dist: float) -> np.ndarray:
    from scipy.spatial import cKDTree
    d, _ = cKDTree(mesh.xyz[name_nodes]).query(mesh.xyz, k=1)
    return d <= dist


def locate(mesh: Mesh, node: int) -> dict:
    p = mesh.xyz[node]
    best, best_d = None, float("inf")
    for name, fs in mesh.faces.items():
        if fs.nodes.size == 0:
            continue
        d = float(np.min(np.linalg.norm(mesh.xyz[fs.nodes] - p, axis=1)))
        if d < best_d:
            best, best_d = name, d
    return {"node": int(node) + 1, "xyz_mm": [round(float(v), 4) for v in p], "nearest_region": best,
            "distance_to_region_mm": round(best_d, 4)}


def loc_str(loc: dict) -> str:
    x, y, z = loc["xyz_mm"]
    s = f"x={x:.3f}, y={y:.3f}, z={z:.3f} mm (node {loc['node']}"
    if loc.get("nearest_region"):
        s += f"; {loc['distance_to_region_mm']:.2f} mm from '{loc['nearest_region']}'"
    return s + ")"


def post_process(case: dict, mesh: Mesh, res: dict, forces: np.ndarray, constraints: list[dict]) -> dict:
    u, rf, s = res["DISP"], res["FORC"], res["STRESS"]
    vm = von_mises(s)
    s1 = principal(s)[:, 0]
    umag = np.linalg.norm(u, axis=1)

    assessed = np.ones(mesh.xyz.shape[0], dtype=bool)
    for i, ex in enumerate(case.get("stress", {}).get("exclude", [])):
        assessed &= ~_near(mesh, mesh.faces[f"exclude:{i}"].nodes, float(ex["distance_mm"]))
    if not assessed.any():
        raise CaseError("[stress].exclude removes every node -- nothing left to assess")

    def peak(values: np.ndarray, mask: np.ndarray) -> tuple[float, dict]:
        idx = np.flatnonzero(mask)
        k = int(idx[np.argmax(values[idx])])
        return float(values[k]), locate(mesh, k)

    out: dict = {}
    out["peak_von_mises"], out["peak_von_mises_loc"] = peak(vm, assessed)
    out["peak_principal"], out["peak_principal_loc"] = peak(s1, assessed)
    out["global_peak_von_mises"], out["global_peak_von_mises_loc"] = peak(vm, np.ones_like(assessed))
    out["max_displacement"], out["max_displacement_loc"] = peak(umag, np.ones_like(assessed))

    # reactions: only on constrained (node, dof) pairs
    c = mesh.xyz.mean(axis=0)
    per_bc = {}
    constrained = np.zeros_like(forces, dtype=bool)
    for con in constraints:
        r = np.zeros(3)
        for d in con["dofs"]:
            constrained[con["nodes"], d - 1] = True
            r[d - 1] = float(rf[con["nodes"], d - 1].sum())
        per_bc[con["name"]] = r.tolist()
    # nodes shared by two BCs (common edges) would double-count per BC: total over the unique mask
    fr = np.where(constrained, rf, 0.0)
    reac = fr.sum(axis=0)
    reac_m = np.cross(mesh.xyz - c, fr).sum(axis=0)
    assert not np.any(forces[constrained]), "loads on constrained dofs must be removed before solving"
    fa = forces.sum(axis=0)
    ma = np.cross(mesh.xyz - c, forces).sum(axis=0)
    size = float(np.linalg.norm(np.ptp(mesh.xyz, axis=0)))
    # characteristic force / moment of the load case: a pure torque has ~0 net force, a pure force
    # can have ~0 moment about the centroid, so each balance is normalised by the larger scale.
    # prescribed-displacement-only cases: the reactions must balance each other
    r_bc = max([float(np.linalg.norm(v)) for v in per_bc.values()] + [0.0])
    f_char = max(float(np.linalg.norm(fa)), float(np.linalg.norm(ma)) / size, r_bc)
    m_char = max(float(np.linalg.norm(ma)), f_char * size)
    if f_char == 0:
        raise FeaError("applied loads and reactions are all zero -- nothing was loaded")
    force_pct = 100.0 * float(np.linalg.norm(fa + reac)) / f_char
    moment_pct = 100.0 * float(np.linalg.norm(ma + reac_m)) / m_char
    out["reaction_force_n"] = reac.tolist()
    out["applied_force_n"] = fa.tolist()
    out["reaction_by_bc_n"] = per_bc
    out["reaction_force_imbalance_pct"] = force_pct
    out["reaction_moment_imbalance_pct"] = moment_pct
    out["reaction_imbalance_pct"] = max(force_pct, moment_pct)

    out["hand_calc_fea"] = {}
    for hc in case["hand_calc"]:
        fea = hc["fea"]
        q = fea["quantity"]
        if q in ("peak_von_mises", "peak_principal", "max_displacement"):
            out["hand_calc_fea"][hc["name"]] = (out[q], out[f"{q}_loc"])
            continue
        fs = mesh.faces[f"hc:{hc['name']}"]
        area, cen, vals, pts, wj = tet10.face_integrals(mesh.xyz, fs.tris, u)
        if q == "face_mean_displacement":
            comp = str(fea.get("component", "magnitude"))
            sign = -1.0 if comp.startswith("-") else 1.0
            key = comp.lstrip("+-")
            if key == "magnitude":
                v = float(np.linalg.norm(np.einsum("kq,kqd->d", wj, vals) / area))
            elif key in ("x", "y", "z"):
                v = sign * float(np.einsum("kq,kq->", wj, vals[..., "xyz".index(key)]) / area)
            else:
                raise CaseError(f"hand_calc {hc['name']}: component must be x|y|z|-x|-y|-z|magnitude")
        else:  # face_rotation
            axis = np.asarray(fea.get("axis"), dtype=float)
            if axis.shape != (3,) or np.linalg.norm(axis) == 0:
                raise CaseError(f"hand_calc {hc['name']}: face_rotation needs axis = [ax, ay, az]")
            axis = axis / np.linalg.norm(axis)
            cc = np.asarray(fea.get("center_mm", cen), dtype=float)
            ar = np.cross(axis, pts - cc)
            v = float(np.einsum("kq,kqd,kqd->", wj, ar, vals) / np.einsum("kq,kqd,kqd->", wj, ar, ar))
        out["hand_calc_fea"][hc["name"]] = (v, {"face_mean_over": f"hc:{hc['name']}", "area_mm2": round(area, 4)})

    out["_vm"], out["_xyz"], out["_assessed"] = vm, mesh.xyz, assessed
    out["_point_nodes"] = {ld["name"]: int(mesh.faces[f"load:{ld['name']}"].nodes[0])
                           for ld in case.get("load", []) if ld["type"] == "point_force"}
    out["small_deflection_ratio"] = out["max_displacement"] / float(min(np.ptp(mesh.xyz, axis=0)))
    if not math.isfinite(out["max_displacement"]) or out["max_displacement"] > 10.0 * size:
        raise FeaError(f"max displacement {out['max_displacement']:.3g} mm is larger than the part itself "
                       f"({size:.3g} mm): the stiffness matrix is singular or nearly so (under-constrained model)")
    return out


# --------------------------------------------------------------------------- study

@dataclass
class LevelResult:
    h: float
    n_nodes: int
    n_elements: int
    min_sj: float
    ordering: dict
    post: dict
    loads: list
    work_dir: Path
    volume_mm3: float


def solve_level(case: dict, step: Path, h: float, work_dir: Path, ccx_bin: str, *, precheck: bool = True) -> LevelResult:
    sel: dict[str, object] = {}
    for bc in case["bc"]:
        sel[f"bc:{bc['name']}"] = bc["faces"]
    for ld in case.get("load", []):
        if "faces" in ld:
            sel[f"load:{ld['name']}"] = ld["faces"]
    for i, r in enumerate(case.get("refine", [])):
        sel[refine_key(i, r)] = r["faces"]
    for i, ex in enumerate(case.get("stress", {}).get("exclude", [])):
        sel[f"exclude:{i}"] = ex["faces"]
    for hc in case["hand_calc"]:
        if "faces" in hc["fea"]:
            sel[f"hc:{hc['name']}"] = hc["fea"]["faces"]
    mcfg = case["mesh"]
    mesh = mesh_part(step, h=h, selections=sel, refine=case.get("refine", []),
                     max_nodes=int(mcfg.get("max_nodes", 400_000)),
                     high_order_optimize=int(mcfg.get("high_order_optimize", 2)), msh_out=work_dir / "mesh.msh")
    if mesh.ordering["n_nonpositive_volume"] or mesh.ordering["max_midside_deviation"] > tet10.MAX_MIDSIDE_DEVIATION:
        raise FeaError(f"tet10 ordering/geometry check failed before solving: {mesh.ordering}")
    if mesh.min_sj <= 0:
        raise FeaError(f"mesh at h={h} mm has an inverted curved element (min scaled Jacobian {mesh.min_sj:.3g}); "
                       "refine near curved faces or keep [mesh].high_order_optimize = 2")
    forces, loads = build_loads(case, mesh)
    constraints = build_constraints(case, mesh)
    forces = drop_constrained_loads(case, mesh, forces, constraints, loads)
    if precheck:
        free = rigid_body_check(mesh, constraints)
        if free:
            raise FeaError("model is under-constrained -- free rigid-body mode(s): " + "; ".join(free)
                           + ". The stiffness matrix is singular; CalculiX/SPOOLES may still print 'Job finished' "
                           "with garbage displacements, so this is refused before solving. Add supports "
                           "(fixed / symmetry / displacement) that remove all six rigid-body modes.")
    inp = write_inp(work_dir / "model.inp", mesh, case["_material"], constraints, forces)
    run_ccx(inp, ccx_bin)
    res = read_frd(inp.with_suffix(".frd"), mesh.xyz.shape[0])
    post = post_process(case, mesh, res, forces, constraints)
    lr = LevelResult(h=h, n_nodes=int(mesh.xyz.shape[0]), n_elements=int(mesh.tets.shape[0]), min_sj=mesh.min_sj,
                     ordering=mesh.ordering, post=post, loads=loads, work_dir=work_dir,
                     volume_mm3=mesh.volume_mm3)
    (work_dir / "level.json").write_text(json.dumps(
        {"h_mm": h, "n_nodes": lr.n_nodes, "n_elements": lr.n_elements, "min_scaled_jacobian": lr.min_sj,
         "tet10_ordering": lr.ordering, "loads": loads, "faces": mesh.face_desc,
         "post": {k: v for k, v in post.items() if not k.startswith("_")}}, indent=2, default=_json_default))
    return lr


def _json_default(o):
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    if isinstance(o, np.ndarray):
        return o.tolist()
    return str(o)


def convergence(values: list[float], sizes: list[float], tol_pct: float) -> dict:
    """% change between the two finest levels, observed order, Richardson estimate, divergence flag."""
    f1, f2, f3 = values[-3:]
    h1, h2, h3 = sizes[-3:]
    d1, d2 = f2 - f1, f3 - f2
    change = abs(d2) / abs(f2) * 100.0 if f2 != 0 else float("inf")
    r = math.sqrt((h1 / h2) * (h2 / h3))
    p = None
    if d1 != 0 and d2 != 0 and (d1 > 0) == (d2 > 0):
        p = math.log(abs(d1) / abs(d2)) / math.log(r)
    converged = change <= tol_pct
    growing = d1 > 0 and d2 > 0
    diverging = (not converged) and growing and (p is None or p < DIVERGENCE_ORDER)
    richardson = f3 + d2 / (r ** p - 1.0) if (p is not None and p > 0) else None
    gci = 1.25 * abs(d2 / f3) / (r ** p - 1.0) * 100.0 if (p is not None and p > 0 and f3 != 0) else None
    state = "converged" if converged else ("diverging" if diverging else "not_converged")
    return {"values": values, "sizes_mm": sizes, "change_pct": change, "observed_order": p,
            "richardson": richardson, "gci_fine_pct": gci, "converged": converged, "diverging": diverging,
            "state": state, "tol_pct": tol_pct}


def hotspot_series(levels: list[LevelResult], point: np.ndarray, radius: float, assessed_only: bool) -> list[float]:
    """Max von Mises inside a FIXED ball around ``point`` at every level.

    Bounded fields make this converge (the ball's true maximum); a singularity at ``point``
    makes it grow without bound as nodes approach the singular point.
    """
    vals = []
    for lv in levels:
        d = np.linalg.norm(lv.post["_xyz"] - point, axis=1)
        m = d <= radius
        if assessed_only:
            m &= lv.post["_assessed"]
        if not m.any():
            m = d <= d.min()
        vals.append(float(lv.post["_vm"][m].max()))
    return vals


def track_hotspots(levels: list[LevelResult], sizes: list[float], tol: float) -> list[dict]:
    fin = levels[-1].post
    radius = 0.5 * sizes[0]
    spots = [("assessed peak", fin["peak_von_mises_loc"], True),
             ("global peak (incl. excluded zones)", fin["global_peak_von_mises_loc"], False)]
    for name, node in fin["_point_nodes"].items():
        spots.append((f"point load '{name}'", locate_from(levels[-1], node), False))
    out = []
    for label, loc, assessed_only in spots:
        pt = np.asarray(loc["xyz_mm"], dtype=float)
        node = loc["node"] - 1
        in_assessed = bool(fin["_assessed"][node])
        vals = hotspot_series(levels, pt, radius, assessed_only and in_assessed)
        out.append({"label": label, "location": loc, "radius_mm": radius, "assessed": in_assessed,
                    "conv": convergence(vals, sizes, tol)})
    return out


def locate_from(level: LevelResult, node: int) -> dict:
    p = level.post["_xyz"][node]
    return {"node": int(node) + 1, "xyz_mm": [round(float(v), 4) for v in p], "nearest_region": None,
            "distance_to_region_mm": 0.0}


def run_study(case: dict, project: Path, work_root: Path, ccx_bin: str, *, precheck: bool = True) -> dict:
    step = prepare_step(case, project, work_root)
    sizes = [float(s) for s in case["mesh"]["sizes_mm"]]
    levels = [solve_level(case, step, h, work_root / f"level{i}_h{h:g}mm", ccx_bin, precheck=precheck)
              for i, h in enumerate(sizes)]
    mat = case["_material"]
    tol = float(case["mesh"]["convergence_tol_pct"])
    stol = float(case["mesh"].get("stress_convergence_tol_pct", tol))
    fin = levels[-1].post
    hcs = []
    for hc in case["hand_calc"]:
        calc = handcalc.evaluate(hc["formula"], hc.get("inputs", {}), mat["E"], mat["nu"])
        q = hc["fea"]["quantity"]
        if calc.unit != QUANTITIES[q]:
            raise CaseError(f"hand_calc {hc['name']}: formula gives {calc.unit} but fea.quantity {q} is {QUANTITIES[q]}")
        vals = [lv.post["hand_calc_fea"][hc["name"]][0] for lv in levels]
        is_stress = q in ("peak_von_mises", "peak_principal")
        fea_v, loc = fin["hand_calc_fea"][hc["name"]]
        hcs.append({"name": hc["name"], "quantity": q, "unit": calc.unit, "hand": calc.value, "fea": fea_v,
                    "diff_pct": (fea_v - calc.value) / calc.value * 100.0, "tol_pct": float(hc["tolerance_pct"]),
                    "formula": calc.formula, "reference": calc.reference, "notes": calc.notes, "location": loc,
                    "conv": convergence(vals, sizes, stol if is_stress else tol)})
    stress_conv = convergence([lv.post["peak_von_mises"] for lv in levels], sizes, stol)
    global_conv = convergence([lv.post["global_peak_von_mises"] for lv in levels], sizes, stol)
    hotspots = track_hotspots(levels, sizes, stol)
    study = {
        "case": case["case"]["name"], "step": str(step), "step_sha256": sha256(step), "material": mat,
        "sizes_mm": sizes, "levels": levels, "hand_calcs": hcs, "stress_conv": stress_conv,
        "global_stress_conv": global_conv, "hotspots": hotspots,
        "singularity_suspected": any(hs["assessed"] and hs["conv"]["diverging"] for hs in hotspots),
        "safety_factor": mat["yield"] / fin["peak_von_mises"] if fin["peak_von_mises"] > 0 else float("inf"),
        "reaction_imbalance_pct": max(lv.post["reaction_imbalance_pct"] for lv in levels),
        "small_deflection_ratio": fin["small_deflection_ratio"],
        "max_midside_deviation": max(lv.ordering["max_midside_deviation"] for lv in levels),
        "volume_mm3": levels[-1].volume_mm3,
        "mass_kg": mat["density"] * levels[-1].volume_mm3 * 1e-9,
    }
    (work_root / "summary.json").write_text(json.dumps(
        {k: v for k, v in study.items() if k != "levels"} | {"levels": [
            {"h_mm": lv.h, "n_nodes": lv.n_nodes, "n_elements": lv.n_elements, "min_sj": lv.min_sj,
             "peak_von_mises_mpa": lv.post["peak_von_mises"], "peak_loc": lv.post["peak_von_mises_loc"],
             "global_peak_von_mises_mpa": lv.post["global_peak_von_mises"],
             "global_peak_loc": lv.post["global_peak_von_mises_loc"],
             "max_displacement_mm": lv.post["max_displacement"], "max_disp_loc": lv.post["max_displacement_loc"],
             "reaction_imbalance_pct": lv.post["reaction_imbalance_pct"],
             "hand_calc_fea": lv.post["hand_calc_fea"]} for lv in levels]},
        indent=2, default=_json_default))
    return study

