"""Helpers for the verification-ladder tests (docs/standards/verification-ladder.md).

The fixture is built the way a user gets a project: scaffold
``templates/project/`` with ``/forge:new-project``'s own scaffold.py into a
temp dir, then overlay the committed fixture sources from
``tests/fixtures/ladder-project/`` and commit, so ``forge verify --all`` and
``make verify`` run against a real product repo with the real toolchain.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent.parent
PLUGIN_ROOT = TESTS_DIR.parent
REPO_ROOT = PLUGIN_ROOT.parent.parent
FIXTURE = TESTS_DIR / "fixtures" / "ladder-project"
SCAFFOLD = PLUGIN_ROOT / "skills" / "new-project" / "scripts" / "scaffold.py"
FORGE_BIN = PLUGIN_ROOT / "bin" / "forge"
FORGE_HOME = Path(os.environ.get("FORGE_HOME", str(Path.home() / ".forge")))
FORGE_PYTHON = FORGE_HOME / "bin" / "forge-python"
LADDER_DOC = REPO_ROOT / "docs" / "standards" / "verification-ladder.md"

# The automatable rungs, in ladder order (verify.RUNG_ORDER minus "visual",
# which make verify does not run -- see the ladder doc).
RUNGS = ("syntax", "build", "validity", "numeric", "physics")

# Every (domain, entrypoint) the template forge.toml registers, with the rung
# its [[verify]] block declares and the evidence level the ladder doc states
# for a passing run on this fixture.
EXPECTED = {
    ("docs", "gardening-docs"): ("syntax", "L1"),
    ("sys", "modeling-systems"): ("build", "L1"),
    ("fw", "building-firmware"): ("build", "L1"),
    ("sys", "writing-requirements"): ("validity", "L1"),
    ("sys", "tracing-requirements"): ("validity", "L1"),
    ("elec", "checking-ecad"): ("validity", "L1"),
    ("compliance", "mapping-compliance"): ("validity", "L0"),
    ("mech", "verifying-geometry"): ("numeric", "L1"),
    ("mech", "checking-dfm"): ("numeric", "L1"),
    ("mech", "stacking-tolerances"): ("numeric", "L1"),
    ("mfg", "checking-dfm"): ("numeric", "L1"),
    ("mfg", "costing-bom"): ("numeric", "L1"),
    ("sim", "running-fea"): ("physics", "L2"),
    ("elec", "designing-circuits"): ("physics", "L2"),
}

REPORT_LINE = re.compile(r"^\[(?P<status>[A-Z/]+)\] (?P<domain>[a-z]+)/(?P<skill>[a-z-]+) \((?P<rung>[a-z?]+)\)")


def _git(project: Path, *args: str) -> None:
    env = {**os.environ, "GIT_AUTHOR_NAME": "ladder", "GIT_AUTHOR_EMAIL": "ladder@example.invalid",
           "GIT_COMMITTER_NAME": "ladder", "GIT_COMMITTER_EMAIL": "ladder@example.invalid"}
    subprocess.run(["git", "-C", str(project), *args], check=True, capture_output=True, env=env)


def make_project(dest: Path, *, overlay: bool = True) -> Path:
    """Scaffold a fresh product repo at ``dest`` and (by default) overlay the
    ladder fixture sources on top, committed as a second commit."""
    r = subprocess.run([sys.executable, str(SCAFFOLD), str(dest), "--name", "ladder", "--skip-doctor"],
                       capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stdout + r.stderr
    if overlay:
        shutil.copytree(FIXTURE, dest, dirs_exist_ok=True)
        _git(dest, "add", "-A")
        _git(dest, "commit", "-q", "-m", "ladder fixture sources")
    return dest


def copy_project(src: Path, dest: Path) -> Path:
    """Copy a built project (sources and git history, not out/ or the manifest's
    runs) so a seeded variant starts from the same committed state."""
    shutil.copytree(src, dest, ignore=shutil.ignore_patterns("out", ".forge"))
    subprocess.run(["git", "-C", str(dest), "checkout", "-q", "--", "evidence"], check=True)
    return dest


def forge_verify(project: Path, *args: str, timeout: int = 900) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(FORGE_BIN), "verify", "--all", "--project", str(project), *args],
                          capture_output=True, text=True, timeout=timeout)


def report(stdout: str) -> list[dict[str, str]]:
    """The ``[STATUS] domain/skill (rung)`` lines of a forge verify run, in order."""
    return [m.groupdict() for line in stdout.splitlines() if (m := REPORT_LINE.match(line))]


def by_key(rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, str]]:
    return {(r["domain"], r["skill"]): r for r in rows}


def verify_entries(project: Path) -> list[dict]:
    data = json.loads((project / "evidence" / "manifest.json").read_text())
    return [e for e in data["entries"] if e.get("recorded_by") == "forge verify"]


def check(project: Path, check_id: str) -> dict:
    return json.loads((project / "out" / "verify" / f"{check_id}.json").read_text())


def failing_checks(project: Path) -> dict[str, dict]:
    out = {}
    for p in sorted((project / "out" / "verify").glob("*.json")):
        try:
            d = json.loads(p.read_text())
        except ValueError:
            continue
        if d.get("schema") == "forge.check/1" and d.get("status") != "pass":
            out[d["check_id"]] = d
    return out
