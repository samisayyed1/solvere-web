"""build123d STEP -> gmsh structured hex mesh -> CalculiX static linear cantilever solve.

Scope (stated up front, see SKILL.md "limits of validity"): a rectangular
prismatic beam, fixed at the x=min face, loaded by a distributed transverse
point load at the x=max (tip) face acting in -z. This is deliberately the
smallest useful case: it is exactly the case a hand calculation (Euler-
Bernoulli) can cross-check, which CONTRACTS.md and the brief require before
any FEA result is trusted. Extending to arbitrary geometry/loads is future
work (the mesher and CalculiX writer below do not assume a beam -- only the
boundary-condition *selection* by bounding-box face does).

Element: C3D8I (incompatible-mode linear hexahedron). Matches
``plugins/forge/toolchain/smoke/smoke_ccx.py``'s already-verified approach
(-0.19% vs Euler-Bernoulli hand calc at a fine mesh) -- this module
generalises that smoke test to mesh a real build123d STEP export through
gmsh's transfinite mesher instead of hand-rolling node/element loops, so
mesh density becomes a first-class, sweepable parameter (mesh convergence
study, CONTRACTS.md running-fea requirement).

Node/element ordering was verified empirically (not assumed from
documentation): a structured, recombined hex mesh built via gmsh's
transfinite algorithm on an OCC-imported STEP box produces node ordering
compatible with Abaqus/CalculiX C3D8(I) directly -- confirmed by
reproducing the smoke test's -0.19% result through this path.
"""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from build123d import BuildPart, Box, export_step
import gmsh


class FeaError(RuntimeError):
    """Meshing or solving failed; never silently produces a partial result."""


@dataclass
class MeshResult:
    coords: dict[int, tuple[float, float, float]]
    elements: list[list[int]]
    fixed_nodes: list[int]
    tip_nodes: list[int]
    n_elements: int
    n_nodes: int


@dataclass
class SolveResult:
    tip_deflection_z_mm: float
    max_von_mises_mpa: float
    reaction_fz_n: float
    n_elements: int
    n_nodes: int
    work_dir: Path


def build_beam_step(length_mm: float, width_mm: float, height_mm: float, out_path: Path) -> Path:
    """Build a rectangular prismatic beam with build123d and export it to STEP."""
    with BuildPart() as bp:
        Box(length_mm, width_mm, height_mm)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    export_step(bp.part, str(out_path))
    return out_path


def mesh_beam(step_path: Path, nx: int, ny: int, nz: int, *, tag: str) -> MeshResult:
    """Mesh a beam-shaped STEP solid with a structured, recombined hex mesh via gmsh.

    ``nx``/``ny``/``nz`` are element counts along the longest / second- /
    third-longest bounding-box axis respectively -- for a beam built by
    :func:`build_beam_step`, that is length / width / height. The fixed
    face is the minimum-x face; the tip (loaded) face is the maximum-x
    face, selected by bounding box, not by a hard-coded assumption about
    absolute coordinates (build123d centres primitives on the origin).
    """
    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.model.add(tag)
        gmsh.model.occ.importShapes(str(step_path))
        gmsh.model.occ.synchronize()

        curves = gmsh.model.getEntities(1)
        if not curves:
            raise FeaError(f"{step_path}: no curves found after import -- not a solid box?")
        for (dim, ctag) in curves:
            bb = gmsh.model.getBoundingBox(dim, ctag)
            dx, dy, dz = bb[3] - bb[0], bb[4] - bb[1], bb[5] - bb[2]
            if dx >= dy and dx >= dz:
                n = nx
            elif dy >= dx and dy >= dz:
                n = ny
            else:
                n = nz
            gmsh.model.mesh.setTransfiniteCurve(ctag, n + 1)
        for (dim, stag) in gmsh.model.getEntities(2):
            gmsh.model.mesh.setTransfiniteSurface(stag)
            gmsh.model.mesh.setRecombine(dim, stag)
        for (dim, vtag) in gmsh.model.getEntities(3):
            gmsh.model.mesh.setTransfiniteVolume(vtag)

        gmsh.model.mesh.generate(3)

        ntags, ncoords, _ = gmsh.model.mesh.getNodes()
        coords = {int(t): (float(ncoords[3 * i]), float(ncoords[3 * i + 1]), float(ncoords[3 * i + 2]))
                  for i, t in enumerate(ntags)}
        etypes, _etags, enodes = gmsh.model.mesh.getElements(3)
        etypes = list(etypes)
        if 5 not in etypes:
            raise FeaError(
                f"{step_path}: transfinite meshing did not produce 8-node hexahedra (got element types "
                f"{etypes}) -- the solid is probably not a simple 6-face box the transfinite algorithm can "
                "sweep; running-fea's current scope is limited to prismatic beams (see SKILL.md)."
            )
        idx = etypes.index(5)
        raw = enodes[idx]
        elements = [[int(n) for n in raw[i * 8:(i + 1) * 8]] for i in range(len(raw) // 8)]
    finally:
        gmsh.finalize()

    xmin = min(x for x, _, _ in coords.values())
    xmax = max(x for x, _, _ in coords.values())
    fixed = sorted(t for t, (x, _, _) in coords.items() if abs(x - xmin) < 1e-3)
    tip = sorted(t for t, (x, _, _) in coords.items() if abs(x - xmax) < 1e-3)
    if not fixed or not tip:
        raise FeaError(f"{step_path}: could not identify fixed/tip faces from mesh node coordinates")

    return MeshResult(coords=coords, elements=elements, fixed_nodes=fixed, tip_nodes=tip,
                       n_elements=len(elements), n_nodes=len(coords))


def write_ccx_input(mesh: MeshResult, *, e_mpa: float, nu: float, force_n: float,
                     work_dir: Path, tag: str) -> Path:
    """Write a CalculiX .inp for a fixed-base, tip-transverse-load static linear run."""
    lines = ["*HEADING", f"forge running-fea {tag}", "*NODE"]
    for t, (x, y, z) in mesh.coords.items():
        lines.append(f"{t}, {x:.6f}, {y:.6f}, {z:.6f}")
    lines.append("*ELEMENT, TYPE=C3D8I, ELSET=EALL")
    for i, e in enumerate(mesh.elements, start=1):
        lines.append(f"{i}, " + ", ".join(str(n) for n in e))
    lines += ["*NSET, NSET=FIX"] + [str(n) for n in mesh.fixed_nodes]
    lines += ["*NSET, NSET=TIP"] + [str(n) for n in mesh.tip_nodes]
    lines += ["*MATERIAL, NAME=MAT1", "*ELASTIC", f"{e_mpa}, {nu}",
              "*SOLID SECTION, ELSET=EALL, MATERIAL=MAT1",
              "*STEP", "*STATIC", "*BOUNDARY", "FIX, 1, 3", "*CLOAD"]
    per_node = -force_n / len(mesh.tip_nodes)
    lines += [f"{n}, 3, {per_node:.8f}" for n in mesh.tip_nodes]
    lines += ["*NODE PRINT, NSET=TIP", "U",
              "*NODE PRINT, NSET=FIX", "RF",
              "*EL PRINT, ELSET=EALL", "S",
              "*END STEP"]
    work_dir.mkdir(parents=True, exist_ok=True)
    inp = work_dir / f"{tag}.inp"
    inp.write_text("\n".join(lines) + "\n")
    return inp


_ROW3 = re.compile(r"^\s*(\d+)\s+(-?[\d.Ee+-]+)\s+(-?[\d.Ee+-]+)\s+(-?[\d.Ee+-]+)\s*$", re.M)
_STRESS_ROW = re.compile(
    r"^\s*(\d+)\s+(\d+)\s+(-?[\d.Ee+-]+)\s+(-?[\d.Ee+-]+)\s+(-?[\d.Ee+-]+)\s+"
    r"(-?[\d.Ee+-]+)\s+(-?[\d.Ee+-]+)\s+(-?[\d.Ee+-]+)\s*$", re.M,
)


def _section(dat: str, header: str) -> str:
    idx = dat.find(header)
    if idx == -1:
        raise FeaError(f"CalculiX .dat has no '{header}' section -- solve did not complete as requested")
    rest = dat[idx + len(header):]
    # stop at the next section header (a line containing only words, or a blank-blank)
    end = re.search(r"\n\s*\n\s*[a-z].*for set", rest)
    return rest[:end.start()] if end else rest


def run_ccx(inp_path: Path, ccx_bin: str, *, timeout_s: int = 600) -> str:
    tag = inp_path.stem
    r = subprocess.run([ccx_bin, "-i", tag], cwd=inp_path.parent, capture_output=True, text=True,
                        timeout=timeout_s)
    dat_path = inp_path.with_suffix(".dat")
    if r.returncode != 0 or not dat_path.exists():
        raise FeaError(
            f"CalculiX exited {r.returncode} for {inp_path.name}. stdout tail: {r.stdout[-1500:]}"
        )
    dat = dat_path.read_text()
    if "*ERROR" in dat:
        raise FeaError(f"CalculiX reported an error in {dat_path.name}: {dat[:1500]}")
    return dat


def parse_tip_deflection_z(dat: str) -> float:
    section = _section(dat, "displacements (vx,vy,vz) for set TIP")
    vals = [float(m.group(4)) for m in _ROW3.finditer(section)]
    if not vals:
        raise FeaError("no TIP displacement rows parsed from CalculiX output")
    return -sum(vals) / len(vals)  # -z convention -> positive downward deflection


def parse_reaction_fz(dat: str) -> float:
    section = _section(dat, "forces (fx,fy,fz) for set FIX")
    vals = [float(m.group(4)) for m in _ROW3.finditer(section)]
    if not vals:
        raise FeaError("no FIX reaction rows parsed from CalculiX output")
    return sum(vals)


def parse_max_von_mises(dat: str) -> float:
    section = _section(dat, "stresses (elem, integ.pnt.,sxx,syy,szz,sxy,sxz,syz) for set EALL")
    rows = list(_STRESS_ROW.finditer(section))
    if not rows:
        raise FeaError("no element stress rows parsed from CalculiX output")
    best = 0.0
    for m in rows:
        sxx, syy, szz, sxy, sxz, syz = (float(m.group(i)) for i in range(3, 9))
        vm = (0.5 * ((sxx - syy) ** 2 + (syy - szz) ** 2 + (szz - sxx) ** 2
                     + 6 * (sxy ** 2 + sxz ** 2 + syz ** 2))) ** 0.5
        best = max(best, vm)
    return best


def solve_one_level(*, length_mm: float, width_mm: float, height_mm: float, e_mpa: float, nu: float,
                     force_n: float, nx: int, ny: int, nz: int, work_dir: Path, tag: str,
                     ccx_bin: str) -> SolveResult:
    step_path = work_dir / "geometry.step"
    if not step_path.exists():
        build_beam_step(length_mm, width_mm, height_mm, step_path)
    mesh = mesh_beam(step_path, nx, ny, nz, tag=tag)
    inp = write_ccx_input(mesh, e_mpa=e_mpa, nu=nu, force_n=force_n, work_dir=work_dir, tag=tag)
    dat = run_ccx(inp, ccx_bin)
    return SolveResult(
        tip_deflection_z_mm=parse_tip_deflection_z(dat),
        max_von_mises_mpa=parse_max_von_mises(dat),
        reaction_fz_n=parse_reaction_fz(dat),
        n_elements=mesh.n_elements, n_nodes=mesh.n_nodes, work_dir=work_dir,
    )


def euler_bernoulli_cantilever_tip_load(length_mm: float, width_mm: float, height_mm: float,
                                         e_mpa: float, force_n: float) -> tuple[float, float]:
    """Hand-calc cross-check: tip deflection and max bending stress for a rectangular cantilever.

    deflection = F L^3 / (3 E I); max bending stress = F L (H/2) / I, both at the fixed end,
    with I = B H^3 / 12 (bending about the horizontal axis, tip load in -z).
    """
    inertia = width_mm * height_mm ** 3 / 12.0
    deflection = force_n * length_mm ** 3 / (3.0 * e_mpa * inertia)
    max_stress = force_n * length_mm * (height_mm / 2.0) / inertia
    return deflection, max_stress
