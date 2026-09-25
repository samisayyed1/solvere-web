"""Tests for hooks/_failclosed.py: the shared "any exception -> exit 2" wrapper."""

from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from pathlib import Path

from .hookutil import HOOKS_DIR

DUMMY_HANDLER = textwrap.dedent(f"""\
    import sys
    sys.path.insert(0, {str(HOOKS_DIR)!r})
    from _failclosed import run_hook

    def handle(data):
        if data.get("boom"):
            raise RuntimeError("kaboom")
        if data.get("bad_return"):
            return "not-an-int", None
        if data.get("unencodable"):
            return 0, {{"bad": object()}}
        return 0, {{"echo": data.get("value")}}

    if __name__ == "__main__":
        run_hook(handle)
    """)


def _write_dummy(tmp_path: Path) -> Path:
    script = tmp_path / "dummy_hook.py"
    script.write_text(DUMMY_HANDLER)
    return script


def _run(script: Path, stdin_text: str, timeout: float = 10.0) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(script)], input=stdin_text,
                           capture_output=True, text=True, timeout=timeout)


def test_normal_path_exits_0_with_json(tmp_path):
    script = _write_dummy(tmp_path)
    proc = _run(script, json.dumps({"value": 42}))
    assert proc.returncode == 0
    assert json.loads(proc.stdout) == {"echo": 42}


def test_empty_stdin_is_treated_as_empty_object(tmp_path):
    script = _write_dummy(tmp_path)
    proc = _run(script, "")
    assert proc.returncode == 0
    assert json.loads(proc.stdout) == {"echo": None}


def test_exception_in_handler_exits_2_with_stderr_reason(tmp_path):
    """Sabotage case: any exception anywhere in handle() must fail closed (exit 2)."""
    script = _write_dummy(tmp_path)
    proc = _run(script, json.dumps({"boom": True}))
    assert proc.returncode == 2
    assert "kaboom" in proc.stderr
    assert proc.stdout == ""  # exit-2 reason travels on stderr, not stdout JSON


def test_malformed_stdin_json_exits_2(tmp_path):
    script = _write_dummy(tmp_path)
    proc = _run(script, "{not valid json")
    assert proc.returncode == 2
    assert proc.stderr.strip() != ""


def test_stdin_json_that_is_not_an_object_exits_2(tmp_path):
    script = _write_dummy(tmp_path)
    proc = _run(script, json.dumps([1, 2, 3]))
    assert proc.returncode == 2


def test_handler_returning_non_int_code_exits_2(tmp_path):
    script = _write_dummy(tmp_path)
    proc = _run(script, json.dumps({"bad_return": True}))
    assert proc.returncode == 2


def test_unencodable_output_exits_2(tmp_path):
    script = _write_dummy(tmp_path)
    proc = _run(script, json.dumps({"unencodable": True}))
    assert proc.returncode == 2
