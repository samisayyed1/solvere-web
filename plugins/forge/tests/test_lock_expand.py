"""Portable MCP launch specs (ADR-001 §8.L): the lock stores ${FORGE_HOME}/${REPO_ROOT}
tokens and only the spawned process sees real paths."""

from __future__ import annotations

import json
from pathlib import Path

from forge import lock

REPO = Path(__file__).resolve().parents[3]


def test_tokens_expand_to_this_machine(monkeypatch, tmp_path):
    monkeypatch.setenv("FORGE_HOME", str(tmp_path / "fh"))
    monkeypatch.setenv("FORGE_REPO_ROOT", str(tmp_path / "repo"))
    out = lock.expand_argv(["${FORGE_HOME}/bin/srt", "--settings", "${REPO_ROOT}/security/srt/x.json", "--flag"])
    assert out == [f"{tmp_path}/fh/bin/srt", "--settings", f"{tmp_path}/repo/security/srt/x.json", "--flag"]


def test_unexpanded_default_repo_root_is_this_checkout(monkeypatch):
    monkeypatch.delenv("FORGE_REPO_ROOT", raising=False)
    assert lock.expand_argv(["${REPO_ROOT}"]) == [str(REPO)]


def test_committed_server_config_is_machine_independent():
    text = (REPO / "security" / "mcp-servers.json").read_text()
    assert "/Users/" not in text and "/root/" not in text and "/home/" not in text
    for s in json.loads(text)["servers"]:
        assert s["command"][0].startswith("${FORGE_HOME}/"), s["id"]


def test_probe_launches_expanded_argv_but_lock_entry_keeps_tokens(monkeypatch, tmp_path):
    from forge.mcp_probe import ProbeResult
    import dataclasses

    seen: list[list[str]] = []

    def fake_probe(argv, **_kw):
        seen.append(list(argv))
        fields = {f.name: None for f in dataclasses.fields(ProbeResult)}
        fields.update(tools=[], prompts=[], resources=[], resource_templates=[],
                      server_info={}, capabilities={})
        return ProbeResult(**fields)

    monkeypatch.setattr(lock, "probe_server", fake_probe)
    monkeypatch.setenv("FORGE_HOME", str(tmp_path / "fh"))
    entry = lock.probe_and_build_entry(lock.ServerConfig(id="x", command=["${FORGE_HOME}/bin/srt", "a"]))
    assert seen == [[f"{tmp_path}/fh/bin/srt", "a"]]  # the process sees real paths
    assert entry["launch"]["command"] == ["${FORGE_HOME}/bin/srt", "a"]  # the lock does not
