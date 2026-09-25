#!/usr/bin/env python3
"""Verify entrypoint for running-fea (CONTRACTS.md §9).

For each ``analysis/fea/<case>.toml`` (or just ``--changed`` ones): builds
the beam geometry with build123d, meshes it with gmsh at every declared
refinement level, solves each level with CalculiX, cross-checks the
finest level against an Euler-Bernoulli hand calculation, checks mesh
convergence across the levels, computes a safety factor against the
material yield, and checks the reaction-force balance. Writes
``out/verify/sim.fea_<case>.json`` and emits the check at level L2 only
when both the hand-calc and the convergence study pass (otherwise L1) --
CONTRACTS.md §4 evidence levels.

    forge-python skills/running-fea/scripts/verify.py --project <root> [--changed <path> ...] [--fast]

Two case schemas (SKILL.md): a case whose ``[geometry]`` names ``step`` or
``build123d`` runs the GENERAL path (general_fea.py: any single solid, gmsh
tet10 -> CalculiX C3D10, face selectors, hand calcs, convergence and
singularity detection); a case with ``length_mm/width_mm/height_mm`` runs the
original structured-hex BOX path below (mesh_and_solve.py, cantilever only).
Limits of validity for both: linear elastic, small deflection, static, no contact.
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
import mesh_and_solve as m  # noqa: E402

_SAFE = re.compile(r"[^a-z0-9_]+")
DEFAULT_CCX = Path.home() / ".forge" / "bin" / "ccx"


def _safe_name(name: str) -> str:
    slug = _SAFE.sub("_", name.strip().lower()).strip("_")
    return slug or "case"


def _find_case_files(project: Path, changed: list[str]) -> list[Path]:
    cases_dir = project / "analysis" / "fea"
    if changed:
        out = []
        for c in changed:
            p = (project / c).resolve() if not Path(c).is_absolute() else Path(c)
            try:
                p.relative_to(cases_dir.resolve())
            except ValueError:
                continue
            if p.suffix == ".toml" and p.exists():
                out.append(p)
        return sorted(out)
    if not cases_dir.is_dir():
        return []
    return sorted(cases_dir.glob("*.toml"))


def _require(d: dict, path: str, keys: list[str]) -> None:
    missing = [k for k in keys if k not in d]
    if missing:
        raise ValueError(f"[{path}] missing required key(s): {', '.join(missing)}")


def _load_case(path: Path) -> dict:
    data = tomllib.loads(path.read_text())
    if "case" not in data:
        raise ValueError(f"{path}: missing [case] table")
    _require(data["case"], "case", ["name"])
    for section, keys in (
        ("geometry", ["length_mm", "width_mm", "height_mm"]),
        ("material", ["E_MPa", "nu", "yield_MPa", "source"]),
        ("load", ["force_n"]),
        ("mesh", ["levels", "convergence_tol_pct"]),
        ("hand_calc", ["deflection_tolerance_pct", "stress_tolerance_pct"]),
        ("requirement", ["min_safety_factor", "max_reaction_imbalance_pct"]),
    ):
        if section not in data:
            raise ValueError(f"{path}: missing [{section}] table")
        _require(data[section], section, keys)
    levels = data["mesh"]["levels"]
    if not isinstance(levels, list) or len(levels) < 3:
        raise ValueError(
            f"{path}: [mesh].levels must have >= 3 refinement levels for a convergence study, got "
            f"{len(levels) if isinstance(levels, list) else levels!r}"
        )
    for lvl in levels:
        if not (isinstance(lvl, list) and len(lvl) == 3):
            raise ValueError(f"{path}: each [mesh].levels entry must be [nx, ny, nz], got {lvl!r}")
    return data


def _is_general(case_path: Path) -> bool:
    """General (tet10) schema: [geometry] names a STEP file or a build123d script."""
    try:
        geo = tomllib.loads(case_path.read_text()).get("geometry", {})
    except tomllib.TOMLDecodeError:
        return False
    return isinstance(geo, dict) and ("step" in geo or "build123d" in geo)


def _run_general(case_path: Path, project: Path, ccx_bin: str) -> int:
    import general_fea as g
    import general_report as rep

    target = str(case_path.relative_to(project)) if case_path.is_relative_to(project) else str(case_path)
    try:
        case = g.load_case(case_path, project)
    except (g.CaseError, ValueError) as exc:
        chk = Check(f"sim.fea_{_safe_name(case_path.stem)}", target, level="L1", project=project)
        return chk.error(f"{case_path.name}: {exc}")
    name = case["case"]["name"]
    chk = Check(f"sim.fea_{_safe_name(name)}", target, level="L1", project=project)
    if not shutil.which(ccx_bin) and not Path(ccx_bin).exists():
        return chk.error(f"CalculiX binary not found at {ccx_bin!r}. Install it via "
                         "plugins/forge/toolchain/install.sh (tier T4) or pass --ccx-bin.")
    try:
        study = g.run_study(case, project, project / "out" / "fea" / _safe_name(name), ccx_bin)
        evidence_ok = rep.record(chk, study, case, name)
        import build123d
        import gmsh as _gmsh
        import numpy
        chk.tool("gmsh", getattr(_gmsh, "__version__", str(_gmsh.GMSH_API_VERSION)))
        chk.tool("build123d", build123d.__version__)
        chk.tool("numpy", numpy.__version__)
        chk.tool("ccx", "2.23")
        chk.level = "L2" if evidence_ok else "L1"
        return chk.finish(notes=rep.notes(study, case))
    except (g.CaseError, g.FeaError, CheckContractError) as exc:
        return chk.error(f"{type(exc).__name__}: {exc}")
    except Exception as exc:  # noqa: BLE001 -- fail closed, never a silent pass
        return chk.error(f"{type(exc).__name__}: {exc}")


def _run_one(case_path: Path, project: Path, ccx_bin: str) -> int:
    if _is_general(case_path):
        return _run_general(case_path, project, ccx_bin)
    try:
        case = _load_case(case_path)
    except (tomllib.TOMLDecodeError, ValueError) as exc:
        chk = Check(f"sim.fea_{_safe_name(case_path.stem)}", str(case_path), level="L1", project=project)
        return chk.error(str(exc))

    name = case["case"]["name"]
    check_id = f"sim.fea_{_safe_name(name)}"
    target = str(case_path.relative_to(project)) if case_path.is_relative_to(project) else str(case_path)

    if not shutil.which(ccx_bin) and not Path(ccx_bin).exists():
        chk = Check(check_id, target, level="L1", project=project)
        return chk.error(
            f"CalculiX binary not found at {ccx_bin!r}. Install it via "
            "plugins/forge/toolchain/install.sh (tier T4) or pass --ccx-bin."
        )

    geo, mat, load = case["geometry"], case["material"], case["load"]
    mesh_cfg, hc_cfg, req_cfg = case["mesh"], case["hand_calc"], case["requirement"]
    L, B, H = float(geo["length_mm"]), float(geo["width_mm"]), float(geo["height_mm"])
    E, NU, YIELD = float(mat["E_MPa"]), float(mat["nu"]), float(mat["yield_MPa"])
    F = float(load["force_n"])

    work_root = project / "out" / "fea" / _safe_name(name)
    chk = Check(check_id, target, level="L1", project=project)
    try:
        hand_defl, hand_stress = m.euler_bernoulli_cantilever_tip_load(L, B, H, E, F)

        level_results = []
        for i, (nx, ny, nz) in enumerate(mesh_cfg["levels"]):
            lvl_dir = work_root / f"level{i}_{nx}x{ny}x{nz}"
            result = m.solve_one_level(
                length_mm=L, width_mm=B, height_mm=H, e_mpa=E, nu=NU, force_n=F,
                nx=int(nx), ny=int(ny), nz=int(nz), work_dir=lvl_dir, tag=f"level{i}", ccx_bin=ccx_bin,
            )
            level_results.append(result)

        finest = level_results[-1]
        prev = level_results[-2]
        convergence_pct = abs(finest.tip_deflection_z_mm - prev.tip_deflection_z_mm) / abs(prev.tip_deflection_z_mm) * 100.0
        hand_diff_pct = (finest.tip_deflection_z_mm - hand_defl) / hand_defl * 100.0
        stress_diff_pct = (finest.max_von_mises_mpa - hand_stress) / hand_stress * 100.0
        safety_factor = YIELD / finest.max_von_mises_mpa if finest.max_von_mises_mpa > 0 else float("inf")
        reaction_imbalance_pct = abs(abs(finest.reaction_fz_n) - F) / F * 100.0

        conv_tol = float(mesh_cfg["convergence_tol_pct"])
        defl_tol = float(hc_cfg["deflection_tolerance_pct"])
        stress_tol = float(hc_cfg["stress_tolerance_pct"])
        min_sf = float(req_cfg["min_safety_factor"])
        max_imbalance = float(req_cfg["max_reaction_imbalance_pct"])

        convergence_pass = chk.measure(
            "mesh_convergence_pct_change", round(convergence_pct, 4), "%", max=conv_tol,
            remediation=(
                f"Tip deflection changed {convergence_pct:.2f}% between the two finest mesh levels "
                f"({prev.n_elements} -> {finest.n_elements} elements), above the stated convergence "
                f"tolerance of {conv_tol}%. Add a finer refinement level to [mesh].levels in {case_path.name} "
                "and re-run before trusting this result."
            ),
        )
        hand_calc_pass = chk.measure(
            "hand_calc_deflection_diff_pct", round(hand_diff_pct, 4), "%", min=-defl_tol, max=defl_tol,
            remediation=(
                f"Finest-mesh FEA tip deflection {finest.tip_deflection_z_mm:.5f} mm disagrees with the "
                f"Euler-Bernoulli hand calc {hand_defl:.5f} mm by {hand_diff_pct:+.2f}%, outside the stated "
                f"+/-{defl_tol}% tolerance. Check the geometry, material and load in {case_path.name} match "
                "the hand calc's assumptions (or the hand calc itself is wrong) before trusting this FEA run."
            ),
        )
        chk.measure(
            "hand_calc_stress_diff_pct", round(stress_diff_pct, 4), "%", min=-stress_tol, max=stress_tol,
            remediation=(
                f"Finest-mesh max von Mises stress {finest.max_von_mises_mpa:.2f} MPa disagrees with the "
                f"Euler-Bernoulli bending-stress hand calc {hand_stress:.2f} MPa by {stress_diff_pct:+.2f}%, "
                f"outside the stated +/-{stress_tol}% tolerance (looser than the deflection tolerance because "
                "1-D beam theory does not capture the 3-D stress concentration at a fully clamped root face). "
                "Refine the mesh near the fixed face or widen stress_tolerance_pct with a stated reason."
            ),
        )
        chk.measure(
            "safety_factor", round(safety_factor, 4), "1", min=min_sf,
            remediation=(
                f"Safety factor {safety_factor:.2f} (yield {YIELD} MPa / max von Mises "
                f"{finest.max_von_mises_mpa:.2f} MPa) is below the required minimum {min_sf}. Reduce the "
                "load, thicken the section, or use a higher-yield material."
            ),
        )
        chk.measure(
            "reaction_balance_pct", round(reaction_imbalance_pct, 4), "%", max=max_imbalance,
            remediation=(
                f"Sum of fixed-face reaction forces ({finest.reaction_fz_n:.3f} N) does not balance the "
                f"applied tip load ({F} N) within {max_imbalance}% -- imbalance {reaction_imbalance_pct:.2f}%. "
                "This usually means the boundary conditions or load application are wrong; treat the run as "
                "untrustworthy until this is 0 within solver round-off."
            ),
        )

        import build123d
        import gmsh as _gmsh
        chk.tool("gmsh", getattr(_gmsh, "__version__", str(_gmsh.GMSH_API_VERSION)))
        chk.tool("build123d", build123d.__version__)
        chk.tool("ccx", "2.23")

        chk.level = "L2" if (convergence_pass and hand_calc_pass) else "L1"

        levels_summary = "; ".join(
            f"L{i}({r.n_elements}el)={r.tip_deflection_z_mm:.5f}mm" for i, r in enumerate(level_results)
        )
        notes = (
            f"material={mat.get('name', '?')} source={mat['source']!r}. "
            f"hand-calc: deflection={hand_defl:.5f} mm, bending stress={hand_stress:.2f} MPa "
            f"(Euler-Bernoulli, I=B*H^3/12). Levels: {levels_summary}. "
            "Validity limits: linear elastic, small deflection, rectangular prismatic beam, "
            "fixed-base/tip-transverse-load cantilever only (see SKILL.md)."
        )
        return chk.finish(notes=notes)
    except (m.FeaError, CheckContractError) as exc:
        return chk.error(str(exc))
    except Exception as exc:  # noqa: BLE001 -- fail closed, never a silent pass
        return chk.error(f"{type(exc).__name__}: {exc}")


def main() -> int:
    # Declares this entrypoint's check_id namespace so PostToolUse can bind a
    # fix message to the check that owns it, by check_id rather than which
    # out/verify/*.json file happens to have the newest mtime (M7, review #1).
    print("[FORGE_CHECK_ID_PREFIX] sim.fea_")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", type=Path, default=Path.cwd())
    ap.add_argument("--changed", action="append", default=[])
    ap.add_argument("--fast", action="store_true", help="accepted for interface compatibility; FEA runs are not fast")
    ap.add_argument("--ccx-bin", default=str(DEFAULT_CCX))
    ns = ap.parse_args()
    project = ns.project.resolve()

    case_files = _find_case_files(project, ns.changed)
    if not case_files:
        print("[SKIP] no analysis/fea/*.toml files to check")
        return 0

    worst = 0
    for path in case_files:
        rc = _run_one(path, project, ns.ccx_bin)
        worst = max(worst, rc)
    return worst


if __name__ == "__main__":
    sys.exit(main())
