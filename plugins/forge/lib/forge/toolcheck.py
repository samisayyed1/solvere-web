"""Toolchain manifest checks (BUILD item 1.b).

Reads ``plugins/forge/toolchain/manifest.json`` (schema: ``{"forge_home":
str, "tools": [{"id", "tier", "version", "install", "path", "version_cmd":
[argv], "version_regex", "artifact_sha256", "smoke", "smoke_result"}]}``,
written by a separate installer) and, for each tool entry, runs its
``version_cmd`` and checks the output against ``version_regex``.

This module never writes to ``plugins/forge/toolchain/`` and tolerates a
missing manifest (the installer may not have run yet): that is reported as
a single ``warn``-level :class:`~forge.checks.CheckResult`, not a failure
and not an internal error.
"""

from __future__ import annotations

import json
import os
import platform
import re
import subprocess
from pathlib import Path
from typing import Any

from .checks import CheckResult

__all__ = [
    "ManifestError",
    "load_manifest",
    "check_tool_entry",
    "run_tool_checks",
    "platform_key",
    "resolve_entry",
]


def platform_key() -> str:
    """``darwin-arm64`` or ``linux-x86_64``: the key of a manifest entry's ``platforms`` map."""
    return f"{platform.system().lower()}-{platform.machine().lower()}"


def forge_home() -> Path:
    return Path(os.environ.get("FORGE_HOME") or Path.home() / ".forge")


def _expand(arg: str) -> str:
    """Expand the portable prefixes the manifest uses: ``~/`` and ``$FORGE_HOME``."""
    if arg.startswith("$FORGE_HOME"):
        return str(forge_home()) + arg[len("$FORGE_HOME"):]
    if arg.startswith("~/.forge"):
        return str(forge_home()) + arg[len("~/.forge"):]
    return os.path.expanduser(arg) if arg.startswith("~") else arg


def resolve_entry(entry: dict[str, Any], plat: str | None = None) -> dict[str, Any]:
    """Merge the entry's per-platform override (``platforms[<key>]``) over its base fields.

    The same pinned ``version`` must hold on every platform: an override may change how a
    tool is installed and found (``install``, ``path``, ``version_cmd``, ``version_regex``,
    ``artifact_sha256``) but never what version it is, so an override that sets a different
    ``version`` is rejected by :func:`check_tool_entry`.
    """
    plat = plat or platform_key()
    merged = {k: v for k, v in entry.items() if k != "platforms"}
    override = (entry.get("platforms") or {}).get(plat)
    if isinstance(override, dict):
        merged.update(override)
        merged["_platform"] = plat
    return merged


class ManifestError(Exception):
    """The manifest file exists but is not valid JSON / not the expected shape."""


def load_manifest(path: Path) -> dict[str, Any] | None:
    """Load the toolchain manifest, or ``None`` if it doesn't exist yet."""
    if not path.exists():
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ManifestError(f"could not read manifest {path}: {exc}") from exc
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ManifestError(f"manifest {path} is not valid JSON: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("tools"), list):
        raise ManifestError(
            f"manifest {path} must be an object with a `tools` array"
        )
    return data


def check_tool_entry(
    entry: dict[str, Any], *, timeout: float = 20.0, plat: str | None = None
) -> CheckResult:
    base_version = entry.get("version")
    entry = resolve_entry(entry, plat)
    tool_id = entry.get("id") or "<missing id>"
    check_id = f"tool:{tool_id}"
    version = entry.get("version")

    if base_version and version != base_version:
        return CheckResult(
            id=check_id,
            status="fail",
            rule="A platform override may change how a tool is installed, never its pinned version (ADR-001 §8.L).",
            measured=version,
            expected=base_version,
            fix=f"remove `version` from {tool_id!r}'s `platforms` override, or re-pin every platform via ADR.",
        )

    if not version:
        return CheckResult(
            id=check_id,
            status="fail",
            rule="Every toolchain manifest entry must pin an exact `version` (ADR-001 D13: pin everything).",
            measured="<unpinned>",
            expected="<a pinned version string>",
            fix=f"set a pinned `version` for tool {tool_id!r} in the toolchain manifest.",
            detail="unpinned entry",
        )

    version_cmd = entry.get("version_cmd")
    if not version_cmd or not isinstance(version_cmd, list):
        return CheckResult(
            id=check_id,
            status="fail",
            rule="Every toolchain manifest entry must define `version_cmd` (an argv list) to verify its pinned version.",
            measured=version_cmd,
            expected="<a non-empty argv list>",
            fix=f"add `version_cmd` for tool {tool_id!r} in the toolchain manifest.",
        )

    version_regex = entry.get("version_regex")
    if not version_regex:
        return CheckResult(
            id=check_id,
            status="fail",
            rule="Every toolchain manifest entry must define `version_regex` to verify its pinned version.",
            measured=version_regex,
            expected="<a regex string>",
            fix=f"add `version_regex` for tool {tool_id!r} in the toolchain manifest.",
        )
    try:
        pattern = re.compile(version_regex)
    except re.error as exc:
        return CheckResult(
            id=check_id,
            status="fail",
            rule="`version_regex` must be a valid regular expression.",
            measured=version_regex,
            expected="<a valid regex>",
            fix=f"fix the `version_regex` for tool {tool_id!r}: {exc}",
        )

    version_cmd = [_expand(str(a)) for a in version_cmd]
    rule = f"`{' '.join(version_cmd)}` output must match /{version_regex}/ and equal pinned version {version!r}."
    # Bare tool names resolve from $FORGE_HOME/bin first: that is where the installer links
    # the pinned builds, ahead of whatever the host has on PATH.
    env = dict(os.environ)
    env["PATH"] = str(forge_home() / "bin") + os.pathsep + env.get("PATH", "")
    try:
        proc = subprocess.run(version_cmd, capture_output=True, text=True, timeout=timeout, env=env)
    except FileNotFoundError:
        return CheckResult(
            id=check_id,
            status="fail",
            rule=rule,
            measured="<binary not found>",
            expected=version,
            fix=f"install {tool_id!r} at pinned version {version!r}, or fix its `install`/PATH entry.",
        )
    except subprocess.TimeoutExpired:
        return CheckResult(
            id=check_id,
            status="fail",
            rule=rule,
            measured=f"<timed out after {timeout}s>",
            expected=version,
            fix=f"`{tool_id}`'s version_cmd did not return in time; investigate a hung binary.",
        )
    except OSError as exc:
        return CheckResult(
            id=check_id,
            status="fail",
            rule=rule,
            measured=f"<error: {exc}>",
            expected=version,
            fix=f"`{tool_id}`'s version_cmd could not be run: {exc}.",
        )

    output = (proc.stdout or "") + (proc.stderr or "")
    match = pattern.search(output)
    if not match:
        return CheckResult(
            id=check_id,
            status="fail",
            rule=rule,
            measured=output.strip() or "<empty output>",
            expected=f"output matching /{version_regex}/",
            fix=(
                f"confirm {tool_id!r} is installed and its version_regex is correct; "
                f"raw output was: {output.strip()!r}"
            ),
        )
    if match.groups():
        # The manifest author opted into extraction: compare the captured
        # version substring against the pinned value exactly, so e.g. a
        # regex like `v(\d+\.\d+\.\d+)` catches 1.17.1 silently installed
        # where 1.17.0 was pinned.
        captured = match.group(1)
        if captured != version:
            return CheckResult(
                id=check_id,
                status="fail",
                rule=rule,
                measured=captured,
                expected=version,
                fix=(
                    f"reinstall {tool_id!r} at pinned version {version!r} (found {captured!r}), "
                    "or update the manifest's pinned version after a deliberate, reviewed bump."
                ),
            )
        return CheckResult(id=check_id, status="pass", rule=rule, measured=captured, expected=version)
    # No capturing group: the regex is expected to already spell out the
    # pinned version literally (e.g. `git version 2\.52\.0`), so a
    # successful match already proves the installed tool is at the pinned
    # version -- a *different* installed version simply fails to match
    # (handled above) rather than falling out here as a false mismatch.
    return CheckResult(id=check_id, status="pass", rule=rule, measured=match.group(0), expected=version)


def run_tool_checks(manifest_path: Path, *, timeout: float = 20.0) -> list[CheckResult]:
    try:
        manifest = load_manifest(manifest_path)
    except ManifestError as exc:
        return [
            CheckResult(
                id="toolchain_manifest",
                status="fail",
                rule="The toolchain manifest, if present, must be valid JSON matching the documented schema.",
                measured=str(exc),
                expected="valid JSON: {forge_home, tools: [...]}",
                fix=f"fix or regenerate {manifest_path}.",
            )
        ]
    if manifest is None:
        return [
            CheckResult(
                id="toolchain_manifest",
                status="warn",
                rule="A toolchain manifest lets `forge doctor` verify pinned tool versions.",
                measured="<manifest not found>",
                expected=str(manifest_path),
                fix=(
                    "run the toolchain installer to generate the manifest, or pass "
                    "--manifest to point forge doctor at one."
                ),
            )
        ]
    results = []
    for entry in manifest.get("tools", []):
        results.append(check_tool_entry(entry, timeout=timeout))
    return results
