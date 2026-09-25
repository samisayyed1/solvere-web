# ADR-001 — Forge architecture

- **Status:** Accepted by owner, 2026-09-25
- **Owner decisions (2026-09-25):**
  - Recommended install tiers approved, **including FreeCAD and Blender**.
  - Forge **lives in this repo** (solvere), to govern the work done here.
  - Judges and advisor use **Opus 5.5**.
  - Claude Code updated to **2.1.282**.
  - Official plugins `plugin-dev`, `skill-creator` and `code-review` installed at user scope (marketplace commit `8286e2db0113`).
  - Six Forge habit lines appended to `~/.claude/CLAUDE.md` below the gstack rules.
- **Date:** 2026-09-25
- **Deciders:** owner (approves); Claude (recommends)
- **Evidence:** `docs/research/R1a…R6`, independent cross-check in `docs/research/CROSSCHECK.md`. Tags: [V] verified in primary source, [L] verified locally, [R] reported, [U] unverified. Every decision below cites the research file that supports it.

## 1. Context

Forge is a Claude Code plugin, served from a local marketplace in this repo, that makes Claude Code behave like a disciplined product-engineering organisation. Its core promise is that **verification is the product**: every claim rests on a check that can fail, and the check's evidence is saved.

**Machine** [L] (2026-09-25):

| Item | Value |
|---|---|
| OS / hardware | macOS 15.3, Apple M4 (10 cores), 16 GiB RAM |
| Free disk | ~45 GiB of 460 GiB |
| Tools present | Docker 29.1, git 2.52, gh 2.95, uv 0.11.17, Python 3.14.3, Node 24.19, Bun 1.3.13, Homebrew 6.0.19 |
| Claude Code | terminal CLI 2.1.270; the Desktop app bundles 2.1.280 [R1b] |
| Plan | Max |
| Already installed | gstack 1.58.5.0; plugins `claude-security` 0.11.0 and `security-guidance` 2.0.8 [R4b] |
| Not installed | any CAD, EDA, embedded or simulation tool |

Four platform facts shaped almost every decision below:
1. **Hooks fail open on their own errors.** Only exit code 2 (or an explicit `deny`) blocks. Exit 1, a missing script, malformed JSON and a PreToolUse timeout all let the action proceed [R1a].
2. **A plugin cannot carry policy.** It can't ship `CLAUDE.md`, `.claude/rules/`, or permission or sandbox settings; its `settings.json` honours only `agent` and `subagentStatusLine`. Plugin-shipped agents ignore `hooks`, `mcpServers` and `permissionMode` [R1a, R1c].
3. **The sandbox covers only Bash, PowerShell and Monitor commands (and their children).** Read, Edit and WebFetch, MCP servers and hooks all run unsandboxed on the host. Claude Code also does not detect MCP tool-definition changes [R1c, R6; corrected by CROSSCHECK C12].
4. **The stable channel can't run the default model yet.** Opus 5.5 needs Claude Code ≥ 2.1.280. npm dist-tags on 2026-09-25 are `stable` 2.1.274 and `latest` 2.1.282 [CROSSCHECK C10].

## 2. Decision summary

| # | Area | Decision |
|---|---|---|
| D1 | Platform floor | Require Claude Code **≥ 2.1.281**. The owner upgrades; `forge doctor` checks both the terminal and Desktop CLIs. Degrade gracefully on ≥ 2.1.270 (`@AGENTS.md` import; no `omitClaudeMd`). |
| D2 | Packaging | Marketplace `forge-local` at `.claude-plugin/marketplace.json`, with one plugin at `plugins/forge` (source `./plugins/forge`). Use default component folders only. The version lives only in `plugin.json`. Develop with `claude --plugin-dir ./plugins/forge`. |
| D3 | Context | Plugin skills (with `paths:`) plus a scaffolder. `/forge:new-project` and `/forge:init` write the TOC `CLAUDE.md`, `.claude/rules/*.md` and `.claude/settings.json` into each product repo. The root `CLAUDE.md` is ≤ 100 lines, enforced by a lint. |
| D4 | Enforcement | Every "must" is enforced by a hook, a permission rule, a lint or a test. Gate hooks **fail closed**: an internal error exits 2, JSON is built with an encoder, and every hook has an explicit timeout. CI pipes fixture JSON into every hook. |
| D5 | Done-gate | A command-type Stop/SubagentStop hook compares the domains changed per `git status` against `evidence/manifest.json`. At the 8-block cap it writes `UNVERIFIED`, and downstream gates refuse to proceed. `/goal` is a convenience, never evidence. |
| D6 | Maker ≠ checker | Reviewers are plugin agents with a `tools:` allowlist (Read, Grep, Glob, narrow Bash), `disallowedTools: Write, Edit, NotebookEdit, Agent`, `omitClaudeMd: true` (≥ 2.1.271), explicit `model`/`effort`/`maxTurns`, and **no `memory:`**. Plugin hooks keyed on `agent_type` deny writes, and the SubagentStop hook enforces the verdict schema. |
| D7 | Human sign-off | Content-scoped `permissions.ask` rules, which prompt even in auto and bypass modes and are denied in `dontAsk`. They are backed by PreToolUse argument inspection and signed approval files. Skills with side effects set `disable-model-invocation: true`. Agent-relayed "approvals" never unlock anything. |
| D8 | Orchestration | Fan-out work (concepts, gate reviews, research, regression) runs as plugin workflows in `plugins/forge/workflows/`, from the main thread only. Human sign-offs sit *between* workflows. |
| D9 | Models | Makers use `sonnet` (Sonnet 5) at `effort: high`. Judges (verification-evaluator, red-team) use `opus` (Opus 5.5) at `effort: xhigh`, with `fable` as an owner opt-in. The advisor is optional and never a checker. Nothing pins Haiku 4.5. Eval configs pin full model IDs. |
| D10 | Python / CAD | CPython **3.12** via uv, with `build123d==0.11.1`, `cadquery-ocp-novtk==7.9.3.1` and a `!=7.9.3.1.1` constraint, hash-locked. Not the system 3.14, and not build123d 0.13 yet. |
| D11 | Electronics | KiCad 10.0.6 through `kicad-cli` wrappers, with no MCP needed. **tscircuit** is the primary capture tool and SKiDL the fallback. **atopile is deferred.** ngspice 47 always runs inside an OS sandbox (no network, writes only to `out/`), because a netlist's `shell` command stays available even with `-n`, which only skips `.spiceinit` [CROSSCHECK C17]. A netlist lint also rejects `shell` in `.control` blocks. |
| D12 | MCP | Adopt **build123d-mcp 0.3.87** (hardened). `kicad-mcp-pro 3.35.0` is optional, read-only profile only. `agentic-hil 0.21.5` waits for the HIL phase. No FreeCAD, Blender, Fusion, Context7 or Wokwi MCP. Every server runs behind `forge-mcp-guard` under `srt`. |
| D13 | Supply chain | Pin everything: exact versions plus hashes, 40-char SHAs and OCI digests. Keep `security/mcp-lock.json` (RFC 8785 canonical JSON, SHA-256 per surface). `forge doctor` fails closed, and the runtime guard re-verifies on every list response. |
| D14 | Evals | `claude plugin eval` with 25+ cases in two tiers (smoke / full). Outcome is graded by `regex` over agent-written evidence files, path by `tool_used`. pass@k and pass^k are computed by a Forge script. Pinned agent `claude-opus-5-5` (owner speed-mode rule: top model for eval subject runs) and judge `claude-opus-5-5` for rubric graders, with a `--max-cost-usd` ceiling. |
| D15 | Evidence | L0–L5 credibility levels in `evidence/manifest.json`. "Validated" needs ≥ L4, and "certified" or "production-ready" needs L5. The wording is linted. |

The rest of this ADR gives the rationale, the pins, the permissions and the risks.

## 3. Packaging and repository layout (D2, D3)

```
.claude-plugin/marketplace.json      name "forge-local"; plugins: [{name:"forge", source:"./plugins/forge"}]
plugins/forge/
  .claude-plugin/plugin.json         name, version, description, author, license (no "hooks"/"agents" keys)
  agents/*.md                        16 subagents (§6)
  skills/<gerund-name>/SKILL.md      + references/, scripts/
  hooks/hooks.json                   + hooks/*.py (fail-closed wrappers)
  workflows/*.js                     concept-tournament, gate-review, standards-research, regression-sweep
  output-styles/engineering-report.md  (keep-coding-instructions: true; NOT force-for-plugin)
  .mcp.json                          guarded server launchers (§9), disabled until the lock verifies
  evals/                             claude plugin eval suite (§10)
  bin/forge                          forge doctor | lock | verify | evidence | passk
templates/project/                   the product-repo scaffold (CLAUDE.md TOC, .claude/rules, .claude/settings.json, Makefile, CI, gates)
security/mcp-lock.json               tool-definition lock (§9)
docs/research/, docs/decisions/, docs/standards/
```

- **Why default folders:** declaring `"hooks": "./hooks/hooks.json"` double-loads the file, and `claude plugin validate` doesn't catch it. The `agents` manifest key hides agents from `plugin details` [R1c §3, L].
- **Why `--plugin-dir` for development:** in a git worktree (the setup this session runs in), a repo-local marketplace's relative path resolves to the **main checkout** [R1c]. Final `/plugin install forge@forge-local` happens from the main checkout after merge.
- **CI static gates, which run before any paid eval:**
  - `claude plugin validate . --strict`
  - `claude --plugin-dir plugins/forge plugin list --json`, which catches load failures that validate misses
  - a Forge linter covering agent-frontmatter hygiene (rejecting ignored fields), hook-script existence and executability, skill naming and lengths, and forbidding bare `Bash`/wildcard `allowed-tools` (skill grants aren't trust-gated)
  - `claude plugin details forge` against a token budget [R1a, R1c]

## 4. Context architecture (D3)

- **Plugins cannot ship CLAUDE.md or rules** [R1a, R1c]. Forge delivers context in three ways:
  - skills with trigger-rich descriptions and `paths:`;
  - the scaffolder, which writes `.claude/rules/{mechanical,electrical,firmware,software,systems,simulation,manufacturing,compliance}.md` with `paths:` globs into each product repo;
  - SessionStart `additionalContext` (≤ 2,000 chars) for live state: the current gate, failing checks, open findings, and doctor drift.
- **Rules load only when a matching file is read and are lost at compaction** [R1a]. They are therefore guidance. Every rule that matters has a hook, permission or lint counterpart, and the rule file links to it.
- **Compaction resilience:**
  - PreCompact writes `.forge/state.json` (modified files, open findings, gate, failing checks).
  - SessionStart with matcher `compact` re-injects a summary.
  - The first 5,000 tokens of a skill survive compaction, so non-negotiable rules go first [R1a].
- **AGENTS.md** is read natively from 2.1.277, and fully from 2.1.281. Until the floor is met, the TOC `CLAUDE.md` imports it with `@AGENTS.md` [R1a].
- **User scope:** `~/.claude/CLAUDE.md` already holds the owner's gstack instructions. Forge proposes appending ≤ 15 lines of universal habits: evidence-first, units, ask when a requirement is ambiguous, never say "validated" without physical evidence. **Owner approval is needed.**

## 5. Enforcement architecture (D4, D5, D7)

**Hook design rules** [R1a]:
- Hooks use exec form, pointing at `${CLAUDE_PLUGIN_ROOT}/hooks/<name>.py`. A shared wrapper catches every exception, prints a reason, and exits **2**.
- Every hook sets `timeout`. PreToolUse hooks stay under 1 s; heavy work goes to PostToolUse (< 30 s) or Stop.
- Policy is anchored on `agent_type` (`^forge:…$`) and on `mcp_server.source` (≥ 2.1.274), not on tool-name prefixes.
- A SessionStart self-check verifies that every hook script exists and is executable.

| Event | Forge behaviour |
|---|---|
| SessionStart | Print the gate, failing checks, open assumptions and findings, `forge doctor --quick` drift, and a version-floor warning. |
| UserPromptSubmit | Optional skill suggestions from keywords. No blocking. |
| UserPromptExpansion | Block `/forge:release…`, fab-export and flash commands unless a signed approval file exists. This covers the direct-slash path that PreToolUse doesn't see [R1a]. |
| PreToolUse | Deny destructive shell commands outside `out/`, and force-pushes. Deny writes to `release/`, `security/`, HIL bench config, and params marked `verified` unless the change carries a sourced justification. Deny all writes by reviewer agents. Deny egress outside the allowlist. |
| PostToolUse | Path-dispatched checks, each < 30 s, fed back with exit 2. `cad/` rebuilds the part and runs the validity and params lint. `ecad/` runs ERC. `firmware/` compiles. `requirements/` runs the EARS lint and trace check. `docs/` checks links. |
| Stop / SubagentStop | Evidence gate (D5). SubagentStop also rejects reviewer output that isn't schema-valid. Both honour `stop_hook_active` plus a Forge retry counter. **Never** set `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP=0`. |
| PreCompact | Write the state snapshot. |

**Permission policy** lives in each product repo's committed `.claude/settings.json`, written by the scaffolder, because a plugin can't carry it [R1c]:
- **`deny`:** credential paths, `Agent(fork)` for reviewer contexts, and a small number of dangerous commands.
- **`ask`** (human sign-off, D7): `Bash(git push *)`, `Bash(gh pr merge *)`, vendor upload, quote and fab-order CLIs, flashing, and anything in the signing list. Ask rules prompt even in auto and bypass modes, and are denied in `dontAsk`, which fails closed in CI [R1c].
- **Narrow `allow`** for Forge's own check commands, e.g. `Bash(uv run forge-check *)`. Auto mode drops broad `Bash(*)`, interpreter and `Agent` allow rules, and it can't be committed as a project default [R1b, R1c].

**Sandbox baseline** (product-repo `.claude/settings.json`) [R1c]:
- `sandbox.enabled: true`
- `sandbox.failIfUnavailable: true`
- `sandbox.allowUnsandboxedCommands: false`
- `sandbox.network.allowedDomains` per toolchain: package registries, GitHub API, docs and datasheet hosts
- `sandbox.filesystem.denyRead` for `~/.ssh`, `~/.aws` and `~/.config/gh`
- `excludedCommands`: only `docker *` if needed

`strictAllowlist: true` must be set at **user** scope; it has no effect from repo files. That is part of the owner's Phase 2 setup.

**Network rule** from the brief ("block non-allowlisted domains"): the Bash sandbox allowlist enforces it for shell commands, `WebFetch(domain:…)` permission rules for WebFetch, and `srt` egress profiles for MCP servers. The PreToolUse check is a second layer, not the primary control.

## 6. Agents (D6, D9)

All 16 agents from the brief ship as plugin agents. Every field used is from the verified list [R1a, R1b]: `name, description, tools, disallowedTools, model, effort, maxTurns, memory, isolation, omitClaudeMd, color, skills, background`.

| Role class | Agents | model / effort | memory | Tools |
|---|---|---|---|---|
| Makers | mechanical, electrical, embedded, software-architect, simulation, manufacturing, supply-chain, industrial-designer, ux-designer, rf-emc, test, systems, safety-compliance | `sonnet` / `high` | `project` | Least privilege per role. Only mechanical-engineer may write `cad/`, enforced by a PreToolUse hook on `agent_type`. |
| Interviewer | product-manager | `sonnet` / `high` | `project` | Includes AskUserQuestion. |
| Judges | verification-evaluator, red-team | `opus` / `xhigh` (owner may choose `fable`) | **none** | Read, Grep, Glob, narrow Bash for check scripts. `disallowedTools: Write, Edit, NotebookEdit, Agent`. `omitClaudeMd: true`. |

**Deviation from the brief:** it gives *every* agent `memory: project`, but `memory:` auto-grants Read, Write and Edit [R1a], which would break read-only review. Judges therefore get no memory. Their recurring findings flow through `capturing-failures` into rules, checks and eval cases, which is a stronger mechanism anyway.

Maker agents that edit in parallel use `isolation: worktree` with project `worktree.baseRef: "head"`; otherwise they branch from `main` [R1a]. `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=2`.

## 7. Orchestration, loops and the advisor (D5, D8, D9)

- **Workflows run from the main thread only** (the `Workflow` tool is stripped from subagents, and `workflow()` nests one level) [R1b]:
  - Plugin workflows run as `/forge:<meta.name>`.
  - Scripts are deterministic, and timestamps come in through `args`.
  - Every `agent()` returns an object checked against its schema, which becomes saved evidence.
  - There is no mid-run user input, so each gate is one workflow followed by a human sign-off.
  - Expect about 8 concurrent agents on this M4.
- **`/goal`** is a prompt-based Stop hook whose Haiku evaluator only reads the transcript [R1b]. Forge suggests `/goal` only with the check command, the evidence path and an explicit bound named in the condition. The authoritative gate stays the command-type Stop hook (D5).
- **Advisor** (`/advisor`, saved as `advisorModel`): with Opus 5.5 as the main model, only `fable` or `opus` advisors are accepted [R1b]. It sees the maker's whole transcript, Claude decides when to call it, and calls can't be forced. So it is an **escalation aid, never the checker**.
  - Recommendation: `/advisor opus` by default, or `/advisor fable` if the owner accepts Fable usage (Fable 5.1 lists at $10/$50 per MTok, vs $4/$20 for Opus 5.5) [R1b].
- **Long-running work:**
  - Monitor (≤ 30 min, re-armed) for sim and build logs inside a session.
  - Desktop scheduled tasks for local overnight regressions.
  - Cloud routines only for repo hygiene that needs no local toolchain.
  - Channels and agent teams are research previews and not dependencies [R1b].
- **Computer use** is interactive-only and not used for verification [R1b].

## 8. Toolchain and pins (Phase 2 install plan)

Each tier installs independently and is **verified by `forge doctor` before the next one**. The versions are the research-verified latest-compatible releases as of 2026-09-25 [R4a, R4b]. Exact hashes are recorded in lockfiles at install time; the research already recorded several (e.g. build123d wheel `4e95fa7c…`, kicad-mcp-pro wheel `b2297186…`, KiCad cask `ef4dcd42…`, FreeCAD `f5c0ece7…`).

| Tier | Component | Pin | Install | Disk (est.) |
|---|---|---|---|---|
| T0 core | Claude Code | ≥ 2.1.281 (owner upgrades) | npm / installer | — |
| | git, gh, uv, Node, Bun | present (2.52 / 2.95 / 0.11.17 / 24.19 / 1.3.13) | — | — |
| | CPython | 3.12.x (uv-managed) | `uv python install 3.12` | 0.1 GiB |
| | pixi (conda-forge lockfiles) | pin at install | brew | 0.1 GiB |
| | `srt` (Anthropic sandbox-runtime) | pin at install | npm, `--ignore-scripts` | < 0.1 GiB |
| T1 mechanical | build123d + OCP | 0.11.1 + cadquery-ocp-novtk 7.9.3.1 (`!=7.9.3.1.1`, excluded on one maintainer report [R]; the wheel isn't yanked, so a Phase 2 smoke test confirms) | uv, `--require-hashes` | ~1 GiB |
| | trimesh, PyVista, VTK | 5.1.0 / 0.49.0 / 9.7.0 (≥ 9.5.1 for CVE fixes) | uv | ~0.5 GiB |
| | build123d-mcp | 0.3.87 (tag `61443b8…`) | locked venv, guarded | ~0.3 GiB |
| | FreeCAD (optional) | 1.1.3; bundles ccx, gmsh, freecadcmd | brew cask | ~2 GiB |
| T2 electrical | KiCad + kicad-cli | 10.0.6 | brew cask | 5–8 GiB |
| | tscircuit / @tscircuit/cli | 0.0.2646 / 0.1.2152, `TSCI_TELEMETRY_DISABLED=1` | npm/bun, lockfile | ~0.5 GiB |
| | ngspice | 47; run `-b -n` **inside `srt`/Seatbelt**, since `-n` doesn't disable `shell` | brew | < 0.1 GiB |
| | SKiDL (fallback) | 2.3.0 | uv | < 0.1 GiB |
| | kicad-mcp-pro (optional) | 3.35.0 (commit `f641a925…`), review/readonly profile | locked venv, guarded | ~0.2 GiB |
| T3 embedded | Renode | 1.17.0 (arm64 portable DMG, SHA-256 pinned) | download | 0.3 GiB |
| | Zephyr + SDK | 4.4.x (or 3.7 LTS) + SDK 1.0.1 minimal + arm only, `west.yml` pinned | west | 5–7 GiB |
| | ESP-IDF | v6.1, one target only, when a product needs it | EIM | 3.5–5 GiB |
| | agentic-hil | 0.21.5, at the HIL phase only | uv tool, manual MCP registration | < 0.1 GiB |
| T4 simulation | gmsh | 4.15.2 | uv wheel | < 0.1 GiB |
| | CalculiX | 2.23 | conda-forge via pixi lock | ~0.3 GiB |
| T5 rendering | PyVista/VTK offscreen + build123d SVG → PNG (resvg) | as T1 | uv | — |
| | Blender (optional) | 5.2.2 LTS, `-b --factory-startup`, `-Y` default | brew cask | ~1 GiB |
| T6 systems | SysML v2 Pilot kernel | `jupyter-sysml-kernel` 0.62.0 + Java 21 | pixi | ~1 GiB |
| | spec42 (evaluate as the CI checker) | v0.53.1 (MIT) | release archive, SHA pinned | < 0.1 GiB |

**As installed (Phase 2, 2026-09-25):** all tiers above, including FreeCAD and Blender, per `plugins/forge/toolchain/manifest.json` (28 entries, all verified). Four things differ from the table:
- **KiCad** was installed from the cask's own DMG, verified against the same sha256, because the cask needs `sudo`.
- **kicad-mcp-pro** runs on Python 3.13, which it requires.
- **`srt`** is `@anthropic-ai/sandbox-runtime` 0.0.77 (its CLI reports 1.0.0).
- **Disk** use was about 15 GiB, leaving 29 GiB free.

The smoke tests compare measured values with hand calculations:

| Tool | Measured | Hand calculation |
|---|---|---|
| CAD volume | 964.6571 mm³ | 964.6571 mm³ |
| CalculiX cantilever tip deflection | 0.19012 mm | 0.19048 mm |
| ngspice RC response at τ | 0.632120 V | 0.632121 V |

**Recommended Phase 2 install:** T0, T1 (without FreeCAD), T2, T4, T5 (without Blender), T6, plus Renode, for about **10–13 GiB**. Defer Zephyr and ESP-IDF until the firmware eval or a product needs them, and install only one path. FreeCAD and Blender are opt-in. This keeps ≥ 25 GiB free for builds, renders and Docker.

**Deferred or not adopted** [R4a, R4b]:
- **atopile:** published wheels are built from a private repo, and the product is moving to a hosted 0.16.
- **Fusion:** the personal licence is non-commercial with a US$1,000 revenue cap.
- **Blender MCP:** runs model code unguarded.
- **FreeCAD MCPs:** arbitrary Python, no read-only mode.
- **mixelpixx, Seeed and lamaalrajih KiCad MCPs.**
- **Context7:** queries leave the machine to a private backend.
- **Wokwi:** firmware runs in their cloud.
- **Elmer, OpenFOAM, FEniCSx:** OpenFOAM via a digest-pinned Docker image, `--network none`, when CFD is needed.
- **Syside:** CI support is paid.
- **Quilter / Flux:** noted only.

### 8.L Linux x86_64 path (added 2026-09-25, for the cloud build machine)

The cloud machine is Ubuntu 24.04 on x86_64, with no brew, no root package installs and GitHub release downloads blocked by the network policy (github.com HTTPS is scoped per repository; git clones of public repositories work). `install.sh` detects the platform and sources `toolchain/linux/tiers.sh`. **Every version is the same as the macOS pin.** Only the artifact and its integrity anchor differ:

| Component | Pin | Linux artifact | Integrity anchor |
|---|---|---|---|
| pixi | 0.81.0 | conda-forge `linux-64/pixi-0.81.0-hf01adef_0.conda` | sha256 `691c4f46…3e10` |
| git, gh, uv, Node | 2.52.0, 2.95.0, 0.11.17, 24.19.0 | conda-forge, `conda-core/pixi.lock` | pixi lock (sha256 per package) |
| CAD env, build123d-mcp, kicad-mcp-pro | as T1/T2 | the same universal `uv.lock` files (manylinux wheels) | uv lock hashes |
| X11/GL runtime libs for gmsh/OCP | — | conda-forge in `conda/pixi.lock` (`[target.linux-64]`); only libGLU, libXft and libOpenGL are exposed on the private path `~/.forge/lib` | pixi lock |
| CalculiX, SysML kernel, Java 21 | 2.23, 0.62.0, 21 | the same `conda/pixi.lock`, with a linux-64 section added (the osx-arm64 entries are byte-identical: 87 URLs before and after) | pixi lock |
| FreeCAD | 1.1.3 | conda-forge `freecad==1.1.3`, `conda-freecad/pixi.lock` (the official Linux AppImage is a GitHub release asset) | pixi lock |
| KiCad | 10.0.6 | the official `kicad-10.0-releases` PPA `.deb` plus its dependency closure from the Ubuntu snapshot `20260925T000000Z`, unpacked in user space by `linux/debfetch.py` (no root, no dpkg database) | PPA key fingerprint `FDA854F6…FAD7A805`, gpgv on every InRelease, Packages sha256 from InRelease, `.deb` sha256 from Packages, all 118 recorded in `linux/debs.lock.json`; kicad `.deb` `a4920d3f…926d` |
| ngspice | 47 | built from the official git tag `ngspice-47` (conda-forge stops at 41, Ubuntu at 42), toolchain `conda-build/pixi.lock` | tag commit `a80f6e3e95d51534905b1f23410a951802666656`, checked before building |
| spec42 | 0.53.1 | `cargo build --locked` from git tag `v0.53.1` (Rust 1.97.1 per its `rust-toolchain.toml`), embedding the OMG SysML stdlib KPARs (`Systems-Modeling/SysML-v2-Release` tag `2026-04`) and the elan8 domain (v0.3.0) and method (v0.2.0) libraries, which its release CI fetches as GitHub release assets | commits: spec42 `f0d268fc…61c8`, stdlib `9baca590…ea8f`, domain `e91156d4…7c03`, method `00e21183…d9e1`; `Cargo.lock` |
| Blender | 5.2.2 | official `download.blender.org/.../blender-5.2.2-linux-x64.tar.xz` | sha256 `84098912…a168`, equal to Blender's published `blender-5.2.2.sha256` |
| Renode | 1.17.0 | official `builds.renode.io/renode-1.17.0.linux-portable.tar.gz` | sha256 `92a33d6a…00eb`. The same server's `osx-arm64-portable.dmg` hashes to the GitHub-release pin `63b1fb69…4c12`, so it serves the same release. |
| srt, tscircuit | as T0/T2 | the same `package-lock.json` | npm integrity hashes |

`forge doctor` reads the same `manifest.json`. Each entry keeps one `version` and adds a `platforms["linux-x86_64"]` override for `install` and `artifact_sha256`. `toolcheck.resolve_entry` rejects any override that changes the version. Paths are written `~/.forge/...` and expanded per machine.

Disk: `all` takes about 16 GiB on Linux (3.3 GiB of it is KiCad 3D models), so the Linux floor is 20 GiB free to start and 5 GiB free after (macOS stays at 25/25).

Network: nothing had to be allowed. conda.anaconda.org, snapshot.ubuntu.com, ppa.launchpadcontent.net, keyserver.ubuntu.com, download.blender.org, builds.renode.io, pypi.org, crates.io and git clones of github.com/git.code.sf.net are all reachable under the "Trusted" policy. If the owner wants the GitHub release archives themselves (the macOS artifacts), **github.com release downloads** (`github.com/<owner>/<repo>/releases/download/...` and its `release-assets.githubusercontent.com` redirect) would have to be allowed for elan8/spec42, renode/renode and FreeCAD/FreeCAD.

**Software side** (optional, owner approval — brief §2):
- Keep gstack 1.58.5.0 pinned (upstream is 1.89.0.0; review the changelog before upgrading; no auto-upgrade; don't let `setup` add hooks).
- Keep `claude-security` and `security-guidance`, with `ENABLE_STOP_REVIEW=0` in multi-agent worktrees.
- Add `plugin-dev`, `skill-creator` and `code-review` from `claude-plugins-official`, pinned to marketplace commit `8286e2db…`.
- Use the MCP registry as a metadata index only [R4b].

## 9. MCP servers, permissions and rug-pull defence (D12, D13)

| Server | Status | Launch | Exposed tools | Who may call |
|---|---|---|---|---|
| build123d-mcp 0.3.87 | Adopt (T1) | `forge-mcp-guard` → `srt` profile (write only to project `cad/` and `out/`, no network, no Apple Events) → locked venv; `--tools` allowlist; `--memory-limit-mb`, `--cpu-limit-s`; stdio | Allowlist **excludes** `install_skill` (writes `.claude/skills` and `AGENTS.md`), `execute_file`, `bank_candidate`, `load_part`, `search_library` | mechanical-engineer (build); judges get the measure and render tools only (enforced by hook) |
| kicad-mcp-pro 3.35.0 | Optional (T2) | guard → `srt` (no network) → `KICAD_MCP_PROFILE=review`, `KICAD_MCP_OPERATING_MODE=readonly`, `KICAD_MCP_WORKSPACE_ROOT=<project>` | Review profile. Deny `lib_get_bom_with_pricing` (network) | electrical-engineer, judges |
| agentic-hil 0.21.5 | HIL phase | Manual project-scope registration. Bench config lives outside the workspace | Deny `project_config_create`, `project_config_set`, `project_config_adopt_hardware`, `server_upgrade`. Interlocks off | embedded-engineer, test-engineer, each run with human `ask` |

- **Why a runtime guard as well as `forge doctor`:**
  - Claude Code silently reloads on `list_changed` and keys `.mcp.json` approvals by server name [R6].
  - A malicious server can show clean definitions to a one-off probe. `forge-mcp-guard` is a stdio proxy, modelled on Trail of Bits' `mcp-context-protector` trust-on-first-use approach. It re-verifies every list response against the lock and blocks on mismatch [R6].
- **What the lock (`security/mcp-lock.json`) hashes, per server:**
  - the launch spec (command, args, env names without values) and the package artifact's integrity hash;
  - server `instructions`;
  - each tool's name, description, `inputSchema`, `outputSchema`, annotations and `_meta`;
  - prompts, resources and templates, and `skill://` content.
  
  Hashing is RFC 8785 canonical JSON with SHA-256, per item and in aggregate, so drift shows as a readable diff. The probe tries `server/discover` (spec revision 2026-07-28) first and falls back to `initialize` [R6].
- **Headless runs** (CI, scheduled tasks, `claude -p` over any repo Forge didn't author) always pass [R6]:
  - `--strict-mcp-config --mcp-config <forge profile>`
  - `--setting-sources user` (or `--bare`)
  - hooks disabled
- **Secrets:** only `${VAR}` references, injected per server by a Keychain-backed launcher, with `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1`.
- **Forge's own `.claude/**` files are an attack surface for other tools too** (Cursor CVE-2026-48124 ran hooks from `.claude/settings.local.json`) [R6]. They are hashed in the lock and scanned for hidden Unicode.
- **Pinning policy** [R6]:
  - npm: exact version plus lockfile integrity, `--ignore-scripts`, and a ≥ 7-day minimum release age.
  - uv: `==` plus `--require-hashes`, and `--exclude-newer` where practical.
  - OCI images: by digest.
  - git and marketplace sources: 40-char SHA.
  - Third-party marketplaces: auto-update disabled.
- **Snyk Agent Scan** (formerly mcp-scan) is **not** a default, because it uploads descriptions to a third party. It stays optional with owner consent.

## 10. Evals (D14)

Verified constraints of `claude plugin eval` [R1c, L]:
- **Grader types:** `regex`, `tool_used`, `tool_order`, `file_exists`, `llm` and `baseline`. **No custom-code graders, and no built-in pass@k or pass^k.**
- **Baseline:** a no-plugin arm is built in, so the Δ is reported directly.
- **Runs:** 3 per case by default (range 1–50).
- **Ceiling:** `--max-cost-usd` is checked before each run launches.
- **Exit codes:** 0 pass, 1 fail or load error, 2 partial (e.g. the ceiling was hit), 130 interrupted, 143 terminated.
- **Judge:** the default `--judge-model` is Haiku.
- **Isolation:** runs get a throwaway home and config. Only Bash is OS-sandboxed; plugin hooks and real MCP servers run on the host.

**Design:**
- **"Checks that can fail" inside evals:** because graders can't run code, the agent must run Forge's checker. The checker writes machine-readable results (`out/verify/*.json`), and a `regex` grader asserts on that file. `tool_used` with `input_match` proves the checker actually ran, and a `tool_used: Skill` indicator records skill firing. Every suite includes a should-not-fire case.
- **Models:** agent `--model claude-sonnet-5` (the production maker model) and judge `--judge-model claude-opus-5-5`. The judge must differ from the agent, and **not** Haiku 4.5, which may retire from 2026-10-15 [R1b]. `llm` graders are reserved for short rubric judgements, such as render PNGs against a written rubric.
- **pass@k and pass^k:** computed by `forge passk` from each run's `aggregate-result.json`. Drop `partial: true` runs and runs with skipped paid graders.
- **Suites:**
  - **Smoke:** about 8 cases × 3 runs × 2 arms (48 runs), for iteration.
  - **Full:** 25+ cases × 3 runs × 2 arms (≥ 150 runs), for release gates and CI on `plugins/forge/**` changes.
  - The seeded-defect review set targets recall ≥ 0.8 and reports precision.
- **Mocking:** MCP servers are mocked in evals unless a case opts in (`--scaffold` / MCP opt-in), because real servers run unsandboxed.
- **CI command:**

  ```
  claude plugin eval plugins/forge --trust-plugin --json results.json \
    --model claude-sonnet-5 --judge-model claude-opus-5-5 \
    --threshold <explicit> --max-cost-usd <ceiling> --no-publish
  ```

  CI fails on a non-zero exit. The static gates (§3) run first.
- **Cost:** see §12. A full suite is roughly 150 agent runs, so it is *not* run on every edit.

## 11. Evidence and credibility (D15)

- **Where evidence lives:** `evidence/manifest.json` holds one entry per result-bearing artifact: check id, command, tool versions, git SHA, resolved model (from `tool_response.resolvedModel`), inputs hash, result, level (L0–L5) and timestamp.
- **Wording lint:** reports are linted for "validated" (needs L4 or higher) and for "certified" or "production-ready" (needs L5).
- **Forced stops:** a forced stop at the Stop-hook cap writes `UNVERIFIED`, which blocks gate records and releases [R1a].

## 12. Model strategy and how cost scales

| Role | Model | List price in/out per MTok [R1b] | Expected token share |
|---|---|---|---|
| Main session | Owner's choice (default Opus 5.5) | $4 / $20 | orchestration only |
| Makers (13 agents + product-manager) | Sonnet 5 | $2 / $10 | ~70–80% |
| Judges (evaluator, red-team) | Opus 5.5 (Fable opt-in) | $4 / $20 (Fable $10 / $50) | ~10–20% |
| Eval agent / judge | Sonnet 5 / Opus 5.5, pinned | as above | per suite |
| Advisor | Opus (Fable opt-in) | advisor rates, not cached | small, Claude-initiated |

- **What cost scales with:** cost grows roughly linearly with (verification rungs run × domains changed) for normal work, and with (cases × runs × 2 arms) for evals.
- **Levers:** tighter skill scopes, deterministic scripts instead of LLM steps, the smoke tier during iteration, and `--max-cost-usd` on every eval.
- **On a subscription:** usage counts against plan limits. Fan-outs check `get_usage` first and are staggered across 5-hour windows, not launched at once.
- **Sonnet 5 is half the price of Opus 5.5, not a tenth.** The larger saving comes from moving work into scripts, not from model choice.

## 13. Harness rules adopted from R2

These come from Anthropic's, OpenAI's and Hashimoto's harness guidance [R2]. Each has an enforcing mechanism, not just a sentence in a prompt.

1. **"Done" is agreed before building.** Every task starts with acceptance criteria written as executable checks. For CAD, the requirement tests are written from the spec by a different agent, and mutation-hardened before anyone trusts them [R2, R3]. *Mechanism:* the spec gate in `modeling-cad-parts`; `verifying-geometry` refuses to run without a test file.
2. **Enforcement strength goes prompt < `/goal` < Stop hook < independent verifier.** Forge's gates use the top two [R2]. *Mechanism:* D5 + D6.
3. **The evaluator applies hard thresholds per criterion.** Any criterion below its threshold is FAIL, with no averaging [R2]. *Mechanism:* the verdict schema, enforced by SubagentStop.
4. **Status lives on disk, and agents flip status, not scope.** `requirements/trace.json` and `evidence/manifest.json` are the source of truth. Outside the systems-engineer role, changes may touch only status and result fields [R2]. *Mechanism:* a diff lint in PostToolUse and CI.
5. **The root file is a map, not a manual.** The root `CLAUDE.md`/`AGENTS.md` is ≤ 100 lines of pointers into `docs/` [R2]. *Mechanism:* a line-count lint, plus `gardening-docs` and a link check.
6. **Every failure message says how to fix it.** Every Forge check prints the rule it applied, the measured value against the required value with units, and the fix [R2]. *Mechanism:* a shared check-result helper; the linter rejects checks without a remediation string.
7. **A smoke test runs at session start.** SessionStart runs `forge doctor --quick` and the fastest verify rung before new work [R2]. *Mechanism:* the SessionStart hook.
8. **Loops are bounded.** Every loop has deterministic stop criteria and a turn cap. Repair loops allow at most 3 execution attempts and 2–3 geometric rounds, and keep the best result so far [R2, R3]. *Mechanism:* skill scripts; workflow `maxTurns`.
9. **Evals grow from real failures.** Each case has a reference solution, and outcome graders count for more than path graders [R2]. *Mechanism:* `capturing-failures` adds an eval case for every escaped defect.
10. **Every harness part assumes a model weakness.** When the model changes, remove parts one at a time and delete any whose Δ ≈ 0 [R2]. *Mechanism:* the weekly routine plus eval ablation (`--ablation`).

## 14. Stage gates

G0–G6 as in the brief (`docs/standards/gates.md`). Each gate record contains:
- the criteria;
- evidence links;
- the evaluator verdict (PASS / FAIL / BLOCKED per criterion);
- red-team findings;
- open risks;
- a **blank human sign-off line**.

Only a human passes a gate. Forge recommends, and the gate-review workflow ends before sign-off (§7).

## 15. Deviations from the brief (and why)

1. **Judges get no `memory:`,** because it grants Write/Edit (§6).
2. **atopile is deferred; tscircuit is primary,** because atopile's published wheels come from a private repo and the product is moving to a hosted service [R4b].
3. **No FreeCAD MCP server; FreeCAD runs via `freecadcmd` scripts.** Headless full-page TechDraw **PDF/SVG** export isn't possible (issue #5710), but full-page **DXF** export works headlessly [R4a; CROSSCHECK C21]. `drafting-drawings` therefore exports the TechDraw page as DXF headlessly and converts DXF → PDF with a scripted renderer (candidate: ezdxf's drawing add-on, to be proven in Phase 3). A human GUI export remains the fallback.
4. **`/goal` is never the gate.** The advisor is never the checker [R1b].
5. **Plugin-level policy is impossible,** so permissions, sandbox and rules are scaffolded into each product repo [R1a, R1c].
6. **Network blocking is primarily sandbox and permission rules;** the hook is a secondary layer (§5).
7. **pass@k and pass^k are computed by a Forge script,** because the runner doesn't provide them [R1c].
8. **build123d is pinned at 0.11.1 (not 0.13.0) on Python 3.12 (not the system 3.14),** for MCP ecosystem compatibility [R4a].
9. **The global `~/.claude/CLAUDE.md` is merged, not replaced,** because it already contains the owner's gstack rules (§4).
10. **Evals are staged smoke → full** to respect plan limits (§10).

## 16. Known risks

| # | Risk | Mitigation | Residual |
|---|---|---|---|
| 1 | **Valid CAD that is still wrong.** Frontier models reach 67–94% executability but voxel IoU ≤ 0.28. In Autodesk's editing benchmark, experts accepted only 25% of GPT 5.2's edits although 99% were valid. Tests an LLM writes itself catch only ~65% of wrong models until hardened [R3]. | Spec gate before any CAD; executable requirement tests written by a different agent and mutation-hardened; measure after every feature; capped repair loops that keep the best result. | High. This is the core problem Forge exists for. |
| 2 | **Third-party MCP code on the host.** build123d-mcp's sandbox is Python-level only and probably bypassable via `io.open`. Some servers are young and have a single maintainer [R4a, R4b, R6]. | `srt` sandbox, guard proxy, tool allowlists, hash pins, re-vetting on every bump. Report the bypass upstream privately (owner approval). | Medium |
| 3 | **Hooks fail open;** the Stop cap is 8 [R1a]. | A fail-closed wrapper, CI fixture tests for every hook, and `UNVERIFIED` recorded on a forced stop. | Low–medium |
| 4 | **Platform drift.** The CLI ships many releases a week, and the stable channel lags [R1a, R1b]. | Version floor in doctor; re-run evals after any Claude Code or model change; weekly digest check. | Medium |
| 5 | **Eval cost and plan limits.** Evals run "as you" [R1c]. | Smoke tier, cost ceilings, staggering, pinned models. | Medium |
| 6 | **Disk** (~45 GiB free). | Tiered installs, one embedded path at a time, Docker VM disk capped. | Low |
| 7 | **Haiku 4.5 retirement** (≥ 2026-10-15) affects `/goal` and agent-view summaries [R1b]. | Nothing pins Haiku; eval judge is Opus. | Low |
| 8 | **Headless drawing gap** (TechDraw PDF) [R4a]. | Headless DXF page export → scripted PDF, or a human GUI step. | Low |
| 9 | **Standards summaries could be mistaken for compliance** [R5]. | Every compliance output carries "not a compliance determination" wording and a human sign-off line; the L5 wording lint applies. | Low |
| 10 | **Name collision:** a CAD app named "Forge" appears on the CADGenBench leaderboard [R3]. | Plugin namespace `forge` is local; rename before any public release. | Low |

## 17. Free-first policy and owner approvals

Everything adopted above is free and open source, except these, which need **explicit owner approval**:
- Syside Business;
- Fusion;
- Wokwi paid tiers;
- Quilter / Flux;
- Snyk Agent Scan;
- Fable usage (billing);
- any cloud simulation.

**Approvals requested with this ADR:**
- Upgrade Claude Code to ≥ 2.1.281.
- Where Forge lives: this `solvere` worktree or a dedicated repo.
- Phase 2 tiers and a disk budget of about 10–13 GiB.
- Optional official plugins (plugin-dev, skill-creator, code-review).
- Reviewer and advisor model: Opus 5.5, or Fable 5.1.
- Appending ≤ 15 lines to the global `~/.claude/CLAUDE.md`.

## 18. Consequences

- **Positive:**
  - Gates are mechanical and fail closed.
  - Reviewers can't edit.
  - Every third-party tool is pinned, sandboxed and drift-checked.
  - The eval suite measures Forge against plain Claude Code.
- **Negative:**
  - More moving parts (guard proxy, lockfiles, scaffolder).
  - Product repos must carry their own `.claude/settings.json`.
  - Some brief items are deferred (atopile, FreeCAD MCP, headless TechDraw PDF).
- **Revisit when:**
  - build123d-mcp lifts its `<0.12` cap, allowing the move to build123d 0.13 / OCP 8;
  - FreeCAD 26.3 ships;
  - Claude Code adds native MCP definition pinning;
  - evals show a component adds no Δ, in which case it is removed (harness simplification).
