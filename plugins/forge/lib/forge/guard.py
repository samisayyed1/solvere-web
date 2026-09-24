"""forge-mcp-guard: a fail-closed stdio proxy (BUILD item 4).

docs/research/R6 section 6, "Runtime guard (recommended, not optional)":
a malicious server can serve clean definitions to a one-off doctor probe
and poisoned ones in a real session (after N calls, after a date, keyed
on clientInfo). ``forge doctor`` alone cannot see that. So every
guarded server is launched as::

    forge-mcp-guard --server <id> [--lock PATH] -- <real command argv...>

The guard sits between Claude Code (its own stdin/stdout) and the real
server (a child process it spawns), and:

1. **Refuses to start** if ``security/mcp-lock.json`` has no entry for
   ``--server`` -- fail closed, exit 2. This is deliberate: an unlocked
   server has never been through ``forge lock mcp --write`` (a human
   step), so the guard has nothing to check it against.
2. **Re-verifies every** ``tools/list`` / ``prompts/list`` /
   ``resources/list`` / ``resources/templates/list`` response, and the
   ``server/discover``/``initialize`` result's ``instructions``, against
   the lock. Because this happens on *every* such response -- not only
   ones that follow a ``notifications/*/list_changed`` -- a rug pull is
   caught whenever it happens, which subsumes the narrower "re-verify
   after list_changed" requirement.
3. On a mismatch, **replaces the response** with a JSON-RPC error
   (code -32001, naming the drifted item) instead of forwarding the
   poisoned definitions, and logs the drift to stderr.
4. **Rejects `tools/call`** for any tool name absent from the lock,
   without forwarding the call to the server at all.
5. **Drops non-JSON-RPC stdout noise** from the server (and, for
   robustness, malformed input from the client) rather than forwarding
   or crashing on it.

Known limitation: list responses are verified page by page as they
stream past, so a server that only omits an already-approved item on
some pages while keeping the rest plausible is not caught by item-level
comparison alone. Every item that *is* seen is still checked exactly
against the lock, which is where rug-pulls (changed/added items) show up.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import threading
from pathlib import Path
from typing import IO, Any, Callable

from . import jcs
from .lock import LockError, load_lock

__all__ = ["GuardError", "run_guard"]

DRIFT_ERROR_CODE = -32001

_LIST_METHODS = {
    "tools/list": ("tools", "tools", "name"),
    "prompts/list": ("prompts", "prompts", "name"),
    "resources/list": ("resources", "resources", "uri"),
    "resources/templates/list": ("resource_templates", "resourceTemplates", "uriTemplate"),
}
_HANDSHAKE_METHODS = {"server/discover", "initialize"}


class GuardError(Exception):
    pass


class _PendingRequests:
    """Tracks in-flight client->server request ids so a server response can
    be matched back to the method it answers (JSON-RPC responses don't
    repeat the method name)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._methods: dict[Any, str] = {}

    def note(self, req_id: Any, method: str) -> None:
        with self._lock:
            self._methods[req_id] = method

    def pop(self, req_id: Any) -> str | None:
        with self._lock:
            return self._methods.pop(req_id, None)


def _make_writer(stream: IO[str]) -> Callable[[dict[str, Any]], None]:
    write_lock = threading.Lock()

    def write(obj: dict[str, Any]) -> None:
        line = json.dumps(obj, ensure_ascii=False)
        with write_lock:
            try:
                stream.write(line + "\n")
                stream.flush()
            except (ValueError, OSError):
                pass  # the peer went away; nothing more we can do

    return write


def _drift_error(req_id: Any, server_id: str, item: str) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {
            "code": DRIFT_ERROR_CODE,
            "message": (
                f"forge-mcp-guard: definition drift detected for server "
                f"{server_id!r} in {item!r}; response withheld. See "
                "docs/research/R6 section 6 and security/mcp-lock.json."
            ),
        },
    }


def _log(message: str) -> None:
    print(f"[forge-mcp-guard] {message}", file=sys.stderr, flush=True)


def _verify_response(
    msg: dict[str, Any], method: str, lock_entry: dict[str, Any], server_id: str
) -> dict[str, Any]:
    """Re-verify a server->client response for a tracked method; if it
    drifts from the lock, return a replacement -32001 error instead."""
    result = msg.get("result")
    if result is None:
        return msg  # an error response from the server itself; nothing to check

    surfaces = lock_entry.get("surfaces") or {}
    req_id = msg.get("id")

    if method in _HANDSHAKE_METHODS:
        instructions = result.get("instructions")
        locked = surfaces.get("instructions") or {}
        if jcs.hash_canonical(instructions) != locked.get("hash"):
            _log(f"DRIFT server={server_id} item=instructions -- response replaced with {DRIFT_ERROR_CODE}")
            return _drift_error(req_id, server_id, "instructions")
        return msg

    surface, result_key, key_field = _LIST_METHODS[method]
    items = result.get(result_key) or []
    locked_items = (surfaces.get(surface) or {}).get("items", {}) or {}
    for item in items:
        name = item.get(key_field)
        locked_item = locked_items.get(name)
        if locked_item is None or jcs.hash_canonical(item) != locked_item.get("hash"):
            field = f"{surface}.{name!r}"
            _log(f"DRIFT server={server_id} item={field} -- response replaced with {DRIFT_ERROR_CODE}")
            return _drift_error(req_id, server_id, field)
    return msg


def _handle_client_line(
    raw_line: str,
    *,
    lock_entry: dict[str, Any],
    server_id: str,
    pending: _PendingRequests,
    write_to_server: Callable[[dict[str, Any]], None],
    write_to_client: Callable[[dict[str, Any]], None],
) -> None:
    line = raw_line.strip()
    if not line:
        return
    try:
        msg = json.loads(line)
    except json.JSONDecodeError:
        _log(f"dropped non-JSON-RPC input from client: {line!r}")
        return
    if not isinstance(msg, dict):
        _log(f"dropped non-object input from client: {line!r}")
        return

    method = msg.get("method")
    req_id = msg.get("id")

    if method == "tools/call":
        name = (msg.get("params") or {}).get("name")
        locked_tools = (lock_entry.get("surfaces", {}).get("tools") or {}).get("items", {}) or {}
        if name not in locked_tools:
            _log(f"REJECT tools/call for unlisted tool {name!r} on server {server_id!r}")
            if req_id is not None:
                write_to_client(
                    {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {
                            "code": DRIFT_ERROR_CODE,
                            "message": (
                                f"forge-mcp-guard: tool {name!r} is not present in "
                                f"security/mcp-lock.json for server {server_id!r}; call rejected."
                            ),
                        },
                    }
                )
            return

    if req_id is not None and method:
        pending.note(req_id, method)
    write_to_server(msg)


def _handle_server_line(
    raw_line: str,
    *,
    lock_entry: dict[str, Any],
    server_id: str,
    pending: _PendingRequests,
    write_to_client: Callable[[dict[str, Any]], None],
) -> None:
    line = raw_line.strip()
    if not line:
        return
    try:
        msg = json.loads(line)
    except json.JSONDecodeError:
        _log(f"dropped non-JSON-RPC output from server {server_id!r}: {line!r}")
        return
    if not isinstance(msg, dict):
        _log(f"dropped non-object output from server {server_id!r}: {line!r}")
        return

    req_id = msg.get("id")
    is_response = req_id is not None and "method" not in msg
    if is_response:
        method = pending.pop(req_id)
        if method in _HANDSHAKE_METHODS or method in _LIST_METHODS:
            msg = _verify_response(msg, method, lock_entry, server_id)
    write_to_client(msg)


def _kill(proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    try:
        if os.name == "posix":
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        else:
            proc.terminate()
    except (ProcessLookupError, PermissionError, OSError):
        pass
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try:
            if os.name == "posix":
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            else:
                proc.kill()
        except (ProcessLookupError, PermissionError, OSError):
            pass


def run_guard(
    *,
    server_id: str,
    real_argv: list[str],
    lock_path: Path,
    client_in: IO[str] | None = None,
    client_out: IO[str] | None = None,
) -> int:
    """Run the guard proxy; returns a process exit code (never raises)."""
    client_in = client_in if client_in is not None else sys.stdin
    client_out = client_out if client_out is not None else sys.stdout

    try:
        lock_obj = load_lock(lock_path)
    except LockError as exc:
        _log(f"cannot read lock {lock_path}: {exc} -- refusing to start (fail closed)")
        return 2

    lock_entry = (lock_obj.get("servers") or {}).get(server_id)
    if lock_entry is None:
        _log(
            f"refusing to start: no lock entry for server {server_id!r} in {lock_path} "
            "(fail closed -- run `forge lock mcp --write` as a human, first)"
        )
        return 2

    if not real_argv:
        _log("no real server command given after `--`.")
        return 2

    try:
        proc = subprocess.Popen(
            real_argv,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=None,  # inherited: the wrapped server's stderr passes straight through
            text=True,
            encoding="utf-8",
            bufsize=1,
            start_new_session=(os.name == "posix"),
        )
    except OSError as exc:
        _log(f"failed to start real server {real_argv!r}: {exc}")
        return 2

    pending = _PendingRequests()
    write_to_client = _make_writer(client_out)
    write_to_server = _make_writer(proc.stdin)

    def pump_client_to_server() -> None:
        try:
            for raw_line in client_in:
                _handle_client_line(
                    raw_line,
                    lock_entry=lock_entry,
                    server_id=server_id,
                    pending=pending,
                    write_to_server=write_to_server,
                    write_to_client=write_to_client,
                )
        except (ValueError, OSError):
            pass
        finally:
            try:
                proc.stdin.close()
            except OSError:
                pass

    def pump_server_to_client() -> None:
        try:
            for raw_line in proc.stdout:
                _handle_server_line(
                    raw_line,
                    lock_entry=lock_entry,
                    server_id=server_id,
                    pending=pending,
                    write_to_client=write_to_client,
                )
        except (ValueError, OSError):
            pass

    client_to_server = threading.Thread(target=pump_client_to_server, daemon=True)
    server_to_client = threading.Thread(target=pump_server_to_client, daemon=True)
    client_to_server.start()
    server_to_client.start()

    try:
        exit_code = proc.wait()
    finally:
        _kill(proc)
        client_to_server.join(timeout=2)
        server_to_client.join(timeout=2)

    return exit_code if exit_code is not None else 0
