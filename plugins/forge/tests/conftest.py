"""Shared pytest fixtures: repo paths, the lib/ path, and the fake MCP server."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = TESTS_DIR.parent  # plugins/forge
REPO_ROOT = PLUGIN_ROOT.parent.parent
LIB_DIR = PLUGIN_ROOT / "lib"
FIXTURES_DIR = TESTS_DIR / "fixtures"
FAKE_SERVER_SCRIPT = FIXTURES_DIR / "fake_mcp_server.py"
BIN_FORGE = PLUGIN_ROOT / "bin" / "forge"
BIN_GUARD = PLUGIN_ROOT / "bin" / "forge-mcp-guard"

if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))


@pytest.fixture
def fake_server_argv() -> list[str]:
    """argv that launches the fake MCP server fixture in default (clean,
    discover-era) mode."""
    return [sys.executable, str(FAKE_SERVER_SCRIPT)]


@pytest.fixture
def repo_root() -> Path:
    return REPO_ROOT
