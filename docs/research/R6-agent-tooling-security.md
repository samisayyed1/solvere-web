# R6 — Security of agent tooling (MCP, skills, plugins, agent configs)

- Date accessed: 2026-09-25 · Author: research agent (Phase 1) · Scope: MCP spec security model, attack classes, 2025–2026 incidents, Claude Code trust/sandbox model, defences, and a concrete `security/mcp-lock.json` design for Forge on macOS.

Tag legend: **[V]** verified in a primary source (linked) · **[L]** verified locally (command given) · **[R]** reported by a secondary source · **[U]** unverified / not found.

Local baseline [L]: `claude --version` → `2.1.270 (Claude Code)`; `sw_vers` → macOS 15.3 (24D2059), arm64; `docker version` → client 29.1.3, Docker Desktop context present but daemon not running; `docker mcp version` → v0.35.0; `node` v24.19.0, `npm` 11.17.0, `uv` 0.11.17, `python3` 3.14.3; OrbStack, Lima, Tart, UTM and `srt` not installed (`command -v`).

## Summary

1. **Current MCP revision is `2026-07-28`** (released 2026-07-28, RC 2026-05-29). It makes the protocol stateless: the `initialize` handshake is gone, and a mandatory `server/discover` RPC replaces it. A tool-list probe therefore has to handle both protocol eras. [V] ([versioning](https://modelcontextprotocol.io/specification/versioning), [changelog](https://modelcontextprotocol.io/specification/2026-07-28/changelog), [release](https://github.com/modelcontextprotocol/modelcontextprotocol/releases/tag/2026-07-28))
2. **The MCP spec has no tool-definition signing or integrity mechanism.** Tool annotations are hints that clients MUST treat as untrusted unless the server is trusted. Proposals for digest pinning, signing or attestation (ETDI #649, SEP-1766, SEP-2395, SEP-3140) were closed; SEP-2809 (admission attestation) is still open. [V] ([tools](https://modelcontextprotocol.io/specification/2026-07-28/server/tools), [schema.ts](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/schema/2026-07-28/schema.ts), [SEP-1766](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1766))
3. **Claude Code does not detect or re-approve MCP tool-definition changes.** When a server sends `list_changed`, Claude Code refreshes tools, prompts and resources automatically. Approval of project `.mcp.json` servers is stored as a list of server **names**. Neither the docs nor the CHANGELOG (through 2.1.282) mention a hash, a diff or re-approval. **Forge's lock and runtime guard would be the only rug-pull detector.** [V] docs + [L] CHANGELOG search
4. **Claude Code's sandbox covers Bash only.** MCP servers and command hooks run as unconstrained host processes. To contain them, run the server itself under `srt` (sandbox-runtime), in a container or in a VM. [V] ([sandbox-environments](https://code.claude.com/docs/en/sandbox-environments))
5. **Headless runs skip workspace trust.** `claude -p` and the SDK never show the trust dialog. In a folder that was never trusted they run repo hooks and connect `.mcp.json` servers without asking. Any unattended Forge job needs `--strict-mcp-config`, `--setting-sources user` (or `--bare`) and `disableAllHooks`. [V] ([permissions](https://code.claude.com/docs/en/permissions#what-runs-before-you-trust-a-folder), [hooks](https://code.claude.com/docs/en/hooks#workspace-trust))
6. **Poisoned repo config files are the main attack class from 2025 to 2026.** Cases include Claude Code (CVE-2025-59536, CVE-2026-21852, CVE-2026-33068, CVE-2026-40068), Cursor (CVE-2025-54136 "MCPoison", CVE-2025-54135, CVE-2025-64109, CVE-2026-48124, where Cursor ran hooks from a `.claude/settings.local.json`), Codex CLI (CVE-2025-61260), Gemini CLI (GHSA-wpqr-6v78-jr5g) and Copilot (CVE-2025-53773). [V]
7. **The MCP and skill supply chain is being actively exploited:**
   - postmark-mcp (2025-09): a backdoor added in v1.0.16 after 15 clean releases.
   - Nx "s1ngularity" (2025-08): used installed AI CLIs with permission-bypass flags.
   - SANDWORM_MODE (2026-02): typosquatted Claude Code packages and planted a rogue MCP server in agent configs.
   - ClawHavoc / ToxicSkills (2026-02): hundreds of malicious ClawHub skills delivering macOS AMOS.
   - Mini Shai-Hulud (2026-05): reported to persist through `.claude/` and `.vscode/` files.

   [V]/[R] per item below.
8. **Allowed domains can still be used to exfiltrate data.** Claude Code CVE-2026-54316 used the pre-approved `huggingface.co` as a covert channel. CVE-2026-24052 was a `startsWith` domain check that could be bypassed. The sandbox docs warn that broad domains plus domain fronting defeat hostname allowlists. [V]
9. **Available defences:**
   - Scanners: Snyk Agent Scan (formerly Invariant `mcp-scan`) runs servers and **sends tool descriptions to Snyk's API**, and needs `SNYK_TOKEN`. Trail of Bits `mcp-context-protector` does trust-on-first-use pinning of instructions, descriptions and schemas at runtime (the closest existing model for Forge's lock).
   - Container isolation: Docker MCP Gateway runs servers in containers with signature checks, secret blocking and optional `--block-network`.
   - Pinning: npm 11 `min-release-age` and uv `--exclude-newer` give a release-age cooldown.

   [V]/[L]
10. **Recommendation.** Use a JCS (RFC 8785) + SHA-256 lock. It should cover the launch spec, the artifact integrity, server `instructions`, and full canonical tool, prompt, resource and skill definitions, with per-item hashes. Enforce it in two places: a `doctor` probe, and a stdio **guard proxy** that fails closed on drift at runtime. A doctor probe alone can be evaded by a server that fingerprints the probe. [design; see §Implications]

## Findings

### 1. MCP specification (current revision 2026-07-28)

**Revision and transports**
- The current revision is **2026-07-28**; earlier ones are 2025-11-25, 2025-06-18, 2025-03-26 and 2024-11-05. Version IDs mark the last backwards-incompatible change. [V] ([versioning](https://modelcontextprotocol.io/specification/versioning)); GitHub releases show `2026-07-28` published 2026-07-28 and `2026-07-28-RC` published 2026-05-29. [L] `gh api repos/modelcontextprotocol/modelcontextprotocol/releases`
- There are two standard transports, **stdio** and **Streamable HTTP**. HTTP+SSE is formally Deprecated. [V] ([transports](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports), [deprecated](https://modelcontextprotocol.io/specification/2026-07-28/deprecated))
- On Streamable HTTP, servers MUST validate `Origin` against DNS rebinding and SHOULD bind to 127.0.0.1 when running locally. [V] ([streamable-http](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http))
- **2026-07-28 breaking changes:**
  - No `initialize` handshake and no sessions. Version and capabilities travel in each request's `_meta`.
  - A mandatory `server/discover` RPC.
  - `subscriptions/listen` replaces the GET stream.
  - The MRTR pattern replaces server-initiated requests.
  - `tools/list` MUST NOT vary per connection (it MAY vary by authorization) and SHOULD be returned in deterministic order.
  - List results carry the required cache fields `ttlMs` and `cacheScope`.

  [V] ([changelog](https://modelcontextprotocol.io/specification/2026-07-28/changelog), [tools](https://modelcontextprotocol.io/specification/2026-07-28/server/tools))
- **Talking to older servers.** A client that supports both eras SHOULD probe with `server/discover` first. It falls back to `initialize` on any other error or timeout, and the fallback MUST NOT key on one specific error code. [V] ([stdio](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/stdio))
- **Model-visible surfaces beyond tools** (all must be locked):
  - `instructions` in the `server/discover` / `initialize` result.
  - prompts, resources and resource templates.
  - `_meta` on tools.
  - `skill://` resources under the **Skills Extension** (SEP-2640, merged 2026-09-13).

  [V] ([discover](https://modelcontextprotocol.io/specification/2026-07-28/server/discover), [SEP-2640](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2640))
- Roots, Sampling, Logging and Dynamic Client Registration were deprecated in 2026-07-28. Their earliest removal is the first revision released on or after 2027-07-28. [V] ([deprecated](https://modelcontextprotocol.io/specification/2026-07-28/deprecated))

**Authorization model** (HTTP transports only; stdio servers SHOULD take credentials from the environment instead) [V] ([authorization](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization))
- Built on OAuth 2.1 (draft-ietf-oauth-v2-1-13). MCP servers are resource servers and MUST publish **Protected Resource Metadata (RFC 9728)**. Clients MUST use it to discover the authorization server, and MUST support both RFC 8414 and OIDC discovery. [V]
- **Resource indicators (RFC 8707):** clients MUST send `resource` set to the server's canonical URI. Servers MUST validate that the token audience is themselves. [V]
- **No token passthrough:** clients MUST NOT send tokens from other issuers, and servers MUST NOT accept or pass along any token that was not issued for them. Upstream calls use a separate token. [V] ([security-considerations](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization/security-considerations), [best practices](https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices))
- New in 2026-07-28:
  - Clients MUST validate `iss` (RFC 9207) when it is present.
  - Credentials are keyed by issuer.
  - Client ID Metadata Documents are preferred, and DCR is deprecated.

  [V] ([changelog](https://modelcontextprotocol.io/specification/2026-07-28/changelog))
- Token theft: secure storage is required, access tokens should be short-lived, and public clients MUST rotate refresh tokens. [V]
- Confused deputy: MCP proxy servers that use static client IDs MUST get user consent for each dynamically registered client. [V]

**Security best-practices page** (2026-07-28 edition) [V] ([link](https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices))
- Sections: confused deputy, token passthrough, SSRF, state-handle hijacking, local MCP server compromise, OAuth URL validation, stdio in proxy scenarios, mix-up, localhost redirect impersonation, CIMD trust, scope minimization.
- For local servers it asks clients to:
  - show the full command before one-click install;
  - run servers sandboxed with minimal privileges;
  - restrict filesystem and network access.
- It does **not** cover tool poisoning or rug pulls. An open docs PR #3072 proposes a "Local Server Security" guide. [V] ([PR #3072](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/3072))

**Tool annotations**
- The fields are `title`, `readOnlyHint` (default false), `destructiveHint` (default true), `idempotentHint` (default false) and `openWorldHint` (default true).
- The schema calls them hints that may not describe behaviour faithfully and warns against basing tool-use decisions on annotations from untrusted servers. The tools page says clients MUST treat them as untrusted unless the server is trusted. [V] ([schema.ts](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/schema/2026-07-28/schema.ts), [tools](https://modelcontextprotocol.io/specification/2026-07-28/server/tools))
- The spec asks for a human in the loop, for inputs to be shown before a call, for results to be validated, and for tool names to be de-duplicated with a server prefix. [V]

**2026 integrity and registry status**
- No signing or integrity checks for tool definitions exist in core or extensions. Closed proposals: ETDI PR #649 (closed 2025-09-24), SEP-1766 digest-pinned tool versioning (closed 2026-06-24), SEP-2395 MCPS, SEP-2267 attestation, SEP-3140 signed capability declarations. Still open: SEP-2809 "Attested Tool-Server Admission". [V] (`gh search prs/issues`, e.g. [SEP-2809](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2809))
- The **MCP Registry** is still in **preview**. What it does:
  - Authenticates namespaces (GitHub, DNS or HTTP) and verifies package ownership.
  - Delegates security scanning to npm, PyPI, Docker Hub and downstream aggregators.
  - Removes only malware, spam, illegal content and broken servers.
  - `server.json` `fileSha256` is required for MCPB packages and optional otherwise.

  [V] ([about](https://modelcontextprotocol.io/registry/about), [moderation](https://modelcontextprotocol.io/registry/moderation-policy), [requirements](https://github.com/modelcontextprotocol/registry/blob/main/docs/reference/server-json/official-registry-requirements.md), [schema](https://github.com/modelcontextprotocol/registry/blob/main/docs/reference/server-json/draft/server.schema.json))
- MCPB bundles support `mcpb sign` / `mcpb verify` at package level. This covers the package, not tool definitions. [V] ([mcpb CLI.md](https://github.com/modelcontextprotocol/mcpb/blob/main/CLI.md))
- Open community issue #3213 reports prompt injection through `server/discover` `instructions`, made worse by `cacheScope: public`. [V] ([#3213](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/3213)) The label "MCP-2026-015" is self-assigned by the reporter and is not an official advisory ID (see Discrepancies).

### 2. Attack classes (primary write-ups)

| Class | What it is | Primary source |
|---|---|---|
| Tool poisoning | Hidden instructions in tool descriptions: visible to the model, not shown to the user. Demonstrated leaking SSH keys and config via Cursor. | Invariant Labs, 2025-04-01 [V] ([blog](https://invariantlabs.ai/blog/mcp-security-notification-tool-poisoning-attacks)) |
| Rug pull | A server changes its descriptions after the user has approved it. Invariant recommends version pinning and checksums. | Same [V] |
| Tool shadowing / cross-server | One server's description rewrites how the agent uses a *different* trusted server's tools (e.g. redirecting email recipients). | Same [V] |
| Prompt injection via tool output | A malicious GitHub issue injects the agent through the GitHub MCP server, which then leaks private repo data into a public PR ("toxic agent flow"). | Invariant Labs, 2025-05-26 [V] ([blog](https://invariantlabs.ai/blog/mcp-github-vulnerability)) |
| Lethal trifecta | Private data + untrusted content + an outbound channel together make exfiltration trivial. Mixing MCP tools tends to assemble all three. | S. Willison, 2025-06-16 [V] ([post](https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/)) |
| Confused deputy / token passthrough | OAuth proxy abuse with static client IDs; tokens accepted for the wrong audience. | MCP spec best practices [V] |
| Token theft / client RCE via OAuth metadata | `mcp-remote` executed OS commands built from a malicious `authorization_endpoint` (CVE-2025-6514, fixed 0.1.16). | [GHSA-6xpm-ggf7-wc3p](https://github.com/advisories/GHSA-6xpm-ggf7-wc3p), JFrog [V] |
| Local server exposure | MCP Inspector's proxy had no auth, so any web page could reach it and get RCE (CVE-2025-49596, fixed 0.14.1). | [GHSA-7f8r-222p-6f5g](https://github.com/advisories/GHSA-7f8r-222p-6f5g) [V] |
| Server-side path bypass | Reference filesystem server let prefix collisions and symlinks escape its allowed directories (CVE-2025-53109/53110, fixed 2025.7.1). | [GHSA-q66q-fx2p-7w4m](https://github.com/advisories/GHSA-q66q-fx2p-7w4m) [V] |
| Supply chain (malicious package) | postmark-mcp npm impersonation silently BCC'd every email. Backdoor added in v1.0.16 after 15 clean versions. Postmark had not published on npm. | [Postmark advisory](https://postmarkapp.com/blog/information-regarding-malicious-postmark-mcp-package), 2025-09-25 [V]. Discovered by Koi Security, ~1,500 weekly downloads [R] ([THN](https://thehackernews.com/2025/09/first-malicious-mcp-server-found.html)). npm now returns "Unpublished on 2025-09-25" [L] `npm view postmark-mcp` |
| Exfiltration via allowed domains | Pre-approved `huggingface.co` in Claude Code WebFetch used as a covert download-count channel (CVE-2026-54316). Domain check done with `startsWith` (CVE-2026-24052). | [GHSA-fg94-h982-f3mm](https://github.com/anthropics/claude-code/security/advisories/GHSA-fg94-h982-f3mm), [GHSA-vhw5-3g5m-8ggf](https://github.com/anthropics/claude-code/security/advisories/GHSA-vhw5-3g5m-8ggf) [V] |

### 3. 2025–2026 incidents: poisoned agent configs, malicious skills, worms

| Date | Incident | What happened | Primary source | Mitigation |
|---|---|---|---|---|
| 2025-03-18 | Rules File Backdoor (Cursor, Copilot) | Hidden Unicode (zero-width, bidi) instructions in rules files steer code generation. Cursor treated it as the user's responsibility. GitHub added a hidden-Unicode warning (2025-05-01). | [Pillar Security](https://www.pillar.security/blog/new-vulnerability-in-github-copilot-and-cursor-how-hackers-can-weaponize-code-agents) [V] | Scan agent config and rules files for invisible characters; review them like code |
| 2025-07-25/28 | Gemini CLI allowlist + README injection | Weak prefix allowlist, injection hidden in README "licence" text, whitespace hiding the payload. Fixed v0.1.14. | [Tracebit](https://tracebit.com/blog/code-exec-deception-gemini-ai-cli-hijack) [V] | Upgrade; sandbox |
| 2025-08-01/05 | Cursor **MCPoison** CVE-2025-54136 | MCP approval was tied to the server **name**, so an approved `.mcp.json` entry could be swapped for a malicious command without a new prompt. Fixed in 1.3 by re-approving on any change. | [GHSA-24mc-g4xr-4395](https://github.com/cursor/cursor/security/advisories/GHSA-24mc-g4xr-4395), [Check Point](https://research.checkpoint.com/2025/cursor-vulnerability-mcpoison/) [V] | Bind approval to a content hash |
| 2025-08-02 | Cursor CurXecute CVE-2025-54135 | Agent could *create* a missing `.cursor/mcp.json` without approval, so prompt injection led to RCE. | [GHSA-4cxx-hrm3-49rm](https://github.com/cursor/cursor/security/advisories/GHSA-4cxx-hrm3-49rm) [V] | Protect config paths from agent writes |
| 2025-08-12 | Copilot CVE-2025-53773 | Injection writes `chat.tools.autoApprove: true` into `.vscode/settings.json`, enabling "YOLO" mode and RCE. | [Embrace The Red](https://embracethered.com/blog/posts/2025/github-copilot-remote-code-execution-via-prompt-injection), [GHSA-3m2x-p87c-pwv6](https://github.com/advisories/GHSA-3m2x-p87c-pwv6) [V] | Agent may not edit its own security settings |
| 2025-08-26 | Nx **s1ngularity** (CVE-2025-10894) | Malicious `nx` postinstall stole credentials to public GitHub repos and appended `sudo shutdown` to shell rc files. It also ran a file-search prompt through local AI CLIs. | [GHSA-cxm3-wv7p-598c](https://github.com/advisories/GHSA-cxm3-wv7p-598c) [V]. Flags used were `claude --dangerously-skip-permissions`, `gemini --yolo`, `q --trust-all-tools` [R] ([StepSecurity](https://www.stepsecurity.io/blog/supply-chain-security-alert-popular-nx-build-system-package-compromised-with-data-stealing-malware)) | Don't leave permission-bypass flags usable outside a sandbox; `--ignore-scripts`; release-age cooldown |
| 2025-09-23 | Shai-Hulud npm worm | Self-replicating: 500+ packages, credential theft, republishing. | [CISA](https://www.cisa.gov/news-events/alerts/2025/09/23/widespread-supply-chain-compromise-impacting-npm-ecosystem) [V] | Pin versions, rotate credentials, phishing-resistant MFA |
| 2025-09-25 | postmark-mcp | See §2. | [V] | Pin exact versions and integrity hashes; allowlist egress |
| 2025-10-03 → 2026-04-24 | Claude Code trust-boundary CVEs | CVE-2025-59536: project code ran before the trust dialog. CVE-2026-21852: `ANTHROPIC_BASE_URL` in repo settings leaked API keys before trust. CVE-2026-33068: repo `.claude/settings.json` `defaultMode: bypassPermissions` skipped the trust dialog. CVE-2026-40068: a worktree `commondir` pointing at a trusted path ran `.claude/settings.json` hooks. | [Claude Code advisories](https://github.com/anthropics/claude-code/security/advisories), [Check Point 2026-02-25](https://research.checkpoint.com/2026/rce-and-api-token-exfiltration-through-claude-code-project-files-cve-2025-59536/) [V] | All fixed by ≤2.1.84. Local 2.1.270 is above every patched version [L] |
| 2025-11-03 | Cursor CLI CVE-2025-64109 | A repo `.cursor/mcp.json` server ran without any prompt in Cursor CLI. | [GHSA-4hwr-97q3-37w2](https://github.com/cursor/cursor/security/advisories/GHSA-4hwr-97q3-37w2) [V] | Prompt before enabling |
| 2025-11-24 | Shai-Hulud 2.0 | ~800 packages; preinstall stage using `setup_bun.js`; GitHub Actions persistence. Wiz found no AI-config targeting. | [Wiz](https://www.wiz.io/blog/shai-hulud-2-0-ongoing-supply-chain-attack) [V] | Restrict lifecycle scripts; limit build egress |
| 2025-12-01 (CVE record 2026-04-14) | Codex CLI CVE-2025-61260 | A repo `.env` set `CODEX_HOME=./.codex`; MCP commands in `./.codex/config.toml` ran at startup without approval. | [Check Point](https://research.checkpoint.com/2025/openai-codex-cli-command-injection-vulnerability/), [GHSA-xrxf-jgv3-qmrm](https://github.com/advisories/GHSA-xrxf-jgv3-qmrm) [V] | Upgrade; distrust repo `.env` |
| 2026-02-05 | Snyk **ToxicSkills** | 3,984 skills from ClawHub and skills.sh: 36.82% had at least one flaw, 76 were confirmed malicious. | [Snyk](https://snyk.io/blog/toxicskills-malicious-ai-agent-skills-clawhub/) [V] | Scan and review skills; isolate |
| 2026-02 (THN) / 2026-02-23 (Trend) | **ClawHavoc** (OpenClaw/ClawHub) | 341 of 2,857 skills malicious; 335 used fake "prerequisites" to install **Atomic macOS Stealer** (keychain, browser, wallet theft). Later counts reached 824 and 1,184. | Trend Micro/TrendAI [V] ([blog](https://www.trendaisecurity.com/en-us/resources-insights/trendai-security-blog/malicious-openclaw-skills-used-to-distribute-atomic-macos-stealer)). Koi count [R] ([THN](https://thehackernews.com/2026/02/researchers-find-341-malicious-clawhub.html)); Koi's original URL now redirects to a Palo Alto Networks product page [L] | Isolated testing; never let a skill install prerequisites |
| 2026-02-20 | **SANDWORM_MODE** npm worm | 19 packages including typosquats `claud-code`, `cloude-code`, `cloude`. Writes a rogue MCP server into Claude Desktop/Code, Cursor, Continue and Windsurf configs; its tool descriptions tell the agent to collect SSH, AWS and npm secrets. Exfiltrates over HTTPS, the GitHub API and DNS. | [Socket](https://socket.dev/blog/sandworm-mode-npm-worm-ai-toolchain-poisoning) [V] | Lock detects *new* servers; config-file integrity checks |
| 2026-05-11/12 | **Mini Shai-Hulud** (TanStack and others) | 84 malicious versions of 42 `@tanstack/*` packages published through a legitimate OIDC trusted publisher: Pwn Request, then cache poisoning, then OIDC token extraction. | [GHSA-g7cv-rxg3-hmpx](https://github.com/advisories/GHSA-g7cv-rxg3-hmpx) [V]. Persistence via `.claude/` hooks, `.vscode/tasks.json` and MCP configs [R] ([Akamai](https://www.akamai.com/blog/security-research/mini-shai-hulud-worm-returns-goes-public); a TanStack issue comment lists `.claude/setup.mjs` [R]) | Provenance alone is not enough; cooldown + config integrity |
| 2026-05-21 | Cursor CVE-2026-48124 | **Cursor ran Claude hook commands from `.claude/settings.local.json`** without approval. | [GHSA-pc9j-3qc2-95wv](https://github.com/cursor/cursor/security/advisories/GHSA-pc9j-3qc2-95wv) [V] | Forge's `.claude/` files are an attack surface for *other* tools too |
| 2026-06-25 | Claude Code CVE-2026-55607 | **Seatbelt sandbox escape** on macOS via git worktree path confusion + fsmonitor: overwrite `~/.zshenv`. Fixed 2.1.163. | [GHSA-7835-87q9-rgvv](https://github.com/anthropics/claude-code/security/advisories/GHSA-7835-87q9-rgvv) [V] | Sandbox is defence in depth, not a boundary |

Other Claude Code sandbox escapes: CVE-2026-39861 (symlink; fixed 2.1.64) and CVE-2026-25725 (bubblewrap, a missing `settings.json` could be created with persistent hooks; fixed 2.1.2). [V] ([advisories list](https://github.com/anthropics/claude-code/security/advisories); [L] `gh api repos/anthropics/claude-code/security-advisories` → 30 advisories, newest 2026-06-25)

### 4. Claude Code specifics (docs at code.claude.com; local 2.1.270; docs/CHANGELOG describe up to 2.1.282)

- **Trust dialog.** New codebases and new MCP servers require trust. Trust verification is **disabled with `-p`**, and trust in the home directory is session-only. [V] ([security](https://code.claude.com/docs/en/security))
- **What runs before trust.** In an interactive session, hooks from every settings file wait for trust.

  Under `-p`/SDK the folder counts as trusted, so:
  - repo hooks run;
  - `.mcp.json` servers connect "approved or not";
  - the `env` block and helpers apply;
  - a skill's `allowed-tools` is never gated by trust.

  [V] ([permissions](https://code.claude.com/docs/en/permissions#what-runs-before-you-trust-a-folder), [hooks](https://code.claude.com/docs/en/hooks#workspace-trust))
- **Project `.mcp.json` approval.**
  - Interactive sessions prompt for each server.
  - `enableAllProjectMcpServers` / `enabledMcpjsonServers` committed in a repo are ignored until trust (v2.1.196+).
  - `enabledMcpjsonServers` is a list of **server names**.
  - `disabledMcpjsonServers` always rejects.
  - `claude mcp reset-project-choices` clears approvals.

  [V] ([mcp](https://code.claude.com/docs/en/mcp#project-server-approvals-and-workspace-trust), [settings-reference](https://code.claude.com/docs/en/settings-reference)); [L] `claude mcp --help`
- **Tool-definition change detection: none documented.** "Dynamic tool updates" says Claude Code refreshes tools, prompts and resources on `list_changed` with no approval step. The CHANGELOG through 2.1.282 has no hashing, pinning or re-approval entry; one fix even makes prompts and resources refresh when `listChanged` wasn't declared. [V] ([mcp#dynamic-tool-updates](https://code.claude.com/docs/en/mcp#dynamic-tool-updates)); [L] `grep -i 'rug|tool definition|re-approv|list_changed' CHANGELOG.md`
  - Whether Claude Code re-prompts when an approved `.mcp.json` entry's *command* changes (the MCPoison pattern) is **not documented** [U]. Approval appears to be name-keyed [V], so treat it as not re-prompted.
- **Descriptions are capped.** Tool descriptions and server instructions are truncated at 2,048 characters. `CLAUDE_CODE_MAX_MCP_DESCRIPTION_LENGTH` needs v2.1.280. With tool search, only tool names and server `instructions` load at session start. [V] ([mcp](https://code.claude.com/docs/en/mcp#scale-with-mcp-tool-search))
- **Sandbox scope.**
  - The built-in sandbox covers Bash, PowerShell and Monitor commands and their children.
  - Read, Edit and WebFetch are governed by permission rules instead.
  - **MCP servers and command hooks run unconstrained on the host.**
  - To contain everything, run Claude Code (or each MCP server) under `@anthropic-ai/sandbox-runtime`, a dev container, a container or a VM.

  [V] ([sandbox-environments](https://code.claude.com/docs/en/sandbox-environments), [sandboxing#scope](https://code.claude.com/docs/en/sandboxing#scope)). Hook docs repeat that hook commands run unsandboxed [V] ([hooks](https://code.claude.com/docs/en/hooks)).
- **Sandbox network.** Traffic goes through a proxy that allowlists by hostname and does not inspect TLS by default. `strictAllowlist` (v2.1.219+, user/managed/CLI only) denies instead of prompting; `allowManagedDomainsOnly` does the same from managed settings. The docs warn that broad domains plus **domain fronting** can defeat the allowlist, and that allowing the Docker socket through `allowUnixSockets` is a host escape. [V] ([sandboxing](https://code.claude.com/docs/en/sandboxing))
- **Protected paths.** The sandbox denies writes to `.claude` settings, skills, agents, commands and hooks, to `.mcp.json`, and to shell rc files and `.git/hooks`/`config`, even inside allowed directories. [V]
- **Sandbox fallback.** `failIfUnavailable` blocks startup when the sandbox can't run. `allowUnsandboxedCommands: false` disables the `dangerouslyDisableSandbox` retry. [V]
- **Credentials.**
  - API keys and OAuth tokens live in the macOS Keychain. [V] ([security](https://code.claude.com/docs/en/security))
  - `.mcp.json` supports `${VAR}` and `${VAR:-default}` expansion.
  - Credential variables read as **empty** in a remote server's `url`/`headers`, so a repo or plugin can't send your Anthropic or cloud credentials to a server it names.
  - `headersHelper` from a repo or plugin runs without credential env vars and only after trust (v2.1.238+).

  [V] ([mcp](https://code.claude.com/docs/en/mcp#environment-variable-expansion-in-mcp-json))
  - `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1` strips credentials from Bash, hooks and **MCP stdio servers**. [V] ([env-vars](https://code.claude.com/docs/en/env-vars))
  - `sandbox.credentials` can deny or mask secrets. Masking only works from user or managed settings. [V]
- **Permission rules and managed control.**
  - Rules take the forms `mcp__server`, `mcp__server__*` and `mcp__server__tool`.
  - A tool whose `_meta["anthropic/requiresUserInteraction"]` is true always prompts, whatever the allow rules or mode.
  - Managed `allowedMcpServers` / `deniedMcpServers` match on `serverCommand` (exact argv) or `serverUrl`; `serverName` "is not a security control".
  - `allowManagedMcpServersOnly` and `managed-mcp.json` give exclusive control. On macOS these files live in `/Library/Application Support/ClaudeCode/`.

  [V] ([permissions](https://code.claude.com/docs/en/permissions), [mcp](https://code.claude.com/docs/en/mcp#require-approval-for-a-specific-tool), [managed-mcp](https://code.claude.com/docs/en/managed-mcp), [managed-settings](https://code.claude.com/docs/en/managed-settings))
- **Hook provenance.** Hook input for MCP tools carries `mcp_server.source` (plugin, sdk, user, project, …) from v2.1.274. That is **newer than the local 2.1.270**. [V]
- **Headless and lockdown CLI flags** [L] (`claude --help`):
  - `--strict-mcp-config`: only use `--mcp-config` servers.
  - `--setting-sources`
  - `--bare`: skips hooks, plugins, CLAUDE.md discovery and keychain reads.
  - `--restricted`: removes code-running tools and WebFetch, ignores user/project/local settings, refuses `bypassPermissions`.
  - `--disallowed-tools`
- **Plugins.**
  - Plugins "can execute arbitrary code" with user privileges. Anthropic doesn't control or verify their MCP servers.
  - `claude-plugins-community` is automatically screened and **pinned to commit SHAs**.
  - Marketplace entries can pin `sha`.
  - Official marketplaces **auto-update by default**, which is a rug-pull channel. `DISABLE_AUTOUPDATER` disables it.
  - `strictKnownMarketplaces` restricts which sources can be added.

  [V] ([discover-plugins](https://code.claude.com/docs/en/discover-plugins), [plugin-marketplaces](https://code.claude.com/docs/en/plugin-marketplaces))
- **`claude plugin eval` caveats** (needs v2.1.269+):
  - Each run gets a throwaway home and config under `claude -p`.
  - Granted Bash is sandboxed.
  - The plugin's **hooks and real MCP servers run outside the sandbox and can reach any host**.
  - `--scaffold` scripts run as you.
  - A passing suite is not a security vetting.

  [V] ([plugin-evals](https://code.claude.com/docs/en/plugin-evals)); [L] `claude plugin --help`
- **Advisory floor.** Every published Claude Code advisory is patched at or below 2.1.163. Local 2.1.270 is above all of them. [L] (advisory JSON compared with `claude --version`)

### 5. Defences and tools

**Pinning**
- npm: pin with `npx -y pkg@x.y.z`. That fixes the top-level version only; transitive dependencies float unless you use a lockfile (`npm ci` with `integrity` sha512) or `npm-shrinkwrap.json`. npm 11.17 has `min-release-age` (days; "complement to `before`"), `ignore-scripts` and `allow-git`. [L] `npm config ls -l`; `npm/docs/content/using-npm/config.md`
- uv: `uvx pkg==x.y.z` or `--from pkg==x.y.z`. `--exclude-newer` and `--exclude-newer-package` limit to uploads before a date; `--constraints`, `--no-build` and `pip --require-hashes` are available. [L] `uvx --help`, `uv help pip install`
- Containers: OCI images by **digest**. Docker MCP Gateway requires a digest and verifies signatures for `mcp/` images. [V] ([docker/mcp-gateway security.md](https://github.com/docker/mcp-gateway/blob/main/docs/security.md))
- Git and plugins: full 40-char commit SHA (marketplace `sha`). [V]

**Scanners and runtime guards (status 2026-09)**
- **Snyk Agent Scan** (`snyk/agent-scan`, formerly Invariant `mcp-scan`; Invariant was acquired by Snyk in June 2025 [R]).
  - Latest v0.6.4 (2026-09-21). Needs `SNYK_TOKEN`.
  - **Runs** discovered MCP servers (asking for consent interactively) and **sends tool names, descriptions and skill content to Snyk's API**, with secrets redacted.
  - `inspect` lists components without analysis.
  - `guard` installs Claude Code hooks.
  - Current docs say nothing about rug-pull or baseline diffing [U].

  [V] ([README](https://github.com/snyk/agent-scan), [cli-reference](https://github.com/snyk/agent-scan/blob/main/docs/cli-reference.md))
- **Trail of Bits `mcp-context-protector`.**
  - A wrapper that pins server config on first use: instructions, tool descriptions and input schemas.
  - Compares **semantically**, ignoring ordering.
  - **Blocks tool calls on drift**, including after `list_changed`, until approved in the CLI.
  - Optional guardrail quarantine for responses; strips ANSI.
  - Last push 2026-04.

  [V] ([README](https://github.com/trailofbits/mcp-context-protector))
- **Cisco `mcp-scanner`**: active, 4.8.4 (2026-08-28). [V] repo metadata; features not reviewed [U].
- **MCP Inspector CLI** (`@modelcontextprotocol/inspector --cli … --method tools/list`, `--protocol-era legacy|auto|modern`) can list tools deterministically. v2.8.0. It **stores stdio `env` secrets in plaintext** when no OS keychain is available. [V] ([cli README](https://github.com/modelcontextprotocol/inspector/blob/main/clients/cli/README.md)); [L] `npm view`

**Sandbox options on macOS**

| Option | Isolates | Notes |
|---|---|---|
| Built-in Bash sandbox (Seatbelt) | Bash, PowerShell, Monitor only | MCP servers and hooks unconstrained; had escape CVE-2026-55607 [V] |
| `@anthropic-ai/sandbox-runtime` (`srt`) | Any process, e.g. `srt npx -y server` | Seatbelt profile + HTTP/SOCKS proxy allowlist; network denied by default; beta (v0.0.77); now at `anthropics/sandbox-runtime` [V] ([README](https://github.com/anthropics/sandbox-runtime)). Uses `sandbox-exec`, which Apple's man page marks **DEPRECATED** [L] `man sandbox-exec` |
| Docker Desktop / Docker MCP Gateway | Containers inside a Linux VM | Host env not passed; `no-new-privileges`; CPU and memory limits; read-only binds under trusted roots; secret blocking on by default; egress **not** denied by default (`--block-network`/`allowHosts`) [V]. Daemon not running locally; `docker mcp` v0.35.0 vs upstream v0.44.1 [L] |
| Dev container | Whole Claude Code | Reference image has a default-deny iptables firewall; team convention, not enforced [V] ([devcontainer](https://code.claude.com/docs/en/devcontainer)) |
| Docker Sandboxes (`sbx`) | microVM per agent | Docs describe microVM isolation plus network and MCP policies; details thin [V] ([docs](https://docs.docker.com/ai/sandboxes/)) |
| VM: Lima / Tart / UTM | Full OS | Strongest local option; heavier. Tart repo now resolves to `openai/tart` [L] `gh api repos/cirruslabs/tart`. None installed [L] |

A likely problem for Forge: CAD and EDA MCP servers usually drive **macOS GUI apps** (KiCad, FreeCAD, Fusion) over local sockets or Apple Events. Containers and VMs can't reach those apps directly, and `srt` blocks Apple Events by default (`allowAppleEvents` removes code-execution isolation) [V]. Isolation will need deciding per server. [analysis]

**Secrets**
- Keep `${VAR}` references in `.mcp.json`. Resolve them at launch from the macOS Keychain with `security find-generic-password -s <service> -a <acct> -w` (the `/usr/bin/security` binary is present [L]) inside a Forge wrapper, so the secret reaches only that server's environment.
- Set `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1`, and use `sandbox.credentials` deny rules. [V]

### 6. Recommended `security/mcp-lock.json` design [design; built on the sources above]

**What to hash (per server)**
1. **Launch spec:**
   - `type` (stdio/http), `command`, full `args`, `cwd`
   - **names** of `env` keys (never values) and header names
   - `url` for remote servers
   - wrapper (srt profile hash, docker image digest)

   This catches MCPoison-style command swaps and the SANDWORM "new server" injection.
2. **Artifact:**
   - ecosystem, name, exact version
   - npm `dist.integrity` (sha512), plus a hash of the resolved dependency tree/lockfile
   - PyPI wheel sha256 (`--require-hashes`)
   - OCI digest, or git commit SHA
   - MCPB `fileSha256` / signature

   Catches postmark-style version bumps and transitive swaps.
3. **Protocol identity:** negotiated protocol version, `serverInfo.name`/`version`, capabilities.
4. **Model-visible surfaces (full canonical objects):**
   - `instructions`
   - every Tool object: `name`, `title`, `description`, `inputSchema`, `outputSchema`, `annotations`, `icons`, `_meta` — `_meta` matters because `anthropic/requiresUserInteraction` changes client behaviour
   - prompts (with arguments)
   - resources and resource templates
   - `skill://` contents when `io.modelcontextprotocol/skills` is declared

   Exclude only volatile envelope fields: `nextCursor`, `ttlMs`, `cacheScope`, `resultType`, result-level `_meta`.

**Canonicalization**
- **RFC 8785 JCS** (sorted keys, ES6 number serialisation, UTF-8, no whitespace) [V] ([RFC 8785](https://www.rfc-editor.org/rfc/rfc8785)).
- Sort list items by `name` (or `uri`) and **fail on duplicate names**.
- **Do not Unicode-normalise.** Hidden or bidi characters must change the hash.
- Hash with SHA-256 → `sha256:<hex>`.
- Store a per-item hash (for readable diffs), a per-surface hash, and a server `fingerprint` over {launch, artifact, protocol, surfaces}.
- Store a top-level `lockHash` over all servers, and commit the lock to git.

**Schema sketch**
```json
{
  "lockVersion": 1,
  "canonicalization": "RFC8785-JCS",
  "hash": "sha256",
  "generatedAt": "2026-09-25T00:00:00Z",
  "claudeCodeMin": "2.1.163",
  "servers": {
    "kicad": {
      "launch": {"type": "stdio", "command": "forge-mcp-guard", "args": ["kicad", "--", "srt", "--settings", "security/srt/kicad.json", "uvx", "--exclude-newer", "2026-09-01", "kicad-mcp==1.4.2"], "envKeys": ["KICAD_API_TOKEN"], "hash": "sha256:…"},
      "artifact": {"ecosystem": "pypi", "name": "kicad-mcp", "version": "1.4.2", "sha256": ["…"], "hash": "sha256:…"},
      "protocol": {"version": "2025-11-25", "serverInfo": {"name": "kicad-mcp", "version": "1.4.2"}},
      "surfaces": {
        "instructions": "sha256:…",
        "tools": {"count": 12, "hash": "sha256:…", "items": {"open_board": "sha256:…"}},
        "prompts": {"count": 0, "hash": "sha256:…"},
        "resources": {"count": 0, "hash": "sha256:…"},
        "resourceTemplates": {"count": 0, "hash": "sha256:…"},
        "skills": null
      },
      "fingerprint": "sha256:…",
      "policy": {"allowTools": ["open_board", "run_drc"], "readOnly": true, "egress": ["api.kicad.org"]},
      "findings": {"hiddenUnicode": 0, "ansi": 0, "urls": [], "overlong": []},
      "approvedBy": "owner", "approvedAt": "2026-09-25"
    }
  },
  "lockHash": "sha256:…"
}
```

**Getting the definitions deterministically (`forge-mcp-probe`)**
- Write a zero-dependency Python-stdlib or Node client. Don't depend on the Inspector for the security path; use it as a cross-check only.
- Spawn the server **through the same wrapper and sandbox** it runs under in production, with network off except the allowlist.
- Stdio framing: newline-delimited JSON-RPC.
- Handshake:
  1. Send `server/discover` with `_meta` protocolVersion `2026-07-28`.
  2. On any other error or a timeout, fall back to `initialize` with `2025-11-25` + `notifications/initialized`.

  [V] ([stdio backward compat](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/stdio))
- Page through `tools/list` until there is no `nextCursor`. Do the same for `prompts/list`, `resources/list` and `resources/templates/list` when the capability is present.
- Enforce timeouts, kill the process group, and capture stderr separately.
- **Run twice and compare** to catch non-determinism. The spec says `tools/list` MUST NOT vary per connection [V].
- For HTTP servers, probe with the **same credentials** as production (lists MAY vary by authorization [V]).
- **Doctor fails when:**
  - any server is present in `.mcp.json`, `~/.claude.json`, plugin `.mcp.json` or subagent frontmatter but missing from the lock;
  - the launch or artifact hash differs;
  - any surface hash differs (print a per-item diff);
  - hidden Unicode, ANSI escapes or instruction-like markers appear in new text;
  - the Claude Code version is below `claudeCodeMin`.

**Runtime guard (recommended, not optional)**
- A malicious server can serve clean definitions to a doctor probe and poisoned ones in real sessions: after N calls, after a date, or keyed on `clientInfo`. So register each server in `.mcp.json` as `forge-mcp-guard <name> -- <real command>`.
- The guard is a stdio proxy that re-hashes every `tools/list` / `prompts/list` / `resources/list` / `server/discover` result against the lock.
- On mismatch it **fails closed**: it returns an error or withholds the list, blocks `tools/call`, and logs.
- This is the same model as mcp-context-protector [V]. It closes the gap left by Claude Code auto-refreshing on `list_changed` [V].

## Threat → mitigation → Forge mechanism table

| Threat | Mitigation | Forge mechanism |
|---|---|---|
| Tool poisoning (hidden instructions in descriptions/instructions) | Review full text; scan for hidden Unicode, ANSI, injection markers; cap length | `forge mcp add` shows full definitions + findings before owner approval; lock records `findings` |
| Rug pull (definitions change after approval) | Content-hash pinning + fail closed | `security/mcp-lock.json` + `doctor` probe + **`forge-mcp-guard` runtime proxy** (Claude Code has no detector) |
| Config swap (MCPoison-style) / new server injected into configs (SANDWORM) | Bind approval to the launch-spec hash; inventory every config source | Lock `launch.hash`; doctor scans `.mcp.json`, `~/.claude.json`, plugins, agent frontmatter; `disabledMcpjsonServers` for unknown servers; optional managed `allowedMcpServers` with exact `serverCommand` |
| Tool shadowing / cross-server contamination | Few servers per session; unique prefixes; no untrusted servers alongside high-privilege ones | Per-role MCP profiles via `--strict-mcp-config --mcp-config security/profiles/<role>.json` |
| Prompt injection via tool output or fetched content | Break the lethal trifecta; human approval for egress and writes | Read-only profiles (`--restricted` / deny rules); egress allowlist; `requiresUserInteraction` for Forge's own sensitive tools |
| Exfiltration via allowed domains | Narrow allowlists (no broad `github.com`, `huggingface.co`); TLS-inspecting proxy if needed | `sandbox.network.allowedDomains` + `strictAllowlist: true` in **user** settings; per-server `srt` allowlists; deny-list known paste/webhook hosts |
| Malicious or typosquatted package (postmark-mcp, SANDWORM) | Exact pins + integrity hashes + release-age cooldown + no install scripts | Lock `artifact`; `npm_config_min_release_age`, `--ignore-scripts`, `uvx --exclude-newer`, `--require-hashes`; OCI digests |
| Malicious skills/plugins (ClawHavoc, ToxicSkills) | Vet source; pin SHA; no auto-update; isolate first run | Forge vendors skills by commit SHA; hashes `SKILL.md` + files; disables third-party marketplace auto-update; evaluates in container/VM |
| Poisoned repo agent config (hooks, settings, `.mcp.json`, CLAUDE.md/AGENTS.md, `.env`) | Don't auto-trust; headless flags; config integrity | Headless jobs: `--strict-mcp-config --setting-sources user --settings '{"disableAllHooks":true}'` or `--bare`; doctor hashes Forge-owned `.claude/**`; hidden-Unicode scan of instruction files |
| Agent editing its own security config (Copilot YOLO, CurXecute) | Protected paths; deny rules | Rely on sandbox protected paths; add `Edit`/`Write` deny rules for `.claude/**`, `.mcp.json`, `security/**`; `ConfigChange` hook to alert |
| MCP server or hook running unsandboxed on host | Wrap processes; least privilege | Every third-party stdio server launched via `srt` (or Docker MCP Gateway); hooks Forge-authored only |
| Token theft / confused deputy (HTTP servers) | OAuth 2.1 + RFC 8707 audience + no passthrough; narrow scopes | Prefer servers with RFC 9728/8707 support; `oauth.scopes` pinning; tokens in Keychain; no static tokens in files |
| Secret leakage via env | Env-var references only; scrub | `${VAR}` refs, Keychain-backed wrapper, `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1`, `sandbox.credentials` deny |
| Unattended "YOLO" abuse (s1ngularity) | Never allow bypass mode outside isolation | Doctor flags `bypassPermissions`/`--dangerously-skip-permissions` usage outside a container or VM profile |
| Client/tool CVEs | Version floor | Doctor enforces `claudeCodeMin` (≥2.1.163 today), `mcp-remote` ≥0.1.16, Inspector ≥0.14.1 |

## Implications for Forge (numbered decisions)

1. **Forge must own rug-pull detection.** Claude Code auto-refreshes on `list_changed` and keys `.mcp.json` approval by name [V]. Ship `security/mcp-lock.json` (JCS + SHA-256, §6) and a `doctor` that fails closed.
2. **Add a runtime guard as well as the doctor check.** Wrap every third-party server in `forge-mcp-guard`, which re-verifies definitions on every list response and on `list_changed`. A doctor probe alone can be evaded.
3. **Hash every model-visible surface, not just tools:**
   - `instructions`, prompts, resources and templates, `skill://` content
   - tool `_meta`, annotations and output schemas
   - the launch spec and artifact integrity
4. **Support both MCP eras in the probe.** Use `server/discover` first, then fall back to `initialize`, per the 2026-07-28 backward-compatibility rules.
5. **Assume MCP servers and hooks are unsandboxed.** Launch every third-party stdio server under `srt` with a per-server profile (FS allowlist, egress allowlist, no Apple Events). Use Docker MCP Gateway for servers that don't need host GUI apps. Decide per CAD/EDA server how it reaches the GUI app.
6. **Headless jobs** (CI, scheduled, sub-agents run via `claude -p`) must pass `--strict-mcp-config --mcp-config <forge profile>`, `--setting-sources user` (or `--bare`) and `--settings '{"disableAllHooks":true}'` when the repo isn't Forge-authored.
7. **Least-privilege profiles:**
   - one MCP profile per role;
   - read-only roles use `--restricted` or deny rules;
   - never mix an untrusted-content server with a secrets or egress server in one session (lethal trifecta).
8. **Pin everything:**
   - npm: exact version + lockfile integrity + `min-release-age` ≥ 7 days + `ignore-scripts`
   - uv: `==` + `--exclude-newer` + `--require-hashes` where feasible
   - OCI: digests
   - git and plugins: 40-char SHA
   - third-party marketplace auto-update: disabled
9. **Secrets:** only `${VAR}` references. Use a Keychain-backed launcher that injects secrets into the one server's environment, and set `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1`.
10. **Network:**
    - sandbox `allowedDomains` + `strictAllowlist` from user settings;
    - no broad domains;
    - document the domain-fronting limitation;
    - per-server egress in `srt`/Docker.
11. **Minimum Claude Code version.** Enforce ≥2.1.163 (all advisories patched). Recommend ≥2.1.274 (hook `mcp_server.source` provenance, v2 MCP runtime) and ≥2.1.280 if Forge wants to tune the description cap. Local is 2.1.270.
12. **Protect Forge's `.claude/**` files.** Other tools execute them too (Cursor CVE-2026-48124). Hash them in the lock and scan instruction files for hidden Unicode.
13. **Don't use Snyk Agent Scan as a default.** It uploads tool descriptions to a third party and needs an account. Keep it as optional, owner-consented analysis. Model Forge's guard on mcp-context-protector's TOFU approach.

## Not found / discrepancies

- **Tool-definition signing in 2026:** none in the MCP spec or its extensions. Signing and attestation SEPs were closed; SEP-2809 is still open. [V]
- **Claude Code re-prompt when an approved `.mcp.json` command changes:** not documented [U]. A live test was not run (the brief says research only).
- **Codex CVE-2025-61260 fixed version:** Check Point says fixed in 0.23.0. GHSA-xrxf-jgv3-qmrm lists `<= 0.23.0` as vulnerable with no patched version. [V] both
- **"MCP-2026-015" / "MCP-2026-008":** reporter-assigned labels on community issues #3213 (open), #3227 and #3228 (closed). They are not official advisory IDs or CVEs. [V]
- **ClawHavoc primary source:** Koi's original blog URL now 301-redirects to a Palo Alto Networks product page [L], so the Koi numbers (341, 824) rest on secondary coverage [R]. Trend Micro's write-up (primary) confirms AMOS delivery through SKILL.md "prerequisites". The Trend URL redirects to trendaisecurity.com.
- **Mini Shai-Hulud `.claude/` persistence:** reported by Akamai and a TanStack issue comment [R]. The primary GHSA-g7cv-rxg3-hmpx does not mention AI-agent config persistence.
- **Shai-Hulud 2.0:** Wiz found no targeting of AI configs. The brief's framing of "npm worms targeting AI tool configs" fits SANDWORM_MODE (2026-02) and reportedly Mini Shai-Hulud (2026-05), not the 2025 Shai-Hulud waves.
- **s1ngularity CLI flags:** the GHSA includes the malicious prompt. The exact flags come from StepSecurity [R].
- **A malicious AGENTS.md used in the wild:** no specific confirmed incident found [U]. The related vectors (rules files, README injection, CLAUDE.md imports) are documented.
- **Snyk Agent Scan rug-pull/baseline feature:** not documented in the current README or CLI reference [U]. It keeps a `~/.mcp-scan` storage file.
- **Repo moves:** `anthropic-experimental/sandbox-runtime` → `anthropics/sandbox-runtime`, and `cirruslabs/tart` → `openai/tart` [L] (`gh api` redirects). Claude Code docs still link the old sandbox-runtime path.
- **Docs are ahead of the local version:** code.claude.com and the CHANGELOG describe up to 2.1.282; local is 2.1.270. Features gated at 2.1.274/2.1.280 are unavailable locally.
- **Web search budget:** exhausted during research. Later verification used WebFetch on known URLs and `gh api` only.

## Sources

| # | Title | URL | Type | Published | Accessed |
|---|---|---|---|---|---|
| 1 | MCP Versioning | https://modelcontextprotocol.io/specification/versioning | Spec | living | 2026-09-25 |
| 2 | MCP 2026-07-28 Key Changes | https://modelcontextprotocol.io/specification/2026-07-28/changelog | Spec | 2026-07-28 | 2026-09-25 |
| 3 | MCP release 2026-07-28 | https://github.com/modelcontextprotocol/modelcontextprotocol/releases/tag/2026-07-28 | Spec release | 2026-07-28 | 2026-09-25 |
| 4 | MCP Tools (2026-07-28) | https://modelcontextprotocol.io/specification/2026-07-28/server/tools | Spec | 2026-07-28 | 2026-09-25 |
| 5 | MCP schema.ts (ToolAnnotations) | https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/schema/2026-07-28/schema.ts | Spec | 2026-07-28 | 2026-09-25 |
| 6 | MCP Authorization | https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization | Spec | 2026-07-28 | 2026-09-25 |
| 7 | MCP Authorization security considerations | https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization/security-considerations | Spec | 2026-07-28 | 2026-09-25 |
| 8 | MCP Security Best Practices | https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices | Spec guidance | 2026-07-28 | 2026-09-25 |
| 9 | MCP stdio transport | https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/stdio | Spec | 2026-07-28 | 2026-09-25 |
| 10 | MCP server/discover | https://modelcontextprotocol.io/specification/2026-07-28/server/discover | Spec | 2026-07-28 | 2026-09-25 |
| 11 | MCP Streamable HTTP | https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http | Spec | 2026-07-28 | 2026-09-25 |
| 12 | MCP Deprecated features | https://modelcontextprotocol.io/specification/2026-07-28/deprecated | Spec | 2026-07-28 | 2026-09-25 |
| 13 | MCP Registry about / moderation | https://modelcontextprotocol.io/registry/about | Vendor doc | living | 2026-09-25 |
| 14 | Registry official requirements; server.schema.json | https://github.com/modelcontextprotocol/registry/blob/main/docs/reference/server-json/official-registry-requirements.md | Vendor doc | living | 2026-09-25 |
| 15 | SEP-2640 Skills Extension | https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2640 | Spec PR | merged 2026-09-13 | 2026-09-25 |
| 16 | SEP-1766 Digest-pinned tool versioning (closed) | https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1766 | Spec proposal | 2025-11-05 | 2026-09-25 |
| 17 | SEP-2809 ATSA (open) | https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2809 | Spec proposal | 2026-05-28 | 2026-09-25 |
| 18 | Issue #3213 discover instructions injection | https://github.com/modelcontextprotocol/modelcontextprotocol/issues/3213 | Community issue | 2026-08-07 | 2026-09-25 |
| 19 | MCPB CLI (sign/verify) | https://github.com/modelcontextprotocol/mcpb/blob/main/CLI.md | Vendor doc | living | 2026-09-25 |
| 20 | Invariant Labs: Tool Poisoning Attacks | https://invariantlabs.ai/blog/mcp-security-notification-tool-poisoning-attacks | Researcher | 2025-04-01 | 2026-09-25 |
| 21 | Invariant Labs: GitHub MCP exploited | https://invariantlabs.ai/blog/mcp-github-vulnerability | Researcher | 2025-05-26 | 2026-09-25 |
| 22 | Willison: The lethal trifecta | https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/ | Researcher | 2025-06-16 | 2026-09-25 |
| 23 | Postmark: malicious postmark-mcp | https://postmarkapp.com/blog/information-regarding-malicious-postmark-mcp-package | Vendor advisory | 2025-09-25 | 2026-09-25 |
| 24 | THN: first malicious MCP server | https://thehackernews.com/2025/09/first-malicious-mcp-server-found.html | Secondary | 2025-09 | 2026-09-25 |
| 25 | GHSA-6xpm-ggf7-wc3p mcp-remote CVE-2025-6514 | https://github.com/advisories/GHSA-6xpm-ggf7-wc3p | Advisory | 2025-07-09 | 2026-09-25 |
| 26 | GHSA-7f8r-222p-6f5g Inspector CVE-2025-49596 | https://github.com/advisories/GHSA-7f8r-222p-6f5g | Advisory | 2025-06-13 | 2026-09-25 |
| 27 | GHSA-q66q-fx2p-7w4m server-filesystem CVE-2025-53109 | https://github.com/advisories/GHSA-q66q-fx2p-7w4m | Advisory | 2025-07-01 | 2026-09-25 |
| 28 | Claude Code security advisories (30) | https://github.com/anthropics/claude-code/security/advisories | Vendor advisories | 2025-06-23 → 2026-06-25 | 2026-09-25 |
| 29 | Check Point: Claude Code project-file RCE | https://research.checkpoint.com/2026/rce-and-api-token-exfiltration-through-claude-code-project-files-cve-2025-59536/ | Researcher | 2026-02-25 | 2026-09-25 |
| 30 | Check Point: Cursor MCPoison | https://research.checkpoint.com/2025/cursor-vulnerability-mcpoison/ | Researcher | 2025-08-05 | 2026-09-25 |
| 31 | Cursor advisories (GHSA-24mc…, 4cxx…, 4hwr…, pc9j…) | https://github.com/cursor/cursor/security/advisories | Vendor advisories | 2025-08-01 → 2026-07-14 | 2026-09-25 |
| 32 | Check Point: Codex CLI CVE-2025-61260 | https://research.checkpoint.com/2025/openai-codex-cli-command-injection-vulnerability/ | Researcher | 2025-12-01 | 2026-09-25 |
| 33 | GHSA-xrxf-jgv3-qmrm Codex | https://github.com/advisories/GHSA-xrxf-jgv3-qmrm | Advisory | 2026-04-14 | 2026-09-25 |
| 34 | GHSA-wpqr-6v78-jr5g Gemini CLI trust hardening | https://github.com/advisories/GHSA-wpqr-6v78-jr5g | Vendor advisory | 2026-04-24 | 2026-09-25 |
| 35 | Tracebit: Gemini CLI code exec | https://tracebit.com/blog/code-exec-deception-gemini-ai-cli-hijack | Researcher | 2025-07-28 | 2026-09-25 |
| 36 | Embrace The Red: Copilot CVE-2025-53773 | https://embracethered.com/blog/posts/2025/github-copilot-remote-code-execution-via-prompt-injection | Researcher | 2025-08-12 | 2026-09-25 |
| 37 | Pillar: Rules File Backdoor | https://www.pillar.security/blog/new-vulnerability-in-github-copilot-and-cursor-how-hackers-can-weaponize-code-agents | Researcher | 2025-03-18 | 2026-09-25 |
| 38 | GHSA-cxm3-wv7p-598c Nx s1ngularity | https://github.com/advisories/GHSA-cxm3-wv7p-598c | Vendor advisory | 2025-08-27 | 2026-09-25 |
| 39 | StepSecurity: s1ngularity | https://www.stepsecurity.io/blog/supply-chain-security-alert-popular-nx-build-system-package-compromised-with-data-stealing-malware | Secondary/researcher | 2025-08-26 | 2026-09-25 |
| 40 | CISA: Shai-Hulud | https://www.cisa.gov/news-events/alerts/2025/09/23/widespread-supply-chain-compromise-impacting-npm-ecosystem | Government advisory | 2025-09-23 | 2026-09-25 |
| 41 | Wiz: Shai-Hulud 2.0 | https://www.wiz.io/blog/shai-hulud-2-0-ongoing-supply-chain-attack | Researcher | 2025-11-24 | 2026-09-25 |
| 42 | Socket: SANDWORM_MODE | https://socket.dev/blog/sandworm-mode-npm-worm-ai-toolchain-poisoning | Researcher | 2026-02-20 | 2026-09-25 |
| 43 | GHSA-g7cv-rxg3-hmpx TanStack malware | https://github.com/advisories/GHSA-g7cv-rxg3-hmpx | Advisory | 2026-05-12 | 2026-09-25 |
| 44 | Akamai: Mini Shai-Hulud | https://www.akamai.com/blog/security-research/mini-shai-hulud-worm-returns-goes-public | Researcher/secondary | 2026-05-15 | 2026-09-25 |
| 45 | Snyk: ToxicSkills | https://snyk.io/blog/toxicskills-malicious-ai-agent-skills-clawhub/ | Researcher | 2026-02-05 | 2026-09-25 |
| 46 | Trend Micro: OpenClaw skills deliver AMOS | https://www.trendaisecurity.com/en-us/resources-insights/trendai-security-blog/malicious-openclaw-skills-used-to-distribute-atomic-macos-stealer | Researcher | 2026-02-23 | 2026-09-25 |
| 47 | THN: 341 malicious ClawHub skills | https://thehackernews.com/2026/02/researchers-find-341-malicious-clawhub.html | Secondary | 2026-02 | 2026-09-25 |
| 48 | Claude Code docs: Security | https://code.claude.com/docs/en/security | Vendor doc | living | 2026-09-25 |
| 49 | Claude Code docs: MCP | https://code.claude.com/docs/en/mcp | Vendor doc | living | 2026-09-25 |
| 50 | Claude Code docs: Permissions | https://code.claude.com/docs/en/permissions | Vendor doc | living | 2026-09-25 |
| 51 | Claude Code docs: Sandboxing | https://code.claude.com/docs/en/sandboxing | Vendor doc | living | 2026-09-25 |
| 52 | Claude Code docs: Sandbox environments | https://code.claude.com/docs/en/sandbox-environments | Vendor doc | living | 2026-09-25 |
| 53 | Claude Code docs: Hooks | https://code.claude.com/docs/en/hooks | Vendor doc | living | 2026-09-25 |
| 54 | Claude Code docs: Managed MCP / managed settings | https://code.claude.com/docs/en/managed-mcp | Vendor doc | living | 2026-09-25 |
| 55 | Claude Code docs: Settings reference | https://code.claude.com/docs/en/settings-reference | Vendor doc | living | 2026-09-25 |
| 56 | Claude Code docs: Discover plugins / marketplaces | https://code.claude.com/docs/en/discover-plugins | Vendor doc | living | 2026-09-25 |
| 57 | Claude Code docs: Plugin evals | https://code.claude.com/docs/en/plugin-evals | Vendor doc | living | 2026-09-25 |
| 58 | Claude Code docs: Env vars | https://code.claude.com/docs/en/env-vars | Vendor doc | living | 2026-09-25 |
| 59 | Claude Code CHANGELOG (to 2.1.282) | https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md | Vendor changelog | living | 2026-09-25 |
| 60 | snyk/agent-scan README + CLI reference | https://github.com/snyk/agent-scan | Tool doc | v0.6.4 2026-09-21 | 2026-09-25 |
| 61 | trailofbits/mcp-context-protector | https://github.com/trailofbits/mcp-context-protector | Tool doc | pushed 2026-04-14 | 2026-09-25 |
| 62 | docker/mcp-gateway security model | https://github.com/docker/mcp-gateway/blob/main/docs/security.md | Tool doc | living (v0.44.1) | 2026-09-25 |
| 63 | anthropics/sandbox-runtime README | https://github.com/anthropics/sandbox-runtime | Tool doc | v0.0.77 2026-09-18 | 2026-09-25 |
| 64 | Docker Sandboxes | https://docs.docker.com/ai/sandboxes/ | Vendor doc | living | 2026-09-25 |
| 65 | MCP Inspector CLI README | https://github.com/modelcontextprotocol/inspector/blob/main/clients/cli/README.md | Tool doc | v2.8.0 2026-09-23 | 2026-09-25 |
| 66 | cisco-ai-defense/mcp-scanner | https://github.com/cisco-ai-defense/mcp-scanner | Tool repo | 4.8.4 2026-08-28 | 2026-09-25 |
| 67 | RFC 8785 JSON Canonicalization Scheme | https://www.rfc-editor.org/rfc/rfc8785 | Standard | 2020-06 | 2026-09-25 |
| 68 | npm config docs (local, npm 11.17.0) `min-release-age` | local: `$(npm root -g)/npm/docs/content/using-npm/config.md` | Local [L] | — | 2026-09-25 |
| 69 | uv 0.11.17 `uvx --help` (`--exclude-newer`) | local CLI | Local [L] | — | 2026-09-25 |
| 70 | Lima / Tart (openai/tart) / UTM / OrbStack repos | https://github.com/lima-vm/lima · https://github.com/openai/tart · https://github.com/utmapp/UTM · https://github.com/orbstack/orbstack | Tool repos | various | 2026-09-25 |
