#!/usr/bin/env python3
"""PreToolUse guardrails (CONTRACTS.md §8, ADR-001 §5, brief §3.4).

Matched on ``Write|Edit|MultiEdit|NotebookEdit|Bash|WebFetch`` in
``hooks/hooks.json``. Budget: <= 1 s (R1a §15 -- a PreToolUse timeout means
the tool call *proceeds*, so this script must stay fast: at most a couple of
file reads and regex/TOML checks, no subprocesses).

No-op (exit 0, fast) when the project has no ``forge.toml``.

Policy is anchored on ``agent_type`` (CONTRACTS §13), never on tool-name
prefixes, per ADR-001 §5.

Protections implemented here:
  1. Judge agents (``forge:verification-evaluator``, ``forge:red-team``) may
     never use a write tool -- maker != checker (ADR-001 D6).
  2. ``cad/**`` may only be written by ``forge:mechanical-engineer``; the
     main thread (empty ``agent_type``) gets ``ask`` instead of a hard deny.
  3. Protected paths (``release/**``, ``security/**``,
     ``.claude/settings*.json``, ``hil/bench*.toml``) are never written by
     any tool call.
  4. ``reviews/G*.md``: an edit that fills a previously-blank
     "Human sign-off:" line is denied (only a human may fill it, CONTRACTS §7).
  5. ``params/params.toml``: a Write/Edit/MultiEdit that changes a leaf
     whose current ``status`` is ``verified`` is denied; the sourced path is
     ``forge params set --justification`` (invoked via Bash, which this hook
     does not intercept the same way).
  6. Destructive Bash outside ``out/`` (rm -rf, git push --force*, git reset
     --hard, git clean -fd, dd, mkfs, chmod -R 777, ``> /dev/``) is denied.
  7. Bash ``curl``/``wget`` and WebFetch to a domain outside forge.toml
     ``[network] allowed_domains`` are denied.

This is defense-in-depth: the primary control for shell destructiveness and
network egress is the product repo's sandboxed ``.claude/settings.json``
(ADR-001 §5); this hook is a second, plugin-shipped layer that also covers
non-sandboxed contexts.
"""

from __future__ import annotations

import re
import shlex
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (  # noqa: E402
    find_project_root, load_forge_toml, glob_match, is_judge, is_mechanical_engineer, tomllib,
)

WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}

PROTECTED_PREFIXES = ("release/", "security/")
SETTINGS_RE = re.compile(r"^\.claude/settings.*\.json$")

# Only the sign-off value itself (up to the next "  Name:" field, or end of
# line if there is none) -- the rest of the line ("Name: ___  Date: ___
# Decision: ...", CONTRACTS.md §7) is not part of what a human "fills in"
# here and must not be mistaken for filled sign-off text.
SIGNOFF_RE = re.compile(r"^Human sign-off:\s*(.*?)(?:\s{2,}Name:|\s*$)", re.MULTILINE)

FORCE_PUSH_RE = re.compile(r"git\s+push\b[^|;&]*(--force(-with-lease)?\b|(?<!\S)-f\b)")
RESET_HARD_RE = re.compile(r"git\s+reset\s+--hard\b")
DD_RE = re.compile(r"(^|[;&|]\s*)dd\s")
MKFS_RE = re.compile(r"(^|[;&|]\s*)mkfs[.\w]*\s")
DEV_REDIRECT_RE = re.compile(r">\s*/dev/")
CURL_WGET_RE = re.compile(r"(^|[\s;&|])(curl|wget)\s")
URL_RE = re.compile(r"https?://([^/\s'\"]+)")

_ALWAYS_DENY = (
    (FORCE_PUSH_RE, "force-push is never allowed"),
    (RESET_HARD_RE, "git reset --hard discards uncommitted work"),
    (DD_RE, "dd can overwrite a raw device"),
    (MKFS_RE, "mkfs destroys a filesystem"),
    (DEV_REDIRECT_RE, "redirecting output to a device file is never allowed"),
)


def _deny(reason: str) -> dict:
    return {"hookSpecificOutput": {
        "hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": reason,
    }}


def _ask(reason: str) -> dict:
    return {"hookSpecificOutput": {
        "hookEventName": "PreToolUse", "permissionDecision": "ask", "permissionDecisionReason": reason,
    }}


def _rel_path(project: Path, file_path: str) -> str | None:
    try:
        p = Path(file_path)
        if not p.is_absolute():
            p = project / p
        return p.resolve().relative_to(project.resolve()).as_posix()
    except (OSError, ValueError):
        return None


def _read_old_content(project: Path, file_path: str) -> str | None:
    try:
        p = Path(file_path)
        if not p.is_absolute():
            p = project / p
        if not p.is_file():
            return None
        return p.read_text()
    except OSError:
        return None


def _compute_new_content(tool_name: str, tool_input: dict, old_content: str | None) -> str | None:
    """Best-effort simulation of the post-edit file content. ``None`` means
    "could not be simulated" -- callers must then fail closed for anything
    that relies on it (e.g. the verified-params guard)."""
    if tool_name == "Write":
        return tool_input.get("content")
    if tool_name == "Edit":
        if old_content is None:
            return None
        old_s, new_s = tool_input.get("old_string", ""), tool_input.get("new_string", "")
        if old_s and old_s not in old_content:
            return None
        count = 0 if tool_input.get("replace_all") else 1
        return old_content.replace(old_s, new_s, -1 if count == 0 else count) if old_s else old_content
    if tool_name == "MultiEdit":
        content = old_content
        for edit in tool_input.get("edits") or []:
            if content is None:
                return None
            old_s, new_s = edit.get("old_string", ""), edit.get("new_string", "")
            if old_s and old_s not in content:
                return None
            count = 0 if edit.get("replace_all") else 1
            content = content.replace(old_s, new_s, -1 if count == 0 else count) if old_s else content
        return content
    return None  # NotebookEdit and anything else: not modeled beyond path rules


def _is_blank_signoff(value: str) -> bool:
    return re.sub(r"[_\s]", "", value) == ""


def _signoff_filled(old_content: str | None, new_content: str | None) -> bool:
    if new_content is None:
        return False
    new_vals = SIGNOFF_RE.findall(new_content)
    if not new_vals:
        return False
    old_vals = SIGNOFF_RE.findall(old_content) if old_content else []
    for i, new_v in enumerate(new_vals):
        if _is_blank_signoff(new_v):
            continue
        old_v = old_vals[i] if i < len(old_vals) else ""
        if _is_blank_signoff(old_v):
            return True
    return False


def _iter_param_leaves(data, prefix=()):
    if not isinstance(data, dict):
        return
    if "value" in data and "status" in data:
        yield prefix, data
        return
    for key, val in data.items():
        if isinstance(val, dict):
            yield from _iter_param_leaves(val, prefix + (key,))


def _get_path(data, path):
    node = data
    for key in path:
        if not isinstance(node, dict) or key not in node:
            return None
        node = node[key]
    return node


def _verified_param_violation(old_content: str | None, new_content: str | None) -> str | None:
    if tomllib is None:
        return None
    if new_content is None:
        return ("params.toml could not be simulated for this edit (old_string not found in the "
                "current file); denied out of caution. Re-read the file, or use "
                "`forge params set <key> --justification \"...\"`.")
    try:
        new_data = tomllib.loads(new_content)
    except tomllib.TOMLDecodeError as exc:
        return f"the edited params.toml would no longer parse as TOML ({exc}); fix syntax or use `forge params set`."
    try:
        old_data = tomllib.loads(old_content) if old_content else {}
    except tomllib.TOMLDecodeError:
        old_data = {}
    changed = [".".join(path) for path, leaf in _iter_param_leaves(old_data)
               if leaf.get("status") == "verified" and _get_path(new_data, path) != leaf]
    if not changed:
        return None
    return ("direct edits to verified param(s) are blocked: " + ", ".join(sorted(changed)) +
            ". Change them with `forge params set <key> --justification \"<source>\"` (run via Bash), "
            "which records the old value in params/CHANGELOG.md.")


def _handle_write_tool(project: Path, tool_name: str, tool_input: dict, agent_type: str | None) -> dict | None:
    if is_judge(agent_type):
        return _deny(f"{agent_type} is a read-only reviewer (CONTRACTS.md §13, maker != checker); "
                     f"it must never use {tool_name}.")

    file_path = tool_input.get("file_path")
    if not file_path:
        return None
    rel = _rel_path(project, file_path)
    if rel is None:
        return None

    if glob_match("cad/**", rel):
        if is_mechanical_engineer(agent_type):
            pass
        elif not agent_type:
            return _ask(f"{rel} is under cad/**, normally authored only by forge:mechanical-engineer "
                        "(CONTRACTS.md §13). Confirm this main-thread edit is intended.")
        else:
            return _deny(f"{rel} is under cad/**; only forge:mechanical-engineer may write there "
                         f"(CONTRACTS.md §13), not {agent_type}.")

    if rel.startswith(PROTECTED_PREFIXES):
        return _deny(f"{rel} is release/security-controlled and may not be written by an agent.")
    if SETTINGS_RE.match(rel):
        return _deny(f"{rel} is a Claude Code settings file; agents may not edit it.")
    if glob_match("hil/bench*.toml", rel):
        return _deny(f"{rel} is HIL bench configuration; agents may not edit it (brief §3.4).")

    if glob_match("reviews/G*.md", rel):
        old_content = _read_old_content(project, file_path)
        new_content = _compute_new_content(tool_name, tool_input, old_content)
        if _signoff_filled(old_content, new_content):
            return _deny(f"{rel}: the 'Human sign-off:' line may only be filled in by a human "
                         "(CONTRACTS.md §7). Leave it blank.")

    if rel == "params/params.toml":
        old_content = _read_old_content(project, file_path)
        new_content = _compute_new_content(tool_name, tool_input, old_content)
        violation = _verified_param_violation(old_content, new_content)
        if violation:
            return _deny(violation)

    return None


def _split_segments(command: str) -> list[str]:
    return re.split(r"&&|\|\||;|\|", command)


def _all_within_out(paths: list[str]) -> bool:
    if not paths:
        return False
    for p in paths:
        norm = p[2:] if p.startswith("./") else p
        if not (norm == "out" or norm.startswith("out/")):
            return False
    return True


def _rm_is_recursive_force(flags: list[str]) -> bool:
    short = "".join(t.lstrip("-") for t in flags if t.startswith("-") and not t.startswith("--"))
    long_flags = {t for t in flags if t.startswith("--")}
    recursive = "r" in short or "R" in short or "--recursive" in long_flags
    force = "f" in short or "--force" in long_flags
    return recursive and force


def _check_scoped_destructive(command: str) -> str | None:
    for segment in _split_segments(command):
        segment = segment.strip()
        if not segment:
            continue
        try:
            tokens = shlex.split(segment)
        except ValueError:
            continue
        if not tokens:
            continue
        prog = tokens[0].rsplit("/", 1)[-1]
        rest = tokens[1:]
        if prog == "rm":
            flags = [t for t in rest if t.startswith("-")]
            paths = [t for t in rest if not t.startswith("-")]
            if _rm_is_recursive_force(flags) and not _all_within_out(paths):
                return f"`rm` with recursive+force flags must stay inside out/: {segment!r}"
        elif prog == "git" and rest[:1] == ["clean"]:
            tail = rest[1:]
            flags = [t for t in tail if t.startswith("-")]
            paths = [t for t in tail if not t.startswith("-")]
            short = "".join(t.lstrip("-") for t in flags if not t.startswith("--"))
            force = "f" in short or "--force" in flags
            untracked_dirs = "d" in short or "x" in short or "-X" in flags
            if force and untracked_dirs and not _all_within_out(paths):
                return f"`git clean` with force+untracked-dirs must be scoped to out/: {segment!r}"
        elif prog == "chmod":
            flags = [t for t in rest if t.startswith("-")]
            nonflags = [t for t in rest if not t.startswith("-")]
            if any(f in ("-R", "--recursive") for f in flags) and nonflags:
                mode, paths = nonflags[0], nonflags[1:]
                if mode == "777" and not _all_within_out(paths):
                    return f"`chmod -R 777` outside out/ is blocked: {segment!r}"
    return None


def _host_of(netloc: str) -> str:
    return netloc.split("@")[-1].split(":")[0].lower()


def _extract_domains(text: str) -> list[str]:
    return [_host_of(m) for m in URL_RE.findall(text)]


def _allowed_domains(project: Path) -> list[str]:
    net = load_forge_toml(project).get("network") or {}
    return [str(d).lower() for d in (net.get("allowed_domains") or [])]


def _domain_allowed(domain: str, allowed: list[str]) -> bool:
    return any(domain == a or domain.endswith("." + a) for a in allowed)


def _check_network(project: Path, command: str) -> str | None:
    if not CURL_WGET_RE.search(command):
        return None
    domains = _extract_domains(command)
    if not domains:
        return None
    allowed = _allowed_domains(project)
    bad = [d for d in domains if not _domain_allowed(d, allowed)]
    if not bad:
        return None
    allow_desc = ", ".join(allowed) if allowed else "(none configured)"
    return (f"network egress to {', '.join(sorted(set(bad)))} is not in forge.toml "
            f"[network] allowed_domains {allow_desc}. Add the domain there or route through an "
            "already-allowed mirror.")


def _handle_bash(project: Path, tool_input: dict) -> dict | None:
    command = tool_input.get("command") or ""
    if not command.strip():
        return None
    for rx, why in _ALWAYS_DENY:
        if rx.search(command):
            return _deny(f"blocked destructive command ({why}): {command.strip()[:200]!r}")
    scoped = _check_scoped_destructive(command)
    if scoped:
        return _deny(scoped)
    net = _check_network(project, command)
    if net:
        return _deny(net)
    return None


def _handle_webfetch(project: Path, tool_input: dict) -> dict | None:
    url = tool_input.get("url") or ""
    m = URL_RE.search(url)
    if not m:
        return None
    domain = _host_of(m.group(1))
    allowed = _allowed_domains(project)
    if _domain_allowed(domain, allowed):
        return None
    allow_desc = ", ".join(allowed) if allowed else "(none configured)"
    return _deny(f"WebFetch to {domain} is not in forge.toml [network] allowed_domains {allow_desc}.")


def handle(data: dict) -> tuple[int, dict | None]:
    project = find_project_root(data.get("cwd"))
    if project is None:
        return 0, None  # not a Forge product repo: no-op fast (brief §3.4)

    tool_name = data.get("tool_name") or ""
    tool_input = data.get("tool_input") or {}
    agent_type = data.get("agent_type")

    if tool_name in WRITE_TOOLS:
        result = _handle_write_tool(project, tool_name, tool_input, agent_type)
        return 0, result
    if tool_name == "Bash":
        result = _handle_bash(project, tool_input)
        return 0, result
    if tool_name == "WebFetch":
        result = _handle_webfetch(project, tool_input)
        return 0, result
    return 0, None


if __name__ == "__main__":
    from _failclosed import run_hook
    run_hook(handle)
