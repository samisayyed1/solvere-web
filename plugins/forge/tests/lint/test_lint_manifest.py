"""Tests for `forge lint manifest` (ADR-001 SS3, CONTRACTS.md SS1)."""

from __future__ import annotations

import json

from forge.lintlib import manifest


def _status(results, check_id):
    for r in results:
        if r.id == check_id:
            return r
    raise AssertionError(f"no result with id {check_id!r} in {[r.id for r in results]}")


def _write_plugin_json(repo_root, data):
    d = repo_root / "plugins" / "forge" / ".claude-plugin"
    d.mkdir(parents=True, exist_ok=True)
    (d / "plugin.json").write_text(json.dumps(data))


def _write_marketplace_json(repo_root, data):
    d = repo_root / ".claude-plugin"
    d.mkdir(parents=True, exist_ok=True)
    (d / "marketplace.json").write_text(json.dumps(data))


def test_plugin_json_missing_is_SKIP(tmp_path):
    results = manifest.lint_manifest(tmp_path / "plugins" / "forge", tmp_path)
    assert _status(results, "manifest.plugin_json").status == "skip"


def test_plugin_json_without_hooks_or_agents_keys_PASSES(tmp_path):
    _write_plugin_json(tmp_path, {"name": "forge", "version": "0.1.0"})
    results = manifest.lint_manifest(tmp_path / "plugins" / "forge", tmp_path)
    assert _status(results, "manifest.no_hooks_agents_keys").status == "pass"


def test_plugin_json_with_hooks_key_FAILS(tmp_path):
    _write_plugin_json(tmp_path, {"name": "forge", "hooks": "./hooks/hooks.json"})
    results = manifest.lint_manifest(tmp_path / "plugins" / "forge", tmp_path)
    r = _status(results, "manifest.no_hooks_agents_keys")
    assert r.status == "fail"
    assert r.measured == ["hooks"]


def test_plugin_json_with_agents_key_FAILS(tmp_path):
    _write_plugin_json(tmp_path, {"name": "forge", "agents": "./agents"})
    results = manifest.lint_manifest(tmp_path / "plugins" / "forge", tmp_path)
    r = _status(results, "manifest.no_hooks_agents_keys")
    assert r.status == "fail"
    assert r.measured == ["agents"]


def test_plugin_json_malformed_json_FAILS(tmp_path):
    d = tmp_path / "plugins" / "forge" / ".claude-plugin"
    d.mkdir(parents=True)
    (d / "plugin.json").write_text("{not valid json")
    results = manifest.lint_manifest(tmp_path / "plugins" / "forge", tmp_path)
    assert _status(results, "manifest.plugin_json_parse").status == "fail"


def test_marketplace_json_missing_is_SKIP(tmp_path):
    _write_plugin_json(tmp_path, {"name": "forge"})
    results = manifest.lint_manifest(tmp_path / "plugins" / "forge", tmp_path)
    assert _status(results, "manifest.marketplace_json").status == "skip"


def test_marketplace_name_not_reserved_PASSES(tmp_path):
    _write_marketplace_json(tmp_path, {"name": "forge-local", "plugins": []})
    results = manifest.lint_manifest(tmp_path / "plugins" / "forge", tmp_path)
    assert _status(results, "manifest.marketplace_name").status == "pass"


def test_marketplace_name_reserved_official_FAILS(tmp_path):
    _write_marketplace_json(tmp_path, {"name": "claude-plugins-official", "plugins": []})
    results = manifest.lint_manifest(tmp_path / "plugins" / "forge", tmp_path)
    assert _status(results, "manifest.marketplace_name").status == "fail"


def test_marketplace_name_reserved_anthropic_prefix_FAILS(tmp_path):
    _write_marketplace_json(tmp_path, {"name": "anthropic-internal", "plugins": []})
    results = manifest.lint_manifest(tmp_path / "plugins" / "forge", tmp_path)
    assert _status(results, "manifest.marketplace_name").status == "fail"


def test_plugin_source_dir_exists_PASSES(tmp_path):
    (tmp_path / "plugins" / "forge").mkdir(parents=True)
    _write_marketplace_json(tmp_path, {"name": "forge-local", "plugins": [{"name": "forge", "source": "./plugins/forge"}]})
    results = manifest.lint_manifest(tmp_path / "plugins" / "forge", tmp_path)
    assert _status(results, "manifest.plugin_sources_exist").status == "pass"


def test_plugin_source_dir_missing_FAILS(tmp_path):
    _write_marketplace_json(
        tmp_path, {"name": "forge-local", "plugins": [{"name": "forge", "source": "./plugins/does-not-exist"}]}
    )
    results = manifest.lint_manifest(tmp_path / "plugins" / "forge", tmp_path)
    r = _status(results, "manifest.plugin_sources_exist")
    assert r.status == "fail"
    assert r.measured == ["./plugins/does-not-exist"]
