"""Helpers and fixtures for Forge hook tests.

Deliberately not a ``conftest.py``: pytest's default "prepend" import mode
(no ``__init__.py`` in ``tests/``) gives every ``conftest.py`` the bare
module name ``conftest``, and a second one in this directory collides with
``plugins/forge/tests/conftest.py`` (owned by another builder) the moment
both get imported in the same process -- pytest then resolves ``conftest``
to whichever loaded first, breaking the other one's ``from conftest import
...``. Naming this module ``hookutil`` avoids the collision entirely.
Fixture functions defined here (``forge_project`` etc.) still work as
ordinary pytest fixtures once a test module does
``from hookutil import forge_project, ...`` -- pytest discovers fixtures in
a test module's own namespace, not only in ``conftest.py``.

Every test pipes real JSON to a hook script's stdin as a subprocess (the
same way Claude Code invokes it) and asserts on the exit code and parsed
stdout JSON, per CONTRACTS.md §8 ("fixture tests in tests/hooks/ ... pipe
JSON to stdin and assert the exit code and output").
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pytest

TESTS_DIR = Path(__file__).resolve().parent  # plugins/forge/tests/hooks
PLUGIN_ROOT = TESTS_DIR.parent.parent          # plugins/forge
HOOKS_DIR = PLUGIN_ROOT / "hooks"
LIB_DIR = PLUGIN_ROOT / "lib"

if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))


class HookResult:
    def __init__(self, *, returncode: int, output: Any, stderr: str, raw_stdout: str) -> None:
        self.returncode = returncode
        self.output = output
        self.stderr = stderr
        self.raw_stdout = raw_stdout

    @property
    def reason(self) -> str | None:
        if isinstance(self.output, dict):
            if "reason" in self.output:
                return self.output["reason"]
            hso = self.output.get("hookSpecificOutput")
            if isinstance(hso, dict):
                return hso.get("permissionDecisionReason")
        return None

    @property
    def permission_decision(self) -> str | None:
        if isinstance(self.output, dict):
            hso = self.output.get("hookSpecificOutput")
            if isinstance(hso, dict):
                return hso.get("permissionDecision")
        return None


def run_hook(script_name: str, payload: dict | str, *, timeout: float = 15.0) -> HookResult:
    """Run ``hooks/<script_name>`` as a real subprocess, stdin = ``payload``."""
    stdin_text = payload if isinstance(payload, str) else json.dumps(payload)
    proc = subprocess.run(
        [sys.executable, str(HOOKS_DIR / script_name)],
        input=stdin_text, capture_output=True, text=True, timeout=timeout,
    )
    output: Any = None
    if proc.stdout.strip():
        try:
            output = json.loads(proc.stdout)
        except json.JSONDecodeError:
            output = proc.stdout
    return HookResult(returncode=proc.returncode, output=output, stderr=proc.stderr, raw_stdout=proc.stdout)


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True)


PARAMS_TOML = """\
[enclosure.wall_thickness]
value = 2.0
unit = "mm"
status = "assumed"
source = "R5d FDM min wall 0.8-1.2mm; chosen 2.0 for stiffness"

[enclosure.height]
value = 40.0
unit = "mm"
status = "verified"
source = "measured on rev A prototype"
verified_by = "Alice Chen"
evidence = ["EV-0001"]
"""

FORGE_TOML = """\
[project]
name = "smoke"
gate = "G1"

[[verify]]
domain = "mech"
paths = ["cad/**", "params/**"]
entrypoints = ["verifying-geometry"]
rung = "numeric"

[[verify]]
domain = "docs"
paths = ["docs/**", "*.md"]
entrypoints = ["gardening-docs"]
rung = "syntax"

[network]
allowed_domains = ["github.com", "octopart.com"]
"""

REVIEW_MD = """\
# G1 review

Human sign-off: ____________  Name: ____  Date: ____  Decision: PASS / FAIL
"""


def make_forge_project(root: Path) -> Path:
    """A minimal, committed Forge product repo at ``root`` (a real git repo)."""
    (root / "cad").mkdir(parents=True, exist_ok=True)
    (root / "params").mkdir(parents=True, exist_ok=True)
    (root / "reviews").mkdir(parents=True, exist_ok=True)
    (root / "evidence").mkdir(parents=True, exist_ok=True)
    (root / "forge.toml").write_text(FORGE_TOML)
    (root / "params" / "params.toml").write_text(PARAMS_TOML)
    (root / "cad" / "enclosure.py").write_text("print('part')\n")
    (root / "reviews" / "G1.md").write_text(REVIEW_MD)
    (root / ".gitignore").write_text("out/\n.forge/\n")

    _git(root, "init", "-q")
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "config", "user.name", "Forge Test")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    return root


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True).stdout


def commit_all(root: Path, msg: str = "change") -> str:
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", msg)
    return git(root, "rev-parse", "HEAD").strip()


def verify_patterns(project: Path, domain: str, entrypoint: str) -> list[str]:
    import tomllib
    toml = tomllib.loads((project / "forge.toml").read_text())
    pats: list[str] = []
    for b in toml.get("verify", []):
        if b.get("domain") == domain and entrypoint in b.get("entrypoints", []):
            pats.extend(b.get("paths", []))
    return pats


def record_run(project: Path, domain: str, entrypoint: str, *, status: str = "pass", check_id: str | None = None,
               fast: bool = False, scope: list[str] | None = None, returncode: int | None = None) -> str:
    """What ``forge verify`` does for one entrypoint: write a real
    ``forge.check/1`` result through ``forge.checkresult`` and record a
    bound evidence entry through ``forge.evidence.add_verify_entry``."""
    from forge import evidence
    from forge.checkresult import Check
    cid = check_id or f"{domain}.{entrypoint.replace('-', '_')}"
    chk = Check(cid, "t", project=project)
    if status == "pass":
        chk.measure("x", 1.0, "mm", min=0.0)
    else:
        chk.measure("x", -1.0, "mm", min=0.0, remediation="x is -1 mm, below the 0 mm minimum; fix it")
    rc = chk.finish()
    return evidence.add_verify_entry(
        project, domain=domain, entrypoint=entrypoint, returncode=rc if returncode is None else returncode,
        check_files=[project / "out" / "verify" / f"{cid}.json"],
        patterns=verify_patterns(project, domain, entrypoint), scope=scope, fast=fast)


def touch_newer(path: Path) -> None:
    """Bump an mtime a bit into the future so ordering assertions aren't racy on fast filesystems."""
    import os
    future = time.time() + 2
    os.utime(path, (future, future))


# ---------------------------------------------------------------------------
# pytest fixtures -- imported by name into each test module (see module
# docstring for why these don't live in a conftest.py here).
# ---------------------------------------------------------------------------

@pytest.fixture
def forge_project(tmp_path: Path) -> Path:
    return make_forge_project(tmp_path / "proj")


@pytest.fixture
def non_forge_project(tmp_path: Path) -> Path:
    d = tmp_path / "not-forge"
    d.mkdir()
    return d


@pytest.fixture
def head_sha(forge_project: Path) -> str:
    out = subprocess.run(["git", "-C", str(forge_project), "rev-parse", "HEAD"],
                          capture_output=True, text=True, check=True).stdout.strip()
    return out
