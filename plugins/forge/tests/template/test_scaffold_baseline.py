"""The scaffolders leave a git baseline commit, so the Stop hook's evidence
gate has something to diff against (lib/forge/gitbaseline.py)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = PLUGIN_ROOT.parent.parent
NEW_PROJECT = PLUGIN_ROOT / "skills" / "new-project" / "scripts" / "scaffold.py"
INIT = PLUGIN_ROOT / "skills" / "init" / "scripts" / "scaffold.py"
WRAPPER = PLUGIN_ROOT / "hooks" / "_failclosed.py"


def _env_without_git_identity(tmp_path: Path) -> dict:
    """No global/system git config at all: the scaffolder must still commit."""
    env = dict(os.environ, GIT_CONFIG_GLOBAL=str(tmp_path / "empty-gitconfig"), GIT_CONFIG_NOSYSTEM="1",
               HOME=str(tmp_path / "home"))
    for k in ("GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL"):
        env.pop(k, None)
    (tmp_path / "home").mkdir(exist_ok=True)
    (tmp_path / "empty-gitconfig").write_text("")
    return env


def _git(path: Path, *args: str, env=None) -> str:
    return subprocess.run(["git", "-C", str(path), *args], capture_output=True, text=True, check=True,
                          env=env).stdout


def _stop(project: Path) -> int:
    return subprocess.run([sys.executable, str(WRAPPER), "stop"], input=json.dumps({"cwd": str(project)}),
                          capture_output=True, text=True).returncode


def test_new_project_is_a_repo_with_one_clean_baseline_commit(tmp_path):
    target = tmp_path / "p"
    env = _env_without_git_identity(tmp_path)
    r = subprocess.run([sys.executable, str(NEW_PROJECT), str(target), "--name", "P", "--skip-doctor",
                        "--forge-root", str(REPO_ROOT)], capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stderr
    assert _git(target, "rev-list", "--count", "HEAD", env=env).strip() == "1"
    assert _git(target, "status", "--porcelain", env=env).strip() == ""
    assert "forge.toml" in _git(target, "ls-files", env=env).split()
    assert _git(target, "log", "-1", "--format=%ae", env=env).strip() == "forge-scaffold@localhost"
    assert _stop(target) == 0


def test_new_project_uses_the_users_git_identity_when_set(tmp_path):
    target = tmp_path / "p"
    env = _env_without_git_identity(tmp_path)
    (tmp_path / "empty-gitconfig").write_text("[user]\n\tname = Ada\n\temail = ada@example.com\n")
    subprocess.run([sys.executable, str(NEW_PROJECT), str(target), "--skip-doctor"], check=True,
                   capture_output=True, env=env)
    assert _git(target, "log", "-1", "--format=%ae", env=env).strip() == "ada@example.com"


def test_without_the_baseline_stop_blocks(tmp_path):
    """Seeded wrong: no commit means every file is 'changed' and the gate blocks."""
    target = tmp_path / "p"
    subprocess.run([sys.executable, str(NEW_PROJECT), str(target), "--skip-doctor", "--no-commit"], check=True,
                   capture_output=True)
    assert not (target / ".git").exists()
    subprocess.run(["git", "init", "-q", str(target)], check=True)
    assert _stop(target) == 2


def test_init_commits_only_forge_files_in_an_existing_repo(tmp_path):
    repo = tmp_path / "existing"
    env = _env_without_git_identity(tmp_path)
    repo.mkdir()
    _git(repo, "init", "-q", env=env)
    (repo / "app.py").write_text("print('mine')\n")
    _git(repo, "add", "app.py", env=env)
    _git(repo, "-c", "user.name=u", "-c", "user.email=u@e", "commit", "-q", "-m", "user work", env=env)
    (repo / "app.py").write_text("print('uncommitted user edit')\n")
    (repo / "scratch.txt").write_text("untracked user file\n")
    r = subprocess.run([sys.executable, str(INIT), str(repo), "--forge-root", str(REPO_ROOT)],
                       capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stderr
    committed = _git(repo, "show", "--name-only", "--format=", "HEAD", env=env).split()
    assert "forge.toml" in committed and ".gitignore" in committed
    assert "app.py" not in committed and "scratch.txt" not in committed
    assert not any(c.startswith("out/") for c in committed), "gitignored template files are not committed"
    status = _git(repo, "status", "--porcelain", env=env)
    assert " M app.py" in status and "?? scratch.txt" in status


def test_init_git_inits_a_plain_directory(tmp_path):
    d = tmp_path / "plain"
    d.mkdir()
    (d / "notes.md").write_text("# notes\n")
    env = _env_without_git_identity(tmp_path)
    r = subprocess.run([sys.executable, str(INIT), str(d)], capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stderr
    assert (d / ".git").is_dir()
    assert "forge.toml" in _git(d, "ls-files", env=env).split()
    assert "notes.md" not in _git(d, "ls-files", env=env).split()
