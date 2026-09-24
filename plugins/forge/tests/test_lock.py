"""Tests for forge.lock: building, comparing and doctor-checking MCP server
definition locks (BUILD items 2-3; docs/research/R6 section 6).
"""

from __future__ import annotations

import os

from forge import lock as lock_module


def _env(**overrides) -> dict[str, str]:
    env = dict(os.environ)
    env.update(overrides)
    return env


def _server_config(fake_server_argv, **kwargs) -> lock_module.ServerConfig:
    return lock_module.ServerConfig(
        id=kwargs.pop("id", "fake"),
        command=fake_server_argv,
        env=kwargs.pop("env", []),
        **kwargs,
    )


def _write_servers_config(path, *configs: lock_module.ServerConfig) -> None:
    import json

    servers = []
    for c in configs:
        servers.append(
            {
                "id": c.id,
                "pending_install": c.pending_install,
                "command": c.command,
                "env": c.env,
                "cwd": c.cwd,
                "artifact": c.artifact,
            }
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"schema": 1, "servers": servers}))


# --------------------------------------------------------------------------
# build_entry / probe_and_build_entry
# --------------------------------------------------------------------------


def test_probe_and_build_entry_shape(fake_server_argv):
    config = _server_config(fake_server_argv, artifact={"ecosystem": "pypi", "name": "fake", "version": "1.0.0"})
    entry = lock_module.probe_and_build_entry(config, timeout=5)
    assert entry["id"] == "fake"
    assert entry["launch"]["command"] == fake_server_argv
    assert entry["launch"]["env"] == []
    assert set(entry["surfaces"]["tools"]["items"]) == {"add", "echo"}
    assert entry["fingerprint"].startswith("sha256:")


def test_env_values_are_never_stored_only_names(fake_server_argv, monkeypatch):
    monkeypatch.setenv("FAKE_SECRET_TOKEN", "super-secret-value")
    config = _server_config(fake_server_argv, env=["FAKE_SECRET_TOKEN"])
    entry = lock_module.probe_and_build_entry(config, timeout=5)
    dumped = str(entry)
    assert "super-secret-value" not in dumped
    assert "FAKE_SECRET_TOKEN" in entry["launch"]["env"]


def test_duplicate_tool_names_are_rejected():
    class FakeProbe:
        protocol_era = "legacy"
        protocol_version = "2025-11-25"
        server_info = {}
        instructions = None
        capabilities = {}
        tools = [{"name": "dup", "description": "a"}, {"name": "dup", "description": "b"}]
        prompts = []
        resources = []
        resource_templates = []

    config = lock_module.ServerConfig(id="x", command=["true"])
    try:
        lock_module.build_entry(config, FakeProbe())
        assert False, "expected LockError for duplicate tool names"
    except lock_module.LockError as exc:
        assert "duplicate" in str(exc)


# --------------------------------------------------------------------------
# probe -> lock -> re-probe equal
# --------------------------------------------------------------------------


def test_probe_lock_reprobe_are_equal(fake_server_argv, tmp_path):
    config = _server_config(fake_server_argv, artifact={"ecosystem": "pypi", "name": "fake", "version": "1.0.0"})
    first = lock_module.probe_and_build_entry(config, timeout=5)
    second = lock_module.probe_and_build_entry(config, timeout=5)
    assert first["fingerprint"] == second["fingerprint"]

    lock_path = tmp_path / "mcp-lock.json"
    lock_obj = {
        "schema": lock_module.LOCK_SCHEMA,
        "generated_at": "2026-09-25T00:00:00Z",
        "servers": {config.id: first},
        "lock_hash": lock_module.compute_lock_hash({config.id: first}),
    }
    lock_module.save_lock(lock_path, lock_obj)

    reloaded = lock_module.load_lock(lock_path)
    third = lock_module.probe_and_build_entry(config, timeout=5)
    drifts = lock_module.diff_entry(config.id, reloaded["servers"][config.id], third)
    assert drifts == []


def test_diff_entry_is_clean_between_two_probes_of_the_same_clean_server(fake_server_argv):
    config = _server_config(fake_server_argv)
    a = lock_module.probe_and_build_entry(config, timeout=5)
    b = lock_module.probe_and_build_entry(config, timeout=5)
    assert lock_module.diff_entry(config.id, a, b) == []


# --------------------------------------------------------------------------
# MUTATE -> drift, naming the tool and the field
# --------------------------------------------------------------------------


def test_diff_entry_FAILS_to_stay_clean_when_tool_description_mutates(fake_server_argv):
    clean_config = _server_config(fake_server_argv)
    clean = lock_module.probe_and_build_entry(clean_config, timeout=5)

    mutated_argv = fake_server_argv  # same command; env below flips behaviour
    mutated_config = lock_module.ServerConfig(id="fake", command=mutated_argv, env=[])
    # FAKE_MCP_MUTATE_AFTER=0 -> mutated from the very first tools/list call,
    # matching a single-shot doctor probe. Probe directly with the mutating
    # environment (bypassing _prepare_env, since the test wants full control
    # over the child's env rather than only the declared var names).
    from forge.mcp_probe import probe_server

    probe = probe_server(
        mutated_argv, env=_env(FAKE_MCP_MUTATE="1", FAKE_MCP_MUTATE_AFTER="0"), timeout=5
    )
    mutated = lock_module.build_entry(mutated_config, probe)

    drifts = lock_module.diff_entry("fake", clean, mutated)
    assert drifts, "expected drift to be detected"
    fields = [d.field for d in drifts]
    assert "surfaces.tools.add" in fields
    add_drift = next(d for d in drifts if d.field == "surfaces.tools.add")
    assert add_drift.expected["description"] == "Add two integers and return their sum."
    assert "POST" in add_drift.measured["description"]
    assert add_drift.rule
    assert add_drift.fix


def test_run_mcp_checks_MUTATE_reports_drift_naming_tool_and_field(fake_server_argv, tmp_path):
    """End-to-end: build a lock from a clean probe, then run the doctor-level
    MCP checks against a server that mutates from the first call. The
    resulting check must fail, and its id/measured must name the tool and
    field that changed."""
    servers_path = tmp_path / "mcp-servers.json"
    lock_path = tmp_path / "mcp-lock.json"

    clean_config = _server_config(fake_server_argv, id="fake")
    clean_entry = lock_module.probe_and_build_entry(clean_config, timeout=5)
    lock_module.save_lock(
        lock_path,
        {
            "schema": lock_module.LOCK_SCHEMA,
            "generated_at": "2026-09-25T00:00:00Z",
            "servers": {"fake": clean_entry},
            "lock_hash": lock_module.compute_lock_hash({"fake": clean_entry}),
        },
    )

    # The server this doctor run will actually talk to always mutates (from
    # the first call), simulating a rug pull that happened after the lock
    # was approved.
    mutated_argv = list(fake_server_argv)
    mutated_config = lock_module.ServerConfig(
        id="fake",
        command=mutated_argv,
        env=["FAKE_MCP_MUTATE", "FAKE_MCP_MUTATE_AFTER"],
    )
    _write_servers_config(servers_path, mutated_config)

    os.environ["FAKE_MCP_MUTATE"] = "1"
    os.environ["FAKE_MCP_MUTATE_AFTER"] = "0"
    try:
        results = lock_module.run_mcp_checks(servers_path, lock_path, timeout=5, quick=False)
    finally:
        del os.environ["FAKE_MCP_MUTATE"]
        del os.environ["FAKE_MCP_MUTATE_AFTER"]

    failed = [r for r in results if r.status == "fail"]
    assert failed, "MUTATE must produce at least one failing check"
    names = [r.id for r in failed]
    assert any("fake" in n and "add" in n for n in names), names
    tool_drift = next(r for r in failed if "add" in r.id)
    assert "description" not in tool_drift.id  # field is the tool name, value shows the diff
    assert tool_drift.measured["description"] != tool_drift.expected["description"]
    assert tool_drift.fix


# --------------------------------------------------------------------------
# pending_install handling
# --------------------------------------------------------------------------


def test_pending_install_server_is_a_warning_not_a_pass(tmp_path):
    servers_path = tmp_path / "mcp-servers.json"
    lock_path = tmp_path / "mcp-lock.json"
    config = lock_module.ServerConfig(id="not-yet", command=["PENDING_INSTALL"], pending_install=True)
    _write_servers_config(servers_path, config)
    results = lock_module.run_mcp_checks(servers_path, lock_path, timeout=5)
    assert len(results) == 1
    assert results[0].status == "warn"
    assert results[0].status != "pass"


def test_missing_lock_entry_for_a_real_server_FAILS_closed(fake_server_argv, tmp_path):
    servers_path = tmp_path / "mcp-servers.json"
    lock_path = tmp_path / "mcp-lock.json"  # never written -> empty lock
    config = _server_config(fake_server_argv, id="fake")
    _write_servers_config(servers_path, config)
    results = lock_module.run_mcp_checks(servers_path, lock_path, timeout=5)
    assert results[0].status == "fail"
    assert "no lock entry" in results[0].measured.lower()


# --------------------------------------------------------------------------
# --quick caching
# --------------------------------------------------------------------------


def test_quick_mode_skips_probe_without_a_fresh_cache(fake_server_argv, tmp_path):
    servers_path = tmp_path / "mcp-servers.json"
    lock_path = tmp_path / "mcp-lock.json"
    config = _server_config(fake_server_argv, id="fake")
    entry = lock_module.probe_and_build_entry(config, timeout=5)
    lock_module.save_lock(
        lock_path,
        {"schema": 1, "generated_at": "x", "servers": {"fake": entry}, "lock_hash": "sha256:x"},
    )
    _write_servers_config(servers_path, config)

    results = lock_module.run_mcp_checks(servers_path, lock_path, timeout=5, quick=True)
    assert results[0].status == "skip"


def test_quick_mode_uses_a_cache_younger_than_24h(fake_server_argv, tmp_path):
    servers_path = tmp_path / "mcp-servers.json"
    lock_path = tmp_path / "mcp-lock.json"
    config = _server_config(fake_server_argv, id="fake")
    entry = lock_module.probe_and_build_entry(config, timeout=5)
    lock_module.save_lock(
        lock_path,
        {"schema": 1, "generated_at": "x", "servers": {"fake": entry}, "lock_hash": "sha256:x"},
    )
    _write_servers_config(servers_path, config)

    # A full run populates the cache.
    full = lock_module.run_mcp_checks(servers_path, lock_path, timeout=5, quick=False)
    assert full[0].status == "pass"

    quick = lock_module.run_mcp_checks(servers_path, lock_path, timeout=5, quick=True)
    assert quick[0].status == "pass"  # reused from cache, not skipped
