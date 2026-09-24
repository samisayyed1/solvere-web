"""Tests for forge.mcp_probe: the stdlib-only MCP stdio client (BUILD item 3).

Exercises both protocol eras against tests/fixtures/fake_mcp_server.py,
cursor-based pagination, noise-dropping, and the timeout path.
"""

from __future__ import annotations

import os
import sys
import time

import pytest

from forge import mcp_probe


def _env(**overrides) -> dict[str, str]:
    env = dict(os.environ)
    env.update(overrides)
    return env


def test_probe_uses_server_discover_by_default(fake_server_argv):
    result = mcp_probe.probe_server(fake_server_argv, env=_env(), timeout=5)
    assert result.protocol_era == "2026-07-28"
    assert result.protocol_version == "2026-07-28"
    assert result.server_info == {"name": "fake-mcp-server", "version": "1.0.0"}
    assert "Forge tests only" in result.instructions
    assert {t["name"] for t in result.tools} == {"add", "echo"}
    assert len(result.prompts) == 1
    assert len(result.resources) == 1
    assert len(result.resource_templates) == 1


def test_probe_falls_back_to_legacy_initialize(fake_server_argv):
    """When server/discover isn't implemented (any error -- not one specific
    code -- per the 2026-07-28 stdio backward-compat rule), the probe must
    fall back to initialize + notifications/initialized and still succeed."""
    result = mcp_probe.probe_server(fake_server_argv, env=_env(FAKE_MCP_PROTOCOL="legacy"), timeout=5)
    assert result.protocol_era == "legacy"
    assert result.protocol_version == "2025-11-25"
    assert {t["name"] for t in result.tools} == {"add", "echo"}


def test_both_protocol_eras_return_equivalent_tool_definitions(fake_server_argv):
    discover = mcp_probe.probe_server(fake_server_argv, env=_env(), timeout=5)
    legacy = mcp_probe.probe_server(
        fake_server_argv, env=_env(FAKE_MCP_PROTOCOL="legacy"), timeout=5
    )
    assert discover.tools == legacy.tools
    assert discover.instructions == legacy.instructions


def test_probe_pages_through_cursors(fake_server_argv):
    result = mcp_probe.probe_server(
        fake_server_argv, env=_env(FAKE_MCP_PAGE_SIZE="1"), timeout=5
    )
    # Two tools, page size 1 -> at least two tools/list round trips were
    # needed; the probe must still assemble the full set in order.
    assert [t["name"] for t in result.tools] == ["add", "echo"]


def test_probe_tolerates_noise_on_stdout(fake_server_argv):
    result = mcp_probe.probe_server(fake_server_argv, env=_env(FAKE_MCP_NOISE="1"), timeout=5)
    assert {t["name"] for t in result.tools} == {"add", "echo"}


def test_probe_extra_tool_mode_is_visible_to_the_probe(fake_server_argv):
    result = mcp_probe.probe_server(fake_server_argv, env=_env(FAKE_MCP_EXTRA_TOOL="1"), timeout=5)
    assert {t["name"] for t in result.tools} == {"add", "echo", "delete_all"}


def test_probe_mutate_mode_from_first_call(fake_server_argv):
    result = mcp_probe.probe_server(
        fake_server_argv,
        env=_env(FAKE_MCP_MUTATE="1", FAKE_MCP_MUTATE_AFTER="0"),
        timeout=5,
    )
    add_tool = next(t for t in result.tools if t["name"] == "add")
    assert "POST" in add_tool["description"]


# --- Proof the timeout / error paths actually fire -------------------------


def test_probe_FAILS_fast_on_a_dead_command(tmp_path):
    with pytest.raises(mcp_probe.MCPProbeError):
        mcp_probe.probe_server([str(tmp_path / "does-not-exist")], env=_env(), timeout=2)


def test_request_times_out_when_server_never_answers():
    """A server that reads stdin but never writes a response must trip the
    client's timeout rather than hang forever."""
    silent = [sys.executable, "-c", "import sys; sys.stdin.readline()"]
    start = time.monotonic()
    with pytest.raises(mcp_probe.MCPTimeout):
        with mcp_probe.MCPStdioClient(silent, env=_env()) as client:
            client.request("server/discover", {"protocolVersion": "2026-07-28"}, timeout=1)
    elapsed = time.monotonic() - start
    assert elapsed < 5  # bounded, not hung
