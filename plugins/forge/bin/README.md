# Forge supply-chain / health-check CLI

Standard-library-only Python 3.12+. No install step: run `forge` and
`forge-mcp-guard` with a bare `python3`.

## `forge doctor`

Exits **0** (all good), **1** (a check failed), or **2** (internal error --
fail closed, never a silent 0).

```
forge doctor [--quick] [--json] [--manifest PATH] [--lock PATH]
```

- **a.** Claude Code version floor (terminal CLI, plus any Desktop-bundled
  CLI under `~/Library/Application Support/Claude*/`); floor pinned once
  in `forge.version_check.MIN_CLAUDE_CODE_VERSION`.
- **b.** Pinned tool versions from `plugins/forge/toolchain/manifest.json`
  (or `--manifest`): runs each `version_cmd`, checks `version_regex`,
  fails on a missing binary, a version mismatch, or an unpinned entry.
- **c.** MCP servers in `security/mcp-servers.json`, probed and compared
  against `security/mcp-lock.json` (or `--lock`). `"pending_install":
  true` is a **warning**, never a pass. `--quick` skips this probe unless
  a cached result under 24h old exists.
- **d.** Forge's own protected files (`security/files-lock.json`).

Every failure states the rule, measured vs. expected, and how to fix it.

## `forge lock mcp` / `forge lock files`

```
forge lock mcp [--server ID] [--write]
forge lock files [--write]
```

Probes MCP server(s) (or hashes the tracked file set) and prints the
canonical entry; without `--write` it's a dry run.

**Only a human runs `--write`, never an agent.** Writing the lock *is* the
approval step -- it's what tells `doctor`/`forge-mcp-guard` to trust a
definition going forward. Review the printed diff first.

## `forge-mcp-guard`

```
forge-mcp-guard --server ID [--lock PATH] -- <real command argv...>
```

Stdio proxy in front of a real MCP server. Refuses to start if the lock
has no entry for `ID` (exit 2); re-verifies every list response and
`instructions` against the lock, replacing a mismatch with JSON-RPC
`-32001`; rejects `tools/call` for any unlisted tool; drops non-JSON-RPC
noise instead of forwarding or crashing on it.

## Tests

`uv run --with pytest pytest plugins/forge/tests/` -- see
`plugins/forge/tests/RESULTS.md` for the last run's summary.
