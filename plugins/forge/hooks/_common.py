"""Shared helpers for Forge hook scripts. Imported only by ``hooks/*.py``.

Standard library only (CONTRACTS.md §8, §10). This module also wires
``plugins/forge/lib`` onto ``sys.path`` so hooks can import the pure-stdlib
``forge.*`` core libraries (``forge.evidence``, ``forge.checkresult``,
``forge.state``, ``forge.minischema``) instead of duplicating that logic.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

HOOKS_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = HOOKS_DIR.parent
FORGE_REPO_ROOT = PLUGIN_ROOT.parent.parent  # plugins/forge -> plugins -> repo_root (mirrors cli.py)
LIB_DIR = PLUGIN_ROOT / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

MIN_PYTHON = (3, 11)


class HookRuntimeError(RuntimeError):
    """The hook cannot enforce its policy on this interpreter (fail closed)."""


def _require_tomllib():
    """Forge hooks need ``tomllib`` (Python >= 3.11) to read ``forge.toml``
    and ``params/params.toml``. Without it every guard that parses TOML would
    silently turn into a no-op (review #1, C3), so the hook fails CLOSED:
    under the ``_failclosed`` wrapper this exception becomes exit 2; when a
    hook script is run directly, the ``SystemExit(2)`` below does the same."""
    try:
        import tomllib as _tomllib  # noqa: PLC0415
        return _tomllib
    except ImportError:
        msg = (f"forge hook error: Python {sys.version.split()[0]} at {sys.executable} has no tomllib "
               f"(needs >= {MIN_PYTHON[0]}.{MIN_PYTHON[1]}); Forge guardrails cannot run, so this tool call "
               "is blocked. Put a Python >= 3.11 first on PATH as `python3` (or install the Forge "
               "toolchain: plugins/forge/toolchain/install.sh) and restart Claude Code.")
        if os.environ.get("FORGE_HOOK_WRAPPED"):
            raise HookRuntimeError(msg) from None
        print(msg, file=sys.stderr)
        raise SystemExit(2) from None


tomllib = _require_tomllib()


from forge.evidence import glob_match as _evidence_glob_match  # noqa: E402


# ---------------------------------------------------------------------------
# Project / forge.toml discovery
# ---------------------------------------------------------------------------

def find_project_root(cwd: str | Path | None) -> Path | None:
    """Walk up from ``cwd`` looking for ``forge.toml``.

    Returns ``None`` when this isn't a Forge product repo at all, which is
    the standard "no-op fast" signal every hook (other than SessionStart's
    one-line hint) uses to exit 0 immediately (brief §3.4).
    """
    if not cwd:
        return None
    try:
        start = Path(cwd).resolve()
    except OSError:
        return None
    for candidate in (start, *start.parents):
        if (candidate / "forge.toml").is_file():
            return candidate
    return None


def load_forge_toml(root: Path) -> dict[str, Any]:
    """Best-effort parse of ``forge.toml``; ``{}`` on a missing file.

    A ``forge.toml`` that exists but does not parse raises
    :class:`HookRuntimeError` (fail closed): treating it as empty would
    silently switch off every ``[[verify]]`` domain of the evidence gate."""
    path = root / "forge.toml"
    try:
        text = path.read_text()
    except FileNotFoundError:
        return {}
    except (OSError, UnicodeDecodeError) as exc:
        raise HookRuntimeError(f"cannot read {path}: {exc}") from exc
    try:
        return tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise HookRuntimeError(f"{path} is not valid TOML ({exc}); the Forge gate cannot run until it is fixed") from exc


# ---------------------------------------------------------------------------
# git
# ---------------------------------------------------------------------------

def git(root: Path, *args: str, timeout: float = 5.0) -> str:
    """Run git in ``root``; empty string on any failure (never raises)."""
    try:
        res = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True, text=True, timeout=timeout,
        )
        return res.stdout
    except (OSError, subprocess.SubprocessError):
        return ""


def changed_paths(root: Path) -> list[str]:
    """Paths with uncommitted changes (staged, unstaged, untracked) per
    ``git status --porcelain`` -- the PreCompact snapshot's "modified files".
    The Stop gate does NOT use this: it diffs against the last-green SHA
    (``forge.state.changed_since``) so committed changes are gated too."""
    out = git(root, "status", "--porcelain=v1", "--untracked-files=all")
    paths: list[str] = []
    for line in out.splitlines():
        if len(line) < 4:
            continue
        rest = line[3:]
        if " -> " in rest:  # rename/copy: "old -> new"
            rest = rest.split(" -> ", 1)[1]
        rest = rest.strip()
        if rest.startswith('"') and rest.endswith('"') and len(rest) >= 2:
            rest = rest[1:-1]
        if rest:
            paths.append(rest)
    return paths


def head_sha(root: Path) -> str:
    sha = git(root, "rev-parse", "HEAD").strip()
    return sha or "nogit"


# ---------------------------------------------------------------------------
# glob matching for forge.toml [[verify]] paths (supports ** and *)
# ---------------------------------------------------------------------------

def glob_match(pattern: str, path: str) -> bool:
    """Match ``path`` (relative, forward-slash) against a glob supporting
    ``**`` (any depth) and ``*``/``?`` (single segment). Shared with
    ``forge verify`` via :func:`forge.evidence.glob_match`."""
    return _evidence_glob_match(pattern, path)


def any_glob_match(patterns: list[str], path: str) -> bool:
    return any(glob_match(pat, path) for pat in patterns)


# ---------------------------------------------------------------------------
# JSON I/O
# ---------------------------------------------------------------------------

def read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return default


def write_json_atomic(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".tmp{os.getpid()}")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    os.replace(tmp, path)


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


# ---------------------------------------------------------------------------
# agent identity (CONTRACTS.md §13 -- policy is anchored on agent_type)
# ---------------------------------------------------------------------------

JUDGE_AGENT_TYPES = {"forge:verification-evaluator", "forge:red-team"}
MECHANICAL_AGENT_TYPE = "forge:mechanical-engineer"


def is_judge(agent_type: str | None) -> bool:
    """Read-only reviewer roles (maker != checker, ADR-001 D6). These may not
    write through any tool, and their Bash is limited to a read-only
    allowlist (review #1, M2)."""
    return (agent_type or "") in JUDGE_AGENT_TYPES


def is_mechanical_engineer(agent_type: str | None) -> bool:
    return (agent_type or "") == MECHANICAL_AGENT_TYPE


def truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


# ---------------------------------------------------------------------------
# out/verify/*.json and reviews/G*.md scanning (shared by SessionStart and PreCompact)
# ---------------------------------------------------------------------------

_FENCE_RE = re.compile(r"```json\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)


def failing_checks(project: Path) -> list[str]:
    """``check_id``s of every ``out/verify/*.json`` result whose status != pass."""
    verify_dir = project / "out" / "verify"
    out: list[str] = []
    if not verify_dir.is_dir():
        return out
    for f in sorted(verify_dir.glob("*.json")):
        data = read_json(f)
        if isinstance(data, dict) and data.get("status") != "pass":
            out.append(data.get("check_id", f.stem))
    return out


def open_review_findings(project: Path) -> list[dict[str, Any]]:
    """Criteria with ``verdict != PASS`` across every ``reviews/G*.md`` verdict block."""
    findings: list[dict[str, Any]] = []
    reviews_dir = project / "reviews"
    if not reviews_dir.is_dir():
        return findings
    for f in sorted(reviews_dir.glob("G*.md")):
        try:
            text = f.read_text()
        except OSError:
            continue
        for block in _FENCE_RE.findall(text):
            try:
                payload = json.loads(block)
            except json.JSONDecodeError:
                continue
            if not isinstance(payload, dict) or payload.get("schema") != "forge.verdict/1":
                continue
            for c in payload.get("criteria", []):
                if isinstance(c, dict) and c.get("verdict") != "PASS":
                    findings.append({
                        "file": f.name, "id": c.get("id"), "verdict": c.get("verdict"),
                        "severity": c.get("severity"), "finding": c.get("finding"),
                    })
    return findings
