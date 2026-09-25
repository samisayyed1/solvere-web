"""Review #1, C3: hooks must fail CLOSED (exit 2, clear message) when the
interpreter has no ``tomllib`` (Python < 3.11), instead of silently turning
the evidence gate and the verified-param guard off.

``tomllib`` is removed by poisoning ``sys.modules`` before the hook runs,
which is exactly what an interpreter without the module looks like to an
``import``. If an old Python (3.10 or earlier) happens to be installed, the
real thing is tested too.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from .hookutil import HOOKS_DIR, PLUGIN_ROOT, forge_project  # noqa: F401

WRAPPER = HOOKS_DIR / "_failclosed.py"
HOOK_EVENTS = ("pre_tool_use", "post_tool_use", "stop", "subagent_stop", "session_start",
               "user_prompt_submit", "user_prompt_expansion", "pre_compact")

NO_TOMLLIB = (
    "import sys, runpy\n"
    "sys.modules['tomllib'] = None  # an interpreter without tomllib\n"
    "target = sys.argv[1]\n"
    "sys.argv = sys.argv[1:]\n"
    "runpy.run_path(target, run_name='__main__')\n"
)


def _run_without_tomllib(tmp_path: Path, argv: list[str], payload: dict) -> subprocess.CompletedProcess:
    shim = tmp_path / "no_tomllib.py"
    shim.write_text(NO_TOMLLIB)
    return subprocess.run([sys.executable, str(shim), *argv], input=json.dumps(payload),
                          capture_output=True, text=True, timeout=30)


def _cad_edit(project: Path) -> dict:
    return {"cwd": str(project), "tool_name": "Edit", "agent_type": "forge:electrical-engineer",
            "tool_input": {"file_path": str(project / "params" / "params.toml"),
                           "old_string": "value = 40.0", "new_string": "value = 30.0"}}


@pytest.mark.parametrize("module", HOOK_EVENTS)
def test_wrapper_fails_closed_without_tomllib(tmp_path, forge_project, module):
    """Seeded wrong: every hook, run the way hooks.json runs it, must exit 2."""
    result = _run_without_tomllib(tmp_path, [str(WRAPPER), module], _cad_edit(forge_project))
    assert result.returncode == 2, (result.returncode, result.stdout, result.stderr)
    assert "tomllib" in result.stderr
    assert "python3" in result.stderr.lower()


def test_direct_script_also_fails_closed_without_tomllib(tmp_path, forge_project):
    """Running a hook script directly (not via the wrapper) is closed too."""
    result = _run_without_tomllib(tmp_path, [str(HOOKS_DIR / "stop.py")], {"cwd": str(forge_project)})
    assert result.returncode == 2
    assert "tomllib" in result.stderr


def test_wrapper_passes_with_tomllib(forge_project):
    """Pass case: the same verified-param edit is *denied* (not crashed) on a good interpreter."""
    result = subprocess.run([sys.executable, str(WRAPPER), "pre_tool_use"], input=json.dumps(_cad_edit(forge_project)),
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_wrapper_rejects_unknown_hook_name():
    result = subprocess.run([sys.executable, str(WRAPPER), "nope"], input="{}", capture_output=True, text=True)
    assert result.returncode == 2


def test_wrapper_turns_import_errors_into_exit_2(tmp_path):
    """An import-time crash in a hook module must not exit 1 (fail open)."""
    shutil.copytree(HOOKS_DIR, tmp_path / "hooks", ignore=shutil.ignore_patterns("__pycache__"))
    (tmp_path / "hooks" / "stop.py").write_text("raise ImportError('broken install')\n")
    shutil.copytree(PLUGIN_ROOT / "lib", tmp_path / "lib", ignore=shutil.ignore_patterns("__pycache__"))
    result = subprocess.run([sys.executable, str(tmp_path / "hooks" / "_failclosed.py"), "stop"],
                            input="{}", capture_output=True, text=True, timeout=30)
    assert result.returncode == 2
    assert "broken install" in result.stderr


def test_hooks_json_runs_every_hook_through_the_wrapper():
    config = json.loads((HOOKS_DIR / "hooks.json").read_text())
    for event, groups in config["hooks"].items():
        for group in groups:
            for hook in group["hooks"]:
                assert hook["args"][0] == "${CLAUDE_PLUGIN_ROOT}/hooks/_failclosed.py", event
                assert hook["args"][1] in HOOK_EVENTS, event


OLD_PYTHONS = [p for p in (shutil.which("python3.10"), shutil.which("python3.9"), "/usr/bin/python3.9")
               if p and Path(p).exists()]


@pytest.mark.skipif(not OLD_PYTHONS, reason="no Python < 3.11 installed to test against")
def test_real_old_python_fails_closed(forge_project):
    result = subprocess.run([OLD_PYTHONS[0], str(WRAPPER), "stop"], input=json.dumps({"cwd": str(forge_project)}),
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 2
    assert "too old" in result.stderr or "tomllib" in result.stderr
