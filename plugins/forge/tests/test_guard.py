"""Tests for forge-mcp-guard: the fail-closed runtime stdio proxy
(BUILD item 4; docs/research/R6 section 6, "Runtime guard").

These drive the real `bin/forge-mcp-guard` executable as a subprocess (the
same way Claude Code would spawn it), with tests/fixtures/fake_mcp_server.py
as the wrapped "real" server, so the whole client <-> guard <-> server
pipeline is exercised end to end.
"""

from __future__ import annotations

import json
import os
import queue
import subprocess
import sys
import threading
import time

from forge import lock as lock_module
from forge.guard import DRIFT_ERROR_CODE
from forge.mcp_probe import probe_server

from conftest import BIN_GUARD


def _env(**overrides) -> dict[str, str]:
    env = dict(os.environ)
    env.update(overrides)
    return env


class GuardHarness:
    """Drives `bin/forge-mcp-guard` as a subprocess and gives tests direct
    access to every raw line it writes to stdout (so noise-dropping can be
    verified directly, not merely tolerated by a lenient reader)."""

    def __init__(self, *, server_id: str, lock_path, real_argv: list[str], env: dict[str, str]):
        argv = [
            sys.executable,
            str(BIN_GUARD),
            "--server",
            server_id,
            "--lock",
            str(lock_path),
            "--",
            *real_argv,
        ]
        self.proc = subprocess.Popen(
            argv,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            bufsize=1,
            env=env,
        )
        self.raw_lines: list[str] = []
        self._queue: "queue.Queue[str | None]" = queue.Queue()
        self._thread = threading.Thread(target=self._pump, daemon=True)
        self._thread.start()
        self._next_id = 1

    def _pump(self) -> None:
        for line in self.proc.stdout:
            self.raw_lines.append(line)
            self._queue.put(line)
        self._queue.put(None)

    def send(self, obj: dict) -> None:
        self.proc.stdin.write(json.dumps(obj, ensure_ascii=False) + "\n")
        self.proc.stdin.flush()

    def send_raw(self, text: str) -> None:
        self.proc.stdin.write(text + "\n")
        self.proc.stdin.flush()

    def recv(self, timeout: float = 5) -> dict:
        line = self._queue.get(timeout=timeout)
        if line is None:
            raise RuntimeError("guard closed stdout before responding")
        return json.loads(line)

    def request(self, method: str, params: dict | None = None, *, timeout: float = 5) -> dict:
        req_id = self._next_id
        self._next_id += 1
        msg = {"jsonrpc": "2.0", "id": req_id, "method": method}
        if params is not None:
            msg["params"] = params
        self.send(msg)
        while True:
            resp = self.recv(timeout=timeout)
            if resp.get("id") == req_id:
                return resp

    def close(self) -> None:
        try:
            self.proc.stdin.close()
        except OSError:
            pass
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill()
        self._thread.join(timeout=2)


def _clean_lock_entry(fake_server_argv, server_id="fake"):
    config = lock_module.ServerConfig(id=server_id, command=fake_server_argv, env=[])
    return config, lock_module.probe_and_build_entry(config, timeout=5)


def _write_lock(lock_path, server_id, entry) -> None:
    lock_module.save_lock(
        lock_path,
        {
            "schema": lock_module.LOCK_SCHEMA,
            "generated_at": "2026-09-25T00:00:00Z",
            "servers": {server_id: entry},
            "lock_hash": lock_module.compute_lock_hash({server_id: entry}),
        },
    )


# --------------------------------------------------------------------------
# Fail closed: no lock entry
# --------------------------------------------------------------------------


def test_guard_FAILS_closed_with_no_lock_entry(fake_server_argv, tmp_path):
    lock_path = tmp_path / "mcp-lock.json"
    lock_module.save_lock(lock_path, {"schema": 1, "generated_at": None, "servers": {}, "lock_hash": None})

    argv = [
        sys.executable,
        str(BIN_GUARD),
        "--server",
        "fake",
        "--lock",
        str(lock_path),
        "--",
        *fake_server_argv,
    ]
    proc = subprocess.run(argv, input="", capture_output=True, text=True, timeout=10)
    assert proc.returncode == 2
    assert "no lock entry" in proc.stderr.lower()


# --------------------------------------------------------------------------
# Clean pass-through
# --------------------------------------------------------------------------


def test_guard_passes_through_tools_list_and_tools_call(fake_server_argv, tmp_path):
    lock_path = tmp_path / "mcp-lock.json"
    config, entry = _clean_lock_entry(fake_server_argv)
    _write_lock(lock_path, "fake", entry)

    harness = GuardHarness(server_id="fake", lock_path=lock_path, real_argv=fake_server_argv, env=_env())
    try:
        discover = harness.request("server/discover", {"protocolVersion": "2026-07-28", "capabilities": {}})
        assert "error" not in discover
        assert discover["result"]["instructions"]

        listed = harness.request("tools/list")
        assert "error" not in listed
        names = {t["name"] for t in listed["result"]["tools"]}
        assert names == {"add", "echo"}

        called = harness.request("tools/call", {"name": "add", "arguments": {"a": 2, "b": 3}})
        assert "error" not in called
        assert called["result"]["structuredContent"]["sum"] == 5
    finally:
        harness.close()


# --------------------------------------------------------------------------
# MUTATE: rug pull mid-session
# --------------------------------------------------------------------------


def test_guard_MUTATE_second_tools_list_replaced_with_drift_error(fake_server_argv, tmp_path):
    """The lock is built from this server's first (clean) tools/list call --
    the default FAKE_MCP_MUTATE_AFTER=1 keeps call #1 clean and mutates from
    call #2 onward, modelling a server that behaves during vetting and flips
    after trust is established. The guard's OWN first tools/list (the
    server's call #1) must therefore still pass; its second tools/list (the
    server's call #2) must be replaced with a -32001 error."""
    lock_path = tmp_path / "mcp-lock.json"
    mutate_env = _env(FAKE_MCP_MUTATE="1")  # FAKE_MCP_MUTATE_AFTER defaults to "1"

    config = lock_module.ServerConfig(id="fake", command=fake_server_argv, env=[])
    probe = probe_server(fake_server_argv, env=mutate_env, timeout=5)
    entry = lock_module.build_entry(config, probe)
    _write_lock(lock_path, "fake", entry)
    # Sanity: the lock really did capture the clean description.
    assert entry["surfaces"]["tools"]["items"]["add"]["value"]["description"] == (
        "Add two integers and return their sum."
    )

    harness = GuardHarness(server_id="fake", lock_path=lock_path, real_argv=fake_server_argv, env=mutate_env)
    try:
        first = harness.request("tools/list")
        assert "error" not in first, "the server's first (clean) call must pass through"

        second = harness.request("tools/list")
        assert second.get("error") is not None, "the server's second (mutated) call must be blocked"
        assert second["error"]["code"] == DRIFT_ERROR_CODE
        assert "add" in second["error"]["message"] or "tools" in second["error"]["message"]
    finally:
        harness.close()


# --------------------------------------------------------------------------
# Unknown tool call rejected
# --------------------------------------------------------------------------


def test_guard_rejects_call_to_a_tool_name_not_in_the_lock(fake_server_argv, tmp_path):
    lock_path = tmp_path / "mcp-lock.json"
    config, entry = _clean_lock_entry(fake_server_argv)
    _write_lock(lock_path, "fake", entry)

    harness = GuardHarness(server_id="fake", lock_path=lock_path, real_argv=fake_server_argv, env=_env())
    try:
        resp = harness.request("tools/call", {"name": "rm_dash_rf", "arguments": {}})
        assert resp.get("error") is not None
        assert resp["error"]["code"] == DRIFT_ERROR_CODE
        assert "rm_dash_rf" in resp["error"]["message"]
    finally:
        harness.close()


# --------------------------------------------------------------------------
# EXTRA_TOOL rejected
# --------------------------------------------------------------------------


def test_guard_rejects_an_extra_tool_not_present_in_the_lock(fake_server_argv, tmp_path):
    lock_path = tmp_path / "mcp-lock.json"
    config, entry = _clean_lock_entry(fake_server_argv)  # lock built WITHOUT the extra tool
    _write_lock(lock_path, "fake", entry)

    extra_env = _env(FAKE_MCP_EXTRA_TOOL="1")
    harness = GuardHarness(server_id="fake", lock_path=lock_path, real_argv=fake_server_argv, env=extra_env)
    try:
        listed = harness.request("tools/list")
        assert listed.get("error") is not None
        assert listed["error"]["code"] == DRIFT_ERROR_CODE
        assert "delete_all" in listed["error"]["message"]

        # Even if the client tries to call the unlisted tool directly, the
        # guard rejects it independent of the tools/list drift above.
        called = harness.request("tools/call", {"name": "delete_all", "arguments": {}})
        assert called.get("error") is not None
        assert called["error"]["code"] == DRIFT_ERROR_CODE
    finally:
        harness.close()


# --------------------------------------------------------------------------
# NOISE lines dropped
# --------------------------------------------------------------------------


def test_guard_drops_noise_lines_from_the_server(fake_server_argv, tmp_path):
    """Every line the guard itself writes to stdout must be valid JSON-RPC:
    the server's non-JSON banner lines must never reach the client, not
    merely be tolerated by a lenient reader on the other end."""
    lock_path = tmp_path / "mcp-lock.json"
    config, entry = _clean_lock_entry(fake_server_argv)
    _write_lock(lock_path, "fake", entry)

    noisy_env = _env(FAKE_MCP_NOISE="1")
    harness = GuardHarness(server_id="fake", lock_path=lock_path, real_argv=fake_server_argv, env=noisy_env)
    try:
        listed = harness.request("tools/list")
        assert "error" not in listed
        assert {t["name"] for t in listed["result"]["tools"]} == {"add", "echo"}

        # Give the background reader a beat to have collected everything
        # written so far, then assert none of it was non-JSON noise.
        time.sleep(0.2)
        for raw in harness.raw_lines:
            raw = raw.strip()
            if not raw:
                continue
            json.loads(raw)  # raises if any noise line leaked through
    finally:
        harness.close()


def test_guard_drops_malformed_input_from_the_client(fake_server_argv, tmp_path):
    """Garbage on the client->server path must not be forwarded to the real
    server (which could crash or misbehave on it) and must not wedge the
    connection -- a well-formed request right after it must still work."""
    lock_path = tmp_path / "mcp-lock.json"
    config, entry = _clean_lock_entry(fake_server_argv)
    _write_lock(lock_path, "fake", entry)

    harness = GuardHarness(server_id="fake", lock_path=lock_path, real_argv=fake_server_argv, env=_env())
    try:
        harness.send_raw("this is not json-rpc at all {{{")
        listed = harness.request("tools/list")
        assert "error" not in listed
    finally:
        harness.close()


# --------------------------------------------------------------------------
# Both protocol eras
# --------------------------------------------------------------------------


def test_guard_works_over_the_legacy_protocol_era(fake_server_argv, tmp_path):
    lock_path = tmp_path / "mcp-lock.json"
    legacy_env = _env(FAKE_MCP_PROTOCOL="legacy")
    config = lock_module.ServerConfig(id="fake", command=fake_server_argv, env=[])
    probe = probe_server(fake_server_argv, env=legacy_env, timeout=5)
    entry = lock_module.build_entry(config, probe)
    _write_lock(lock_path, "fake", entry)

    harness = GuardHarness(server_id="fake", lock_path=lock_path, real_argv=fake_server_argv, env=legacy_env)
    try:
        init = harness.request("initialize", {"protocolVersion": "2025-11-25", "capabilities": {}})
        assert "error" not in init
        harness.send({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
        listed = harness.request("tools/list")
        assert {t["name"] for t in listed["result"]["tools"]} == {"add", "echo"}
    finally:
        harness.close()
