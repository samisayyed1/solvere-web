"""``forge verify`` evidence binding (review #1: C1, C2, M6, M9).

Uses fake entrypoints under a fake plugin tree and the real interpreter as
``forge-python`` (FORGE_PYTHON), so only verify's own recording is tested.
"""

from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from .hookutil import LIB_DIR, PLUGIN_ROOT, run_hook

sys.path.insert(0, str(LIB_DIR))
from forge import evidence, minischema, state  # noqa: E402
from forge.commands import verify  # noqa: E402

PASS = """\
import sys
from pathlib import Path
from forge.checkresult import run_check
with run_check("{cid}", "t", project=Path(sys.argv[sys.argv.index("--project") + 1])) as chk:
    chk.measure("v", 1.0, "1", min=0.0)
"""
FAIL = PASS.replace('chk.measure("v", 1.0, "1", min=0.0)',
                    'chk.measure("v", -1.0, "1", min=0.0, remediation="v is -1, must be >= 0 (seeded)")')
GRAPH_AND_PASS = PASS.replace("with run_check", "_o = Path(sys.argv[sys.argv.index('--project') + 1]) / 'out/verify'\n"
                              "_o.mkdir(parents=True, exist_ok=True)\n"
                              "(_o / 'graph.json').write_text('{{\"nodes\": []}}')\nwith run_check")

TOML = """\
[project]
name = "demo"

[[verify]]
domain = "mech"
paths = ["cad/**"]
entrypoints = ["ep-a", "ep-b"]
rung = "numeric"

[[verify]]
domain = "docs"
paths = ["docs/**", "*.md"]
entrypoints = ["ep-docs"]
rung = "syntax"
"""


class NS:
    def __init__(self, *, all=False, changed=None, project=Path("."), fast=False):
        self.all, self.changed, self.project, self.fast = all, changed, project, fast


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("PYTHONPATH", str(LIB_DIR))
    monkeypatch.setenv("FORGE_PYTHON", sys.executable)
    repo = tmp_path / "repo"
    project = tmp_path / "project"
    (project / "cad").mkdir(parents=True)
    (project / "docs").mkdir()
    (project / "cad" / "part.py").write_text("W = 1\n")
    (project / "docs" / "a.md").write_text("# a\n")
    (project / ".gitignore").write_text("out/\n.forge/\n")
    (project / "forge.toml").write_text(TOML)
    for cmd in (["init", "-q"], ["add", "-A"],
                ["-c", "user.email=t@e", "-c", "user.name=t", "commit", "-q", "-m", "init"]):
        subprocess.run(["git", "-C", str(project), *cmd], check=True, capture_output=True)
    return repo, project


def _ep(repo: Path, skill: str, body: str, cid: str) -> None:
    script = repo / "plugins" / "forge" / "skills" / skill / "scripts" / "verify.py"
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text(textwrap.dedent(body.format(cid=cid)))


def test_one_bound_entry_per_entrypoint_and_docs_is_its_own_domain(env):
    repo, project = env
    _ep(repo, "ep-a", PASS, "mech.a")
    _ep(repo, "ep-b", PASS, "mech.b")
    _ep(repo, "ep-docs", PASS, "docs.links")
    assert verify.run(NS(all=True, project=project), repo) == 0
    entries = evidence.load(project)["entries"]
    assert [(e["domain"], e["entrypoint"]) for e in entries] == [
        ("docs", "ep-docs"), ("mech", "ep-a"), ("mech", "ep-b")]
    schema = json.loads((PLUGIN_ROOT / "schemas" / "evidence.schema.json").read_text())
    assert minischema.validate(evidence.load(project), schema) == []
    for e in entries:
        assert e["recorded_by"] == "forge verify" and e["mode"] == "full" and e["scope"] is None
        (rel,) = e["evidence_files"]
        assert e["evidence_sha256"][rel] == evidence.sha256_file(project / rel)
    assert run_hook("stop.py", {"cwd": str(project)}).returncode == 0


def test_all_pass_run_sets_last_green_with_vouching_entries(env):
    """M9 pass case."""
    repo, project = env
    _ep(repo, "ep-a", PASS, "mech.a")
    _ep(repo, "ep-b", PASS, "mech.b")
    _ep(repo, "ep-docs", PASS, "docs.links")
    verify.run(NS(all=True, project=project), repo)
    lg = state.load(project)["last_green"]
    head = subprocess.run(["git", "-C", str(project), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    assert lg["mech"]["sha"] == head and len(lg["mech"]["evidence_ids"]) == 2
    assert state.resolve_base(project, "mech", evidence.load(project)) == head


def test_failing_entrypoint_blocks_last_green_for_its_domain(env):
    """M9 seeded wrong: a domain with one failing entrypoint is not green."""
    repo, project = env
    _ep(repo, "ep-a", PASS, "mech.a")
    _ep(repo, "ep-b", FAIL, "mech.b")
    _ep(repo, "ep-docs", PASS, "docs.links")
    assert verify.run(NS(all=True, project=project), repo) == 1
    lg = state.load(project)["last_green"]
    assert "mech" not in lg and "docs" in lg


def test_changed_run_records_scope_and_never_sets_last_green(env):
    repo, project = env
    _ep(repo, "ep-a", PASS, "mech.a")
    _ep(repo, "ep-b", PASS, "mech.b")
    (project / "cad" / "part.py").write_text("W = 2\n")
    assert verify.run(NS(changed=["cad/part.py"], project=project), repo) == 0
    entries = evidence.load(project)["entries"]
    assert {e["entrypoint"]: e["scope"] for e in entries} == {"ep-a": ["cad/part.py"], "ep-b": ["cad/part.py"]}
    assert state.load(project)["last_green"] == {}
    assert run_hook("stop.py", {"cwd": str(project)}).returncode == 0


def test_non_check_json_files_are_not_evidence(env):
    """A graph dump written to out/verify is ignored, not a recording error."""
    repo, project = env
    _ep(repo, "ep-docs", GRAPH_AND_PASS, "docs.links")
    _ep(repo, "ep-a", PASS, "mech.a")
    _ep(repo, "ep-b", PASS, "mech.b")
    assert verify.run(NS(all=True, project=project), repo) == 0
    docs = [e for e in evidence.load(project)["entries"] if e["domain"] == "docs"][0]
    assert docs["evidence_files"] == ["out/verify/docs.links.json"]


def test_unknown_domain_is_an_error_not_silently_remapped(env):
    """C1 seeded wrong: the old verify filed unknown domains under sys."""
    repo, project = env
    (project / "forge.toml").write_text(TOML + '\n[[verify]]\ndomain = "weird"\npaths = ["w/**"]\nentrypoints = ["ep-w"]\n')
    _ep(repo, "ep-w", PASS, "weird.x")
    _ep(repo, "ep-a", PASS, "mech.a")
    _ep(repo, "ep-b", PASS, "mech.b")
    _ep(repo, "ep-docs", PASS, "docs.links")
    assert verify.run(NS(all=True, project=project), repo) == 2
    assert not [e for e in evidence.load(project)["entries"] if e["domain"] == "sys"]


def test_error_exit_is_recorded_unverified(env):
    repo, project = env
    _ep(repo, "ep-a", "import sys\nsys.exit(2)\n", "x")
    _ep(repo, "ep-b", PASS, "mech.b")
    _ep(repo, "ep-docs", PASS, "docs.links")
    assert verify.run(NS(all=True, project=project), repo) == 2
    a = [e for e in evidence.load(project)["entries"] if e.get("entrypoint") == "ep-a"][0]
    assert (a["result"], a["status"]) == ("fail", "UNVERIFIED")


def test_skip_entry_needs_no_check_file_but_is_bound_to_inputs(env):
    """An entrypoint that finds nothing to check (exit 0, no result file)."""
    repo, project = env
    _ep(repo, "ep-docs", "print('[SKIP] nothing to check')\n", "x")
    _ep(repo, "ep-a", PASS, "mech.a")
    _ep(repo, "ep-b", PASS, "mech.b")
    (project / "docs" / "b.md").write_text("# b\n")
    assert verify.run(NS(all=True, project=project), repo) == 0
    docs = [e for e in evidence.load(project)["entries"] if e["domain"] == "docs"][0]
    assert docs["notes"].startswith("[SKIP]") and docs["result"] == "pass"
    assert run_hook("stop.py", {"cwd": str(project)}).returncode == 0
    (project / "docs" / "b.md").write_text("# b changed\n")
    assert run_hook("stop.py", {"cwd": str(project)}).returncode == 2


def test_manual_claim_entries_never_carry_binding_fields(tmp_path):
    """`forge evidence add` cannot mint a verify-run entry."""
    forge_bin = PLUGIN_ROOT / "bin" / "forge"
    r = subprocess.run([sys.executable, str(forge_bin), "evidence", "--project", str(tmp_path), "add",
                        "--artifact", "x", "--domain", "docs", "--claim", "docs look fine", "--result", "pass",
                        "--level", "L1"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    (entry,) = evidence.load(tmp_path)["entries"]
    assert "recorded_by" not in entry and "entrypoint" not in entry
    assert evidence.binding_problems(tmp_path, entry, patterns=["docs/**"], changed=[]) != []
