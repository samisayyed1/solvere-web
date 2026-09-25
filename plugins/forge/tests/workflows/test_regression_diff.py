"""regression_diff.py: deterministic diff for the regression-sweep workflow
(M9, review #1: "the diff is done by an LLM with no schema"). Classifies
check_ids by exact status comparison, and flags a domain as stale by
comparing its last_green sha (read through forge.state's public load() API)
against the current tree -- never an LLM's judgement call."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = PLUGIN_ROOT / "workflows" / "scripts" / "regression_diff.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("forge_regression_diff", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def mod():
    return _load_module()


def _check(check_id: str, status: str, *, remediation: str | None = None) -> dict:
    result = {
        "schema": "forge.check/1", "check_id": check_id, "target": "x", "status": status,
        "level": "L1", "measurements": [], "tool_versions": {}, "git_sha": "nogit",
        "started": "2026-01-01T00:00:00Z", "duration_s": 0.1,
    }
    if status != "pass":
        result["measurements"] = [{"name": "m", "value": 1, "unit": "1", "limit": {"max": 0},
                                    "pass": False, "remediation": remediation or "fix it please"}]
    return result


def _write(dir_: Path, check_id: str, status: str, **kw):
    dir_.mkdir(parents=True, exist_ok=True)
    (dir_ / f"{check_id}.json").write_text(json.dumps(_check(check_id, status, **kw)))


def test_new_check_with_no_previous_run(mod, tmp_path):
    _write(tmp_path / "out" / "verify", "geometry.min_wall", "pass")
    result = mod.run(tmp_path, tmp_path / "out" / "verify", tmp_path / "out" / "verify.previous")
    assert result["schema"] == "forge.regression_diff/1"
    assert result["has_previous"] is False
    assert result["checks"]["new"] == ["geometry.min_wall"]
    assert result["checks"]["regressed"] == []


def test_regression_detected_pass_to_fail(mod, tmp_path):
    _write(tmp_path / "out" / "verify.previous", "geometry.min_wall", "pass")
    _write(tmp_path / "out" / "verify", "geometry.min_wall", "fail", remediation="thicken the wall")
    result = mod.run(tmp_path, tmp_path / "out" / "verify", tmp_path / "out" / "verify.previous")
    assert result["has_previous"] is True
    assert len(result["checks"]["regressed"]) == 1
    r = result["checks"]["regressed"][0]
    assert r["check_id"] == "geometry.min_wall"
    assert r["previous_status"] == "pass" and r["current_status"] == "fail"
    assert "thicken the wall" in r["remediation"]
    assert result["checks"]["fixed"] == []
    assert "1 regressed" in result["summary"]


def test_fix_detected_fail_to_pass(mod, tmp_path):
    _write(tmp_path / "out" / "verify.previous", "geometry.min_wall", "fail")
    _write(tmp_path / "out" / "verify", "geometry.min_wall", "pass")
    result = mod.run(tmp_path, tmp_path / "out" / "verify", tmp_path / "out" / "verify.previous")
    assert len(result["checks"]["fixed"]) == 1
    assert result["checks"]["fixed"][0]["check_id"] == "geometry.min_wall"
    assert result["checks"]["regressed"] == []


def test_unchanged_and_removed_checks(mod, tmp_path):
    _write(tmp_path / "out" / "verify.previous", "a.check", "pass")
    _write(tmp_path / "out" / "verify.previous", "b.check", "pass")
    _write(tmp_path / "out" / "verify", "a.check", "pass")
    result = mod.run(tmp_path, tmp_path / "out" / "verify", tmp_path / "out" / "verify.previous")
    assert result["checks"]["unchanged"] == ["a.check"]
    assert result["checks"]["removed"] == ["b.check"]
    assert result["checks"]["new"] == []


def test_non_check_json_files_are_ignored(mod, tmp_path):
    verify_dir = tmp_path / "out" / "verify"
    verify_dir.mkdir(parents=True)
    (verify_dir / "not_a_check.json").write_text(json.dumps({"schema": "something.else/1"}))
    result = mod.run(tmp_path, verify_dir, tmp_path / "out" / "verify.previous")
    assert result["checks"]["new"] == []


def _init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=path, check=True)
    (path / "README.md").write_text("x\n")
    subprocess.run(["git", "add", "."], cwd=path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=path, check=True)


def test_domain_flagged_stale_when_last_green_sha_is_behind(mod, tmp_path):
    _init_git_repo(tmp_path)
    from forge.checkresult import git_sha
    from forge import state as forge_state
    stale_sha = git_sha(tmp_path)
    forge_state.set_last_green(tmp_path, "mech", sha=stale_sha)
    (tmp_path / "cad").mkdir()
    (tmp_path / "cad" / "part.py").write_text("# changed\n")
    result = mod.diff_domains(tmp_path)
    mech = next(d for d in result if d["domain"] == "mech")
    assert mech["changed_paths"] == ["cad/part.py"]
    assert mech["stale"] is True
    assert mech["last_green"]["sha"] == stale_sha


def test_domain_not_stale_when_no_changed_files(mod, tmp_path):
    _init_git_repo(tmp_path)
    result = mod.diff_domains(tmp_path)
    mech = next(d for d in result if d["domain"] == "mech")
    assert mech["stale"] is False
    assert mech["changed_paths"] == []


def test_domain_not_stale_when_last_green_sha_matches_current(mod, tmp_path):
    _init_git_repo(tmp_path)
    from forge.checkresult import git_sha
    from forge import state as forge_state
    (tmp_path / "cad").mkdir()
    (tmp_path / "cad" / "part.py").write_text("# changed\n")
    current_sha = git_sha(tmp_path)  # includes "-dirty" since cad/part.py is untracked/uncommitted
    forge_state.set_last_green(tmp_path, "mech", sha=current_sha)
    result = mod.diff_domains(tmp_path)
    mech = next(d for d in result if d["domain"] == "mech")
    assert mech["stale"] is False


def test_domain_diff_without_git_repo_never_raises(mod, tmp_path):
    result = mod.diff_domains(tmp_path)
    assert isinstance(result, list) and len(result) == len(mod.DOMAIN_PATH_PREFIXES)


def test_main_prints_valid_json_and_exits_0(tmp_path, capsys):
    proc = subprocess.run([sys.executable, str(SCRIPT), "--project", str(tmp_path)],
                          capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0
    parsed = json.loads(proc.stdout)
    assert parsed["schema"] == "forge.regression_diff/1"
