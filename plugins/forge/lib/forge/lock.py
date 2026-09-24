"""MCP server-definition locking: build, compare, cache (BUILD items 2-3;
docs/research/R6 section 6, "Recommended security/mcp-lock.json design").

A locked server entry canonicalizes and hashes (RFC 8785 JCS + SHA-256):

- the **launch spec**: command argv, env var *names* only (never values),
  and cwd;
- the **artifact**: ecosystem/name/version/sha256 as declared in
  security/mcp-servers.json;
- the **negotiated protocol**: era (2026-07-28 `server/discover` vs.
  legacy `initialize`), version, serverInfo, capabilities;
- every **model-visible surface**: `instructions`, and each `tools`,
  `prompts`, `resources` and `resources/templates` item, keyed by its
  name (or `uri`/`uriTemplate`) -- duplicates are rejected, and ordering
  falls out of JCS's own UTF-16 key sort, satisfying R6's "sort list
  items by name ... and fail on duplicate names".

:func:`diff_entry` turns two entries into a list of :class:`Drift`, one
per differing field, each already carrying the rule/measured/expected/fix
shape every Forge check must report (see :mod:`forge.checks`).
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import jcs
from .checks import CheckResult
from .mcp_probe import probe_server

__all__ = [
    "LockError",
    "ServerConfig",
    "Drift",
    "load_servers_config",
    "load_lock",
    "save_lock",
    "build_entry",
    "probe_and_build_entry",
    "diff_entry",
    "compute_lock_hash",
    "run_mcp_checks",
]

LOCK_SCHEMA = 1
SERVERS_CONFIG_SCHEMA = 1

_SURFACE_KEY_FIELD = {
    "tools": "name",
    "prompts": "name",
    "resources": "uri",
    "resource_templates": "uriTemplate",
}
_SURFACE_SINGULAR = {
    "tools": "tool",
    "prompts": "prompt",
    "resources": "resource",
    "resource_templates": "resource template",
}
# A minimal, safe base environment inherited into every probed server's
# process, regardless of that server's own declared env var names.
_BASE_ENV_KEYS = ("PATH", "HOME", "LANG", "LC_ALL", "SYSTEMROOT", "TEMP", "TMP")


class LockError(Exception):
    """A server config or a probed surface can't be locked as given."""


@dataclass
class ServerConfig:
    id: str
    command: list[str]
    env: list[str] = field(default_factory=list)
    cwd: str | None = None
    pending_install: bool = False
    artifact: dict[str, Any] = field(default_factory=dict)
    notes: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ServerConfig":
        if "id" not in data:
            raise LockError("server config entry is missing required field 'id'")
        return cls(
            id=data["id"],
            command=list(data.get("command") or []),
            env=list(data.get("env") or []),
            cwd=data.get("cwd"),
            pending_install=bool(data.get("pending_install", False)),
            artifact=dict(data.get("artifact") or {}),
            notes=data.get("notes"),
        )


@dataclass
class Drift:
    field: str
    rule: str
    expected: Any
    measured: Any
    fix: str

    def to_check_result(self, server_id: str) -> CheckResult:
        return CheckResult(
            id=f"mcp:{server_id}:{self.field}",
            status="fail",
            rule=self.rule,
            measured=self.measured,
            expected=self.expected,
            fix=self.fix,
        )


# --------------------------------------------------------------------------
# Config / lock file I/O
# --------------------------------------------------------------------------


def load_servers_config(path: Path) -> list[ServerConfig]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise LockError(f"{path} is not valid JSON: {exc}") from exc
    servers = data.get("servers")
    if not isinstance(servers, list):
        raise LockError(f"{path} must have a top-level 'servers' array")
    return [ServerConfig.from_dict(s) for s in servers]


def load_lock(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schema": LOCK_SCHEMA, "generated_at": None, "servers": {}, "lock_hash": None}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise LockError(f"{path} is not valid JSON: {exc}") from exc


def save_lock(path: Path, lock_obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(lock_obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    tmp = path.with_suffix(path.suffix + f".{os.getpid()}.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


# --------------------------------------------------------------------------
# Building a canonical entry from a probe
# --------------------------------------------------------------------------


def _collection(items: list[dict[str, Any]], surface: str) -> dict[str, Any]:
    key_field = _SURFACE_KEY_FIELD[surface]
    keyed: dict[str, Any] = {}
    for item in items:
        name = item.get(key_field)
        if name is None:
            raise LockError(f"{surface} item missing required field {key_field!r}: {item!r}")
        if name in keyed:
            raise LockError(f"{surface} has a duplicate {key_field}: {name!r}")
        keyed[name] = item
    item_entries = {
        name: {"hash": jcs.hash_canonical(value), "value": value}
        for name, value in keyed.items()
    }
    # JCS orders object members by UTF-16 code unit, which is exactly R6's
    # "sort list items by name" recommendation -- hashing the keyed dict
    # gets that ordering for free instead of re-implementing a sort.
    return {"count": len(keyed), "hash": jcs.hash_canonical(keyed), "items": item_entries}


def build_entry(config: ServerConfig, probe) -> dict[str, Any]:
    """Build a canonical, hashed lock entry from a :class:`~forge.mcp_probe.ProbeResult`."""
    launch = {"command": list(config.command), "env": sorted(config.env), "cwd": config.cwd}
    launch_hash = jcs.hash_canonical(launch)

    artifact = dict(config.artifact)
    artifact_hash = jcs.hash_canonical(artifact)

    protocol = {
        "era": probe.protocol_era,
        "version": probe.protocol_version,
        "server_info": probe.server_info,
        "capabilities": probe.capabilities,
    }

    surfaces = {
        "instructions": {
            "hash": jcs.hash_canonical(probe.instructions),
            "value": probe.instructions,
        },
        "tools": _collection(probe.tools, "tools"),
        "prompts": _collection(probe.prompts, "prompts"),
        "resources": _collection(probe.resources, "resources"),
        "resource_templates": _collection(probe.resource_templates, "resource_templates"),
    }

    fingerprint = jcs.hash_canonical(
        {
            "launch": launch_hash,
            "artifact": artifact_hash,
            "protocol": protocol,
            "surfaces": {name: s["hash"] for name, s in surfaces.items()},
        }
    )

    return {
        "id": config.id,
        "launch": {**launch, "hash": launch_hash},
        "artifact": {**artifact, "hash": artifact_hash},
        "protocol": protocol,
        "surfaces": surfaces,
        "fingerprint": fingerprint,
        "probed_at": time.time(),
    }


def _prepare_env(names: list[str]) -> dict[str, str]:
    """Real env for launching a probed server: a safe base, plus any of the
    server's declared var *names* that happen to be set in this process's
    own environment. The lock itself only ever stores the names."""
    env: dict[str, str] = {}
    for key in _BASE_ENV_KEYS:
        if key in os.environ:
            env[key] = os.environ[key]
    for name in names:
        if name in os.environ:
            env[name] = os.environ[name]
    return env


def probe_and_build_entry(
    config: ServerConfig, *, timeout: float = 20.0, client_name: str = "forge-mcp-probe"
) -> dict[str, Any]:
    probe = probe_server(
        config.command,
        env=_prepare_env(config.env),
        cwd=config.cwd,
        timeout=timeout,
        client_name=client_name,
    )
    return build_entry(config, probe)


# --------------------------------------------------------------------------
# Comparison
# --------------------------------------------------------------------------


def _approval_fix(server_id: str) -> str:
    return (
        f"if this change is expected, a human (never an agent) must review it and run "
        f"`forge lock mcp --server {server_id} --write`; otherwise treat it as a possible "
        "rug pull and do not approve it."
    )


def diff_entry(server_id: str, locked: dict[str, Any], probed: dict[str, Any]) -> list[Drift]:
    """Compare a locked entry against a freshly probed one; empty means clean."""
    drifts: list[Drift] = []

    if locked.get("launch", {}).get("hash") != probed["launch"]["hash"]:
        drifts.append(
            Drift(
                field="launch",
                rule="Launch spec (command, env var names, cwd) must match security/mcp-lock.json.",
                expected=locked.get("launch"),
                measured=probed["launch"],
                fix=_approval_fix(server_id),
            )
        )
    if locked.get("artifact", {}).get("hash") != probed["artifact"]["hash"]:
        drifts.append(
            Drift(
                field="artifact",
                rule="Package artifact (version, sha256) must match security/mcp-lock.json.",
                expected=locked.get("artifact"),
                measured=probed["artifact"],
                fix=_approval_fix(server_id),
            )
        )

    locked_protocol = locked.get("protocol") or {}
    probed_protocol = probed["protocol"]
    if locked_protocol.get("version") != probed_protocol.get("version"):
        drifts.append(
            Drift(
                field="protocol.version",
                rule="Negotiated MCP protocol version must match security/mcp-lock.json.",
                expected=locked_protocol.get("version"),
                measured=probed_protocol.get("version"),
                fix=_approval_fix(server_id),
            )
        )

    locked_surfaces = locked.get("surfaces") or {}
    probed_surfaces = probed["surfaces"]

    locked_instructions = locked_surfaces.get("instructions") or {}
    probed_instructions = probed_surfaces["instructions"]
    if locked_instructions.get("hash") != probed_instructions["hash"]:
        drifts.append(
            Drift(
                field="surfaces.instructions",
                rule=(
                    "Server `instructions` text must match security/mcp-lock.json "
                    "(docs/research/R6 #3213: prompt injection via discover/initialize "
                    "instructions is a live attack)."
                ),
                expected=locked_instructions.get("value"),
                measured=probed_instructions["value"],
                fix=_approval_fix(server_id),
            )
        )

    for surface in ("tools", "prompts", "resources", "resource_templates"):
        singular = _SURFACE_SINGULAR[surface]
        locked_items = (locked_surfaces.get(surface) or {}).get("items", {}) or {}
        probed_items = probed_surfaces[surface]["items"]
        for name in sorted(set(locked_items) | set(probed_items)):
            before = locked_items.get(name)
            after = probed_items.get(name)
            if before is None:
                drifts.append(
                    Drift(
                        field=f"surfaces.{surface}.{name}",
                        rule=(
                            f"Every {singular} must be listed in security/mcp-lock.json "
                            "before Forge trusts it (an unlisted item is new, unreviewed "
                            "surface)."
                        ),
                        expected="<absent>",
                        measured=after["value"],
                        fix=_approval_fix(server_id),
                    )
                )
            elif after is None:
                drifts.append(
                    Drift(
                        field=f"surfaces.{surface}.{name}",
                        rule=(
                            f"A locked {singular} disappearing is also drift: a server "
                            "can change behaviour by removing/renaming, not only by "
                            "editing content."
                        ),
                        expected=before["value"],
                        measured="<absent>",
                        fix=_approval_fix(server_id),
                    )
                )
            elif before["hash"] != after["hash"]:
                drifts.append(
                    Drift(
                        field=f"surfaces.{surface}.{name}",
                        rule=(
                            f"{singular} {name!r} must match security/mcp-lock.json "
                            "field-for-field (rug-pull defence)."
                        ),
                        expected=before["value"],
                        measured=after["value"],
                        fix=_approval_fix(server_id),
                    )
                )
    return drifts


def compute_lock_hash(servers: dict[str, Any]) -> str:
    return jcs.hash_canonical({sid: entry.get("fingerprint") for sid, entry in servers.items()})


# --------------------------------------------------------------------------
# Doctor entry point (BUILD item 1.c)
# --------------------------------------------------------------------------


def _load_cache(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _save_cache(path: Path, cache: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _check_one_server(
    config: ServerConfig, locked_entry: dict[str, Any] | None, timeout: float
) -> list[CheckResult]:
    if locked_entry is None:
        return [
            CheckResult(
                id=f"mcp:{config.id}",
                status="fail",
                rule=(
                    "Every non-pending server in security/mcp-servers.json must have a "
                    "matching entry in security/mcp-lock.json (fail closed)."
                ),
                measured="<no lock entry>",
                expected=f"an entry for {config.id!r} in the lock",
                fix=f"a human must review {config.id!r} and run `forge lock mcp --server {config.id} --write`.",
            )
        ]
    try:
        probed_entry = probe_and_build_entry(config, timeout=timeout)
    except Exception as exc:  # noqa: BLE001 -- a probe failure is a check FAIL, not a crash
        return [
            CheckResult(
                id=f"mcp:{config.id}",
                status="fail",
                rule=(
                    f"{config.id!r} must be probeable over MCP stdio "
                    "(server/discover, falling back to initialize)."
                ),
                measured=f"<probe error: {exc}>",
                expected="a successful MCP handshake and list responses",
                fix=f"investigate why {config.id!r} failed to respond; check its launch command, env and logs.",
            )
        ]
    drifts = diff_entry(config.id, locked_entry, probed_entry)
    if not drifts:
        return [
            CheckResult(
                id=f"mcp:{config.id}",
                status="pass",
                rule="Probed launch spec, artifact, protocol and surfaces must match security/mcp-lock.json.",
                measured=probed_entry["fingerprint"],
                expected=locked_entry.get("fingerprint"),
            )
        ]
    return [d.to_check_result(config.id) for d in drifts]


def run_mcp_checks(
    servers_config_path: Path,
    lock_path: Path,
    *,
    timeout: float = 20.0,
    quick: bool = False,
    cache_path: Path | None = None,
    cache_max_age_s: float = 24 * 3600,
) -> list[CheckResult]:
    if cache_path is None:
        cache_path = lock_path.with_name(lock_path.name + ".doctor-cache.json")

    if not servers_config_path.exists():
        return [
            CheckResult(
                id="mcp_servers_config",
                status="warn",
                rule="security/mcp-servers.json lists the MCP servers Forge should vet.",
                measured="<not found>",
                expected=str(servers_config_path),
                fix=f"create {servers_config_path} (see plugins/forge/bin/README.md).",
            )
        ]
    try:
        servers = load_servers_config(servers_config_path)
    except LockError as exc:
        return [
            CheckResult(
                id="mcp_servers_config",
                status="fail",
                rule="security/mcp-servers.json must be valid per its documented schema.",
                measured=str(exc),
                expected="valid JSON matching the schema",
                fix=f"fix {servers_config_path}.",
            )
        ]

    try:
        lock_obj = load_lock(lock_path)
    except LockError as exc:
        return [
            CheckResult(
                id="mcp_lock",
                status="fail",
                rule="security/mcp-lock.json must be valid JSON.",
                measured=str(exc),
                expected="valid JSON matching the lock schema",
                fix=f"fix or regenerate {lock_path}.",
            )
        ]
    locked_servers = lock_obj.get("servers", {}) or {}
    cache = _load_cache(cache_path)
    now = time.time()
    results: list[CheckResult] = []

    for config in servers:
        if config.pending_install:
            results.append(
                CheckResult(
                    id=f"mcp:{config.id}",
                    status="warn",
                    rule=(
                        "A server marked pending_install has not been vetted and must "
                        "not be treated as passing."
                    ),
                    measured="pending_install=true",
                    expected="a completed installation, probed and locked",
                    fix=(
                        f"once the toolchain installer supplies a real launch command "
                        f"for {config.id!r}, run `forge lock mcp --server {config.id} --write`."
                    ),
                )
            )
            continue

        if quick:
            cached = cache.get(config.id)
            if cached and (now - cached.get("checked_at", 0)) < cache_max_age_s:
                for item in cached["results"]:
                    results.append(CheckResult(**item))
                continue
            results.append(
                CheckResult(
                    id=f"mcp:{config.id}",
                    status="skip",
                    rule="`--quick` skips live MCP probes unless a cached result younger than 24h exists.",
                    measured="<no fresh cache>",
                    expected="a probe within the last 24h, or a full `forge doctor` run",
                    fix=f"run `forge doctor` without --quick to refresh the MCP probe cache for {config.id!r}.",
                )
            )
            continue

        server_results = _check_one_server(config, locked_servers.get(config.id), timeout)
        results.extend(server_results)
        cache[config.id] = {
            "checked_at": now,
            "results": [r.to_dict() for r in server_results],
        }

    if not quick:
        _save_cache(cache_path, cache)
    return results
