"""Claude Code version-floor checks (ADR-001 D1 / BUILD item 1.a).

The minimum supported Claude Code version lives in exactly one place,
:data:`MIN_CLAUDE_CODE_VERSION`, so a floor bump never requires hunting
through the codebase.
"""

from __future__ import annotations

import errno
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .checks import CheckResult

__all__ = [
    "MIN_CLAUDE_CODE_VERSION",
    "RECOMMENDED_CLAUDE_CODE_VERSION",
    "Version",
    "parse_version",
    "compare_versions",
    "check_claude_binary",
    "find_desktop_claude_binaries",
    "run_version_floor_checks",
]

#: The single source of truth for Forge's Claude Code version floors (ADR-001 D1).
#: Below MIN fails: Opus 5.5, Forge's default model, needs >= 2.1.280.
#: Below RECOMMENDED warns: native AGENTS.md in every session type arrives in
#: 2.1.281, and Forge falls back to an ``@AGENTS.md`` import until then.
MIN_CLAUDE_CODE_VERSION = (2, 1, 280)
RECOMMENDED_CLAUDE_CODE_VERSION = (2, 1, 281)

Version = tuple[int, int, int]

_VERSION_RE = re.compile(r"(\d+)\.(\d+)\.(\d+)")

# How deep under ~/Library/Application Support/Claude*/ to search for a
# bundled `claude` binary. Electron app bundles nest resources fairly
# deep; this bound keeps a --quick doctor run fast even on a large
# install rather than doing an unbounded filesystem walk.
_DESKTOP_SEARCH_MAX_DEPTH = 10


def parse_version(text: str) -> Version | None:
    """Extract the first ``x.y.z`` version triple from free-form CLI output."""
    match = _VERSION_RE.search(text)
    if not match:
        return None
    return (int(match.group(1)), int(match.group(2)), int(match.group(3)))


def compare_versions(a: Version, b: Version) -> int:
    """Return -1, 0 or 1 as ``a`` is less than, equal to, or greater than ``b``."""
    return (a > b) - (a < b)


def _format_version(v: Version) -> str:
    return ".".join(str(part) for part in v)


def check_claude_binary(
    binary: str,
    *,
    check_id: str,
    min_version: Version = MIN_CLAUDE_CODE_VERSION,
    recommended_version: Version = RECOMMENDED_CLAUDE_CODE_VERSION,
    timeout: float = 20.0,
) -> CheckResult:
    """Run ``<binary> --version`` and check it against the version floor."""
    rule = (
        f"Claude Code at {binary!r} must be >= "
        f"{_format_version(min_version)} (ADR-001 D1)."
    )
    try:
        proc = subprocess.run(
            [binary, "--version"],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError:
        return CheckResult(
            id=check_id,
            status="fail",
            rule=rule,
            measured="<binary not found>",
            expected=_format_version(min_version),
            fix=f"install or fix PATH so that {binary!r} resolves to a Claude Code CLI.",
        )
    except subprocess.TimeoutExpired:
        return CheckResult(
            id=check_id,
            status="fail",
            rule=rule,
            measured="<timed out>",
            expected=_format_version(min_version),
            fix=f"`{binary} --version` did not return within {timeout}s; investigate a hung CLI.",
        )
    except OSError as exc:
        if exc.errno == errno.ENOEXEC:
            # e.g. the Linux binary Desktop ships for its VM sessions: not runnable
            # on this host and not a CLI Forge sessions use here.
            return CheckResult(
                id=check_id,
                status="skip",
                rule=rule,
                measured="<not an executable for this OS (ENOEXEC)>",
                expected=_format_version(min_version),
            )
        return CheckResult(
            id=check_id,
            status="fail",
            rule=rule,
            measured=f"<error: {exc}>",
            expected=_format_version(min_version),
            fix=f"`{binary} --version` could not be run: {exc}.",
        )

    output = (proc.stdout or "") + (proc.stderr or "")
    version = parse_version(output)
    if version is None:
        return CheckResult(
            id=check_id,
            status="fail",
            rule=rule,
            measured=output.strip() or "<empty output>",
            expected=_format_version(min_version),
            fix=(
                f"`{binary} --version` did not print a recognisable x.y.z version; "
                "confirm it is really the Claude Code CLI."
            ),
        )
    if compare_versions(version, min_version) < 0:
        return CheckResult(
            id=check_id,
            status="fail",
            rule=rule,
            measured=_format_version(version),
            expected=_format_version(min_version),
            fix=f"upgrade Claude Code at {binary!r} to >= {_format_version(min_version)}.",
        )
    if compare_versions(version, recommended_version) < 0:
        return CheckResult(
            id=check_id,
            status="warn",
            rule=rule,
            measured=_format_version(version),
            expected=_format_version(recommended_version),
            fix=(
                f"works, but >= {_format_version(recommended_version)} is recommended "
                "(native AGENTS.md); update Claude Code (Desktop updates its bundled CLI itself)."
            ),
        )
    return CheckResult(
        id=check_id,
        status="pass",
        rule=rule,
        measured=_format_version(version),
        expected=_format_version(min_version),
    )


def find_desktop_claude_binaries(home: Path | None = None) -> list[Path]:
    """Search ``~/Library/Application Support/Claude*/`` for a `claude` binary.

    Returns an empty list (never raises) when the Desktop app, or macOS's
    Application Support layout, isn't present -- the check must skip
    gracefully rather than fail when there's nothing to check.
    """
    home = home or Path.home()
    base = home / "Library" / "Application Support"
    if not base.is_dir():
        return []
    found: list[Path] = []
    try:
        candidates = sorted(base.glob("Claude*"))
    except OSError:
        return []
    for app_dir in candidates:
        if not app_dir.is_dir():
            continue
        found.extend(_bounded_find_executable(app_dir, "claude", _DESKTOP_SEARCH_MAX_DEPTH))
    return _newest_per_install(found)


def _newest_per_install(paths: list[Path]) -> list[Path]:
    """Keep only the highest-versioned binary under each install root.

    Desktop keeps superseded ``<root>/<x.y.z>/...`` directories after an
    update; only the newest one is live, so older ones must not fail the floor.
    Paths without a version directory are all kept.
    """
    best: dict[tuple[str, ...], tuple[Version, Path]] = {}
    kept: list[Path] = []
    for path in paths:
        parts = path.parts
        idx = next((i for i, part in enumerate(parts) if re.fullmatch(r"\d+\.\d+\.\d+", part)), None)
        if idx is None:
            kept.append(path)
            continue
        key, version = parts[:idx], parse_version(parts[idx])
        assert version is not None
        if key not in best or compare_versions(version, best[key][0]) > 0:
            best[key] = (version, path)
    return kept + [path for _, path in best.values()]


def _bounded_find_executable(root: Path, name: str, max_depth: int) -> list[Path]:
    found: list[Path] = []
    root_depth = len(root.parts)
    try:
        walker = os.walk(root, onerror=lambda _err: None)
    except OSError:
        return found
    for dirpath, dirnames, filenames in walker:
        depth = len(Path(dirpath).parts) - root_depth
        if depth >= max_depth:
            dirnames[:] = []  # stop descending further
            continue
        if name in filenames:
            candidate = Path(dirpath) / name
            if candidate.is_file() and os.access(candidate, os.X_OK):
                found.append(candidate)
    return found


def run_version_floor_checks(
    *,
    terminal_binary: str = "claude",
    min_version: Version = MIN_CLAUDE_CODE_VERSION,
    home: Path | None = None,
    timeout: float = 20.0,
) -> list[CheckResult]:
    """Check the terminal CLI, plus every Desktop-bundled CLI found (if any)."""
    results = [
        check_claude_binary(
            terminal_binary,
            check_id="claude_code_version:terminal",
            min_version=min_version,
            timeout=timeout,
        )
    ]
    for binary in find_desktop_claude_binaries(home=home):
        results.append(
            check_claude_binary(
                str(binary),
                check_id=f"claude_code_version:desktop:{binary}",
                min_version=min_version,
                timeout=timeout,
            )
        )
    return results
