"""Dry-run every eval case's graders against hand-made good and bad outcomes.

Brief §0: "a test that cannot fail proves nothing". For every case under
plugins/forge/evals/ this test

* runs the case's real scaffold_script into a throwaway HOME (so the base
  workspace is exactly what a run starts from),
* applies each variant in the case's ``selftest.json`` on top of it, and
* checks with ``_tools/grader_sim.py`` that ``good`` passes every free grader,
  each ``bad-*`` variant fails every grader it lists, and every free grader is
  failed by at least one bad variant (so no grader is a tautology).

It also checks suite-level rules: >= 25 cases with the brief §6 domain
minimums, exactly 8 smoke cases, explicit max_turns/timeout_seconds on every
case, an outcome grader and a path grader per case, llm rubrics with PASS and
FAIL conditions, and answer keys that never reach the workspace.

Needs PyYAML: run under ``~/.forge/bin/forge-python -m pytest`` (canonical) or
``uv run --with pytest --with pyyaml pytest``.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

EVALS = Path(__file__).resolve().parents[2] / "evals"
sys.path.insert(0, str(EVALS / "_tools"))

import grader_sim as gs  # noqa: E402

SKIP_DIRS = {"_lib", "_tools", "results", "mocks"}
PATH_TYPES = {"tool_used", "tool_order"}


def _case_dirs() -> list[Path]:
    out = []
    for p in sorted(EVALS.rglob("*")):
        if not p.is_dir() or any(part in SKIP_DIRS for part in p.relative_to(EVALS).parts):
            continue
        if "fixture" in p.relative_to(EVALS).parts or "key" in p.relative_to(EVALS).parts \
                or "reference" in p.relative_to(EVALS).parts:
            continue
        if (p / "case.yaml").is_file() or (p / "prompt.md").is_file():
            out.append(p)
    return out


CASES = _case_dirs()
IDS = [c.relative_to(EVALS).as_posix() for c in CASES]


@pytest.fixture(scope="module")
def scaffolds(tmp_path_factory) -> dict[Path, dict[str, str]]:
    cache: dict[Path, dict[str, str]] = {}

    def get(case_dir: Path) -> dict[str, str]:
        if case_dir not in cache:
            cache[case_dir] = gs.scaffold_files(case_dir, tmp_path_factory.mktemp(case_dir.name))
        return cache[case_dir]
    return get  # type: ignore[return-value]


# ------------------------------------------------------------ suite shape

def _tags(case: dict) -> set[str]:
    return set(case.get("tags") or [])


def test_suite_size_and_domain_minimums():
    cases = [gs.load_case(c) for c in CASES]
    names = [c["name"] for c in cases]
    assert len(names) == len(set(names)), "case names must be unique"
    assert len(cases) >= 25
    need = {"mechanical": 3, "electrical": 2, "firmware": 1, "requirements": 2,
            "seeded": 3, "discipline": 3, "nofire": 1}
    for tag, n in need.items():
        have = sum(1 for c in cases if tag in _tags(c))
        assert have >= n, f"{tag}: {have} < {n}"
    assert sum(1 for c in cases if "smoke" in _tags(c)) == 8


def test_seeded_sets_cover_all_eight_defect_types():
    types = set()
    for key in EVALS.glob("review/seeded-*/key/answer_key.json"):
        k = json.loads(key.read_text())
        assert 5 <= len(k["defects"]) <= 10, key
        types |= {d["type"] for d in k["defects"]}
    assert {"wall_below_min", "interference", "missing_strain_relief", "tolerance_stack",
            "regulator_dissipation", "missing_esd_path", "untested_requirement",
            "unsupported_claim"} <= types


def test_seeded_cases_generated_files_up_to_date():
    r = subprocess.run([sys.executable, str(EVALS / "_tools" / "gen_seeded.py"), "--check"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


# ------------------------------------------------------------ per case

@pytest.mark.parametrize("case_dir", CASES, ids=IDS)
def test_case_shape(case_dir: Path):
    case = gs.load_case(case_dir)
    ex = case.get("execution") or {}
    assert isinstance(ex.get("max_turns"), int) and 5 <= ex["max_turns"] <= 200, "explicit max_turns"
    assert isinstance(ex.get("timeout_seconds"), int) and 300 <= ex["timeout_seconds"] <= 3600, "explicit timeout"
    assert case.get("prompt"), "prompt body"
    graders = case["graders"]
    assert graders
    types = {g["type"] for g in graders}
    assert types - PATH_TYPES - {"llm", "baseline"} or "llm" in types, "needs an outcome grader"
    assert types & PATH_TYPES, "needs a path grader (tool_used / tool_order)"
    for g in graders:
        assert g.get("name") and g.get("type") in gs.FREE_TYPES | gs.PAID_TYPES, g
        if g["type"] == "regex":
            gs.js_regex(g["pattern"], g.get("flags", ""))
        if g["type"] == "tool_used" and g.get("input_match"):
            gs.js_regex(g["input_match"])
        if g["type"] == "llm":
            assert "PASS" in g["criteria"] and "FAIL" in g["criteria"], g["name"]
    env = ex.get("env") or {}
    assert all(k.startswith("EVAL_") for k in env)
    if (case.get("context") or {}).get("scaffold_script"):
        assert (case_dir / case["context"]["scaffold_script"]).is_file()


@pytest.mark.parametrize("case_dir", CASES, ids=IDS)
def test_graders_pass_good_and_fail_bad(case_dir: Path, scaffolds):
    case = gs.load_case(case_dir)
    st = case_dir / "selftest.json"
    assert st.is_file(), "every case needs selftest.json"
    variants = json.loads(st.read_text())["variants"]
    assert "good" in variants and any(n.startswith("bad-") for n in variants)
    base = scaffolds(case_dir)
    free = [g for g in case["graders"] if g["type"] in gs.FREE_TYPES]
    failed_somewhere: set[str] = set()

    good = gs.grade_all(case, gs.outcome_from_variant(variants, "good", base))
    bad_good = {k: v for k, v in good.items() if v is False}
    assert not bad_good, f"good outcome fails: {bad_good}"

    for name, v in variants.items():
        if not name.startswith("bad-"):
            continue
        res = gs.grade_all(case, gs.outcome_from_variant(variants, name, base))
        expect = v.get("expect") or {}
        assert expect, f"{name} must name the graders it is meant to fail"
        for gname, want in expect.items():
            assert gname in res, f"{name}: unknown grader {gname}"
            assert res[gname] is want, f"{name}: {gname} expected {want}, got {res[gname]}"
        failed_somewhere |= {k for k, ok in res.items() if ok is False}

    never = [g["name"] for g in free if g["name"] not in failed_somewhere]
    assert not never, f"graders never shown to fail: {never}"


@pytest.mark.parametrize("case_dir", CASES, ids=IDS)
def test_answer_keys_never_reach_workspace(case_dir: Path, scaffolds):
    files = scaffolds(case_dir)
    leaked = [p for p in files if "answer_key" in p or p.startswith(("key/", "reference/"))
              or p.endswith("selftest.json") or p.endswith("good_findings.json")]
    assert not leaked, leaked
    if (case_dir / "key").is_dir():
        for k in (case_dir / "key").glob("*.json"):
            text = k.read_text()
            assert not any(text == v for v in files.values())


def test_scaffold_links_forge_home(tmp_path):
    case = EVALS / "discipline" / "mark-gate-passed"
    gs.scaffold_files(case, tmp_path)
    link = tmp_path / "home" / ".forge"
    assert link.is_symlink() or link.is_dir()
