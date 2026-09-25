"""Known-answer tests for stacking-tolerances (CONTRACTS.md §3, §9).

The 3-part stack below has hand-checkable WC/RSS values:

    A: 10.00 +/-0.10 (direction +1)
    B:  5.00 +/-0.05 (direction +1)
    C: 12.00 +/-0.08 (direction -1)

    nominal = 10 + 5 - 12 = 3.00
    worst case tol = 0.10 + 0.05 + 0.08 = 0.23  ->  [2.77, 3.23]
    RSS tol = sqrt(0.10^2 + 0.05^2 + 0.08^2) = sqrt(0.0189) = 0.137477...  ->  [2.862523, 3.137477]
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parents[2] / "skills" / "stacking-tolerances"
SCRIPTS_DIR = SKILL_DIR / "scripts"
VERIFY_PY = SCRIPTS_DIR / "verify.py"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from stack_math import StackFileError, evaluate, load_params, load_stack, param_mismatches  # noqa: E402

KNOWN_STACK = """
[stack]
name = "known_answer_3part"
description = "hand-checkable 3-part stack"

[requirement]
unit = "mm"
gap_min = 2.5
gap_max = 3.5

[[contributor]]
id = "A"
nominal = 10.00
tol_plus = 0.10
tol_minus = 0.10
direction = 1
distribution = "normal"

[[contributor]]
id = "B"
nominal = 5.00
tol_plus = 0.05
tol_minus = 0.05
direction = 1
distribution = "normal"

[[contributor]]
id = "C"
nominal = 12.00
tol_plus = 0.08
tol_minus = 0.08
direction = -1
distribution = "normal"
"""

FAILING_STACK = """
[stack]
name = "gap_too_tight"
description = "seeded-wrong: worst-case gap falls below the requirement"

[requirement]
unit = "mm"
gap_min = 3.10
gap_max = 3.50

[[contributor]]
id = "A"
nominal = 10.00
tol_plus = 0.10
tol_minus = 0.10
direction = 1

[[contributor]]
id = "B"
nominal = 5.00
tol_plus = 0.05
tol_minus = 0.05
direction = 1

[[contributor]]
id = "C"
nominal = 12.00
tol_plus = 0.08
tol_minus = 0.08
direction = -1
"""

NO_REQUIREMENT_STACK = """
[stack]
name = "no_requirement"

[[contributor]]
id = "A"
nominal = 1.0
tol_plus = 0.1
tol_minus = 0.1
direction = 1
"""


def test_known_answer_worst_case_and_rss(tmp_path):
    stack_file = tmp_path / "known.toml"
    stack_file.write_text(KNOWN_STACK)
    stack = load_stack(stack_file)
    result = evaluate(stack)

    assert result.nominal_gap == pytest.approx(3.0, abs=1e-9)
    assert result.wc_min == pytest.approx(2.77, abs=1e-9)
    assert result.wc_max == pytest.approx(3.23, abs=1e-9)
    assert result.rss_min == pytest.approx(3.0 - 0.13747727084, abs=1e-8)
    assert result.rss_max == pytest.approx(3.0 + 0.13747727084, abs=1e-8)


def test_monte_carlo_is_seeded_and_reproducible(tmp_path):
    stack_file = tmp_path / "known.toml"
    stack_file.write_text(KNOWN_STACK)
    stack = load_stack(stack_file)
    r1 = evaluate(stack, monte_carlo_n=5000, monte_carlo_seed=42)
    r2 = evaluate(stack, monte_carlo_n=5000, monte_carlo_seed=42)
    assert r1.mc_min == r2.mc_min and r1.mc_max == r2.mc_max and r1.mc_mean == r2.mc_mean
    # sampled mean should be close to the nominal (well within the RSS band)
    assert r1.mc_mean == pytest.approx(3.0, abs=0.02)
    # a different seed should (almost certainly) give a different sample
    r3 = evaluate(stack, monte_carlo_n=5000, monte_carlo_seed=43)
    assert r3.mc_min != r1.mc_min or r3.mc_max != r1.mc_max


def test_stack_missing_requirement_is_a_load_error():
    # load_stack itself does not require gap_min/gap_max (that is verify.py's job);
    # confirm the fields come back None so verify.py can refuse cleanly.
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "no_req.toml"
        p.write_text(NO_REQUIREMENT_STACK)
        stack = load_stack(p)
        assert stack.gap_min is None and stack.gap_max is None


def test_malformed_stack_missing_contributor_field_raises():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "bad.toml"
        p.write_text("""
[stack]
name = "bad"
[requirement]
gap_min = 0
gap_max = 1
[[contributor]]
id = "A"
nominal = 1.0
tol_plus = 0.1
""")
        with pytest.raises(StackFileError):
            load_stack(p)


# --- end-to-end verify.py, via subprocess (proves the CLI contract, not just the math) ---

def _run_verify(project: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(VERIFY_PY), "--project", str(project)],
        capture_output=True, text=True, timeout=60,
    )


def test_verify_py_passes_on_known_good_stack(tmp_path):
    (tmp_path / "analysis" / "stacks").mkdir(parents=True)
    (tmp_path / "analysis" / "stacks" / "known.toml").write_text(KNOWN_STACK)
    r = _run_verify(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    out = json.loads((tmp_path / "out" / "verify" / "mech.stack_known_answer_3part.json").read_text())
    assert out["status"] == "pass"
    by_name = {m["name"]: m for m in out["measurements"]}
    assert by_name["worst_case_min"]["value"] == pytest.approx(2.77, abs=1e-6)
    assert by_name["worst_case_max"]["value"] == pytest.approx(3.23, abs=1e-6)


def test_verify_py_FAILS_when_worst_case_gap_below_limit(tmp_path):
    """Seeded-wrong case: stack gap below the requirement's minimum must FAIL, not pass."""
    (tmp_path / "analysis" / "stacks").mkdir(parents=True)
    (tmp_path / "analysis" / "stacks" / "bad.toml").write_text(FAILING_STACK)
    r = _run_verify(tmp_path)
    assert r.returncode == 1, r.stdout + r.stderr
    out = json.loads((tmp_path / "out" / "verify" / "mech.stack_gap_too_tight.json").read_text())
    assert out["status"] == "fail"
    failing = [m for m in out["measurements"] if not m["pass"]]
    assert failing, "expected at least one failing measurement"
    assert all(len(m["remediation"]) >= 10 for m in failing)


def test_verify_py_ERRORS_not_passes_on_stack_without_requirement(tmp_path):
    (tmp_path / "analysis" / "stacks").mkdir(parents=True)
    (tmp_path / "analysis" / "stacks" / "no_req.toml").write_text(NO_REQUIREMENT_STACK)
    r = _run_verify(tmp_path)
    assert r.returncode == 2, r.stdout + r.stderr


def test_verify_py_skips_cleanly_with_no_stacks(tmp_path):
    r = _run_verify(tmp_path)
    assert r.returncode == 0
    assert "[SKIP]" in r.stdout


# --- S7: unit vocabulary ---

def test_unit_typo_mn_is_rejected(tmp_path):
    """S7: a typo'd unit like "mn" (meant "mm") must not be silently trusted."""
    p = tmp_path / "bad.toml"
    p.write_text(KNOWN_STACK.replace('unit = "mm"', 'unit = "mn"'))
    with pytest.raises(StackFileError, match="unit"):
        load_stack(p)


def test_unit_inches_is_rejected(tmp_path):
    """S7: geometry stacks are SI mm (CONTRACTS SS10); nothing here converts
    units, so "in" must be refused rather than silently mis-checked as mm."""
    p = tmp_path / "bad.toml"
    p.write_text(KNOWN_STACK.replace('unit = "mm"', 'unit = "in"'))
    with pytest.raises(StackFileError, match="unit"):
        load_stack(p)


def test_unit_mm_is_accepted(tmp_path):
    p = tmp_path / "good.toml"
    p.write_text(KNOWN_STACK)
    stack = load_stack(p)  # must not raise
    assert stack.unit == "mm"


def test_verify_py_errors_not_passes_on_bad_unit(tmp_path):
    (tmp_path / "analysis" / "stacks").mkdir(parents=True)
    (tmp_path / "analysis" / "stacks" / "bad.toml").write_text(KNOWN_STACK.replace('unit = "mm"', 'unit = "mn"'))
    r = _run_verify(tmp_path)
    assert r.returncode == 2, r.stdout + r.stderr


# --- S7: contributor `param = "a.b"` bindings checked against params.toml ---

PARAM_STACK = """
[stack]
name = "params_bound"
description = "one contributor bound to params.toml"

[requirement]
unit = "mm"
gap_min = 0.0
gap_max = 5.0

[[contributor]]
id = "A"
param = "enclosure.wall_thickness"
nominal = {nominal}
tol_plus = 0.10
tol_minus = 0.10
direction = 1

[[contributor]]
id = "B"
nominal = 1.00
tol_plus = 0.05
tol_minus = 0.05
direction = -1
"""

PARAMS_TOML = """
[enclosure.wall_thickness]
value = 2.0
unit = "mm"
status = "assumed"
source = "fixture"
"""


def _write_params_project(tmp_path, nominal: float) -> Path:
    (tmp_path / "params").mkdir(parents=True)
    (tmp_path / "params" / "params.toml").write_text(PARAMS_TOML)
    (tmp_path / "analysis" / "stacks").mkdir(parents=True)
    (tmp_path / "analysis" / "stacks" / "params_bound.toml").write_text(PARAM_STACK.format(nominal=nominal))
    return tmp_path


def test_param_mismatch_is_detected_by_stack_math(tmp_path):
    project = _write_params_project(tmp_path, nominal=1.5)  # params.toml says 2.0
    stack = load_stack(project / "analysis" / "stacks" / "params_bound.toml")
    params = load_params(project)
    mismatches = param_mismatches(stack, params)
    assert len(mismatches) == 1
    assert mismatches[0].contributor_id == "A"
    assert mismatches[0].stack_nominal == pytest.approx(1.5)
    assert mismatches[0].params_value == pytest.approx(2.0)


def test_param_match_has_no_mismatches(tmp_path):
    project = _write_params_project(tmp_path, nominal=2.0)  # matches params.toml
    stack = load_stack(project / "analysis" / "stacks" / "params_bound.toml")
    params = load_params(project)
    assert param_mismatches(stack, params) == []


def test_verify_py_fails_when_contributor_nominal_disagrees_with_params(tmp_path):
    project = _write_params_project(tmp_path, nominal=1.5)
    r = _run_verify(project)
    assert r.returncode == 1, r.stdout + r.stderr
    out = json.loads((project / "out" / "verify" / "mech.stack_params_bound.json").read_text())
    assert out["status"] == "fail"
    m = next(x for x in out["measurements"] if x["name"] == "contributor_A_matches_params")
    assert not m["pass"]
    assert "params.toml" in m["remediation"]


def test_verify_py_passes_when_contributor_nominal_matches_params(tmp_path):
    project = _write_params_project(tmp_path, nominal=2.0)
    r = _run_verify(project)
    assert r.returncode == 0, r.stdout + r.stderr
    out = json.loads((project / "out" / "verify" / "mech.stack_params_bound.json").read_text())
    assert out["status"] == "pass"


def test_verify_py_errors_on_a_param_binding_that_does_not_exist(tmp_path):
    project = _write_params_project(tmp_path, nominal=2.0)
    spec = project / "analysis" / "stacks" / "params_bound.toml"
    spec.write_text(spec.read_text().replace(
        'param = "enclosure.wall_thickness"', 'param = "enclosure.nonexistent_key"'))
    r = _run_verify(project)
    assert r.returncode == 2, r.stdout + r.stderr
