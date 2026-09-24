# Phase 1 research — summary

- **Date:** 2026-09-25 · Claude Code 2.1.270 (terminal) / 2.1.280 (Desktop) · macOS 15.3, Apple M4
- **Method:** 11 research agents. Nine each covered one topic; the R5 agent was stopped part-way, and its finished sub-agent reports were kept as R5a–R5d. Two narrower re-runs followed (R2, R5e). Agents tagged every claim: **[V]** read in a primary source, **[L]** verified by a local command, **[R]** secondary source only, **[U]** unverified.
- **Independent check:** a separate agent that authored none of the research tried to refute 29 load-bearing claims. **26 were confirmed, 3 corrected, 0 refuted and 0 unverifiable** ([CROSSCHECK.md](CROSSCHECK.md)). The corrections are applied in [ADR-001](../decisions/ADR-001-forge-architecture.md).
- **Decision record:** [ADR-001 — Forge architecture](../decisions/ADR-001-forge-architecture.md).

| File | Topic | Lines | [V] | [L] | [R] | [U] |
|---|---|---:|---:|---:|---:|---:|
| [R1a](R1a-claude-code-core.md) | Claude Code: memory, rules, skills, subagents, hooks | 953 | 66 | 14 | 1 | 17 |
| [R1b](R1b-claude-code-orchestration.md) | /goal, loops, routines, workflows, advisor, models, output styles, What's new | 667 | 178 | 25 | 1 | 3 |
| [R1c](R1c-claude-code-plugins-evals-permissions.md) | Plugins, marketplaces, `plugin eval`, permissions, auto mode, sandbox | 967 | 235 | 69 | 6 | 7 |
| [R2](R2-harness-engineering.md) | Harness engineering (Anthropic, OpenAI, Hashimoto) → 41 H-rules | 229 | 92 | 0 | 2 | 8 |
| [R3](R3-ai-for-cad-state-of-the-art.md) | AI-for-CAD research, about 55 sources | 713 | 84 | 0 | 4 | 5 |
| [R4a](R4a-tools-mechanical-simulation-systems.md) | Mechanical CAD, simulation, systems and rendering tools | 266 | 65 | 73 | 10 | 26 |
| [R4b](R4b-tools-electronics-embedded-software.md) | Electronics, embedded and software-side tools | 388 | 51 | 62 | 6 | 21 |
| [R5](R5-engineering-standards.md) | Standards index → R5a–R5e (R5c and R5d tag in a table column) | — | | | | |
| [R6](R6-agent-tooling-security.md) | MCP spec, attacks, 2025–26 incidents, sandboxing, lock design | 492 | 104 | 26 | 11 | 7 |

## What the research changed (the 12 findings that most shape Forge)

1. **Hooks fail open on their own errors.** Only exit 2 or an explicit deny blocks; a crash, a missing script or a PreToolUse timeout lets the action through. A Stop hook is overridden after 8 consecutive blocks. Forge's gates are therefore written to fail closed and are tested in CI [R1a; CROSSCHECK C1, C2].
2. **A plugin can't carry policy.** It can't ship CLAUDE.md, rules, or permission or sandbox settings, and plugin agents ignore `hooks`, `mcpServers` and `permissionMode`. Policy is scaffolded into each product repo, and read-only reviewers are enforced by tool allowlists plus hooks [R1a, R1c; C3, C5].
3. **Giving an agent `memory:` also grants Write and Edit**, so reviewers get no memory [R1a; C4].
4. **`plugin eval` has only six grader types (no code graders) and no pass@k.** Agents run Forge's checkers and write evidence files, regex graders assert on those files, and Forge computes pass@k and pass^k itself [R1c; C6].
5. **`/goal` only has a small model read the transcript, and the advisor sees the maker's whole context.** Neither is a verifier [R1b; C8, C9].
6. **The sandbox doesn't cover MCP servers or hooks, and Claude Code doesn't detect tool-definition changes.** Forge adds its own lock, a runtime guard proxy and a per-server `srt` sandbox [R1c, R6; C12, C25].
7. **Valid CAD is not correct CAD.** Code that runs still scores voxel IoU ≤ 0.28. Numeric requirement tests written before the CAD, by a different agent and mutation-hardened, are the strongest lever. Measured feedback beats visual critique, and model judges overrate their own work [R3; C29].
8. **Physics in the loop helps but isn't sufficient.** With FEA feedback, 59% of designs land in the target safety-factor band vs 22% without. Feedback with margins and locations beats pass/fail [R3; C29].
9. **Tool pins differ from "latest":**
   - build123d 0.11.1 on Python 3.12, not 0.13.0 on 3.14;
   - KiCad 10.0.6 through `kicad-cli`, with no MCP needed;
   - tscircuit instead of atopile, whose published wheels come from a private repo;
   - ngspice only inside an OS sandbox, because `-n` doesn't disable `shell`
   
   [R4a, R4b; C15, C17, C19].
10. **Most MCP servers aren't safe enough to adopt.** Only build123d-mcp (hardened) and kicad-mcp-pro (read-only profile) qualify. No FreeCAD, Blender or Fusion MCP [R4a, R4b].
11. **Regulatory clock:** EU CRA vulnerability and incident reporting has applied since **11 Sep 2026**, and the CRA applies fully from 11 Dec 2027, replacing RED DR 2022/30. RoHS exemption changes arrive on 1 Jul 2026, 11 Dec 2026 and 30 Jun 2027 [R5e].
12. **Platform version:** Opus 5.5 needs Claude Code ≥ 2.1.280. The terminal CLI is 2.1.270, and npm `stable` (2.1.274) is also too old [R1b; C10].

## Brief items that didn't match reality

- **"Stop-hook block limit":** real; it is 8 consecutive blocks, configurable [R1a].
- **"Claude Code team's guidance on loops (June 2026)":** found, but on claude.com/blog, not the Engineering blog [R2].
- **"The 2026 finding that valid CAD fails on dimensions":** there is no single paper. The finding comes from several 2026 benchmarks (BenchCAD, RealCADBench, Autodesk's editing benchmark, CADTests) [R3].
- **CADGenBench** is a leaderboard, not a paper, and most of its runs are self-reported [R3].
- **No independent benchmark of commercial text-to-CAD tools exists;** the evidence is anecdotal [R3].
- **"Agentic HIL":** real (`agentic-hil` 0.21.5, Apache-2.0), with caveats: its installer registers itself with every agent CLI it finds, and it exposes config-write tools [R4b].
- **atopile** is effectively moving to a hosted product, so it is deferred [R4b].
- **Headless TechDraw:** PDF and SVG page export need the GUI; DXF page export works headlessly [R4a; C21].
- **The official Fusion connector** exists, but Fusion's free licence is non-commercial with a US$1,000 revenue cap [R4a].
- **The MCP spec changed:** revision 2026-07-28 replaced the `initialize` handshake with `server/discover` [R6; C26].
- **The name "Forge"** collides with a CAD app on the CADGenBench leaderboard [R3].

## Known gaps

- Several web-search budgets ran out, so some later checks used known URLs, `gh api` and registry JSON instead.
- **Unverified:** installed disk sizes (estimates only); ECHA's SCIP duty and latest SVHC count (site returned 403); Xometry figures behind download forms; the claim that the `cadquery-ocp-novtk` 7.9.3.1.1 wheel is broken (one maintainer comment; a Phase 2 smoke test settles it).
- **Needs a live test in Phase 2–3:** whether rules trigger on newly created files, the permission-rule syntax for plugin workflows, and whether CAD/EDA binaries work under macOS Seatbelt.
