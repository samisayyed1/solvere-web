"""M7 (review #1): PostToolUse must bind a fix message to the check that owns
it by check_id, not by which out/verify/*.json file happens to have the
newest mtime -- two entrypoints matched on the same changed path can finish
within the same second, and mtimes alone misattribute one entrypoint's
remediations to another ("fix messages from gardening-docs showed up under
tracing-requirements").

This is implemented on the skill side (CONTRACTS.md §9 "check_id namespace"):
every registered verify.py entrypoint prints, as the very first line of
main() -- before any [SKIP] short-circuit -- a line

    [FORGE_CHECK_ID_PREFIX] <prefix>

naming the fixed, unique prefix every check_id it writes starts with.
post_tool_use.py (owned by the enforcement fixer) is what must actually read
this line and filter out/verify/*.json by check_id-prefix instead of mtime;
this test file only proves the skill side of the contract: every registered
entrypoint prints its prefix on every run (including a clean [SKIP]), and no
two entrypoints share a prefix that could let one's remediations be mistaken
for another's.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FORGE_PYTHON = Path.home() / ".forge" / "bin" / "forge-python"
PY = str(FORGE_PYTHON) if FORGE_PYTHON.exists() else sys.executable

_PREFIX_RE = re.compile(r"^\[FORGE_CHECK_ID_PREFIX\]\s+(\S+)\s*$", re.MULTILINE)

# entrypoint -> (script-relative-to-PLUGIN_ROOT, extra argv, needs the CAD env)
ENTRYPOINTS = {
    "writing-requirements": ("skills/writing-requirements/scripts/verify.py", [], False),
    "tracing-requirements": ("skills/tracing-requirements/scripts/verify.py", [], False),
    "modeling-systems": ("skills/modeling-systems/scripts/verify.py", [], False),
    "verifying-geometry": ("skills/verifying-geometry/scripts/verify.py", [], True),
    "checking-dfm": ("skills/checking-dfm/scripts/verify.py", [], True),
    "stacking-tolerances": ("skills/stacking-tolerances/scripts/verify.py", [], False),
    "running-fea": ("skills/running-fea/scripts/verify.py", [], True),
    "checking-ecad": ("skills/checking-ecad/scripts/verify.py", [], False),
    "designing-circuits": ("skills/designing-circuits/scripts/verify.py", [], False),
    "building-firmware": ("skills/building-firmware/scripts/verify.py", [], False),
    "gardening-docs": ("skills/gardening-docs/scripts/verify.py", [], False),
    "costing-bom": ("skills/costing-bom/scripts/verify.py", [], False),
    "mapping-compliance": ("skills/mapping-compliance/scripts/verify.py", [], False),
}

# The exact/prefix each entrypoint is expected to declare (CONTRACTS §9).
EXPECTED_PREFIX = {
    "writing-requirements": "requirements.ears_lint",
    "tracing-requirements": "requirements.trace_graph",
    "modeling-systems": "systems.sysml_check",
    "verifying-geometry": "geometry.",
    "checking-dfm": "dfm.",
    "stacking-tolerances": "mech.stack_",
    "running-fea": "sim.fea_",
    "checking-ecad": "ecad.",
    "designing-circuits": "spice.",
    "building-firmware": "firmware.",
    "gardening-docs": "gardening.docs",
    "costing-bom": "supply.bom_rollup",
    "mapping-compliance": "compliance.standards_map",
}


def _run(entrypoint: str, project: Path) -> subprocess.CompletedProcess:
    rel, extra, needs_cad = ENTRYPOINTS[entrypoint]
    if needs_cad and not FORGE_PYTHON.exists():
        pytest.skip(f"{entrypoint} needs the CAD env (~/.forge/bin/forge-python not installed)")
    script = PLUGIN_ROOT / rel
    return subprocess.run(
        [PY, str(script), "--project", str(project), *extra],
        capture_output=True, text=True, timeout=120,
    )


@pytest.mark.parametrize("entrypoint", sorted(ENTRYPOINTS))
def test_entrypoint_prints_its_check_id_prefix_even_on_a_clean_skip(entrypoint, tmp_path):
    """Every registered entrypoint declares its check_id prefix on stdout on
    EVERY run -- including the common case where there's nothing to check --
    so a hook can always learn it before deciding whether any remediations
    belong to this run."""
    proc = _run(entrypoint, tmp_path)
    m = _PREFIX_RE.search(proc.stdout)
    assert m, f"{entrypoint} did not print [FORGE_CHECK_ID_PREFIX] on stdout:\n{proc.stdout}\n{proc.stderr}"
    assert m.group(1) == EXPECTED_PREFIX[entrypoint]


def test_no_two_entrypoints_share_an_overlapping_check_id_prefix():
    """A seeded-wrong case for the binding contract itself: if two
    entrypoints' prefixes overlapped, a hook filtering by
    check_id.startswith(prefix) could still misattribute one entrypoint's
    check result to another's run -- exactly the bug this fixes."""
    prefixes = list(EXPECTED_PREFIX.values())
    for i, a in enumerate(prefixes):
        for b in prefixes[i + 1:]:
            assert not a.startswith(b) and not b.startswith(a), (a, b)
