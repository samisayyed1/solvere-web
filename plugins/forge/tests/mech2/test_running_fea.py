"""Known-answer + seeded-wrong tests for running-fea (CONTRACTS.md §3, §9).

The reference case is a 100 x 10 x 10 mm steel cantilever with a 100 N tip
load -- the same case as ``plugins/forge/toolchain/smoke/smoke_ccx.py``,
which already proved -0.19% agreement with Euler-Bernoulli at a fine mesh.
These tests reuse that geometry through the full build123d -> gmsh ->
CalculiX pipeline (not the smoke script's hand-rolled node loop) and are
slower (real solves): expect several seconds per case.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parents[2] / "skills" / "running-fea"
SCRIPTS_DIR = SKILL_DIR / "scripts"
VERIFY_PY = SCRIPTS_DIR / "verify.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "smoke_cantilever.toml"
FORGE_PYTHON = Path.home() / ".forge" / "bin" / "forge-python"
PY = str(FORGE_PYTHON) if FORGE_PYTHON.exists() else sys.executable


def _run_verify(project: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PY, str(VERIFY_PY), "--project", str(project)],
        capture_output=True, text=True, timeout=300,
    )


def _write_case(project: Path, overrides: dict | None = None) -> Path:
    data = tomllib.loads(FIXTURE.read_text())
    if overrides:
        for section, kv in overrides.items():
            data.setdefault(section, {}).update(kv)
    cases_dir = project / "analysis" / "fea"
    cases_dir.mkdir(parents=True, exist_ok=True)
    path = cases_dir / "smoke_cantilever.toml"
    path.write_text(_dump_toml(data))
    return path


def _dump_toml(data: dict) -> str:
    """Minimal TOML writer sufficient for this flat two-level structure (avoids an extra dependency)."""
    lines = []
    for section, kv in data.items():
        lines.append(f"[{section}]")
        for k, v in kv.items():
            if isinstance(v, str):
                lines.append(f'{k} = "{v}"')
            elif isinstance(v, list):
                lines.append(f"{k} = {v!r}".replace("'", ""))
            else:
                lines.append(f"{k} = {v}")
        lines.append("")
    return "\n".join(lines)


@pytest.mark.slow
def test_verify_py_passes_known_good_cantilever_within_5pct(tmp_path):
    """Known-answer test: FEA vs Euler-Bernoulli hand calc, must land inside +/-5% on deflection."""
    _write_case(tmp_path)
    r = _run_verify(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    out = json.loads((tmp_path / "out" / "verify" / "sim.fea_smoke_cantilever.json").read_text())
    assert out["status"] == "pass"
    assert out["level"] == "L2", "hand-calc and convergence both passed, so the check must be L2"
    by_name = {m["name"]: m for m in out["measurements"]}
    assert abs(by_name["hand_calc_deflection_diff_pct"]["value"]) < 5.0
    assert abs(by_name["hand_calc_deflection_diff_pct"]["value"]) < 1.0, "reference case should land well inside tolerance (~0.2%)"
    assert by_name["mesh_convergence_pct_change"]["pass"] is True
    assert by_name["safety_factor"]["value"] > 1.5
    assert abs(by_name["reaction_balance_pct"]["value"]) < 1.0


@pytest.mark.slow
def test_verify_py_FAILS_on_seeded_nonconverged_mesh(tmp_path):
    """Seeded-wrong: an unreasonably tight convergence tolerance must FAIL, downgrading the check to L1."""
    _write_case(tmp_path, overrides={"mesh": {"convergence_tol_pct": 0.01}})
    r = _run_verify(tmp_path)
    assert r.returncode == 1, r.stdout + r.stderr
    out = json.loads((tmp_path / "out" / "verify" / "sim.fea_smoke_cantilever.json").read_text())
    assert out["status"] == "fail"
    assert out["level"] == "L1", "a failed convergence study must not be reported at L2"
    by_name = {m["name"]: m for m in out["measurements"]}
    assert by_name["mesh_convergence_pct_change"]["pass"] is False
    assert len(by_name["mesh_convergence_pct_change"]["remediation"]) >= 10


@pytest.mark.slow
def test_verify_py_FAILS_on_seeded_hand_calc_disagreement(tmp_path):
    """Seeded-wrong: an unreasonably tight hand-calc tolerance must FAIL, downgrading the check to L1."""
    _write_case(tmp_path, overrides={"hand_calc": {"deflection_tolerance_pct": 0.01}})
    r = _run_verify(tmp_path)
    assert r.returncode == 1, r.stdout + r.stderr
    out = json.loads((tmp_path / "out" / "verify" / "sim.fea_smoke_cantilever.json").read_text())
    assert out["status"] == "fail"
    assert out["level"] == "L1"
    by_name = {m["name"]: m for m in out["measurements"]}
    assert by_name["hand_calc_deflection_diff_pct"]["pass"] is False


@pytest.mark.slow
def test_verify_py_FAILS_on_seeded_low_safety_factor_requirement(tmp_path):
    """Seeded-wrong: an unreachable safety-factor requirement must FAIL (but can still be L2 -- hand-calc/convergence are unaffected)."""
    _write_case(tmp_path, overrides={"requirement": {"min_safety_factor": 1000.0}})
    r = _run_verify(tmp_path)
    assert r.returncode == 1, r.stdout + r.stderr
    out = json.loads((tmp_path / "out" / "verify" / "sim.fea_smoke_cantilever.json").read_text())
    assert out["status"] == "fail"
    by_name = {m["name"]: m for m in out["measurements"]}
    assert by_name["safety_factor"]["pass"] is False


def test_verify_py_ERRORS_on_case_missing_required_section(tmp_path):
    cases_dir = tmp_path / "analysis" / "fea"
    cases_dir.mkdir(parents=True)
    (cases_dir / "broken.toml").write_text('[case]\nname = "broken"\n')
    r = _run_verify(tmp_path)
    assert r.returncode == 2, r.stdout + r.stderr


def test_verify_py_ERRORS_on_fewer_than_3_mesh_levels(tmp_path):
    _write_case(tmp_path, overrides={})
    data = tomllib.loads(FIXTURE.read_text())
    data["mesh"]["levels"] = [[10, 2, 2], [20, 4, 4]]
    path = tmp_path / "analysis" / "fea" / "smoke_cantilever.toml"
    path.write_text(_dump_toml(data))
    r = _run_verify(tmp_path)
    assert r.returncode == 2, r.stdout + r.stderr


def test_verify_py_ERRORS_on_safety_factor_below_hard_floor(tmp_path):
    """S8: a min_safety_factor below 1.0 is never a case-file choice, waiver or not."""
    _write_case(tmp_path, overrides={"requirement": {"min_safety_factor": 0.5}})
    r = _run_verify(tmp_path)
    assert r.returncode == 2, r.stdout + r.stderr
    assert "hard floor" in (r.stdout + r.stderr)


def _write_case_no_waiver(project: Path, overrides: dict | None = None) -> Path:
    """Like _write_case, but starts from a copy of the fixture with its
    [waiver] removed -- the fixture carries one to justify its own
    stress_tolerance_pct=15 (see smoke_cantilever.toml), which would
    otherwise mask the "no waiver" ceiling tests below."""
    data = tomllib.loads(FIXTURE.read_text())
    data.pop("waiver", None)
    if overrides:
        for section, kv in overrides.items():
            data.setdefault(section, {}).update(kv)
    cases_dir = project / "analysis" / "fea"
    cases_dir.mkdir(parents=True, exist_ok=True)
    path = cases_dir / "smoke_cantilever.toml"
    path.write_text(_dump_toml(data))
    return path


def test_verify_py_ERRORS_on_hand_calc_tolerance_above_ceiling_without_waiver(tmp_path):
    """S8: deflection_tolerance_pct = 500 is not a real tolerance -- it would
    accept almost any FEA result as agreeing with the hand calc."""
    _write_case_no_waiver(tmp_path, overrides={"hand_calc": {"deflection_tolerance_pct": 500.0}})
    r = _run_verify(tmp_path)
    assert r.returncode == 2, r.stdout + r.stderr
    assert "ceiling" in (r.stdout + r.stderr)


def test_verify_py_ERRORS_on_convergence_tolerance_above_ceiling_without_waiver(tmp_path):
    """S8: convergence_tol_pct = 100 would call an unconverged mesh converged."""
    _write_case_no_waiver(tmp_path, overrides={"mesh": {"convergence_tol_pct": 100.0}})
    r = _run_verify(tmp_path)
    assert r.returncode == 2, r.stdout + r.stderr
    assert "ceiling" in (r.stdout + r.stderr)


def test_verify_py_ERRORS_on_implausible_e_for_named_material(tmp_path):
    """S8: E = 210 MPa for a material named 'steel' is a GPa/MPa unit slip
    (real structural steel is ~200000 MPa); the E plausibility band must
    catch it, never silently trust it."""
    _write_case(tmp_path, overrides={"material": {"name": "generic_structural_steel", "E_MPa": 210.0}})
    r = _run_verify(tmp_path)
    assert r.returncode == 2, r.stdout + r.stderr
    assert "implausible" in (r.stdout + r.stderr)


def test_verify_py_accepts_ceiling_violation_with_a_signed_waiver(tmp_path):
    """Positive case: a [waiver] naming a human and a reason lets a case
    past the hand-calc ceiling that would otherwise be refused -- proven by
    getting past _load_case to the (still slow) solve stage rather than
    erroring at case-load time. We stop short of the real solve here by
    also pushing the safety factor requirement absurdly low is NOT used
    (that stays a hard floor); instead this only checks _load_case directly."""
    sys.path.insert(0, str(SCRIPTS_DIR))
    import verify as v

    data = tomllib.loads(FIXTURE.read_text())
    data["hand_calc"]["deflection_tolerance_pct"] = 500.0
    data["waiver"] = {"signed_by": "Jane Doe", "reason": "rough sizing pass only, refine before gate review"}
    path = tmp_path / "case.toml"
    path.write_text(_dump_toml(data))
    case = v._load_case(path)  # must not raise
    assert case["waiver"]["signed_by"] == "Jane Doe"


def test_load_case_errors_when_waiver_has_no_signed_by(tmp_path):
    sys.path.insert(0, str(SCRIPTS_DIR))
    import verify as v

    data = tomllib.loads(FIXTURE.read_text())
    data["hand_calc"]["deflection_tolerance_pct"] = 500.0
    data["waiver"] = {"reason": "rough sizing pass only, refine before gate review"}
    path = tmp_path / "case.toml"
    path.write_text(_dump_toml(data))
    with pytest.raises(ValueError, match="signed_by"):
        v._load_case(path)


def test_verify_py_skips_cleanly_with_no_cases(tmp_path):
    r = _run_verify(tmp_path)
    assert r.returncode == 0
    assert "[SKIP]" in r.stdout


def test_hand_calc_formula_matches_textbook_cantilever():
    """Pure hand-calc unit test, independent of CalculiX: F L^3/(3EI) and F L (H/2)/I."""
    pytest.importorskip("build123d")  # CAD-env only; runs under ~/.forge/bin/forge-python
    pytest.importorskip("gmsh")
    sys.path.insert(0, str(SCRIPTS_DIR))
    import mesh_and_solve as m

    L, B, H, E, F = 100.0, 10.0, 10.0, 210000.0, 100.0
    defl, stress = m.euler_bernoulli_cantilever_tip_load(L, B, H, E, F)
    inertia = B * H ** 3 / 12.0
    assert defl == pytest.approx(F * L ** 3 / (3 * E * inertia), rel=1e-12)
    assert stress == pytest.approx(F * L * (H / 2) / inertia, rel=1e-12)
    assert defl == pytest.approx(0.19047619047619047, abs=1e-9)
    assert stress == pytest.approx(60.0, abs=1e-9)
