"""Tests for hooks/post_tool_use.py (CONTRACTS.md §8-9)."""

from __future__ import annotations

from pathlib import Path

from .hookutil import forge_project, non_forge_project, run_hook


def _write_payload(project: Path, file_path: Path, content: str = "x") -> dict:
    return {"cwd": str(project), "tool_name": "Write",
            "tool_input": {"file_path": str(file_path), "content": content}}


def _make_relay_interpreter(tmp_path: Path) -> Path:
    """A fake ``forge-python`` that actually execs the given script under the
    real interpreter and forwards its exit code (rather than a fixed stub),
    so tests can control pass/fail via the fake verify.py's own exit code."""
    path = tmp_path / "forge-python"
    path.write_text(
        "#!/usr/bin/env python3\n"
        "import subprocess, sys\n"
        "sys.exit(subprocess.call([sys.executable] + sys.argv[1:]))\n"
    )
    path.chmod(0o755)
    return path


def test_noop_outside_forge_project(non_forge_project):
    result = run_hook("post_tool_use.py", _write_payload(non_forge_project, non_forge_project / "a.py"))
    assert result.returncode == 0
    assert result.output is None


def test_path_with_no_mapped_entrypoint_is_silent(forge_project):
    result = run_hook("post_tool_use.py", _write_payload(forge_project, forge_project / "README.md"))
    assert result.returncode == 0
    assert result.output is None


def test_mapped_path_but_unbuilt_entrypoint_skips_without_claiming_pass(forge_project):
    """verifying-geometry's verify.py does not exist under this fixture's plugin
    tree copy -- but hooks/post_tool_use.py resolves entrypoints from the real
    PLUGIN_ROOT/skills, so this only exercises the skip path when that skill
    genuinely isn't present relative to the *test* plugin tree; skip is still
    the only legal non-pass output regardless."""
    result = run_hook("post_tool_use.py", _write_payload(forge_project, forge_project / "cad" / "enclosure.py"))
    assert result.returncode in (0, 2)
    if result.returncode == 0 and result.output is not None:
        assert "systemMessage" in result.output
        assert "skipped" in result.output["systemMessage"]
    # Never a bare pass claim with no evidence behind it.
    if isinstance(result.output, dict):
        assert result.output.get("decision") != "pass"


def test_entrypoint_pass_produces_no_output(forge_project, tmp_path, monkeypatch):
    """With a fake entrypoint script + a fake forge-python that always exits 0,
    a passing check must not block."""
    skill_dir = tmp_path / "fake_plugin_root" / "skills" / "verifying-geometry" / "scripts"
    skill_dir.mkdir(parents=True)
    (skill_dir / "verify.py").write_text("import sys\nsys.exit(0)\n")

    fake_interpreter = _make_relay_interpreter(tmp_path)

    import post_tool_use as ptu
    monkeypatch.setattr(ptu, "PLUGIN_ROOT", tmp_path / "fake_plugin_root")
    monkeypatch.setattr(ptu, "FORGE_PYTHON", fake_interpreter)

    code, output = ptu.handle({"cwd": str(forge_project), "tool_name": "Write",
                                "tool_input": {"file_path": str(forge_project / "cad" / "enclosure.py"), "content": "x"}})
    assert code == 0
    assert output is None


def test_entrypoint_fail_blocks_with_remediation_summary(forge_project, tmp_path, monkeypatch):
    """Sabotage case: a failing check_result.json must block with exit 2 and
    its remediation text, never a silent pass."""
    skill_dir = tmp_path / "fake_plugin_root" / "skills" / "verifying-geometry" / "scripts"
    skill_dir.mkdir(parents=True)
    (skill_dir / "verify.py").write_text(
        "import json, sys, time\n"
        "from pathlib import Path\n"
        "out = Path(sys.argv[sys.argv.index('--project') + 1]) / 'out' / 'verify'\n"
        "out.mkdir(parents=True, exist_ok=True)\n"
        "(out / 'geometry.min_wall.json').write_text(json.dumps({\n"
        "  'schema': 'forge.check/1', 'check_id': 'geometry.min_wall', 'target': 'cad/enclosure.py',\n"
        "  'status': 'fail', 'level': 'L1',\n"
        "  'measurements': [{'name': 'min_wall', 'value': 1.5, 'unit': 'mm', 'limit': {'min': 2.0}, 'pass': False,\n"
        "                     'remediation': 'Wall is 1.5mm < 2.0mm minimum; thicken it.'}],\n"
        "  'tool_versions': {}, 'git_sha': 'x', 'started': '2026-01-01T00:00:00Z', 'duration_s': 0.1,\n"
        "}))\n"
        "sys.exit(1)\n"
    )

    fake_interpreter = _make_relay_interpreter(tmp_path)

    import post_tool_use as ptu
    monkeypatch.setattr(ptu, "PLUGIN_ROOT", tmp_path / "fake_plugin_root")
    monkeypatch.setattr(ptu, "FORGE_PYTHON", fake_interpreter)

    code, output = ptu.handle({"cwd": str(forge_project), "tool_name": "Write",
                                "tool_input": {"file_path": str(forge_project / "cad" / "enclosure.py"), "content": "x"}})
    assert code == 2
    assert output["decision"] == "block"
    assert "thicken it" in output["reason"].lower()
    assert len(output["reason"]) <= 1500


def test_missing_forge_python_skips_with_note(forge_project, tmp_path, monkeypatch):
    skill_dir = tmp_path / "fake_plugin_root" / "skills" / "verifying-geometry" / "scripts"
    skill_dir.mkdir(parents=True)
    (skill_dir / "verify.py").write_text("import sys\nsys.exit(0)\n")

    import post_tool_use as ptu
    monkeypatch.setattr(ptu, "PLUGIN_ROOT", tmp_path / "fake_plugin_root")
    monkeypatch.setattr(ptu, "FORGE_PYTHON", tmp_path / "does-not-exist")

    code, output = ptu.handle({"cwd": str(forge_project), "tool_name": "Write",
                                "tool_input": {"file_path": str(forge_project / "cad" / "enclosure.py"), "content": "x"}})
    assert code == 0
    assert "skipped" in output["systemMessage"]
    assert "not installed" in output["systemMessage"]
