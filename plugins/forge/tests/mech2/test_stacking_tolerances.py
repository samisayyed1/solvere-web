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

from stack_math import StackFileError, evaluate, load_stack  # noqa: E402

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
