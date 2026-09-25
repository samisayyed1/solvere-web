"""Integration: every review #2 probe (docs/reviews/phase3-review-2.md) for
the findings fixed in round 2 -- N1, N3, N4, N5, N6, N9, N11, N12, N15 and
the finished part of N2 -- run through the REAL ``hooks.json`` commands on a
freshly scaffolded project (the same harness as ``test_scaffold_real_hooks``).

Each test was run against the pre-fix code (commit 7a7bfa5's hooks and
libraries) and failed there; see the round-2 fixer report. Residuals the owner
accepted (N2 index flags before the first green run, N8 hard links) are
documented in ADR-001 §16 and are not engineered here.

"Green" states are made with :func:`fake_green`: a passing ``forge.check/1``
result and a bound ``forge verify`` entry per ``(domain, entrypoint)`` in
``forge.toml``, through the same library calls ``forge verify`` makes, then
``state.set_last_green`` per domain. That is what ``forge verify --all``
leaves behind, without running the real CAD/FEA toolchain.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from .test_scaffold_real_hooks import (  # noqa: F401 -- `project` is a fixture
    PLUGIN_ROOT, Result, _commit, _git, _hook_command, forge, project,
)

LIB = PLUGIN_ROOT / "lib"
if str(LIB) not in sys.path:
    sys.path.insert(0, str(LIB))

MECH = "forge:mechanical-engineer"
ELEC = "forge:electrical-engineer"
EVAL = "forge:verification-evaluator"
RED = "forge:red-team"


# ---------------------------------------------------------------------------
# harness
# ---------------------------------------------------------------------------

def run(event: str, payload: dict, *, match: str | None = None, env_extra: dict | None = None,
        argv0: list[str] | None = None, path_env: str | None = None) -> Result:
    cmd = _hook_command(event, match)
    if argv0 is not None:
        cmd = argv0 + cmd[1:]
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}
    env["CLAUDE_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    if path_env is not None:
        env["PATH"] = path_env
    env.update(env_extra or {})
    proc = subprocess.run(cmd, input=json.dumps(payload), capture_output=True, text=True, timeout=120, env=env)
    return Result(proc)


def pre(cwd: Path, tool: str, tool_input: dict, agent: str | None = None, **kw) -> Result:
    payload = {"hook_event_name": "PreToolUse", "cwd": str(cwd), "session_id": "s",
               "tool_name": tool, "tool_input": tool_input}
    if agent:
        payload["agent_type"] = agent
    return run("PreToolUse", payload, match=tool, **kw)


def bash(cwd: Path, command: str, agent: str | None = None, **kw) -> Result:
    return pre(cwd, "Bash", {"command": command}, agent, **kw)


def stop(cwd: Path, **kw) -> Result:
    return run("Stop", {"hook_event_name": "Stop", "cwd": str(cwd), "session_id": "s",
                        "transcript_path": "/dev/null", "stop_hook_active": False}, **kw)


def session_start(cwd: Path, **kw) -> Result:
    return run("SessionStart", {"hook_event_name": "SessionStart", "cwd": str(cwd), "session_id": "s",
                                "source": "startup"}, match="startup", **kw)


def sh(project: Path, command: str) -> None:
    """Run a shell command in the project directly (what the tool would do
    once PreToolUse let it through, or what a script does behind its back)."""
    subprocess.run(["bash", "-c", command], cwd=project, check=True, capture_output=True, text=True)


def fake_green(project: Path) -> None:
    import tomllib
    from forge import evidence, state
    from forge.checkresult import Check
    toml = tomllib.loads((project / "forge.toml").read_text())
    by_domain: dict[str, list[str]] = {}
    for block in toml["verify"]:
        for ep in block["entrypoints"]:
            domain = block["domain"]
            pats: list[str] = []
            for b in toml["verify"]:
                if b["domain"] == domain and ep in b["entrypoints"]:
                    pats.extend(p for p in b["paths"] if p not in pats)
            cid = f"{domain}.{ep.replace('-', '_')}"
            chk = Check(cid, "t", project=project)
            chk.measure("x", 1.0, "mm", min=0.0)
            assert chk.finish() == 0
            ev = evidence.add_verify_entry(project, domain=domain, entrypoint=ep, returncode=0,
                                           check_files=[project / "out" / "verify" / f"{cid}.json"],
                                           patterns=pats)
            by_domain.setdefault(domain, []).append(ev)
    head = _git(project, "rev-parse", "HEAD").strip()
    for domain, ids in by_domain.items():
        state.set_last_green(project, domain, sha=head, evidence_ids=ids)


def make_verified(project: Path, key_line: str = 'status = "assumed"') -> str:
    """Make enclosure.wall_thickness verified in the committed state (a human did it)."""
    pp = project / "params" / "params.toml"
    text = pp.read_text().replace(key_line, 'status = "verified"', 1).replace(
        'verified_by = ""', 'verified_by = "Alice Chen"', 1).replace("evidence = []", 'evidence = ["EV-0001"]', 1)
    pp.write_text(text)
    _commit(project, "human verified the wall thickness")
    return text


@pytest.fixture
def green(project: Path) -> Path:
    """A scaffold whose every domain has a passing, bound verify run at HEAD."""
    assert stop(project).code == 0  # the first hook run also pins .forge/base_sha
    fake_green(project)
    r = stop(project)
    assert (r.code, r.out) == (0, None), r.reason
    return project


# ---------------------------------------------------------------------------
# N1: deleting forge.toml, and failing closed without it
# ---------------------------------------------------------------------------

N1_DELETE_PROBES = [
    "rm forge.toml",
    "rm -f forge.toml",
    "unlink forge.toml",
    "python3 -c \"import os; os.remove('forge.toml')\"",
    "git checkout HEAD~1 -- forge.toml",
    "git restore forge.toml",
    "git restore --source=HEAD~1 forge.toml",
    "mv forge.toml forge.toml.bak",
    "git rm forge.toml",
]


@pytest.mark.parametrize("command", N1_DELETE_PROBES)
def test_n1_deleting_forge_toml_asks_on_the_main_thread(project, command):
    r = bash(project, command)
    assert r.decision == "ask", (command, r.out, r.stderr)
    assert "forge.toml" in r.reason


@pytest.mark.parametrize("command", N1_DELETE_PROBES)
@pytest.mark.parametrize("agent", [MECH, ELEC])
def test_n1_deleting_forge_toml_is_denied_for_subagents(project, command, agent):
    r = bash(project, command, agent)
    assert r.decision == "deny", (command, r.out, r.stderr)


def _break_forge_toml(project: Path, how: str) -> None:
    if how == "deleted":
        (project / "forge.toml").unlink()
    elif how == "deleted-and-committed":
        (project / "forge.toml").unlink()
        _commit(project, "drop forge.toml")
    elif how == "unparsable":
        (project / "forge.toml").write_text("[project\nname = 'x'\n")
    elif how == "replaced-by-directory":
        (project / "forge.toml").unlink()
        (project / "forge.toml").mkdir()


@pytest.mark.parametrize("how", ["deleted", "deleted-and-committed", "unparsable", "replaced-by-directory"])
def test_n1_missing_forge_toml_fails_closed_in_every_hook(project, how):
    """Review probe: with forge.toml gone, a verified param changed 2.0->0.5
    and cad/bracket.py changed, Stop exited 0, red-team `echo pwn > f` and an
    electrical-engineer Write to release/x were allowed."""
    make_verified(project)
    pp = project / "params" / "params.toml"
    pp.write_text(pp.read_text().replace("value = 2.0", "value = 0.5", 1))
    (project / "cad" / "bracket.py").write_text("WIDTH = 10\n")
    _break_forge_toml(project, how)

    r = stop(project)
    assert r.code == 2, (how, r.out, r.stderr)
    assert "forge.toml" in (r.reason + r.stderr)

    assert bash(project, "echo pwn > f", RED).decision == "deny"
    assert pre(project, "Write", {"file_path": str(project / "release" / "x"), "content": "x"},
               ELEC).decision == "deny"
    assert pre(project, "Write", {"file_path": str(project / "cad" / "y.py"), "content": "x"},
               MECH).decision == "deny"
    r = bash(project, "ls")
    assert r.decision == "deny" and "forge.toml" in r.reason
    # the main thread may restore it, with a prompt
    assert bash(project, "git checkout HEAD -- forge.toml").decision == "ask"
    assert bash(project, "git checkout HEAD -- forge.toml", MECH).decision == "deny"
    assert pre(project, "Write", {"file_path": str(project / "forge.toml"),
                                  "content": "[project]\nname='x'\n"}).decision == "ask"

    post = run("PostToolUse", {"hook_event_name": "PostToolUse", "cwd": str(project), "session_id": "s",
                               "tool_name": "Write", "tool_input": {"file_path": str(project / "cad" / "bracket.py"),
                                                                    "content": "WIDTH = 10\n"},
                               "tool_response": {"success": True}}, match="Write")
    assert post.code == 2, (post.out, post.stderr)
    sub = run("SubagentStop", {"hook_event_name": "SubagentStop", "cwd": str(project), "session_id": "s",
                               "agent_type": EVAL, "last_assistant_message": "done", "stop_hook_active": False},
              match=EVAL)
    assert sub.code == 2
    ups = run("UserPromptSubmit", {"hook_event_name": "UserPromptSubmit", "cwd": str(project),
                                   "session_id": "s", "prompt": "carry on"})
    assert ups.code == 2 and "forge.toml" in (ups.reason + ups.stderr)
    upe = run("UserPromptExpansion", {"hook_event_name": "UserPromptExpansion", "cwd": str(project),
                                      "session_id": "s", "command_name": "forge:checking-dfm"})
    assert upe.code == 2
    pc = run("PreCompact", {"hook_event_name": "PreCompact", "cwd": str(project), "session_id": "s",
                            "trigger": "manual"}, match="manual")
    assert pc.code == 2
    ss = session_start(project)
    assert ss.code == 0
    assert "forge.toml" in ss.out["additionalContext"] and "GUARDRAILS" in ss.out["additionalContext"]


def test_n1_a_directory_that_never_was_a_forge_project_is_still_a_noop(tmp_path):
    d = tmp_path / "plain"
    d.mkdir()
    subprocess.run(["git", "init", "-q", str(d)], check=True)
    assert stop(d).code == 0
    assert bash(d, "rm -rf build").decision is None


# ---------------------------------------------------------------------------
# N2 (finished part): the last-green inputs digest, and index-flag commands
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("flag", ["--assume-unchanged", "--skip-worktree"])
def test_n2_assume_unchanged_after_green_is_still_gated(green, flag):
    """Review probe: after a green run, `git update-index --assume-unchanged
    cad/dims.py`, then W=2.0 -> W=0.1, and Stop exited 0."""
    project = green
    (project / "cad" / "dims.py").write_text("W = 2.0\n")
    _commit(project, "dims")
    fake_green(project)
    assert stop(project).code == 0
    assert bash(project, f"git update-index {flag} cad/dims.py").decision == "deny"
    sh(project, f"git update-index {flag} cad/dims.py")
    (project / "cad" / "dims.py").write_text("W = 0.1\n")
    # git no longer reports THIS file (evidence/manifest.json is legitimately
    # dirty here: fake_green() writes it without committing, unrelated to
    # the index flag under test).
    assert "cad/dims.py" not in _git(project, "status", "--porcelain")
    r = stop(project)
    assert r.code == 2, r.reason
    assert "mech/" in r.reason and "inputs" in r.reason


# ---------------------------------------------------------------------------
# N3: gitignored design files
# ---------------------------------------------------------------------------

def test_n3_gitignoring_a_new_design_file_does_not_hide_it(project):
    """Review probe: `echo cad/new_part.py >> .gitignore; echo x=1 > cad/new_part.py` -> Stop exited 0."""
    sh(project, "echo cad/new_part.py >> .gitignore; echo x=1 > cad/new_part.py")
    r = stop(project)
    assert r.code == 2, r.reason
    assert "cad/new_part.py" in r.reason


def test_n3_gitignored_helper_under_a_domain_glob_is_hashed_after_green(green):
    project = green
    sh(project, "printf 'cad/local/\\n' >> .gitignore")
    _commit(project, "ignore local helpers")
    fake_green(project)
    assert stop(project).code == 0
    (project / "cad" / "local").mkdir()
    (project / "cad" / "local" / "helper.py").write_text("SCALE = 1.0\n")
    r = stop(project)
    assert r.code == 2 and "cad/local/helper.py" in r.reason, r.reason


def test_n3_gitignore_is_an_input_of_every_domain(green):
    project = green
    sh(project, "echo '*.step' >> .gitignore")
    assert stop(project).code == 2
    import tomllib
    sys.path.insert(0, str(PLUGIN_ROOT / "hooks"))
    import stop as stop_hook
    from forge import evidence
    toml = tomllib.loads((project / "forge.toml").read_text())
    required, _ = stop_hook._required(project, toml, evidence.load(project))
    assert {d for d, _ in required} == {b["domain"] for b in toml["verify"]}
    assert all(paths == {".gitignore"} for paths in required.values()), required
    assert ".gitignore" in evidence.domain_inputs(project, ["cad/**"])


# ---------------------------------------------------------------------------
# N4: exec-capable options for judges
# ---------------------------------------------------------------------------

N4_JUDGE_PROBES = [
    "git grep -O'sh -c \"echo x > evidence/manifest.json\"' value",
    "git grep -Otouch value",
    "git grep -O touch value",
    "git grep --open-files-in-pager=touch value",
    "git grep --open-files-in-pager value",
    "git --no-pager grep -O'touch pwned' value",
    "rg --hostname-bin=touch value",
    "sort --compress-program=sh forge.toml",
    "file -C -m forge.toml",
    "tree -R -H . cad",
    "./forge evidence list",
    "/usr/bin/env touch pwned",
]


@pytest.mark.parametrize("agent", [EVAL, RED])
@pytest.mark.parametrize("command", N4_JUDGE_PROBES)
def test_n4_judge_exec_vectors_are_denied(project, agent, command):
    r = bash(project, command, agent)
    assert r.decision == "deny", (command, r.out, r.stderr)


def test_n4_git_grep_pager_really_executes(project):
    """Why N4 matters: the option runs a program (so the deny above is load-bearing)."""
    (project / "notes.txt").write_text("value\n")
    _commit(project, "notes")
    subprocess.run(["git", "grep", "-Otouch pwned", "value"], cwd=project, capture_output=True, timeout=30)
    assert (project / "pwned").exists()


@pytest.mark.parametrize("command", ["git grep -n value", "git grep -e -O value", "git log --oneline -5",
                                     "git diff --stat HEAD", "rg -n value cad", "sort forge.toml"])
def test_n4_read_only_judge_commands_still_work(project, command):
    assert bash(project, command, EVAL).decision is None


# ---------------------------------------------------------------------------
# N5: a cwd outside the project
# ---------------------------------------------------------------------------

def test_n5_outside_cwd_is_still_guarded(project, tmp_path):
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    assert bash(outside, f"rm -rf {project}/cad").decision == "deny"
    assert bash(outside, f"echo x > {project}/evidence/manifest.json", RED).decision == "deny"
    assert pre(outside, "Write", {"file_path": str(project / "release" / "x"), "content": "x"},
               RED).decision == "deny"
    assert pre(outside, "Write", {"file_path": str(project / "cad" / "x.py"), "content": "x"},
               ELEC).decision == "deny"
    assert bash(outside, f"cd {project} && rm -rf cad").decision == "deny"
    # Stop (no target paths) finds the project from CLAUDE_PROJECT_DIR
    (project / "cad" / "bracket.py").write_text("WIDTH = 10\n")
    r = stop(outside, env_extra={"CLAUDE_PROJECT_DIR": str(project)})
    assert r.code == 2 and "cad/bracket.py" in r.reason, r.reason
    # ... and so does PreToolUse, for relative paths too
    r = bash(outside, "echo x > evidence/manifest.json", env_extra={"CLAUDE_PROJECT_DIR": str(project)})
    assert r.decision is None  # relative to cwd: that is outside/evidence, not the project's
    r = pre(outside, "Write", {"file_path": str(project / "evidence" / "manifest.json"), "content": "{}"},
            env_extra={"CLAUDE_PROJECT_DIR": str(project)})
    assert r.decision == "deny"


def test_n5_judges_never_write_even_without_a_project(tmp_path):
    d = tmp_path / "nowhere"
    d.mkdir()
    for agent in (EVAL, RED):
        assert pre(d, "Write", {"file_path": str(d / "x"), "content": "x"}, agent).decision == "deny"
        assert pre(d, "Edit", {"file_path": str(d / "x"), "old_string": "a", "new_string": "b"},
                   agent).decision == "deny"
        assert bash(d, "echo x > f", agent).decision == "deny"
        assert bash(d, "cat /etc/hostname", agent).decision is None


# ---------------------------------------------------------------------------
# N6: self-promotion to verified
# ---------------------------------------------------------------------------

def _promoted(text: str) -> str:
    return text.replace('status = "assumed"', 'status = "verified"', 1).replace(
        'verified_by = ""', 'verified_by = "QA Person"', 1).replace("evidence = []", 'evidence = ["EV-0002"]', 1)


@pytest.mark.parametrize("agent", [MECH, None])
def test_n6_write_or_edit_promoting_a_param_is_denied(project, agent):
    pp = project / "params" / "params.toml"
    text = pp.read_text()
    r = pre(project, "Write", {"file_path": str(pp), "content": _promoted(text)}, agent)
    assert r.decision == "deny", r.out
    assert "enclosure.wall_thickness" in r.reason and "forge params set" in r.reason
    old = 'status = "assumed"\nsource = "R5d FDM min wall'
    r = pre(project, "Edit", {"file_path": str(pp), "old_string": old,
                              "new_string": old.replace("assumed", "verified")}, agent)
    assert r.decision == "deny"
    r = pre(project, "Edit", {"file_path": str(pp), "old_string": 'verified_by = ""\nevidence = []',
                              "new_string": 'verified_by = "QA Person"\nevidence = ["EV-0002"]'}, agent)
    assert r.decision == "deny"


def test_n6_edit_changing_verified_by_of_a_verified_param_is_denied(project):
    make_verified(project)
    pp = project / "params" / "params.toml"
    r = pre(project, "Edit", {"file_path": str(pp), "old_string": 'verified_by = "Alice Chen"',
                              "new_string": 'verified_by = "Bob"'}, MECH)
    assert r.decision == "deny"


VERIFY_CLI = [
    'forge params set enclosure.wall_thickness --status verified --verified-by "QA Person" --evidence EV-0002',
    "plugins/forge/bin/forge params --project . set enclosure.wall_thickness --evidence=EV-0002",
    "~/.forge/bin/forge-python plugins/forge/bin/forge params set enclosure.wall_thickness --verified-by QA",
    "forge params set enclosure.wall_thickness --status=verified",
]


@pytest.mark.parametrize("command", VERIFY_CLI)
def test_n6_params_set_verification_is_ask_on_main_and_deny_for_subagents(project, command):
    assert bash(project, command).decision == "ask", command
    assert bash(project, command, MECH).decision == "deny", command


def test_n6_params_set_value_change_is_not_a_verification(project):
    r = bash(project, 'forge params set enclosure.wall_thickness --value 2.5 --source "R5d FDM table 3 rev B"')
    assert r.decision is None


def test_n6_verification_needs_evidence_tied_to_the_param(project):
    from forge import evidence
    unrelated = evidence.add_entry(project, artifact="model/system.sysml", domain="sys", claim="sysml check ok",
                                   check_ids=["sys.model"], result="pass", level="L1", evidence_files=[])
    r = forge(project, "params", "--project", str(project), "set", "enclosure.wall_thickness", "--status",
              "verified", "--verified-by", "QA Person", "--evidence", unrelated)
    assert r.returncode == 1 and "tied" in r.stderr and "param:enclosure.wall_thickness" in r.stderr, r.stderr
    tied = evidence.add_entry(project, artifact="param:enclosure.wall_thickness", domain="mech",
                              claim="wall measured 2.02 mm on rev A with calipers", check_ids=[], result="pass",
                              level="L4", evidence_files=[], signed_by="QA Person")
    r = forge(project, "params", "--project", str(project), "set", "enclosure.wall_thickness", "--status",
              "verified", "--verified-by", "QA Person", "--evidence", tied)
    assert r.returncode == 0, r.stderr
    assert 'status = "verified"' in (project / "params" / "params.toml").read_text()


def test_n6_self_promotion_behind_the_hooks_is_caught_at_stop(project):
    """Review probe: demote with `forge params set`, then promote by Edit with
    verified_by="QA Person", evidence=["EV-0002"] (a sysml check); after
    `forge verify --all`, Stop exited 0. Here the file is written behind the
    hooks' back and every domain then made green."""
    from forge import evidence
    assert stop(project).code == 0
    ev2 = evidence.add_entry(project, artifact="model/system.sysml", domain="sys", claim="sysml check ok",
                             check_ids=["sys.model"], result="pass", level="L1", evidence_files=[])
    pp = project / "params" / "params.toml"
    pp.write_text(_promoted(pp.read_text()).replace("EV-0002", ev2))
    fake_green(project)
    r = stop(project)
    assert r.code == 2, r.reason
    assert "enclosure.wall_thickness" in r.reason and "tied" in r.reason


# ---------------------------------------------------------------------------
# N9: .mcp.json, Makefile, CI workflows
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("rel", [".mcp.json", "Makefile", ".github/workflows/forge-ci.yml",
                                 ".github/workflows/new.yml"])
def test_n9_guardrail_config_files(project, rel):
    target = str(project / rel)
    assert pre(project, "Write", {"file_path": target, "content": "{}"}, MECH).decision == "deny"
    assert pre(project, "Write", {"file_path": target, "content": "{}"}).decision == "ask"
    assert bash(project, f"echo x >> {rel}", ELEC).decision == "deny"
    assert bash(project, f"echo x >> {rel}").decision == "ask"


# ---------------------------------------------------------------------------
# N11: the pinned scaffold base
# ---------------------------------------------------------------------------

def test_n11_base_sha_is_pinned(project):
    head = _git(project, "rev-parse", "HEAD").strip()
    session_start(project)
    assert (project / ".forge" / "base_sha").read_text() == head + "\n"


def test_n11_amending_the_scaffold_commit(project):
    """Review probe: change cad, `git add -A && git commit --amend --no-edit` (allowed) -> Stop exited 0."""
    assert stop(project).code == 0
    (project / "cad" / "bracket.py").write_text("WIDTH = 10\n")
    for cmd in ("git add -A && git commit --amend --no-edit", "git commit -a --amend -m root",
                "git commit --amend"):
        assert bash(project, cmd).decision == "deny", cmd
    sh(project, "git add -A && git -c user.email=t@e -c user.name=T commit -q --amend --no-edit")
    r = stop(project)
    assert r.code == 2 and "cad/bracket.py" in r.reason, r.reason


def test_n11_amending_a_later_commit_is_fine(project):
    assert stop(project).code == 0
    (project / "docs" / "n.md").write_text("# n\n")
    _commit(project, "second")
    assert bash(project, "git commit --amend --no-edit").decision is None


def test_n11_reset_to_a_new_root(green):
    """Review probe: after a green run, `git reset --soft $(git commit-tree
    $(git write-tree) -m root)` was allowed and Stop exited 0."""
    project = green
    (project / "cad" / "bracket.py").write_text("WIDTH = 10\n")
    assert bash(project, "git add -A && git reset --soft $(git commit-tree $(git write-tree) -m root)"
                ).decision == "deny"
    sh(project, "git add -A")
    root = subprocess.run(["bash", "-c", "git -c user.email=t@e -c user.name=T commit-tree $(git write-tree) -m root"],
                          cwd=project, check=True, capture_output=True, text=True).stdout.strip()
    assert bash(project, f"git reset --soft {root}").decision == "deny"
    assert bash(project, "git reset --soft HEAD").decision is None
    assert bash(project, "git reset HEAD cad/bracket.py").decision is None
    sh(project, f"git reset -q --soft {root}")
    r = stop(project)
    assert r.code == 2 and "cad/bracket.py" in r.reason, r.reason


def test_n11_missing_pin_fails_closed(project):
    assert stop(project).code == 0
    (project / ".forge" / "base_sha").unlink()
    r = stop(project)
    assert r.code == 2 and "base_sha" in r.reason
    assert bash(project, "git commit --amend --no-edit").decision == "deny"
    assert bash(project, f"rm .forge/base_sha").decision == "deny"


# ---------------------------------------------------------------------------
# N12: case-folded verified-param path
# ---------------------------------------------------------------------------

def test_n12_case_variant_of_params_is_checked_against_the_real_file(project):
    text = make_verified(project)
    r = pre(project, "Write", {"file_path": str(project / "PARAMS" / "params.toml"),
                               "content": text.replace("value = 2.0", "value = 0.5", 1)})
    assert r.decision == "deny", r.out
    assert "direct edits to verified param(s) are blocked: enclosure.wall_thickness" in r.reason


def test_n12_simulated_case_insensitive_filesystem(project, monkeypatch):
    """APFS: PARAMS/params.toml *is* params/params.toml. Simulate it in-process."""
    text = make_verified(project)
    sys.path.insert(0, str(PLUGIN_ROOT / "hooks"))
    import pre_tool_use as ptu
    real = project / "params" / "params.toml"
    orig_is_file, orig_read = Path.is_file, Path.read_text

    def fold(p: Path) -> Path:
        s = str(p)
        return real if s.lower() == str(real).lower() else p

    monkeypatch.setattr(Path, "is_file", lambda self: orig_is_file(fold(self)))
    monkeypatch.setattr(Path, "read_text", lambda self, *a, **k: orig_read(fold(self), *a, **k))
    code, out = ptu.handle({"cwd": str(project), "tool_name": "Write", "tool_input": {
        "file_path": str(project / "PARAMS" / "params.toml"), "content": text.replace("value = 2.0", "value = 0.5", 1)}})
    assert code == 0
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "enclosure.wall_thickness" in out["hookSpecificOutput"]["permissionDecisionReason"]


# ---------------------------------------------------------------------------
# N15: python3 on PATH
# ---------------------------------------------------------------------------

def test_n15_session_start_warns_when_python3_is_missing_from_path(project, tmp_path):
    empty = tmp_path / "emptybin"
    empty.mkdir()
    gitbin = Path(subprocess.run(["bash", "-c", "command -v git"], capture_output=True, text=True).stdout.strip())
    (empty / "git").symlink_to(gitbin)
    r = session_start(project, argv0=[sys.executable], path_env=str(empty))
    assert r.code == 0, r.stderr
    ctx = r.out["additionalContext"]
    assert ctx.startswith("FORGE PYTHON CHECK FAILED"), ctx
    assert "python3" in r.out.get("systemMessage", "")


def test_n15_session_start_warns_on_an_old_python3(project, tmp_path):
    shim_dir = tmp_path / "oldbin"
    shim_dir.mkdir()
    shim = shim_dir / "python3"
    shim.write_text("#!/bin/sh\necho 3.10\nexit 0\n")
    shim.chmod(0o755)
    r = session_start(project, argv0=[sys.executable], path_env=f"{shim_dir}:{os.environ['PATH']}")
    assert r.out["additionalContext"].startswith("FORGE PYTHON CHECK FAILED"), r.out


def test_n15_no_warning_with_a_good_python3(project):
    r = session_start(project)
    assert "FORGE PYTHON CHECK FAILED" not in r.out["additionalContext"]
