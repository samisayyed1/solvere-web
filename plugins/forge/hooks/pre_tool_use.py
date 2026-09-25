#!/usr/bin/env python3
"""PreToolUse guardrails (CONTRACTS.md §8, ADR-001 §5, brief §3.4).

Matched on ``Write|Edit|MultiEdit|NotebookEdit|Bash|WebFetch`` in
``hooks/hooks.json``. Budget: <= 1 s (a PreToolUse timeout lets the call
proceed), so this does string work and at most a couple of file reads.
No-op (exit 0) when the project has no ``forge.toml``. Policy is anchored
on ``agent_type`` (CONTRACTS §13), never on tool-name prefixes.

**Paths** are resolved against the call's working directory, normalised
(``..``), symlink-resolved where they exist, then NFC-normalised and
case-folded before any comparison, because macOS APFS is case-insensitive
(review #1, M1).

**Write tools** (Write/Edit/MultiEdit/NotebookEdit, ``file_path`` or
``notebook_path``):
  1. Judges (``forge:verification-evaluator``, ``forge:red-team``) never write.
  2. Protected paths are never written: ``release/``, ``security/``,
     ``evidence/`` (append-only, only via ``forge``), ``out/verify/`` (check
     results are written by check scripts, not by hand), ``.forge/``,
     ``.git/``, ``.claude/`` except ``.claude/rules/``, ``hil/bench*.toml``.
  3. ``forge.toml``: ask on the main thread, deny for subagents (it defines
     what the evidence gate checks).
  4. ``cad/**`` only by ``forge:mechanical-engineer`` (main thread: ask).
  5. ``reviews/G*.md``: filling the blank "Human sign-off:" line is denied.
  6. ``params/params.toml``: changing a ``verified`` leaf is denied.

**Bash** is tokenised by a small shell scanner (quotes, escapes, newlines,
``;``/``&&``/``||``/``|``/``&``, ``$(..)``/backticks/process substitution,
heredocs, redirections), and every simple command -- including ``bash -c``,
``sh -c``, ``eval`` payloads, ``xargs``/``env``/``sudo``-style wrappers and
``find -exec`` -- is checked for: writes into the protected paths above
(redirects, ``tee``, ``sed -i``, ``perl -i``, ``cp``/``mv``/``ln``/
``install``/``rsync``/``truncate``/``touch``/``chmod``, ``curl -o``,
``find -fprint``, ``tar -C``, ``git checkout|restore|rm|mv`` pathspecs), any
shell write to ``params/params.toml`` or ``reviews/G*.md`` (only the
simulating Write/Edit guard or ``forge params set`` may change them),
destructive commands outside ``out/`` (``rm -r``, ``find -delete``,
``git clean``), force pushes (``-f``, ``--force*``, ``--mirror``,
``--delete``, ``+refspec``, ``:ref``, also under ``git -C <dir>``), history
rewrites (``filter-branch``, ``replace``, ``update-ref``, ``--orphan``,
``rebase --root``), ``git reset --hard``, ``dd``, ``mkfs``, device
redirects, shells fed from a pipe, ``eval`` of expanded text, raw-socket
tools, and network egress outside ``forge.toml [network] allowed_domains``
(also URLs inside interpreter one-liners). Interpreter one-liners that name
a protected path next to a write call are denied heuristically.

**Judges' Bash** (M2) is limited to a read-only allowlist (``cat``, ``grep``,
``ls``, ``git log|show|diff|status``, ``forge evidence list|status`` ...),
with no redirection, substitution, heredoc or environment prefix.

This is defence in depth. The sandbox in the product repo's
``.claude/settings.json`` is the primary control; what a determined shell
can still do is written up in ADR-001 §16 with the layer that catches it
(the Stop-time evidence and verified-param diff, CI, human review).
"""

from __future__ import annotations

import os
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (  # noqa: E402
    HookRuntimeError, find_project_root, load_forge_toml, glob_match, is_judge, is_mechanical_engineer, tomllib,
)

WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}

# (case-folded glob, why) -- never writable by any agent, through any tool.
PROTECTED = (
    ("release/**", "release/ is written only by the human-approved release flow"),
    ("security/**", "security/ holds pins and sandbox profiles"),
    ("evidence/**", "evidence/ is append-only and written only by the `forge` CLI"),
    ("out/verify/**", "out/verify/ holds check results, written only by check scripts"),
    (".forge/**", ".forge/ holds the gate's state (last-green, Stop counter)"),
    (".git/**", ".git/ internals decide what the gate diffs against"),
    ("hil/bench*.toml", "HIL bench configuration is human-owned (brief §3.4)"),
)
PROTECTED_DIRS = ("release", "security", "evidence", "out/verify", ".forge", ".git", ".claude")
CLAUDE_DIR_ALLOWED = (".claude/rules/**",)
SHELL_ONLY_FORBIDDEN = (
    ("params/params.toml", "change params with `forge params set` or the Edit tool (the verified-param "
                           "guard can only simulate those)"),
    ("reviews/g*.md", "edit gate records with Write/Edit so the human sign-off guard can check them"),
)

SIGNOFF_RE = re.compile(r"^Human sign-off:\s*(.*?)(?:\s{2,}Name:|\s*$)", re.MULTILINE)
URL_RE = re.compile(r"https?://([^/\s'\"`<>]+)", re.IGNORECASE)
ASSIGN_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
SAFE_DEVICES = {"/dev/null", "/dev/stdout", "/dev/stderr", "/dev/tty"}

SHELLS = {"sh", "bash", "zsh", "dash", "ksh", "mksh", "fish", "ash", "tcsh", "csh"}
INTERPRETERS = {"python", "python3", "forge-python", "perl", "ruby", "node", "nodejs", "deno", "bun",
                "php", "rscript", "lua", "tclsh", "osascript", "pwsh", "powershell"}
RAW_NET = {"nc", "ncat", "netcat", "socat", "telnet", "ftp", "tftp"}
REMOTE_COPY = {"ssh", "scp", "sftp", "rsync"}
KEYWORDS = {"if", "then", "else", "elif", "fi", "do", "done", "while", "until", "for", "in", "case", "esac",
            "{", "}", "(", ")", "!", "time", "coproc", "select", "function"}
WRAPPERS_NOARG = {"nohup", "command", "builtin", "exec", "stdbuf", "unbuffer", "caffeinate", "chronic",
                  "busybox", "toybox"}
# Write/exec-capable calls in interpreter one-liners (python, perl, ruby,
# node...). Plain reads such as open(p) or open(p, "r") do not match.
_PY_WRITE_HINTS = re.compile(
    r"open\s*\([^,)]*,\s*['\"][rbt]*[wax+]|\.open\s*\(\s*['\"][rbt]*[wax+]|\.write\s*\(|write_(text|bytes)|"
    r"os\.(remove|unlink|rename|replace|system|truncate|chmod|popen|exec\w*|spawn\w*|symlink|link)|shutil\.|"
    r"subprocess|\.unlink\s*\(|\.rename\s*\(|\.touch\s*\(|\.symlink_to\s*\(|\bunlink\b|\brename\b|"
    r"writeFile|appendFile|rmSync|unlinkSync|renameSync|File\.(write|open|delete)|IO\.write|FileUtils|"
    r"\bsystem\s*\(|\bexec\s*\(|['\"]\s*\+?>{1,2}|\bqx\b|`", re.IGNORECASE)

_ALWAYS_DENY_PROGS = {"mkfs": "mkfs destroys a filesystem", "dd": "dd can overwrite a raw device",
                      "shutdown": "shutdown/reboot are never allowed", "reboot": "shutdown/reboot are never allowed"}

MAX_DEPTH = 6


# ---------------------------------------------------------------------------
# decisions
# ---------------------------------------------------------------------------

def _deny(reason: str) -> dict:
    return {"hookSpecificOutput": {
        "hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": reason,
    }}


def _ask(reason: str) -> dict:
    return {"hookSpecificOutput": {
        "hookEventName": "PreToolUse", "permissionDecision": "ask", "permissionDecisionReason": reason,
    }}


class Verdict(Exception):
    """Raised inside the Bash analysis to short-circuit with a decision."""

    def __init__(self, kind: str, reason: str) -> None:
        super().__init__(reason)
        self.kind, self.reason = kind, reason


# ---------------------------------------------------------------------------
# path normalisation (M1)
# ---------------------------------------------------------------------------

def fold(rel: str) -> str:
    return unicodedata.normalize("NFC", rel).casefold()


OUTSIDE = "\0outside"


def rel_path(project: Path, raw: str, cwd: Path | None = None) -> str | None:
    """Project-relative, ``..``-normalised, symlink-resolved posix path of
    ``raw``, case-folded. ``OUTSIDE`` for a path outside the project, ``None``
    if it cannot be resolved (variables, ``~user``)."""
    if raw is None:
        return None
    raw = str(raw)
    if not raw or "$" in raw or "`" in raw:
        return None
    if raw.startswith("~"):
        raw = os.path.expanduser(raw)
        if raw.startswith("~"):
            return None
    base = cwd if cwd is not None else project
    p = Path(raw)
    if not p.is_absolute():
        p = base / p
    p = Path(os.path.normpath(str(p)))
    try:
        resolved = p.resolve()
    except (OSError, RuntimeError):
        resolved = p
    proj = project.resolve()
    for candidate in (resolved, p):
        try:
            rel = candidate.relative_to(proj).as_posix()
            return fold("" if rel == "." else rel)
        except ValueError:
            pass
        # case-insensitive filesystems: compare folded strings
        c, r = fold(candidate.as_posix()), fold(proj.as_posix())
        if c == r:
            return ""
        if c.startswith(r.rstrip("/") + "/"):
            return c[len(r.rstrip("/")) + 1:]
    return OUTSIDE


def _glob_prefix(rel: str) -> str:
    """For a target with glob characters, the literal directory prefix."""
    m = re.search(r"[*?\[]", rel)
    if not m:
        return rel
    return rel[: m.start()].rsplit("/", 1)[0] if "/" in rel[: m.start()] else ""


def protected_reason(rel: str) -> str | None:
    """Why the (folded) project-relative path is write-protected, or None."""
    if rel in (None, OUTSIDE):
        return None
    for pat, why in PROTECTED:
        if glob_match(pat, rel) or rel == pat.split("/**")[0]:
            return why
    if rel == ".claude" or rel.startswith(".claude/"):
        if not any(glob_match(p, rel) for p in CLAUDE_DIR_ALLOWED) and rel != ".claude/rules":
            return ".claude/ (settings, hooks, agents) configures the guardrails themselves"
    return None


def covers_protected(rel: str, *, deleting: bool = False) -> str | None:
    """Like :func:`protected_reason`, but also true when ``rel`` is a
    directory *containing* a protected path (``rm -r .``, ``git checkout .``).
    With ``deleting``, ``out/verify`` does not count: removing check results
    only makes the evidence gate fail closed."""
    if rel in (None, OUTSIDE):
        return None
    if deleting and _within_out(rel):
        return None
    why = protected_reason(rel)
    if why:
        return why
    prefix = _glob_prefix(rel)
    for d in PROTECTED_DIRS:
        if deleting and d == "out/verify":
            continue
        if prefix == "" or d == prefix or d.startswith(prefix.rstrip("/") + "/"):
            return f"it covers {d}/"
    return None


def _within_out(rel: str | None) -> bool:
    """Deleting under out/ (build outputs, including out/verify: a deleted
    check result only makes the gate fail closed) is allowed."""
    if rel in (None, OUTSIDE):
        return False
    return rel == "out" or rel.startswith("out/")


# ---------------------------------------------------------------------------
# Write/Edit content simulation (sign-off, verified params)
# ---------------------------------------------------------------------------

def _read_old_content(path: Path) -> str | None:
    try:
        return path.read_text() if path.is_file() else None
    except OSError:
        return None


def _compute_new_content(tool_name: str, tool_input: dict, old_content: str | None) -> str | None:
    """Best-effort post-edit content; ``None`` = could not simulate (callers
    fail closed where it matters)."""
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
    return None


def _is_blank_signoff(value: str) -> bool:
    return re.sub(r"[_\s]", "", value) == ""


def _signoff_filled(old_content: str | None, new_content: str | None) -> bool:
    if new_content is None:
        return False
    new_vals = SIGNOFF_RE.findall(new_content)
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
    if new_content is None:
        return ("params.toml could not be simulated for this edit (old_string not found in the "
                "current file); denied out of caution. Re-read the file, or use "
                "`forge params set <key> --value ... --source \"<citation>\"`.")
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
            ". Change them with `forge params set <key> --value <v> --source \"<citation>\" "
            "--justification \"<why>\"`, which demotes the param to measured and logs params/CHANGELOG.md.")


# ---------------------------------------------------------------------------
# shared path policy (Write tools and Bash write targets)
# ---------------------------------------------------------------------------

def _path_policy(rel: str | None, agent_type: str | None, via: str) -> dict | None:
    if rel in (None, OUTSIDE):
        return None
    why = protected_reason(rel)
    if why:
        return _deny(f"{rel} is protected ({why}); {via} may not write it.")
    if rel == "forge.toml":
        if agent_type:
            return _deny(f"forge.toml defines what the evidence gate checks; {agent_type} may not change it.")
        return _ask("forge.toml defines what the evidence gate checks. Confirm this change is intended.")
    if glob_match("cad/**", rel) or rel == "cad":
        if is_mechanical_engineer(agent_type):
            return None
        if not agent_type:
            return _ask(f"{rel} is under cad/**, normally authored only by forge:mechanical-engineer "
                        "(CONTRACTS.md §13). Confirm this main-thread edit is intended.")
        return _deny(f"{rel} is under cad/**; only forge:mechanical-engineer may write there "
                     f"(CONTRACTS.md §13), not {agent_type}.")
    return None


def _handle_write_tool(project: Path, cwd: Path, tool_name: str, tool_input: dict,
                       agent_type: str | None) -> dict | None:
    if is_judge(agent_type):
        return _deny(f"{agent_type} is a read-only reviewer (CONTRACTS.md §13, maker != checker); "
                     f"it must never use {tool_name}.")
    file_path = tool_input.get("file_path") or tool_input.get("notebook_path")
    if not file_path:
        return None
    rel = rel_path(project, file_path, cwd)
    if rel is None:
        return _deny(f"{tool_name}: cannot resolve {file_path!r} to check it against Forge's protected paths.")
    decision = _path_policy(rel, agent_type, tool_name)
    if decision:
        return decision
    if rel == OUTSIDE:
        return None
    full = Path(file_path) if Path(file_path).is_absolute() else cwd / file_path
    if glob_match("reviews/g*.md", rel):
        old_content = _read_old_content(full)
        new_content = _compute_new_content(tool_name, tool_input, old_content)
        if tool_name == "NotebookEdit" or _signoff_filled(old_content, new_content):
            return _deny(f"{rel}: the 'Human sign-off:' line may only be filled in by a human "
                         "(CONTRACTS.md §7). Leave it blank.")
    if rel == "params/params.toml":
        old_content = _read_old_content(full)
        new_content = _compute_new_content(tool_name, tool_input, old_content)
        violation = _verified_param_violation(old_content, new_content)
        if violation:
            return _deny(violation)
    return None


# ---------------------------------------------------------------------------
# shell scanner
# ---------------------------------------------------------------------------

class Cmd:
    __slots__ = ("words", "redirects", "heredocs", "piped")

    def __init__(self) -> None:
        self.words: list[str] = []
        self.redirects: list[tuple[str, str]] = []
        self.heredocs: list[str] = []
        self.piped = False


_OPS = ("&&", "||", ";;", "|&", ";", "|", "&", "(", ")")
_REDIRS = ("&>>", "&>", ">>", ">|", ">&", "<<<", "<<-", "<<", "<>", "<&", ">", "<")


def _match_paren(s: str, i: int) -> int:
    """Index just past the ``)`` matching the ``(`` at ``s[i]``."""
    depth, j, n = 0, i, len(s)
    while j < n:
        c = s[j]
        if c == "\\":
            j += 2
            continue
        if c == "'":
            k = s.find("'", j + 1)
            j = n if k < 0 else k + 1
            continue
        if c == '"':
            j += 1
            while j < n and s[j] != '"':
                j += 2 if s[j] == "\\" else 1
            j += 1
            continue
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return j + 1
        j += 1
    return n


def scan(src: str, subs: list[str]) -> list[Cmd]:
    """Split ``src`` into simple commands. Command/process substitutions are
    appended to ``subs`` (analysed separately) and leave a placeholder."""
    cmds: list[Cmd] = []
    cur = Cmd()
    word: list[str] = []
    in_word = False
    pending_redir: str | None = None
    pending_heredocs: list[tuple[str, bool, Cmd]] = []
    next_piped = False
    i, n = 0, len(src)

    def end_word() -> None:
        nonlocal word, in_word, pending_redir
        if not in_word:
            return
        text = "".join(word)
        word, in_word = [], False
        if pending_redir is not None:
            op, pending_redir = pending_redir, None
            if op in ("<<", "<<-"):
                delim = text.replace('"', "").replace("'", "")
                pending_heredocs.append((delim, op == "<<-", cur))
            else:
                cur.redirects.append((op, text))
        else:
            cur.words.append(text)

    def end_cmd(piped_next: bool = False) -> None:
        nonlocal cur, next_piped
        end_word()
        if cur.words or cur.redirects or cur.heredocs:
            cmds.append(cur)
        cur = Cmd()
        cur.piped = piped_next
        next_piped = piped_next

    while i < n:
        c = src[i]
        if c == "\\":
            if i + 1 < n and src[i + 1] == "\n":
                i += 2
                continue
            word.append(src[i + 1] if i + 1 < n else "")
            in_word = True
            i += 2
            continue
        if c == "'":
            k = src.find("'", i + 1)
            k = n if k < 0 else k
            word.append(src[i + 1:k])
            in_word = True
            i = k + 1
            continue
        if c == '"':
            j = i + 1
            buf: list[str] = []
            while j < n and src[j] != '"':
                if src[j] == "\\" and j + 1 < n:
                    buf.append(src[j + 1])
                    j += 2
                    continue
                if src[j] == "$" and j + 1 < n and src[j + 1] == "(":
                    k = _match_paren(src, j + 1)
                    subs.append(src[j + 2:k - 1])
                    buf.append("$(...)")
                    j = k
                    continue
                if src[j] == "`":
                    k = src.find("`", j + 1)
                    k = n if k < 0 else k
                    subs.append(src[j + 1:k])
                    buf.append("$(...)")
                    j = k + 1
                    continue
                buf.append(src[j])
                j += 1
            word.append("".join(buf))
            in_word = True
            i = j + 1
            continue
        if c == "$" and i + 1 < n and src[i + 1] == "(":
            k = _match_paren(src, i + 1)
            subs.append(src[i + 2:k - 1].lstrip("("))
            word.append("$(...)")
            in_word = True
            i = k
            continue
        if c == "`":
            k = src.find("`", i + 1)
            k = n if k < 0 else k
            subs.append(src[i + 1:k])
            word.append("$(...)")
            in_word = True
            i = k + 1
            continue
        if c in "<>" and i + 1 < n and src[i + 1] == "(":
            k = _match_paren(src, i + 1)
            subs.append(src[i + 2:k - 1])
            word.append("$(...)")
            in_word = True
            i = k
            continue
        if c == "\n":
            end_cmd()
            if pending_heredocs:
                j = i + 1
                for delim, strip_tabs, owner in pending_heredocs:
                    body: list[str] = []
                    while j < n:
                        k = src.find("\n", j)
                        line = src[j:] if k < 0 else src[j:k]
                        j = n if k < 0 else k + 1
                        if (line.lstrip("\t") if strip_tabs else line) == delim:
                            break
                        body.append(line)
                    owner.heredocs.append("\n".join(body))
                pending_heredocs.clear()
                i = j
                continue
            i += 1
            continue
        if c in " \t":
            end_word()
            i += 1
            continue
        if c == "#" and not in_word:
            k = src.find("\n", i)
            i = n if k < 0 else k
            continue
        redir = next((r for r in _REDIRS if src.startswith(r, i)), None)
        if redir:
            if in_word and "".join(word).isdigit():
                word, in_word = [], False  # fd number, e.g. 2>
            else:
                end_word()
            if redir in (">&", "<&"):
                j = i + 2
                while j < n and src[j] in " \t":
                    j += 1
                m = re.match(r"[0-9]+-?|-", src[j:])
                if m:  # fd duplication (2>&1, >&-): not a file
                    i = j + m.end()
                    continue
                redir = ">" if redir == ">&" else "<"
                pending_redir = redir
                i = j
                continue
            pending_redir = redir
            i += len(redir)
            continue
        op = next((o for o in _OPS if src.startswith(o, i)), None)
        if op:
            if op in ("(", ")") and in_word:
                word.append(c)
                i += 1
                continue
            end_cmd(piped_next=op in ("|", "|&"))
            i += len(op)
            continue
        word.append(c)
        in_word = True
        i += 1
    end_cmd()
    if pending_heredocs:  # unterminated heredoc: body is the rest (already consumed as commands)
        for _, _, owner in pending_heredocs:
            owner.heredocs.append("")
    return cmds


# ---------------------------------------------------------------------------
# Bash analysis
# ---------------------------------------------------------------------------

class Ctx:
    def __init__(self, project: Path, cwd: Path, agent_type: str | None, allowed_domains: list[str]) -> None:
        self.project = project
        self.cwd: Path | None = cwd
        self.agent_type = agent_type
        self.allowed = allowed_domains
        self.asks: list[str] = []

    def rel(self, raw: str, cwd: Path | None | str = "cur") -> str | None:
        base = self.cwd if cwd == "cur" else cwd
        if base is None and not str(raw).startswith(("/", "~")):
            return None
        return rel_path(self.project, raw, base)


def _host_of(netloc: str) -> str:
    return netloc.split("@")[-1].split(":")[0].strip("[]").lower()


def _domain_allowed(domain: str, allowed: list[str]) -> bool:
    return any(domain == a or domain.endswith("." + a) for a in allowed)


def _check_urls(ctx: Ctx, text: str, what: str) -> None:
    bad = sorted({_host_of(h) for h in URL_RE.findall(text)} - {""})
    bad = [d for d in bad if not _domain_allowed(d, ctx.allowed)]
    if bad:
        allow_desc = ", ".join(ctx.allowed) if ctx.allowed else "(none configured)"
        raise Verdict("deny", f"network egress to {', '.join(bad)} ({what}) is not in forge.toml [network] "
                              f"allowed_domains {allow_desc}. Add the domain there or use an allowed mirror.")


def _write_target(ctx: Ctx, raw: str, how: str) -> None:
    if raw == "<stdin-args>":
        raise Verdict("deny", f"{how} on paths read from a pipe (xargs) cannot be checked")
    if raw in SAFE_DEVICES or raw.startswith("/dev/fd/"):
        return
    if raw.startswith("/dev/"):
        raise Verdict("deny", f"redirecting output to a device file ({raw}) is never allowed")
    rel = ctx.rel(raw)
    if rel is None:
        low = fold(raw)
        for d in PROTECTED_DIRS + ("params/params.toml", "forge.toml"):
            if d in low:
                raise Verdict("deny", f"{how} writes to {raw!r}, which cannot be resolved but names {d}")
        if ctx.cwd is None:
            raise Verdict("deny", f"{how} writes to {raw!r} after a `cd` whose target cannot be resolved")
        return
    rel = _glob_prefix(rel) if re.search(r"[*?\[]", rel) else rel
    if rel == OUTSIDE:
        return
    decision = _path_policy(rel, ctx.agent_type, f"Bash ({how})")
    if decision:
        hso = decision["hookSpecificOutput"]
        if hso["permissionDecision"] == "ask":
            ctx.asks.append(hso["permissionDecisionReason"])
            return
        raise Verdict("deny", hso["permissionDecisionReason"])
    for pat, why in SHELL_ONLY_FORBIDDEN:
        if glob_match(pat, rel):
            raise Verdict("deny", f"shell writes to {rel} are blocked: {why}.")


def _destructive_target(ctx: Ctx, raw: str, how: str) -> None:
    """A recursive delete (or similar) of ``raw``: it must stay inside out/."""
    rel = ctx.rel(raw)
    if rel is not None and rel != OUTSIDE:
        why = covers_protected(rel, deleting=True)
        if why:
            raise Verdict("deny", f"{how} of {raw!r} would destroy protected data ({why})")
    if not _within_out(rel):
        raise Verdict("deny", f"{how} must stay inside out/ (got {raw!r})")


def _split_flags(args: list[str]) -> tuple[list[str], list[str]]:
    flags, pos, end = [], [], False
    for a in args:
        if not end and a == "--":
            end = True
            continue
        if not end and a.startswith("-") and a != "-":
            flags.append(a)
        else:
            pos.append(a)
    return flags, pos


def _short_has(flags: list[str], letters: str) -> bool:
    return any(not f.startswith("--") and any(ch in f[1:] for ch in letters) for f in flags)


def _strip_prefix(words: list[str]) -> tuple[list[str], bool]:
    """Drop keywords, env assignments and wrapper commands. Returns the
    remaining words and whether an env-assignment prefix was present."""
    had_env = False
    w = list(words)
    changed = True
    while w and changed:
        changed = False
        while w and (w[0] in KEYWORDS or w[0].startswith("{") and w[0] == "{"):
            w.pop(0)
            changed = True
        while w and ASSIGN_RE.match(w[0]):
            w.pop(0)
            had_env = changed = True
        if not w:
            break
        prog = os.path.basename(w[0])
        if prog in WRAPPERS_NOARG:
            w.pop(0)
            while w and w[0].startswith("-"):
                w.pop(0)
            changed = True
        elif prog in ("sudo", "doas"):
            w.pop(0)
            while w and w[0].startswith("-"):
                opt = w.pop(0)
                if opt in ("-u", "-g", "-C", "-D", "-h", "-p", "-r", "-t", "-U"):
                    w and w.pop(0)
            changed = True
        elif prog == "env":
            w.pop(0)
            while w and (w[0].startswith("-") or ASSIGN_RE.match(w[0])):
                opt = w.pop(0)
                if opt in ("-u", "-C", "-S", "--unset", "--chdir", "--split-string"):
                    w and w.pop(0)
                had_env = True
            changed = True
        elif prog in ("nice", "ionice", "timeout", "time", "watch", "flock", "chroot", "taskset", "setsid"):
            w.pop(0)
            while w and w[0].startswith("-"):
                opt = w.pop(0)
                if opt in ("-n", "-c", "-k", "-s", "--signal", "--kill-after", "-p"):
                    w and w.pop(0)
            if prog in ("timeout", "flock", "chroot", "taskset") and w:
                w.pop(0)  # duration / lock file / root / mask
            changed = True
    return w, had_env


def _analyse(ctx: Ctx, src: str, depth: int = 0) -> None:
    if depth > MAX_DEPTH:
        raise Verdict("deny", "shell command nests too deeply to be checked")
    subs: list[str] = []
    cmds = scan(src, subs)
    for sub in subs:
        saved = ctx.cwd
        _analyse(ctx, sub, depth + 1)
        ctx.cwd = saved
    for cmd in cmds:
        _analyse_cmd(ctx, cmd, depth)


def _analyse_cmd(ctx: Ctx, cmd: Cmd, depth: int) -> None:
    for op, target in cmd.redirects:
        if op in (">", ">>", ">|", "&>", "&>>", "<>"):
            _write_target(ctx, target, f"redirect `{op}`")
    words, _ = _strip_prefix(cmd.words)
    if not words:
        return
    prog = os.path.basename(words[0])
    if prog.endswith(".exe"):
        prog = prog[:-4]
    args = words[1:]
    prog_l = prog.lower()
    prog_base = re.sub(r"[0-9.]+$", "", prog_l)

    if prog_l in _ALWAYS_DENY_PROGS or prog_l.startswith("mkfs"):
        raise Verdict("deny", f"blocked destructive command: {_ALWAYS_DENY_PROGS.get(prog_l, 'mkfs destroys a filesystem')}")

    if prog_l in ("cd", "pushd", "popd"):
        if prog_l == "popd":
            ctx.cwd = None  # the directory stack is not tracked
            return
        if not args:
            ctx.cwd = Path.home()
            return
        target = args[-1] if args[-1] != "--" else None
        if target is None or target == "-" or "$" in target:
            ctx.cwd = None
            return
        base = ctx.cwd
        if base is None and not target.startswith(("/", "~")):
            return
        t = os.path.expanduser(target)
        ctx.cwd = Path(os.path.normpath(str((base or ctx.project) / t))) if not os.path.isabs(t) else Path(os.path.normpath(t))
        return

    if prog_l in SHELLS:
        _analyse_shell(ctx, cmd, args, depth)
        return
    if prog_l in ("eval",):
        text = " ".join(args)
        if "$" in text or "`" in text:
            raise Verdict("deny", "`eval` of expanded text cannot be checked; run the command directly")
        _analyse(ctx, text, depth + 1)
        return
    if prog_l in ("source", "."):
        return  # reading a script file: residual risk (ADR-001 §16)
    if prog_l == "xargs":
        rest = list(args)
        while rest and rest[0].startswith("-"):
            opt = rest.pop(0)
            if opt in ("-I", "-L", "-n", "-P", "-d", "-E", "-s", "-a") and rest:
                rest.pop(0)
        if rest:
            inner = Cmd()
            inner.words = rest + ["<stdin-args>"]
            _analyse_cmd(ctx, inner, depth + 1)
        return

    if prog_l in ("rm", "unlink", "shred", "rmdir", "srm", "trash"):
        flags, pos = _split_flags(args)
        recursive = _short_has(flags, "rR") or "--recursive" in flags
        for p in pos:
            if p == "<stdin-args>":
                if recursive:
                    raise Verdict("deny", "`rm -r` over arguments from a pipe cannot be checked")
                continue
            rel = ctx.rel(p)
            if rel is None and ctx.cwd is None:
                raise Verdict("deny", f"`{prog}` of {p!r} after an unresolvable `cd`")
            why = (covers_protected(rel, deleting=True) if recursive
                   else (None if _within_out(rel) else protected_reason(rel or "")))
            if why:
                raise Verdict("deny", f"`{prog}` of {p!r} would destroy protected data ({why})")
            if recursive:
                _destructive_target(ctx, p, f"`{prog} -r`")
        return

    if prog_l == "find":
        _analyse_find(ctx, args, depth)
        return

    if prog_l in ("sed", "gsed", "perl", "ruby") and any(
            a in ("-i", "--in-place") or a.startswith("--in-place=")
            or (re.match(r"^-[A-Za-z]*i", a) and not a.startswith("--")) for a in args):
        _, pos = _split_flags(args)
        for p in pos:
            _write_target(ctx, p, f"`{prog} -i`")
        if prog_l in ("perl", "ruby"):
            _interpreter(ctx, prog_l, args, cmd)
        return

    if prog_l == "tee":
        for p in _split_flags(args)[1]:
            _write_target(ctx, p, "`tee`")
        return

    if prog_l in ("cp", "install", "rsync", "ln", "mv", "truncate", "touch", "chmod", "chown", "chgrp",
                  "setfacl", "chattr", "mkdir", "mkfifo", "split", "csplit", "patch", "ditto"):
        _analyse_fileop(ctx, prog_l, args)
        if prog_l == "rsync":
            _remote(ctx, prog_l, args)
        return

    if prog_l in ("tar", "bsdtar", "gtar", "unzip", "7z", "cpio"):
        _analyse_archive(ctx, prog_l, args)
        return

    if prog_l == "git":
        _analyse_git(ctx, args)
        return

    if prog_l in ("curl", "wget", "aria2c", "http", "https", "xh"):
        _check_urls(ctx, " ".join(args), prog)
        flags = args
        for k, a in enumerate(flags):
            if a in ("-o", "--output", "-O", "--output-document", "-D", "--dump-header", "-c", "--cookie-jar") \
                    and k + 1 < len(flags) and not (prog_l == "curl" and a == "-O"):
                _write_target(ctx, flags[k + 1], f"`{prog} {a}`")
            elif a.startswith(("--output=", "--output-document=")):
                _write_target(ctx, a.split("=", 1)[1], f"`{prog}`")
        return

    if prog_l in RAW_NET:
        raise Verdict("deny", f"`{prog}` opens raw network connections; not allowed (use an allowlisted https fetch)")
    if prog_l in REMOTE_COPY:
        _remote(ctx, prog_l, args)
        return

    if prog_l in INTERPRETERS or prog_base in INTERPRETERS:
        _interpreter(ctx, prog_base if prog_base in INTERPRETERS else prog_l, args, cmd)
        return


def _analyse_shell(ctx: Ctx, cmd: Cmd, args: list[str], depth: int) -> None:
    k = 0
    payload = None
    script = None
    while k < len(args):
        a = args[k]
        if a == "-c" or (a.startswith("-") and not a.startswith("--") and "c" in a[1:]):
            payload = args[k + 1] if k + 1 < len(args) else ""
            break
        if a in ("-o", "+o", "-O", "+O", "--rcfile", "--init-file"):
            k += 2
            continue
        if a.startswith(("-", "+")):
            k += 1
            continue
        script = a
        break
    if payload is not None:
        saved = ctx.cwd
        _analyse(ctx, payload, depth + 1)
        ctx.cwd = saved
        return
    if script is not None:
        return  # running a script file: residual risk (ADR-001 §16)
    if cmd.heredocs:
        for body in cmd.heredocs:
            _analyse(ctx, body, depth + 1)
        return
    if cmd.piped or any(op in ("<", "<<<") for op, _ in cmd.redirects):
        for op, t in cmd.redirects:
            if op == "<<<":
                _analyse(ctx, t, depth + 1)
                return
        raise Verdict("deny", "feeding a shell from a pipe or file hides the command from the guardrails; "
                              "run the command directly")


def _analyse_find(ctx: Ctx, args: list[str], depth: int) -> None:
    starts: list[str] = []
    k = 0
    while k < len(args) and args[k] in ("-H", "-L", "-P", "-O0", "-O1", "-O2", "-O3", "-D"):
        k += 2 if args[k] == "-D" else 1
    while k < len(args) and not (args[k].startswith("-") or args[k] in ("(", "!", ")", ",")):
        starts.append(args[k])
        k += 1
    if not starts:
        starts = ["."]
    expr = args[k:]
    destructive = "-delete" in expr
    j = 0
    while j < len(expr):
        a = expr[j]
        if a in ("-fprint", "-fprint0", "-fprintf", "-fls") and j + 1 < len(expr):
            _write_target(ctx, expr[j + 1], f"`find {a}`")
        if a in ("-exec", "-execdir", "-ok", "-okdir"):
            end = j + 1
            while end < len(expr) and expr[end] not in (";", "+", "\\;"):
                end += 1
            inner_words = expr[j + 1:end]
            j = end
            if inner_words:
                inner_prog = os.path.basename(inner_words[0]).lower()
                if inner_prog in ("rm", "unlink", "shred", "rmdir", "mv", "truncate", "srm", "trash"):
                    destructive = True
                for s in starts:
                    inner = Cmd()
                    inner.words = [w if w != "{}" else s for w in inner_words]
                    _analyse_cmd(ctx, inner, depth + 1)
        j += 1
    if destructive:
        for s in starts:
            _destructive_target(ctx, s, "`find -delete/-exec rm`")


def _analyse_fileop(ctx: Ctx, prog: str, args: list[str]) -> None:
    flags, pos = _split_flags(args)
    target_dir = None
    for k, a in enumerate(args):
        if a in ("-t", "--target-directory") and k + 1 < len(args):
            target_dir = args[k + 1]
        elif a.startswith("--target-directory="):
            target_dir = a.split("=", 1)[1]
    if target_dir and target_dir in pos:
        pos.remove(target_dir)
    if prog in ("chmod", "chown", "chgrp", "setfacl", "chattr") and pos:
        mode, targets = pos[0], pos[1:]
        recursive = _short_has(flags, "R") or "--recursive" in flags
        for t in targets:
            _write_target(ctx, t, f"`{prog}`")
            if recursive and prog == "chmod" and mode in ("777", "a+rwx", "ugo+rwx", "0777"):
                if not _within_out(ctx.rel(t)):
                    raise Verdict("deny", f"`chmod -R {mode}` outside out/ is blocked")
        return
    if prog in ("mv", "ln", "patch"):
        targets = pos + ([target_dir] if target_dir else [])
    elif prog in ("truncate", "touch", "mkdir", "mkfifo", "split", "csplit"):
        targets = pos
        if prog == "truncate":
            targets = [p for p in pos]
    else:  # cp, install, rsync, ditto
        targets = [target_dir] if target_dir else (pos[-1:] if len(pos) >= 2 else [])
    for t in targets:
        if prog in ("rsync",) and re.match(r"^[^/]*:", t):
            continue
        _write_target(ctx, t, f"`{prog}`")
        if prog == "mv":
            rel = ctx.rel(t)
            why = covers_protected(rel) if rel not in (None, OUTSIDE) else None
            if why:
                raise Verdict("deny", f"`mv` of {t!r} would move protected data ({why})")


def _analyse_archive(ctx: Ctx, prog: str, args: list[str]) -> None:
    for k, a in enumerate(args):
        if a in ("-C", "--directory", "-d") and k + 1 < len(args):
            _write_target(ctx, args[k + 1], f"`{prog}` extraction")
        elif a.startswith("--directory="):
            _write_target(ctx, a.split("=", 1)[1], f"`{prog}` extraction")
        elif prog in ("tar", "bsdtar", "gtar") and a in ("-f", "--file") and k + 1 < len(args):
            if any(("c" in x.lstrip("-") and not x.startswith("--")) or x == "--create" for x in args[:k + 1]):
                _write_target(ctx, args[k + 1], f"`{prog} -c`")


def _remote(ctx: Ctx, prog: str, args: list[str]) -> None:
    hosts = []
    _, pos = _split_flags(args)
    if prog == "ssh":
        hosts = pos[:1]
    else:
        hosts = [p.split(":", 1)[0] for p in pos if re.match(r"^[^/]+:", p) and not p.startswith("/")]
    for h in hosts:
        host = _host_of(h)
        if host and not _domain_allowed(host, ctx.allowed):
            allow_desc = ", ".join(ctx.allowed) if ctx.allowed else "(none configured)"
            raise Verdict("deny", f"`{prog}` to {host} is not in forge.toml [network] allowed_domains {allow_desc}")


def _interpreter(ctx: Ctx, prog: str, args: list[str], cmd: Cmd) -> None:
    code_parts: list[str] = []
    for k, a in enumerate(args):
        if a in ("-c", "-e", "-E", "--eval", "-p", "--print", "-r", "--command") and k + 1 < len(args):
            code_parts.append(args[k + 1])
        elif re.match(r"^-[A-Za-z]*[ceE]$", a) and k + 1 < len(args):
            code_parts.append(args[k + 1])
    code_parts.extend(cmd.heredocs)
    code_parts.extend(t for op, t in cmd.redirects if op == "<<<")
    if not code_parts:
        return  # a script file: residual risk (ADR-001 §16)
    code = "\n".join(code_parts)
    _check_urls(ctx, code, f"inline {prog} code")
    low = fold(code)
    if _PY_WRITE_HINTS.search(code):
        for d in PROTECTED_DIRS + ("params/params.toml", "params.toml", "manifest.json", "state.json"):
            if fold(d) in low:
                raise Verdict("deny", f"inline {prog} code writes near {d}; protected files may not be changed "
                                      "from a one-liner (use the `forge` CLI or the Write/Edit tools)")


_GIT_REWRITE = {"filter-branch", "filter-repo", "replace", "update-ref"}


def _analyse_git(ctx: Ctx, args: list[str]) -> None:
    k = 0
    git_cwd: Path | None | str = "cur"
    while k < len(args) and args[k].startswith("-"):
        a = args[k]
        if a == "-C" and k + 1 < len(args):
            d = args[k + 1]
            base = ctx.cwd
            if "$" in d or (base is None and not d.startswith("/")):
                git_cwd = None
            else:
                git_cwd = Path(os.path.normpath(str((base or ctx.project) / os.path.expanduser(d))))
            k += 2
            continue
        if a in ("-c", "--git-dir", "--work-tree", "--namespace", "--exec-path", "--config-env") and k + 1 < len(args):
            k += 2
            continue
        k += 1
    if k >= len(args):
        return
    sub, rest = args[k], args[k + 1:]
    saved = ctx.cwd
    if git_cwd != "cur":
        ctx.cwd = git_cwd  # type: ignore[assignment]
    try:
        _analyse_git_sub(ctx, sub, rest)
    finally:
        ctx.cwd = saved


def _analyse_git_sub(ctx: Ctx, sub: str, rest: list[str]) -> None:
    flags, pos = _split_flags(rest)
    if sub == "push":
        force = (_short_has(flags, "fd") or any(
            f in ("--force", "--mirror", "--delete", "--prune") or f.startswith(("--force", "--mirror"))
            for f in flags))
        refspecs = pos[1:] if pos else []
        if force or any(r.startswith("+") or r.startswith(":") or ":+" in r for r in refspecs):
            raise Verdict("deny", "blocked destructive command (force-push, +refspec or remote delete is never allowed)")
        return
    if sub == "reset" and "--hard" in flags:
        raise Verdict("deny", "blocked destructive command (git reset --hard discards uncommitted work)")
    if sub in _GIT_REWRITE or (sub in ("checkout", "switch") and "--orphan" in flags) \
            or (sub == "rebase" and "--root" in flags):
        raise Verdict("deny", f"`git {sub}` rewrites the history the evidence gate diffs against")
    if sub == "clean":
        force = _short_has(flags, "f") or "--force" in flags
        if force and not (_short_has(flags, "n") or "--dry-run" in flags):
            if not pos:
                raise Verdict("deny", "`git clean -f` must be scoped to out/")
            for p in pos:
                _destructive_target(ctx, p, "`git clean -f`")
        return
    if sub in ("checkout", "restore", "rm", "mv"):
        if "--" in rest:
            paths = [a for a in rest[rest.index("--") + 1:]]
        elif sub == "checkout" and pos and not os.path.exists(str((ctx.cwd or ctx.project) / pos[0])):
            paths = pos[1:]  # the first word is a branch or commit
        else:
            paths = pos
        for p in paths:
            rel = ctx.rel(p)
            if rel in (None, OUTSIDE):
                continue
            why = covers_protected(rel, deleting=False)
            if why and not (sub == "restore" and ("--staged" in flags or "-S" in flags)
                            and not ("--worktree" in flags or "-W" in flags)):
                raise Verdict("deny", f"`git {sub} {p}` would overwrite or remove protected data ({why})")
            if sub in ("rm", "mv"):
                _write_target(ctx, p, f"`git {sub}`")
        return
    if sub in ("apply", "am") and pos:
        return


# ---------------------------------------------------------------------------
# judges' read-only Bash allowlist (M2)
# ---------------------------------------------------------------------------

JUDGE_READONLY = {
    "cat", "head", "tail", "ls", "grep", "egrep", "fgrep", "rg", "wc", "sort", "uniq", "cut", "tr", "nl",
    "diff", "cmp", "comm", "stat", "file", "du", "df", "pwd", "echo", "printf", "true", "false", "test", "[",
    "basename", "dirname", "realpath", "readlink", "jq", "sha256sum", "shasum", "md5sum", "which", "tree",
    "column", "fold", "od", "hexdump", "xxd", "strings", "date", "find", "git", "forge",
}
JUDGE_GIT = {"log", "show", "diff", "status", "rev-parse", "ls-files", "ls-tree", "blame", "describe",
             "grep", "cat-file", "shortlog", "rev-list", "merge-base", "name-rev", "whatchanged"}
JUDGE_FORGE = {("evidence", "list"), ("evidence", "status"), ("params", "get"), ("params", "lint"),
               ("state", "show"), ("lint", None), ("passk", None)}


def _judge_bash(command: str, agent_type: str) -> str | None:
    """Reason to deny, or None when every command is on the read-only list."""
    subs: list[str] = []
    cmds = scan(command, subs)
    if subs:
        return "command substitution is not allowed for read-only reviewers"
    for cmd in cmds:
        if cmd.heredocs:
            return "heredocs are not allowed for read-only reviewers"
        for op, target in cmd.redirects:
            if op == "<" or (target == "/dev/null" and op in (">", ">>", "&>")):
                continue
            return f"redirection `{op} {target}` is not allowed for read-only reviewers"
        words = cmd.words
        if not words:
            continue
        if ASSIGN_RE.match(words[0]):
            return "environment-variable prefixes are not allowed for read-only reviewers"
        prog = os.path.basename(words[0])
        args = words[1:]
        if prog not in JUDGE_READONLY:
            return f"`{prog}` is not on the read-only reviewer allowlist"
        if prog == "find" and any(a in ("-delete", "-exec", "-execdir", "-ok", "-okdir", "-fprint", "-fprint0",
                                        "-fprintf", "-fls") for a in args):
            return "find actions that run or write are not allowed for read-only reviewers"
        if prog in ("sort", "tree") and any(a == "-o" or a.startswith(("--output", "-o")) for a in args):
            return f"`{prog} -o` writes a file"
        if prog in ("uniq", "xxd") and len(_split_flags(args)[1]) > 1:
            return f"`{prog}` with an output file writes a file"
        if prog == "rg" and any(a.startswith("--pre") for a in args):
            return "`rg --pre` runs a program"
        if prog == "date" and any(a in ("-s", "--set") or a.startswith("--set") for a in args):
            return "`date --set` changes the clock"
        if prog == "git":
            if not args or args[0].startswith("-") and args[0] not in ("--no-pager",):
                return "git global options are not allowed for read-only reviewers"
            a = [x for x in args if x != "--no-pager"]
            if not a or a[0] not in JUDGE_GIT:
                return f"`git {a[0] if a else ''}` is not a read-only git command"
            if any(x.startswith(("--output", "--ext-diff", "--textconv", "-o")) for x in a[1:]):
                return "git options that write files or run programs are not allowed"
        if prog == "forge":
            sub = args[0] if args else ""
            sub2 = args[1] if len(args) > 1 else None
            if (sub, sub2) not in JUDGE_FORGE and (sub, None) not in JUDGE_FORGE:
                return f"`forge {sub} {sub2 or ''}` is not a read-only forge command"
    return None


# ---------------------------------------------------------------------------

def _allowed_domains(toml: dict) -> list[str]:
    net = toml.get("network") or {}
    return [str(d).lower() for d in (net.get("allowed_domains") or [])]


def _handle_bash(project: Path, cwd: Path, tool_input: dict, agent_type: str | None, toml: dict) -> dict | None:
    command = tool_input.get("command") or ""
    if not command.strip():
        return None
    if is_judge(agent_type):
        why = _judge_bash(command, agent_type or "")
        if why:
            return _deny(f"{agent_type} is a read-only reviewer: {why}. Allowed: read-only inspection "
                         "(cat, grep, ls, find without actions, git log/show/diff/status, "
                         "forge evidence list|status, forge params get|lint, forge lint).")
    ctx = Ctx(project, cwd, agent_type, _allowed_domains(toml))
    try:
        _analyse(ctx, command)
    except Verdict as v:
        return _deny(f"{v.reason}: {command.strip()[:200]!r}")
    if ctx.asks:
        return _ask("; ".join(ctx.asks))
    return None


def _handle_webfetch(tool_input: dict, toml: dict) -> dict | None:
    url = tool_input.get("url") or ""
    m = URL_RE.search(url)
    if not m:
        return None
    domain = _host_of(m.group(1))
    allowed = _allowed_domains(toml)
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
    try:
        cwd = Path(data.get("cwd")).resolve()
    except (OSError, TypeError):
        cwd = project

    try:
        toml = load_forge_toml(project)
    except HookRuntimeError as exc:
        target = str(tool_input.get("file_path") or "")
        if tool_name in ("Write", "Edit", "MultiEdit") and rel_path(project, target, cwd) == "forge.toml" \
                and not agent_type:
            return 0, _ask(f"{exc}. Confirm this fix to forge.toml.")
        return 0, _deny(f"{exc}; Forge guardrails are closed until forge.toml parses again.")

    if tool_name in WRITE_TOOLS:
        return 0, _handle_write_tool(project, cwd, tool_name, tool_input, agent_type)
    if tool_name == "Bash":
        return 0, _handle_bash(project, cwd, tool_input, agent_type, toml)
    if tool_name == "WebFetch":
        return 0, _handle_webfetch(tool_input, toml)
    return 0, None


if __name__ == "__main__":
    from _failclosed import run_hook
    run_hook(handle)
