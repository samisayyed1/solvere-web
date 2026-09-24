"""A minimal, dependency-free JSON-RPC 2.0 stdio client for probing MCP servers.

No MCP SDK is used (stdlib only), per the constraint that Forge's runtime
code must run anywhere with a bare ``python3``.

Protocol handling implements docs/research/R6 section 6 ("Getting the
definitions deterministically"):

- Send ``server/discover`` first, using the 2026-07-28 revision's
  no-handshake shape (protocol version and capabilities travel in the
  request, not through a session).
- On *any* error or timeout — not keyed to one specific JSON-RPC error
  code, per the spec's backward-compatibility note — fall back to the
  legacy ``initialize`` + ``notifications/initialized`` handshake.
- Page through ``tools/list``, ``prompts/list``, ``resources/list`` and
  ``resources/templates/list`` using ``cursor``/``nextCursor`` until
  exhausted. A server that doesn't implement a given list method answers
  with JSON-RPC error -32601 (Method not found); that surface is then
  reported as empty rather than as a probe failure.
- Every read is timeout-bounded. The child is always killed on exit,
  including its process group so a server that forks helpers doesn't
  leak them.
- Non-JSON-RPC bytes on stdout ("noise") are logged and skipped rather
  than treated as a fatal parse error, since a misbehaving server may
  print banners or debug output there.
"""

from __future__ import annotations

import json
import os
import queue
import signal
import subprocess
import threading
import time
from dataclasses import dataclass, field
from typing import Any

from . import __version__

__all__ = [
    "DISCOVER_PROTOCOL_VERSION",
    "LEGACY_PROTOCOL_VERSION",
    "MCPProbeError",
    "MCPTimeout",
    "MCPMethodNotFound",
    "ProbeResult",
    "MCPStdioClient",
    "probe_server",
]

DISCOVER_PROTOCOL_VERSION = "2026-07-28"
LEGACY_PROTOCOL_VERSION = "2025-11-25"
_METHOD_NOT_FOUND = -32601


class MCPProbeError(Exception):
    """Base class for anything that goes wrong talking to an MCP server."""


class MCPTimeout(MCPProbeError):
    """No matching response arrived within the allotted time."""


class MCPMethodNotFound(MCPProbeError):
    """The server answered with JSON-RPC -32601 for a method we tried."""

    def __init__(self, method: str, message: str = ""):
        super().__init__(f"{method}: method not found ({message})")
        self.method = method


@dataclass
class ProbeResult:
    """Everything model-visible that a probe collected from one server."""

    protocol_era: str  # "2026-07-28" or "legacy"
    protocol_version: str | None
    server_info: dict[str, Any] | None
    instructions: str | None
    capabilities: dict[str, Any]
    tools: list[dict[str, Any]] = field(default_factory=list)
    prompts: list[dict[str, Any]] = field(default_factory=list)
    resources: list[dict[str, Any]] = field(default_factory=list)
    resource_templates: list[dict[str, Any]] = field(default_factory=list)
    stderr: str = ""


class MCPStdioClient:
    """A single stdio JSON-RPC 2.0 connection to a child MCP server process."""

    def __init__(
        self,
        argv: list[str],
        *,
        env: dict[str, str] | None = None,
        cwd: str | None = None,
    ):
        if not argv:
            raise ValueError("argv must be a non-empty command")
        self._argv = list(argv)
        self._env = env
        self._cwd = cwd
        self._proc: subprocess.Popen | None = None
        self._out_queue: "queue.Queue[tuple[str, Any]]" = queue.Queue()
        self._out_thread: threading.Thread | None = None
        self._err_lines: list[str] = []
        self._err_thread: threading.Thread | None = None
        self._next_id = 1

    def __enter__(self) -> "MCPStdioClient":
        self.start()
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def start(self) -> None:
        kwargs: dict[str, Any] = dict(
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            bufsize=1,
            env=self._env,
            cwd=self._cwd,
        )
        if os.name == "posix":
            kwargs["start_new_session"] = True
        try:
            self._proc = subprocess.Popen(self._argv, **kwargs)
        except OSError as exc:
            raise MCPProbeError(f"failed to start {self._argv!r}: {exc}") from exc
        self._out_thread = threading.Thread(
            target=self._pump, args=(self._proc.stdout, self._out_queue), daemon=True
        )
        self._out_thread.start()
        self._err_thread = threading.Thread(
            target=self._pump_stderr, args=(self._proc.stderr,), daemon=True
        )
        self._err_thread.start()

    @staticmethod
    def _pump(stream: Any, out_queue: "queue.Queue[tuple[str, Any]]") -> None:
        try:
            for line in stream:
                out_queue.put(("line", line))
        except (ValueError, OSError) as exc:  # pipe closed underneath us
            out_queue.put(("error", exc))
        finally:
            out_queue.put(("eof", None))

    def _pump_stderr(self, stream: Any) -> None:
        try:
            for line in stream:
                self._err_lines.append(line)
        except (ValueError, OSError):
            pass

    @property
    def stderr(self) -> str:
        return "".join(self._err_lines)

    def close(self) -> None:
        proc = self._proc
        if proc is None:
            return
        try:
            if proc.stdin and not proc.stdin.closed:
                proc.stdin.close()
        except OSError:
            pass
        if proc.poll() is None:
            self._kill(proc)
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self._kill(proc, force=True)
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass
        if self._out_thread is not None:
            self._out_thread.join(timeout=2)
        if self._err_thread is not None:
            self._err_thread.join(timeout=2)
        self._proc = None

    @staticmethod
    def _kill(proc: subprocess.Popen, force: bool = False) -> None:
        sig = signal.SIGKILL if force else signal.SIGTERM
        try:
            if os.name == "posix":
                os.killpg(os.getpgid(proc.pid), sig)
            else:
                proc.kill() if force else proc.terminate()
        except (ProcessLookupError, PermissionError, OSError):
            try:
                proc.kill()
            except OSError:
                pass

    def _write(self, obj: dict[str, Any]) -> None:
        proc = self._proc
        if proc is None or proc.stdin is None:
            raise MCPProbeError("server process is not running")
        line = json.dumps(obj, ensure_ascii=False)
        try:
            proc.stdin.write(line + "\n")
            proc.stdin.flush()
        except (BrokenPipeError, OSError) as exc:
            raise MCPProbeError(f"failed writing to server stdin: {exc}") from exc

    def _read_message(self, deadline: float) -> dict[str, Any] | None:
        """Read the next well-formed JSON-RPC object, or None on timeout/EOF."""
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return None
            try:
                kind, payload = self._out_queue.get(timeout=remaining)
            except queue.Empty:
                return None
            if kind == "eof":
                return None
            if kind == "error":
                raise MCPProbeError(f"error reading server stdout: {payload}")
            line = payload.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                # Non-JSON-RPC noise on stdout: log and drop, keep waiting.
                self._err_lines.append(f"[stdout-noise] {line}\n")
                continue
            if not isinstance(obj, dict):
                self._err_lines.append(f"[stdout-noise] {line}\n")
                continue
            return obj

    def notify(self, method: str, params: dict[str, Any] | None = None) -> None:
        message: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            message["params"] = params
        self._write(message)

    def request(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        *,
        timeout: float = 20.0,
    ) -> dict[str, Any]:
        req_id = self._next_id
        self._next_id += 1
        message: dict[str, Any] = {"jsonrpc": "2.0", "id": req_id, "method": method}
        if params is not None:
            message["params"] = params
        self._write(message)
        deadline = time.monotonic() + timeout
        while True:
            obj = self._read_message(deadline)
            if obj is None:
                raise MCPTimeout(f"{method}: no response within {timeout}s")
            if obj.get("id") != req_id:
                continue  # a notification, a stale response, or noise-adjacent junk
            if "error" in obj:
                err = obj["error"] or {}
                code = err.get("code")
                msg = err.get("message", "")
                if code == _METHOD_NOT_FOUND:
                    raise MCPMethodNotFound(method, msg)
                raise MCPProbeError(f"{method} failed: [{code}] {msg}")
            return obj.get("result", {})


def _handshake(
    client: MCPStdioClient, timeout: float, client_name: str, client_version: str
) -> tuple[str, dict[str, Any]]:
    discover_params = {
        "protocolVersion": DISCOVER_PROTOCOL_VERSION,
        "capabilities": {},
        "clientInfo": {"name": client_name, "version": client_version},
    }
    try:
        result = client.request("server/discover", discover_params, timeout=timeout)
        return DISCOVER_PROTOCOL_VERSION, result
    except MCPProbeError:
        # Any error or timeout falls back -- never key on one specific code,
        # per the 2026-07-28 stdio backward-compatibility rule (R6 section 1).
        pass
    init_params = {
        "protocolVersion": LEGACY_PROTOCOL_VERSION,
        "capabilities": {},
        "clientInfo": {"name": client_name, "version": client_version},
    }
    result = client.request("initialize", init_params, timeout=timeout)
    client.notify("notifications/initialized", {})
    return "legacy", result


def _list_all(
    client: MCPStdioClient, method: str, result_key: str, timeout: float
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    cursor: str | None = None
    while True:
        params = {"cursor": cursor} if cursor else {}
        try:
            result = client.request(method, params, timeout=timeout)
        except MCPMethodNotFound:
            return []
        items.extend(result.get(result_key) or [])
        cursor = result.get("nextCursor")
        if not cursor:
            return items


def probe_server(
    argv: list[str],
    *,
    env: dict[str, str] | None = None,
    cwd: str | None = None,
    timeout: float = 20.0,
    client_name: str = "forge-mcp-probe",
    client_version: str | None = None,
) -> ProbeResult:
    """Spawn ``argv`` as an MCP stdio server, probe it, and always kill it."""
    with MCPStdioClient(argv, env=env, cwd=cwd) as client:
        era, handshake_result = _handshake(
            client, timeout, client_name, client_version or __version__
        )
        tools = _list_all(client, "tools/list", "tools", timeout)
        prompts = _list_all(client, "prompts/list", "prompts", timeout)
        resources = _list_all(client, "resources/list", "resources", timeout)
        resource_templates = _list_all(
            client, "resources/templates/list", "resourceTemplates", timeout
        )
        stderr = client.stderr
    return ProbeResult(
        protocol_era=era,
        protocol_version=handshake_result.get("protocolVersion"),
        server_info=handshake_result.get("serverInfo"),
        instructions=handshake_result.get("instructions"),
        capabilities=handshake_result.get("capabilities") or {},
        tools=tools,
        prompts=prompts,
        resources=resources,
        resource_templates=resource_templates,
        stderr=stderr,
    )
