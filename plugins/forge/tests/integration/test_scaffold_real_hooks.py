"""Integration: scaffold ``templates/project`` into a real git repo and drive
the REAL hook commands from ``plugins/forge/hooks/hooks.json`` (the same
``command`` + ``args``, ``${CLAUDE_PLUGIN_ROOT}`` substituted, JSON on
stdin) through the review #1 probes. Every probe the review reproduced by
hand is here; each must now come out the safe way.

``forge verify`` runs the real skill entrypoints under
``~/.forge/bin/forge-python``; tests that need it skip only when that
interpreter is genuinely absent.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = PLUGIN_ROOT.parent.parent
TEMPLATES = REPO_ROOT / "templates" / "project"
SCAFFOLD = PLUGIN_ROOT / "skills" / "new-project" / "scripts" / "scaffold.py"
FORGE_BIN = PLUGIN_ROOT / "bin" / "forge"
HOOKS_JSON = PLUGIN_ROOT / "hooks" / "hooks.json"
FORGE_PYTHON = Path(os.environ.get("FORGE_PYTHON", Path.home() / ".forge" / "bin" / "forge-python"))

needs_forge_python = pytest.mark.skipif(not FORGE_PYTHON.is_file(),
                                        reason=f"forge-python not installed at {FORGE_PYTHON}")


# ---------------------------------------------------------------------------
# harness
# ---------------------------------------------------------------------------

def _git(project: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(project), *args], check=True, capture_output=True, text=True).stdout


def _commit(project: Path, msg: str) -> None:
    _git(project, "add", "-A")
    _git(project, "-c", "user.email=t@example.com", "-c", "user.name=Forge Test", "commit", "-q", "-m", msg)


@pytest.fixture
def project(tmp_path: Path) -> Path:
    target = tmp_path / "product"
    res = subprocess.run([sys.executable, str(SCAFFOLD), str(target), "--name", "Probe Product", "--skip-doctor",
                          "--forge-root", str(REPO_ROOT)], capture_output=True, text=True)
    assert res.returncode == 0, f"scaffold failed: {res.stdout}\n{res.stderr}"
    _git(target, "init", "-q")
    _commit(target, "scaffold")
    return target


def _hook_command(event: str, match: str | None = None) -> list[str]:
    config = json.loads(HOOKS_JSON.read_text())
    for group in config["hooks"][event]:
        matcher = group.get("matcher")
        if match is not None and matcher and not re.search(matcher, match):
            continue
        hook = group["hooks"][0]
        args = [a.replace("${CLAUDE_PLUGIN_ROOT}", str(PLUGIN_ROOT)) for a in hook.get("args", [])]
        return [hook["command"], *args]
    raise AssertionError(f"no {event} hook matches {match!r}")


class Result:
    def __init__(self, proc: subprocess.CompletedProcess) -> None:
        self.code = proc.returncode
        self.stderr = proc.stderr
        self.out = json.loads(proc.stdout) if proc.stdout.strip() else None

    @property
    def decision(self) -> str | None:
        if isinstance(self.out, dict):
            return (self.out.get("hookSpecificOutput") or {}).get("permissionDecision") or self.out.get("decision")
        return None

    @property
    def reason(self) -> str:
        if not isinstance(self.out, dict):
            return ""
        return self.out.get("reason") or (self.out.get("hookSpecificOutput") or {}).get(
            "permissionDecisionReason") or self.out.get("systemMessage") or ""


def hook(event: str, payload: dict, match: str | None = None, argv0: list[str] | None = None) -> Result:
    cmd = _hook_command(event, match)
    if argv0 is not None:
        cmd = argv0 + cmd[1:]
    env = dict(os.environ, CLAUDE_PLUGIN_ROOT=str(PLUGIN_ROOT))
    proc = subprocess.run(cmd, input=json.dumps(payload), capture_output=True, text=True, timeout=120, env=env)
    return Result(proc)


def stop(project: Path) -> Result:
    return hook("Stop", {"hook_event_name": "Stop", "cwd": str(project), "session_id": "s",
                         "transcript_path": "/dev/null", "stop_hook_active": False})


def pre(project: Path, tool: str, tool_input: dict, agent_type: str | None = None) -> Result:
    payload = {"hook_event_name": "PreToolUse", "cwd": str(project), "session_id": "s",
               "tool_name": tool, "tool_input": tool_input}
    if agent_type:
        payload["agent_type"] = agent_type
    return hook("PreToolUse", payload, match=tool)


def post_write(project: Path, rel: str, content: str) -> Result:
    path = project / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return hook("PostToolUse", {"hook_event_name": "PostToolUse", "cwd": str(project), "session_id": "s",
                                "tool_name": "Write", "tool_input": {"file_path": str(path), "content": content},
                                "tool_response": {"success": True}}, match="Write")


def forge(project: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(FORGE_BIN), *args], capture_output=True, text=True, timeout=900,
                          cwd=project, env=dict(os.environ, FORGE_PYTHON=str(FORGE_PYTHON)))


def _manifest(project: Path) -> dict:
    return json.loads((project / "evidence" / "manifest.json").read_text())


# ---------------------------------------------------------------------------
# the scaffold itself
# ---------------------------------------------------------------------------

def test_fresh_scaffold_stop_passes(project):
    r = stop(project)
    assert (r.code, r.out) == (0, None), r.stderr


def test_every_template_domain_is_a_real_evidence_domain(project):
    import tomllib
    sys.path.insert(0, str(PLUGIN_ROOT / "lib"))
    from forge import evidence
    toml = tomllib.loads((project / "forge.toml").read_text())
    domains = {b["domain"] for b in toml["verify"]}
    assert domains <= set(evidence.DOMAINS)
    assert {"docs", "mfg", "compliance"} <= domains
    covered = [p for b in toml["verify"] for p in b["paths"]]
    for d in ("bom/**", "mfg/**", "compliance/**"):
        assert d in covered, f"m5: {d} changes must be gated"


# ---------------------------------------------------------------------------
# C1 + M9: docs edit -> verify -> Stop passes; last-green recorded
# ---------------------------------------------------------------------------

@needs_forge_python
def test_docs_edit_then_verify_then_stop_passes(project):
    r = post_write(project, "docs/notes.md", "# Notes\n\nA short design note.\n")
    assert r.code == 0, (r.out, r.stderr)
    blocked = stop(project)
    assert blocked.code == 2 and "docs/gardening-docs" in blocked.reason
    v = forge(project, "verify", "--changed", "docs/notes.md", "--project", str(project))
    assert v.returncode == 0, v.stdout + v.stderr
    entry = _manifest(project)["entries"][-1]
    assert (entry["domain"], entry["entrypoint"], entry["result"]) == ("docs", "gardening-docs", "pass")
    r = stop(project)
    assert (r.code, r.out) == (0, None), r.reason


@needs_forge_python
def test_verify_all_records_last_green(project):
    forge(project, "verify", "--all", "--project", str(project))
    state = json.loads((project / ".forge" / "state.json").read_text())
    assert "docs" in state["last_green"], state
    head = _git(project, "rev-parse", "HEAD").strip()
    assert state["last_green"]["docs"]["sha"] == head
    assert state["last_green"]["docs"]["evidence_ids"]


# ---------------------------------------------------------------------------
# C2: evidence must come from real check runs
# ---------------------------------------------------------------------------

def test_cad_change_with_hand_written_evidence_is_blocked(project):
    (project / "cad" / "bracket.py").write_text("WIDTH = 10\n")
    assert stop(project).code == 2
    add = forge(project, "evidence", "--project", str(project), "add", "--artifact", "cad/bracket.py",
                "--domain", "mech", "--claim", "trust me, it is fine", "--result", "pass", "--level", "L1")
    assert add.returncode == 0, add.stderr
    r = stop(project)
    assert r.code == 2
    assert "mech/" in r.reason


def test_committing_the_change_is_still_blocked(project):
    (project / "cad" / "bracket.py").write_text("WIDTH = 10\n")
    _commit(project, "sneak the change in")
    assert _git(project, "status", "--porcelain").strip() == ""
    r = stop(project)
    assert r.code == 2
    assert "cad/bracket.py" in r.reason


@needs_forge_python
def test_future_dated_evidence_is_blocked(project):
    (project / "docs" / "notes.md").write_text("# Notes\n\nText.\n")
    assert forge(project, "verify", "--changed", "docs/notes.md", "--project", str(project)).returncode == 0
    assert stop(project).code == 0
    # the maker cannot write the manifest through a tool ...
    assert pre(project, "Write", {"file_path": str(project / "evidence" / "manifest.json"),
                                  "content": "{}"}).decision == "deny"
    assert pre(project, "Bash", {"command": "echo '{}' > evidence/manifest.json"}).decision == "deny"
    # ... and a hand-edited future date is rejected anyway
    data = _manifest(project)
    data["entries"][-1]["timestamp"] = "2099-01-01T00:00:00Z"
    (project / "evidence" / "manifest.json").write_text(json.dumps(data, indent=2))
    r = stop(project)
    assert r.code == 2
    assert "future" in r.reason


@needs_forge_python
def test_failing_sibling_check_blocks(project):
    """M6: a new, well-formed EARS requirement passes writing-requirements but
    has no trace.json entry, so its sibling tracing-requirements fails."""
    req = project / "requirements" / "requirements.md"
    req.write_text(req.read_text() + (
        "\n## REQ-MECH-002\n\nWhen the lid is dropped from 1 m onto concrete, the enclosure shall "
        "remain closed.\n\nRationale: drop survival.\nVerify: test\n"))
    forge(project, "verify", "--changed", "requirements/requirements.md", "--project", str(project))
    sys_entries = {e["entrypoint"]: e for e in _manifest(project)["entries"]
                   if e.get("domain") == "sys" and e.get("entrypoint")}
    assert sys_entries["writing-requirements"]["result"] == "pass"
    assert sys_entries["tracing-requirements"]["result"] == "fail"
    r = stop(project)
    assert r.code == 2
    assert "sys/tracing-requirements" in r.reason
    assert "sys/writing-requirements" not in r.reason


# ---------------------------------------------------------------------------
# C1: the 7th-block handoff on the scaffold (docs domain) never raises
# ---------------------------------------------------------------------------

def test_block_cap_handoff_on_docs_resets_the_counter(project):
    (project / "docs" / "notes.md").write_text("# Notes\n")
    codes = [stop(project).code for _ in range(7)]
    assert codes == [2] * 6 + [0]
    state = json.loads((project / ".forge" / "state.json").read_text())
    assert state["stop_block_count"] == 0
    unverified = [e for e in _manifest(project)["entries"] if e["status"] == "UNVERIFIED"]
    assert [e["domain"] for e in unverified] == ["docs"]


# ---------------------------------------------------------------------------
# M5: SubagentStop
# ---------------------------------------------------------------------------

def test_verdict_pass_with_failing_criterion_is_blocked(project):
    verdict = {"schema": "forge.verdict/1", "reviewer": "verification-evaluator", "gate": "G2", "subject": "probe",
               "criteria": [{"id": "REQ-MECH-001", "verdict": "FAIL", "evidence": ["out/verify/x.json"],
                             "finding": "snap-fit force 9 N < 15 N", "severity": "critical",
                             "affects": ["requirements", "function"]}],
               "overall": "PASS", "summary": "looks good", "not_checked": []}
    msg = f"Done.\n\n```json\n{json.dumps(verdict)}\n```\n"
    payload = {"hook_event_name": "SubagentStop", "cwd": str(project), "session_id": "s",
               "agent_type": "forge:verification-evaluator", "last_assistant_message": msg,
               "stop_hook_active": False}
    r = hook("SubagentStop", payload, match="forge:verification-evaluator")
    assert r.code == 2
    assert "overall is PASS" in r.reason
    verdict["overall"] = "FAIL"
    payload["last_assistant_message"] = f"Done.\n\n```json\n{json.dumps(verdict)}\n```\n"
    assert hook("SubagentStop", payload, match="forge:verification-evaluator").code == 0


# ---------------------------------------------------------------------------
# PreToolUse probes (m5, M2, M3, M1)
# ---------------------------------------------------------------------------

def test_notebookedit_into_security_is_denied(project):
    r = pre(project, "NotebookEdit", {"notebook_path": str(project / "security" / "probe.ipynb"),
                                      "new_source": "print(1)"})
    assert r.decision == "deny"


@pytest.mark.parametrize("agent", ["forge:verification-evaluator", "forge:red-team"])
def test_judge_bash_write_is_denied(project, agent):
    assert pre(project, "Bash", {"command": "echo pwned > f.txt"}, agent).decision == "deny"
    assert pre(project, "Bash", {"command": "cat evidence/manifest.json"}, agent).decision is None


REVIEW_M3_PROBES = [
    "sed -i 's/2.0/0.5/' params/params.toml",
    "echo > release/y",
    "echo > .claude/settings.json",
    "echo hi\nrm -rf cad",
    "bash -c 'rm -rf cad'",
    "rm -rf out/../cad",
    "find cad -delete",
    "git -C . push --force",
    "git push origin +main",
    "python3 -c \"import urllib.request as u; u.urlopen('https://unlisted.example.net/x')\"",
    "echo x > evidence/manifest.json",
    "echo x > out/verify/geometry.min_wall.json",
    "echo x | tee Release/y",
]


@pytest.mark.parametrize("command", REVIEW_M3_PROBES)
def test_review_bash_bypass_is_denied(project, command):
    r = pre(project, "Bash", {"command": command})
    assert r.decision == "deny", (command, r.out, r.stderr)


@pytest.mark.parametrize("rel,agent", [("PARAMS/params.toml", None), ("Release/x.txt", None),
                                       ("CAD/part.py", "forge:electrical-engineer")])
def test_case_variants_of_protected_paths_are_guarded(project, rel, agent):
    content = "x"
    if rel.lower() == "params/params.toml":
        # make one param verified first (as a human would, committed), then try to change it by case trick
        pp = project / "params" / "params.toml"
        text = pp.read_text().replace('status = "assumed"', 'status = "verified"', 1).replace(
            'verified_by = ""', 'verified_by = "QA Person"', 1).replace("evidence = []", 'evidence = ["EV-0001"]', 1)
        pp.write_text(text)
        content = text.replace("value = 2.0", "value = 0.5", 1)
    r = pre(project, "Write", {"file_path": str(project / rel), "content": content}, agent)
    if rel.startswith("PARAMS") and not (project / "PARAMS").exists():
        pytest.skip("case-sensitive filesystem: PARAMS/ is a different directory here")
    assert r.decision == "deny", (rel, r.out)


# ---------------------------------------------------------------------------
# M4 on the scaffold
# ---------------------------------------------------------------------------

def test_params_set_value_change_needs_a_citation(project):
    r = forge(project, "params", "--project", str(project), "set", "enclosure.wall_thickness", "--value", "0.5")
    assert r.returncode == 1
    assert "--source" in r.stderr
    text = (project / "params" / "params.toml").read_text()
    r = forge(project, "params", "--project", str(project), "set", "enclosure.wall_thickness", "--value", "2.5",
              "--source", "R5d FDM table 3; 2.5 mm for the rev B lid lip")
    assert r.returncode == 0, r.stderr
    new = (project / "params" / "params.toml").read_text()
    assert new.splitlines()[0] == text.splitlines()[0], "file comments must be preserved"
    assert "value = 2.5" in new


# ---------------------------------------------------------------------------
# C3: the real hooks.json command on an interpreter without tomllib
# ---------------------------------------------------------------------------

def test_hooks_fail_closed_without_tomllib(project, tmp_path):
    shim = tmp_path / "python3"
    shim.write_text(f"#!{sys.executable}\n"
                    "import sys, runpy\n"
                    "sys.modules['tomllib'] = None\n"
                    "sys.argv = sys.argv[1:]\n"
                    "runpy.run_path(sys.argv[0], run_name='__main__')\n")
    shim.chmod(0o755)
    (project / "cad" / "bracket.py").write_text("WIDTH = 10\n")
    r = hook("Stop", {"cwd": str(project)}, argv0=[str(shim)])
    assert r.code == 2 and "tomllib" in r.stderr
    r = hook("PreToolUse", {"cwd": str(project), "tool_name": "Bash", "tool_input": {"command": "ls"}},
             match="Bash", argv0=[str(shim)])
    assert r.code == 2
