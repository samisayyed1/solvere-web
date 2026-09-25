"""workflows/gate-review.js (review #1, M5): the recommendation is computed
from validated verdicts, and a missing or failed judge makes it BLOCKED
instead of being silently filtered out.

The workflow is run for real under node with the workflow runtime's
globals (``args``, ``phase``, ``parallel``, ``agent``, ``log``) mocked.
"""

from __future__ import annotations

import json
import shutil
import subprocess

import pytest

from .hookutil import PLUGIN_ROOT

WORKFLOW = PLUGIN_ROOT / "workflows" / "gate-review.js"
NODE = shutil.which("node")

HARNESS = r"""
const fs = require('fs')
const src = fs.readFileSync(process.argv[2], 'utf8').replace(/^export const meta/m, 'const meta')
const behaviour = JSON.parse(process.argv[3])
const prompts = []
const mocks = {
  args: { project: '/tmp/p', gate: 'G2', specialists: behaviour.specialists || [] },
  phase: () => {},
  log: () => {},
  parallel: async (thunks) => Promise.all(thunks.map((t) => t())),
  agent: async (prompt, opts) => {
    prompts.push(prompt)
    const b = behaviour[opts.label]
    if (opts.label === 'reconcile') return 'reviews/G2.md'
    if (b === 'throw') throw new Error('reviewer crashed')
    if (b === 'null') return null
    return b
  },
}
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor
const fn = new AsyncFunction(...Object.keys(mocks), src)
fn(...Object.values(mocks)).then((r) => {
  process.stdout.write(JSON.stringify({ result: r, reconcilePrompt: prompts[prompts.length - 1] }))
}).catch((e) => { process.stderr.write(String(e.stack || e)); process.exit(3) })
"""


def _verdict(reviewer: str, overall: str, verdicts: list[str]) -> dict:
    crit = []
    for i, v in enumerate(verdicts):
        c = {"id": f"REQ-MECH-00{i + 1}", "verdict": v, "evidence": ["out/verify/x.json"], "finding": "f"}
        if v == "FAIL":
            c.update(severity="major", affects=["function"])
        crit.append(c)
    return {"schema": "forge.verdict/1", "reviewer": reviewer, "gate": "G2", "subject": "s",
            "criteria": crit, "overall": overall, "summary": "", "not_checked": []}


def _run(behaviour: dict, tmp_path) -> dict:
    if NODE is None:
        pytest.skip("node is not installed")
    harness = tmp_path / "harness.js"
    harness.write_text(HARNESS)
    proc = subprocess.run([NODE, str(harness), str(WORKFLOW), json.dumps(behaviour)],
                          capture_output=True, text=True, timeout=60)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


GOOD_EVAL = _verdict("verification-evaluator", "PASS", ["PASS", "PASS"])
GOOD_RED = _verdict("red-team", "PASS", ["PASS"])


def test_all_pass_recommends_pass(tmp_path):
    out = _run({"verification-evaluator": GOOD_EVAL, "red-team": GOOD_RED}, tmp_path)
    assert out["result"]["overall_recommendation"] == "PASS"
    assert "MUST be exactly PASS" in out["reconcilePrompt"]


@pytest.mark.parametrize("failure", ["throw", "null"])
def test_missing_red_team_is_blocked_not_filtered(tmp_path, failure):
    """Seeded wrong: a crashed red-team used to vanish and the evaluator's PASS won."""
    out = _run({"verification-evaluator": GOOD_EVAL, "red-team": failure}, tmp_path)
    assert out["result"]["overall_recommendation"] == "BLOCKED"
    assert [u["role"] for u in out["result"]["unusable"]] == ["red-team"]
    assert "red-team" in out["reconcilePrompt"]


def test_missing_evaluator_is_blocked(tmp_path):
    out = _run({"verification-evaluator": "throw", "red-team": GOOD_RED}, tmp_path)
    assert out["result"]["overall_recommendation"] == "BLOCKED"


def test_overall_pass_over_failing_criterion_is_not_trusted(tmp_path):
    """Seeded wrong: the recommendation used to read v.overall only."""
    lying = _verdict("verification-evaluator", "PASS", ["PASS", "FAIL"])
    out = _run({"verification-evaluator": lying, "red-team": GOOD_RED}, tmp_path)
    assert out["result"]["overall_recommendation"] == "BLOCKED"
    assert "overall is PASS but not every criterion is PASS" in json.dumps(out["result"]["unusable"])


def test_honest_fail_recommends_fail(tmp_path):
    failing = _verdict("verification-evaluator", "FAIL", ["PASS", "FAIL"])
    out = _run({"verification-evaluator": failing, "red-team": GOOD_RED}, tmp_path)
    assert out["result"]["overall_recommendation"] == "FAIL"


def test_failed_specialist_is_reported_and_blocks(tmp_path):
    out = _run({"verification-evaluator": GOOD_EVAL, "red-team": GOOD_RED,
                "mechanical-engineer": "throw", "specialists": ["mechanical-engineer"]}, tmp_path)
    assert out["result"]["overall_recommendation"] == "BLOCKED"
    assert out["result"]["unusable"][0]["role"] == "mechanical-engineer"
