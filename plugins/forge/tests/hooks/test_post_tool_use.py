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


def test_mapped_path_but_unbuilt_entrypoint_skips_without_claiming_pass(forge_project, tmp_path, monkeypatch):
    """A mapped path whose entrypoint script does not exist is reported as
    SKIPPED (exit 0 plus a systemMessage), never as a pass and never silently.
    (Review #1, m5: this used to assert `returncode in (0, 2)`, which cannot fail.)"""
    import post_tool_use as ptu
    empty_root = tmp_path / "plugin_without_skills"
    (empty_root / "skills").mkdir(parents=True)
    monkeypatch.setattr(ptu, "PLUGIN_ROOT", empty_root)
    code, output = ptu.handle({"cwd": str(forge_project), "tool_name": "Write",
                               "tool_input": {"file_path": str(forge_project / "cad" / "enclosure.py"), "content": "x"}})
    assert code == 0
    assert output is not None and "skipped (not run, not passed)" in output["systemMessage"]
    assert "verifying-geometry" in output["systemMessage"]
    assert "decision" not in output


def test_notebookedit_path_is_dispatched(forge_project, tmp_path, monkeypatch):
    """Review #1, m5: NotebookEdit carries notebook_path, not file_path."""
    import post_tool_use as ptu
    skill_dir = tmp_path / "fake_plugin_root" / "skills" / "verifying-geometry" / "scripts"
    skill_dir.mkdir(parents=True)
    (skill_dir / "verify.py").write_text("import sys\nsys.exit(1)\n")
    monkeypatch.setattr(ptu, "PLUGIN_ROOT", tmp_path / "fake_plugin_root")
    monkeypatch.setattr(ptu, "FORGE_PYTHON", _make_relay_interpreter(tmp_path))
    code, output = ptu.handle({"cwd": str(forge_project), "tool_name": "NotebookEdit",
                               "tool_input": {"notebook_path": str(forge_project / "cad" / "study.ipynb")}})
    assert code == 2
    assert output["decision"] == "block"


def test_uppercase_path_is_dispatched_case_insensitively(forge_project, tmp_path, monkeypatch):
    import post_tool_use as ptu
    skill_dir = tmp_path / "fake_plugin_root" / "skills" / "verifying-geometry" / "scripts"
    skill_dir.mkdir(parents=True)
    (skill_dir / "verify.py").write_text("import sys\nsys.exit(1)\n")
    monkeypatch.setattr(ptu, "PLUGIN_ROOT", tmp_path / "fake_plugin_root")
    monkeypatch.setattr(ptu, "FORGE_PYTHON", _make_relay_interpreter(tmp_path))
    code, output = ptu.handle({"cwd": str(forge_project), "tool_name": "Write",
                               "tool_input": {"file_path": str(forge_project / "CAD" / "part.py"), "content": "x"}})
    assert code == 2


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
        "print('[FORGE_CHECK_ID_PREFIX] geometry.')\n"
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


# ---------------------------------------------------------------------------
# review #1, M7: fix messages are bound to checks by check_id prefix
# ---------------------------------------------------------------------------

def _writer(prefix: str, own: dict, foreign: dict | None = None) -> str:
    """A fake entrypoint: declares ``prefix``, writes its own failing result
    and (to model another entrypoint finishing in the same instant) a
    foreign-prefixed failing result too, then exits 1."""
    def result(cid, rem):
        return ("{'schema': 'forge.check/1', 'check_id': %r, 'target': 't', 'status': 'fail', 'level': 'L1', "
                "'measurements': [{'name': 'x', 'value': 1, 'unit': 'mm', 'limit': {'min': 2}, 'pass': False, "
                "'remediation': %r}], 'tool_versions': {}, 'git_sha': 'x', 'started': '2026-01-01T00:00:00Z', "
                "'duration_s': 0.1}") % (cid, rem)
    lines = ["import json, sys", "from pathlib import Path", f"print('[FORGE_CHECK_ID_PREFIX] {prefix}')",
             "out = Path(sys.argv[sys.argv.index('--project') + 1]) / 'out' / 'verify'",
             "out.mkdir(parents=True, exist_ok=True)"]
    for cid, rem in list(own.items()) + list((foreign or {}).items()):
        lines.append(f"(out / '{cid}.json').write_text(json.dumps({result(cid, rem)}))")
    lines.append("sys.exit(1)")
    return "\n".join(lines) + "\n"


def _two_entrypoint_project(project: Path) -> None:
    text = (project / "forge.toml").read_text().replace(
        'entrypoints = ["verifying-geometry"]', 'entrypoints = ["verifying-geometry", "checking-dfm"]')
    (project / "forge.toml").write_text(text)


def test_simultaneous_fixes_land_under_the_right_check(forge_project, tmp_path, monkeypatch):
    """Seeded wrong: each entrypoint also writes the *other's* result in the
    same instant (same-second mtimes). With mtime attribution both messages
    appeared under both entrypoints; with prefix binding each lands once,
    under its owner."""
    import post_tool_use as ptu
    _two_entrypoint_project(forge_project)
    root = tmp_path / "fake_plugin_root"
    for skill, prefix, own, foreign in (
            ("verifying-geometry", "geometry.", {"geometry.min_wall": "GEOM-FIX"}, {"dfm.draft": "DFM-FIX"}),
            ("checking-dfm", "dfm.", {"dfm.draft": "DFM-FIX"}, {"geometry.min_wall": "GEOM-FIX"})):
        d = root / "skills" / skill / "scripts"
        d.mkdir(parents=True)
        (d / "verify.py").write_text(_writer(prefix, own, foreign))
    monkeypatch.setattr(ptu, "PLUGIN_ROOT", root)
    monkeypatch.setattr(ptu, "FORGE_PYTHON", _make_relay_interpreter(tmp_path))
    rel = "cad/enclosure.py"
    deadline = __import__("time").time() + 30
    geo = ptu._run_entrypoint(forge_project, "verifying-geometry", rel, deadline, ptu.FORGE_PYTHON)
    dfm = ptu._run_entrypoint(forge_project, "checking-dfm", rel, deadline, ptu.FORGE_PYTHON)
    assert geo["prefix"] == "geometry." and dfm["prefix"] == "dfm."
    assert geo["remediations"] == ["geometry.min_wall: GEOM-FIX"]
    assert dfm["remediations"] == ["dfm.draft: DFM-FIX"]
    code, output = ptu.handle({"cwd": str(forge_project), "tool_name": "Write",
                               "tool_input": {"file_path": str(forge_project / rel), "content": "x"}})
    assert code == 2
    reason = output["reason"]
    geo_block, dfm_block = reason.split("[FAIL] checking-dfm")
    assert "GEOM-FIX" in geo_block and "DFM-FIX" not in geo_block
    assert "DFM-FIX" in dfm_block and "GEOM-FIX" not in dfm_block


def test_stale_result_of_same_prefix_is_not_reported(forge_project, tmp_path, monkeypatch):
    """A failing result this run did not rewrite (outside --changed) is stale."""
    import json as _json
    import post_tool_use as ptu
    out = forge_project / "out" / "verify"
    out.mkdir(parents=True)
    (out / "geometry.old_part.json").write_text(_json.dumps({
        "schema": "forge.check/1", "check_id": "geometry.old_part", "status": "fail",
        "measurements": [{"pass": False, "remediation": "OLD-STALE-FIX"}]}))
    d = tmp_path / "root" / "skills" / "verifying-geometry" / "scripts"
    d.mkdir(parents=True)
    (d / "verify.py").write_text(_writer("geometry.", {"geometry.min_wall": "NEW-FIX"}))
    monkeypatch.setattr(ptu, "PLUGIN_ROOT", tmp_path / "root")
    monkeypatch.setattr(ptu, "FORGE_PYTHON", _make_relay_interpreter(tmp_path))
    r = ptu._run_entrypoint(forge_project, "verifying-geometry", "cad/enclosure.py",
                            __import__("time").time() + 30, ptu.FORGE_PYTHON)
    assert r["remediations"] == ["geometry.min_wall: NEW-FIX"]


def test_failing_entrypoint_without_prefix_line_is_an_error(forge_project, tmp_path, monkeypatch):
    """Seeded wrong: no [FORGE_CHECK_ID_PREFIX] line, so nothing can be attributed; blocks as an error."""
    import post_tool_use as ptu
    d = tmp_path / "root" / "skills" / "verifying-geometry" / "scripts"
    d.mkdir(parents=True)
    (d / "verify.py").write_text(_writer("geometry.", {"geometry.min_wall": "FIX"}).replace(
        "print('[FORGE_CHECK_ID_PREFIX] geometry.')", "pass"))
    monkeypatch.setattr(ptu, "PLUGIN_ROOT", tmp_path / "root")
    monkeypatch.setattr(ptu, "FORGE_PYTHON", _make_relay_interpreter(tmp_path))
    code, output = ptu.handle({"cwd": str(forge_project), "tool_name": "Write",
                               "tool_input": {"file_path": str(forge_project / "cad" / "enclosure.py"), "content": "x"}})
    assert code == 2
    assert "[ERROR] verifying-geometry" in output["reason"]
    assert "FORGE_CHECK_ID_PREFIX" in output["reason"]


def test_every_registered_entrypoint_declares_a_prefix_post_tool_use_can_parse():
    """The hook's parser accepts the exact line the skills print."""
    import post_tool_use as ptu
    assert ptu.declared_prefix("[FORGE_CHECK_ID_PREFIX] dfm.\n[SKIP] nothing") == "dfm."
    assert ptu.declared_prefix("[SKIP] nothing\n") is None
