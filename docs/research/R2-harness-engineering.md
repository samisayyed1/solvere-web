# R2 — Harness and agent engineering
- Date accessed: 2026-09-25 · Author: research agent (Phase 1) · Scope: Anthropic, OpenAI and Mitchell Hashimoto guidance on agent harnesses (context, tools, verification, evaluators, long-running work, loops, evals, AGENTS.md), turned into testable Forge rules.

**Tag legend.** [V] = read in the primary source at the URL cited (fetched 2026-09-25). [V-arch] = primary-source text read through a Wayback Machine snapshot of the primary URL, because the live URL returned HTTP 403; the title, author and date were cross-checked against the publisher's own RSS feed. [R] = secondary source only. [U] = unverified / inference. Numbered source references such as (S5) point to the Sources table. Forge mechanism names such as `forge-lint` or `.forge/…` are **proposals**, not existing artefacts.

---

## Summary
1. **Verification is the lever everyone agrees on.** Anthropic's Claude Code guidance puts giving Claude a runnable check first. It describes four ways to gate on a check, from weakest to strongest: prompt, `/goal`, Stop hook, fresh-context verifier (S9). Hashimoto (S13) and OpenAI (S11) both build their practice on fast, automatic signals that tell the agent it is wrong. [V]
2. **Maker ≠ checker is backed by evidence.** Agents grading their own work reliably skew positive. It is far easier to tune a separate evaluator to be skeptical than to make a generator self-critical (S7). The Claude Code docs and the loops post both recommend a reviewer with fresh context (S9, S10). [V]
3. **Deterministic mechanisms beat prose.** Claude Code docs describe CLAUDE.md as advisory and hooks as deterministic and guaranteed (S9). OpenAI encodes architecture and "taste" as custom linters and structural tests whose error messages carry fix-it instructions for the agent, and promotes a rule into code when docs fall short (S11). [V/V-arch]
4. **The root context file should be a short map.** OpenAI's single big AGENTS.md failed. They moved to a roughly 100-line table of contents pointing into a versioned `docs/` system of record, checked by linters and CI (S11). Claude Code docs: prune each line that wouldn't cause a mistake if removed, because bloat makes Claude ignore rules (S9). [V/V-arch]
5. **Context is a finite attention budget.** Aim for the smallest set of high-signal tokens. Load context just in time through references, delegate exploration to subagents that return condensed summaries, and use compaction or structured notes for long horizons (S2). [V]
6. **Long-running work needs structured state on disk.** Keep a JSON feature list whose only editable field is pass/fail, a progress log, git commits, an `init.sh` smoke test, and work on one feature per session (S6). Three agents (planner, generator, evaluator) with negotiated "sprint contracts" beat a solo agent, but cost about 20x more (S7). [V]
7. **Every harness component encodes an assumption about what the model can't do.** When the model improves, remove components one at a time. The evaluator is worth its cost only when the task is beyond what the model does reliably alone (S7). [V]
8. **Loops need explicit stop conditions.** The Claude Code team classifies loops as turn-based, goal-based (`/goal`), time-based (`/loop`, `/schedule`) and proactive. They recommend deterministic exit criteria, turn caps, piloting before a large fan-out, and scripts for deterministic work (S10). [V]
9. **Evals are the harness's own test suite.** Start with 20–50 tasks drawn from real failures. Each task should be unambiguous and have a reference solution. Test both directions (should act / should not act), isolate trials, grade outcomes not paths, and calibrate LLM judges against humans. Track pass@k vs pass^k and read transcripts (S5). [V]
10. **"Harness engineering" as a working habit** (Hashimoto): whenever an agent makes a mistake, add a fix so it never makes that mistake again, either an AGENTS.md line or a real tool/script (S13). OpenAI reached the same idea at team scale (S11). [V/V-arch]

---

## Findings

### S1 — Anthropic, "Building effective agents" (Dec 19, 2024)
- Distinguishes **workflows** (LLMs and tools run along predefined code paths) from **agents** (the LLM directs its own process and tool use). Recommends the simplest solution and adding complexity only when it measurably helps. [V]
- Catalogues patterns: prompt chaining with programmatic "gates", routing, parallelisation (sectioning/voting), orchestrator-workers, evaluator-optimizer. Evaluator-optimizer fits when there are clear evaluation criteria and iterating produces measurable gains. [V]
- A separate model call for guardrails/screening tends to beat one call doing both the task and the guardrail. This is early support for maker ≠ checker. [V]
- Agents must get "ground truth" from the environment (tool results, code execution) at each step. Autonomy compounds errors, so test in sandboxes with guardrails. [V]
- Three principles: simplicity, transparency (show the planning steps), and a carefully designed agent-computer interface (ACI) through tool docs and testing. [V]
- Tool advice (App. 2): pick formats close to natural text with no counting or escaping overhead, and "poka-yoke" tools. For SWE-bench they spent more time on tools than on the prompt. Requiring absolute file paths removed a class of errors. [V]
- Coding agents suit this because tests verify the output, but human review remains crucial for fit with wider system requirements. [V]
- The page now carries a note that much of the tooling landscape has changed since Dec 2024, and points to Managed Agents. [V]

### S2 — Anthropic, "Effective context engineering for AI agents" (Sep 29, 2025)
- **Context engineering** means curating the whole token state (system prompt, tools, MCP, data, history) at every inference step. It is the successor to prompt engineering. [V]
- **Context rot**: recall degrades as the token count grows. Treat context as a finite "attention budget" with diminishing returns. Guiding principle: "find the smallest set of high-signal tokens" (S2). [V]
- Write system prompts at the right altitude, between brittle if-else logic and vague guidance. Start with a minimal prompt on the best model, then add instructions or examples driven by observed failures. [V]
- Bloated or overlapping toolsets are a top failure mode: if a human can't say which tool applies, the agent can't either. Prefer a few diverse canonical examples to long lists of edge-case rules. [V]
- **Just-in-time retrieval**: hold lightweight references (paths, queries, links) and load data on demand, which enables progressive disclosure. Claude Code is a hybrid: CLAUDE.md is loaded up front, and glob/grep fetch the rest on demand. [V]
- Long-horizon techniques: **compaction** (tune for recall first, then precision; clearing tool results is the lightest form), **structured note-taking** (NOTES.md, to-do lists, memory tool), and **sub-agents** that explore widely and return summaries of about 1–2k tokens. [V]
- Their standing advice as models improve is to do the simplest thing that works. [V]

### S3 — Anthropic, "Writing effective tools for agents — with agents" (Sep 11, 2025)
- Tools are a contract between deterministic systems and non-deterministic agents, so design them for agents, not as thin API wrappers. [V]
- **Eval-driven tool development**: prototype, write realistic multi-step eval tasks with verifiable outcomes, and run them in simple agent loops. Collect accuracy plus runtime, tool-call count, tokens and errors. Use held-out test sets to avoid overfitting. [V]
- Build fewer, consolidated tools aimed at high-impact workflows (e.g. `search_logs` instead of `read_logs`). **Namespace** tools by service and resource. The choice of prefix vs suffix measurably changes results. [V]
- Return high-signal, human-readable fields rather than opaque IDs. Offer a `response_format` enum (concise/detailed). The concise form used about a third of the tokens in their example. [V]
- Paginate, filter and truncate with sensible defaults. Claude Code capped tool responses at 25,000 tokens by default (current value not re-checked [U]). Error messages should say what to do, not dump codes or tracebacks. [V]
- Describe tools as you would to a new hire, use unambiguous parameter names (`user_id`, not `user`), and enforce with strict data models. Small description edits produced large gains. [V]
- Read the raw transcripts, not only the agent's own feedback, because what agents omit matters. [V]

### S4 — Anthropic, "Code execution with MCP: Building more efficient agents" (Nov 04, 2025)
- Loading every tool definition up front, and passing intermediate results through the model, wastes tokens and invites copy errors. [V]
- Alternative: present MCP servers as a code API on a filesystem (one file per tool). The agent discovers tools by listing directories or calling a `search_tools` tool with a detail level. Their example dropped from about 150k to about 2k tokens. [V]
- Filter and aggregate data inside the execution environment and return only what is needed, e.g. 5 rows instead of 10,000. Loops and conditionals run in code rather than through repeated model turns. [V]
- Intermediate data can stay out of the model entirely. The harness can tokenise PII and set **deterministic rules for where data may flow**. [V]
- State and reusable code persist to files and can become Skills (a SKILL.md next to saved functions). [V]
- Cost: agent-generated code needs a secure sandbox, resource limits and monitoring. Weigh this against the token savings. [V]

### S5 — Anthropic, "Demystifying evals for AI agents" (Jan 09, 2026)
- Vocabulary: task, trial, grader, transcript, **outcome** (the final state of the environment, not what the agent claims), evaluation harness, agent harness. Evaluating "an agent" evaluates the harness and model together. [V]
- Grader types: **code-based** (fast, objective, can be brittle), **model-based** (flexible, non-deterministic, needs human calibration), **human** (gold standard, slow). Scoring can be weighted, binary or hybrid. [V]
- **Capability evals** start at low pass rates. **Regression evals** should sit near 100%. Saturated capability tasks move into the regression suite. [V]
- Roadmap: start early with 20–50 tasks drawn from real failures. Tasks must be unambiguous, so that two experts reach the same verdict, and each needs a **reference solution**. Build balanced sets that test both should-act and should-not-act. Use isolated, clean trials, since shared git history once inflated scores. [V]
- Prefer deterministic graders, then LLM graders, with sparing human validation. Give partial credit. Give LLM judges an "Unknown" option and one isolated judge per rubric dimension. Make graders resistant to hacks. Advice: "grade what the agent produced, not the path it took" (S5). [V]
- **Non-determinism**: pass@k (at least one success in k tries) vs pass^k (all k succeed). Pick according to whether one success or consistency is what matters. [V]
- A 0% pass rate across many trials usually means the task is broken. Don't take scores at face value until someone has read transcripts. Grading bugs once moved a benchmark from 42% to 95%. [V]
- Evals are living artefacts with clear owners. Practise eval-driven development, and let product people contribute tasks as PRs. [V]

### S6 — Anthropic, "Effective harnesses for long-running agents" (Nov 26, 2025)
- Two failure modes: trying to one-shot the whole job and running out of context mid-feature, and a later session seeing progress and **declaring victory prematurely**. Compaction alone was not enough. [V]
- An **initializer agent** writes `init.sh`, a `claude-progress.txt` log, an initial git commit and a **feature list** (200+ end-to-end features, all starting as "failing"). [V]
- Coding agents may only change the `passes` field in that list and are told firmly not to remove or edit tests. JSON was chosen because models are less likely to overwrite it inappropriately than Markdown. [V]
- **One feature per session**. End each session in a clean, mergeable state with descriptive commits and a progress summary. Git makes rollback possible. [V]
- Agents tended to mark features done without end-to-end testing. Explicitly prompting it to test end to end through browser automation, the way a human user would, improved results a lot. Tool blind spots (e.g. native alert modals) remained. [V]
- Session start ritual: `pwd`, read the git log and progress file, pick the highest-priority failing feature, and run a basic end-to-end smoke test **before** new work. [V]
- Open question: whether specialised agents (testing, QA, cleanup) beat one general agent. The authors expect the lessons to carry over to other domains. [V]

### S7 — Anthropic, "Harness design for long-running application development" (Mar 24, 2026)
- Takes GANs as its inspiration: a **generator** and a separate **evaluator**. Later a three-agent **planner → generator → evaluator** design for multi-hour full-stack builds. [V]
- **Self-evaluation is lenient.** Agents praise mediocre work. Tuning a standalone evaluator to be skeptical is far more tractable than making a generator critical of itself. [V]
- Subjective quality becomes gradable through explicit criteria (design quality, originality, craft, functionality), weighting, and **few-shot calibration** of the evaluator. The criteria wording itself steers the generator. [V]
- The evaluator **exercises the running artefact** (Playwright) and grades against **hard per-criterion thresholds**. Any criterion below threshold fails the sprint. Out of the box Claude was a poor QA agent: it talked itself out of real bugs and tested superficially. Several rounds of tuning from its logs were needed. [V]
- Before each sprint, generator and evaluator negotiate a **sprint contract** that defines testable "done" before any code. Agents communicate through files. The planner stays at product and high-level design, because detailed specs that are wrong cascade downstream. [V]
- Result: the solo run took 20 min and cost $9, with a broken core feature. The full harness took 6 h and cost $200, and the core feature worked. [V]
- **Every harness component encodes an assumption about model limits.** Remove components one at a time. With Opus 4.6 the sprint construct was dropped. The evaluator moved to a single end-of-run pass and is worth it only when the task exceeds what the model does reliably alone. [V]
- Context resets (a clean slate plus a handoff artefact) vs compaction: resets fixed Sonnet 4.5's "context anxiety". Opus 4.5 largely removed the need. [V]

### S8 — (index check) Anthropic Engineering blog listing
- The listing shows posts up to Apr 23, 2026 plus a featured undated post, "How we contain Claude across products". There is no loops post on the Engineering blog; the loops guidance is on claude.com/blog (S10). [V]

### S9 — Claude Code Docs, "Best practices for Claude Code" (living doc; the original Engineering post dated Apr 18, 2025 now 308-redirects here)
- Most practices follow from one constraint: the context window fills fast and performance drops as it does. [V]
- **Give Claude a check it can run** (tests, build exit code, linter, fixture diff, screenshot comparison). Gating options, from weakest to strongest: in-prompt → `/goal` (a separate evaluator re-checks after each turn) → **Stop hook** (a script blocks the turn from ending; Claude Code overrides after 8 consecutive blocks) → a verification subagent, so the worker is not the grader. [V]
- Ask for **evidence rather than assertions** (test output, the commands run, screenshots). Failure-pattern fix: "If you can't verify it, don't ship it" (S9). [V]
- Workflow: explore → plan (plan mode) → implement → commit. Skip planning when the diff fits in one sentence. For large features, have Claude interview you into a self-contained SPEC.md that ends in an end-to-end verification step, then run it in a fresh session. [V]
- CLAUDE.md: short, loaded every session, only broadly applicable content. Put occasional knowledge in on-demand **skills**. Prune lines Claude already follows or turn them into hooks. Emphasise at most a few lines. Check it into git. **Hooks** are for zero-exception actions. [V]
- Context hygiene: `/clear` between tasks. After two failed corrections, clear and re-prompt. Customise what compaction preserves through CLAUDE.md. Use subagents for investigation. [V]
- Scale: `claude -p` in CI, fan-out loops with `--allowedTools`, test on 2–3 items before the full batch. Writer/Reviewer sessions. An **adversarial review subagent** sees only the diff and criteria, and should flag only correctness or requirement gaps to avoid over-engineering. [V]

### S10 — Claude blog, "Loop engineering: Getting started with loops" (June 30, 2026; Delba de Oliveira, Michael Segner)
- Defines a loop as an agent repeating cycles of work until a stop condition is met. Loops are classified by trigger, stop criterion, primitive and fitting task. Start simple. [V]
- **Turn-based** (the agentic loop): improve verification by encoding manual checks in a SKILL.md with tools/connectors. The more quantitative the checks, the easier self-verification is. [V]
- **Goal-based** (`/goal`): an evaluator model checks the condition each time Claude tries to stop. Deterministic criteria (tests passed, score thresholds) plus explicit turn caps work best. [V]
- **Time-based** (`/loop` local, `/schedule` cloud routines) for recurring or external-system work. **Proactive** loops combine schedule, goal, dynamic workflows and auto mode for streams such as triage and dependency upgrades. [V]
- Quality: keep the codebase clean because Claude copies existing patterns, make docs reachable, use a second agent to review. "Loops that write code need loops that check it" (S10). Encode each individual failure into the system. [V]
- Cost: choose the right primitive and model, define stop criteria, **pilot before a large run**, **use scripts for deterministic work**, match the interval to the rate of change, review `/usage`. [V]

### S11 — OpenAI, "Harness engineering: leveraging Codex in an agent-first world" (Feb 11, 2026; Ryan Lopopolo)
- Over about five months, roughly 1M lines of code were written with **no manually written code** and about 1,500 merged PRs. Three engineers drove it (later seven), about 3.5 PRs per engineer per day. Thesis: "Humans steer. Agents execute." (S11). [V-arch]
- When the agent fails, the fix is almost never to try harder. Humans ask what capability is missing and how to make it **legible and enforceable** for the agent. [V-arch]
- **Application legibility**: an app instance bootable per git worktree, Chrome DevTools Protocol wired in, and an ephemeral per-worktree observability stack (LogQL/PromQL). This turns numeric performance goals into tractable prompts. Single runs of 6+ hours. [V-arch]
- **Repo as system of record**: the one-big-AGENTS.md approach failed because it crowded out context, too much guidance became no guidance, it went stale, and it couldn't be checked mechanically. Replaced by a roughly 100-line AGENTS.md used as a map into a structured `docs/` tree (design docs, exec plans active/completed, tech-debt tracker, product specs, references, quality score). Linters/CI check freshness and cross-links, and a recurring **doc-gardening agent** opens fix-up PRs. [V-arch]
- **Enforce invariants, not implementations.** A layered domain architecture has mechanically validated dependency directions. Custom lints cover structured logging, naming, file-size limits and reliability rules, and their **error messages inject remediation instructions**. Rules move from docs into code when docs fall short. [V-arch]
- **Merge philosophy**: minimal blocking gates, short-lived PRs, flakes handled by re-runs. The post says this would be irresponsible in a low-throughput setting. Review has moved mostly to agent-to-agent, in a Ralph-Wiggum-style loop until reviewers are satisfied. [V-arch]
- **Entropy / garbage collection**: agents copy existing patterns, including bad ones. Replaced a weekly Friday clean-up of AI slop (20% of the week) with encoded golden principles and recurring background cleanup tasks that update quality grades and open small refactor PRs. [V-arch]
- Autonomy: one prompt can take a change from bug reproduction (with a video) through fix, validation, PR, feedback and merge, **escalating to a human only when judgment is required**. The team warns this depends on repo-specific investment. [V-arch]

### S12 — agents.md (open format site, current)
- AGENTS.md is a "README for agents": a predictable place for build/test commands, code style, testing instructions, security notes and PR conventions that would clutter a README. Plain Markdown with no required fields. [V]
- **Nested files** for monorepos: the nearest AGENTS.md in the directory tree wins, and **explicit user chat prompts override everything**. The site notes the main OpenAI repo had 88 AGENTS.md files. [V]
- Agents will try to run listed test commands and fix failures before finishing. Treat the file as living documentation. [V]
- Claims to be used by more than 60k open-source projects. Now stewarded by the Agentic AI Foundation under the Linux Foundation. [V]
- Supported agents shown include Codex, Jules, Cursor, Gemini CLI, VS Code, Copilot coding agent and others. Claude Code is not among the logos on the landing page. Whether Claude Code natively reads AGENTS.md was not checked here [U]; S9 confirms CLAUDE.md supports `@path` imports [V]. [V]

### S13 — Mitchell Hashimoto, "My AI Adoption Journey" (February 5, 2026)
- Drop chatbots for real coding work. An agent at minimum needs to read files, run programs and make HTTP requests in a loop. [V]
- Build expertise by reproducing your own manual commits with an agent. Break sessions into clear tasks, separate planning sessions from execution sessions, and give the agent a way to verify its work. [V]
- End-of-day agents for research, exploratory parallel tries and **read-only triage** (agents were not allowed to respond publicly, only to report). [V]
- Hand off the "slam dunks" and turn off agent notifications, so the human decides when to switch context. [V]
- **"Engineer the Harness"**: the surest path to right-first-time output is fast, high-quality tools that automatically tell the agent when it is wrong. He calls this "harness engineering": whenever an agent errs, "engineer a solution such that the agent never makes that mistake again" (S13). [V]
- Two forms: (a) AGENTS.md lines, **each tied to an observed bad behaviour**, and (b) real programmed tools (screenshot scripts, filtered test runners) plus an AGENTS.md pointer to them. [V]
- He does not claim to have coined the term, and says he'll adopt an existing one if it exists. [V]

---

## Rulebook
Each rule is written to be testable. Mechanisms are Forge proposals. "Checker" means a separate agent in a fresh context whose tools are restricted.

| # | Rule (testable) | Source(s) | Forge enforcing mechanism |
|---|---|---|---|
| H1 | The root `CLAUDE.md` (and any root `AGENTS.md`) is ≤ 100 non-blank lines and ≤ ~2.5k tokens. It works as a map: every section links to a `docs/` or skill path that exists. | S9, S11, S2 | **CI lint** `forge-lint context`: line/token count plus link-target existence. **Eval case**: a session-start token budget on the injected context. |
| H2 | Every behavioural line in root context names the failure it prevents (incident or eval ID). Lines without provenance fail the lint. | S13, S9 | **Lint**: each rule line carries `(why: EVAL-### / INC-###)`. **Skill** `/forge:postmortem` writes the line and the ID together. |
| H3 | Any "must always / must never" behaviour is enforced by a hook, lint, test or permission rule, not prose alone. Each MUST/NEVER line in context files maps to a mechanism ID. | S9, S11, Forge principle | **Lint** that cross-references MUST/NEVER lines to a `mechanisms.yaml` registry. **CI** fails on unmapped imperatives. |
| H4 | No task starts implementation without a runnable pass/fail check defined (test, DRC/ERC, FEA margin script, dimension check). | S9, S10, S6, S13 | **Skill** `/forge:contract` writes `.forge/tasks/<id>/contract.json`. **PreToolUse hook** blocks Edit/Write on design sources when the active task has no contract. |
| H5 | A task can end as "done" only if its check has passed *after* the last edit to the files in scope. | S9, S6 | **Stop hook**: compare the verification artefact's timestamp and exit code with the last edit time and block if stale or failing. Mind the Claude Code override after 8 consecutive blocks (S9) by also recording the failure in state. |
| H6 | Completion reports include evidence: the exact command, the exit code, key numbers (mass, clearance, margin, DRC count) and artefact paths. Adjectives are not evidence. | S9, Forge "numbers beat pictures" | **Report JSON schema** validated in the Stop hook. **Eval case** fails any transcript whose final report has no evidence block. |
| H7 | Maker ≠ checker. Acceptance comes from a separate checker agent in a fresh context, with read and execute-checks tools only (no Edit/Write). The generator's self-assessment never counts as acceptance. | S7, S9, S10, S1 | **Agent config** `forge-checker` (tools: Read, Grep, Glob, Bash(read-only check cmds)). **Permission deny** on Edit/Write for that agent. **CI** requires a checker verdict file whose `agent_id` differs from the maker's. |
| H8 | The checker grades against explicit criteria with **hard per-criterion thresholds**. Any criterion below threshold is a FAIL, and "minor, approve anyway" is not allowed. | S7, S5 | **Skill** rubric files with numeric thresholds. The checker's output schema has one boolean per criterion; a **CI job** recomputes the overall pass. |
| H9 | Before a checker is trusted, it is calibrated: agreement with human-labelled examples ≥ a set target on a calibration set, re-measured when its model or prompt changes. | S7, S5 | **Eval suite** `checker-calibration` (labelled pass/fail artefacts). **CI** blocks changes to the checker prompt or model when agreement drops. |
| H10 | Checker findings are split into blocking (correctness or requirement gaps) and advisory. Only blocking findings stop progress. | S9 | **Reviewer output schema** with a `severity` enum. The **Stop hook / CI** gates only on `blocking`. |
| H11 | Maker and checker agree on "done" before build (contract), and communicate through files in the repo. | S7, S6 | **Skill** `/forge:contract` has a propose → review → agree cycle. The contract file has `status: agreed` plus both signatures (checked by a hook). |
| H12 | Long-running work keeps its state in a JSON feature/requirement list. Agents may change only `status`/`passes` fields and may never delete or reword criteria. | S6 | **PreToolUse hook** diffs `requirements.json`: rejects changes to anything except status fields. **JSON-schema CI** check. |
| H13 | One requirement or feature per work increment. Each increment ends with the tree clean, checks green and a descriptive commit plus a progress-log entry. | S6, S11 | **Stop hook**: `git status` clean, last commit touches `progress.md`, checks pass. |
| H14 | Every session starts with orientation: working directory, recent git log, progress file, then a **smoke check** of the existing design before new work. | S6 | **SessionStart hook** injects a progress summary and runs `.forge/init.sh --smoke`. A failure is surfaced as the first task. |
| H15 | Exploration and research go to subagents that return ≤ ~2k-token summaries. The main agent keeps context for synthesis and decisions. | S2, S9 | **Agent config**: research/explore agents with an output-length instruction. An **eval** tracks main-context tokens per task. |
| H16 | Domain knowledge (build123d idioms, IPC rules, MCU errata) lives in on-demand skills and `docs/`, not in root context. | S9, S2, S4, S11 | **Lint**: forbid domain sections in root CLAUDE.md. A **plugin eval** checks each skill triggers and does not over-trigger (see H27). |
| H17 | Forge tools/MCP servers are few and consolidated, and namespaced `forge_<domain>_<verb>`. Parameters are unambiguous (`part_id`, `net_name`) and paths absolute. | S3, S1 | **Tool-schema lint** in CI: name pattern, a minimum description length, a banned list of generic parameter names, absolute-path validation in handlers. |
| H18 | Tools that can return large payloads (meshes, netlists, sim fields, logs) support filtering/pagination and a `response_format` (concise/detailed), and by default return summaries plus file paths under a token cap. | S3, S4 | **Tool contract tests** (max response tokens for default args). A **PostToolUse hook** flags outputs over the cap. |
| H19 | Tool errors say what to do next (valid ranges, an example call), not bare codes or tracebacks. | S3, S11 | **Tool contract tests**: an invalid call must return a message matching a remediation pattern. Custom **lint messages** carry fix-it text. |
| H20 | Heavy or deterministic computation (mass properties, tolerance stacks, BOM rollups, DRC parsing) runs as scripts in a sandbox. The model sees only results. | S4, S10 | **Skills ship scripts**. **Sandbox/permission rules** for execution. An **eval** checks that the script is called rather than re-derived. |
| H21 | Architecture and "taste" invariants for design-as-code are enforced by custom lints and structural tests. Examples: units declared, parameters centralised, no magic numbers in CAD, allowed dependency directions between mech/elec/fw modules. | S11 | A **CI lint suite** `forge-lint cad/elec/fw` whose remediation messages are written for agents. |
| H22 | Every observed agent mistake gets a durable fix (lint, hook, tool or context line) **and** a regression eval case that reproduces it. | S13, S11, S10, S5 | **Skill** `/forge:postmortem`. **CI** requires each `incidents/*.md` to link an eval ID and a mechanism ID. |
| H23 | Every loop or routine declares a deterministic stop condition and a turn/cost cap. | S10, S9 | **Lint** on Forge routine/goal definitions (required `stop_when`, `max_turns`, `budget`). **Stop-hook** counters. |
| H24 | Batch/fan-out runs pilot on 2–3 items and are reviewed before the full run. | S9, S10 | **Workflow skill** with a mandatory pilot stage and a human or checker sign-off artefact. |
| H25 | Unattended runs use scoped permissions (explicit allowlists) and sandboxing. Irreversible, physical or money actions (ordering parts, submitting fab files, flashing production hardware) always require a human signature. | S9, S4, S11, S1, Forge principle | **Permission rules** (`ask`/`deny` on fab/order/flash tools). A **PreToolUse hook** requires a signed approval file with a hash of the exact artefact. |
| H26 | Evals start with 20–50 tasks from real failures. Each task has an unambiguous spec and a **reference solution** that passes all graders. A 0% pass@N task is triaged as a possible broken task. | S5 | An **eval suite** layout check in CI (every task has a `reference/` that passes). A **CI job** flags tasks at 0% over N trials. |
| H27 | Eval sets are balanced: every "should do X" behaviour (e.g. run DRC, invoke a skill) has a paired "should not" case. | S5 | **Eval lint**: a paired-case tag coverage check. |
| H28 | Trials run in isolated clean environments (fresh worktree, no prior trial's git history or caches). | S5 | The **eval harness** creates a fresh worktree/container per trial. A **CI assertion** checks that no shared state paths exist. |
| H29 | Graders check **outcomes** (the artefact state and its numbers), not tool-call sequences. Process checks are allowed only where the process is itself a requirement (e.g. "DRC ran on the exported Gerbers"). | S5, S3 | **Eval grader config**: outcome graders are required; `tool_calls` graders must carry a `requirement_ref`. |
| H30 | Deterministic graders first. LLM judges get one isolated rubric dimension each, an "Unknown" option, and periodic human calibration. | S5, S7 | **Eval grader config** and a calibration **CI job**. |
| H31 | Report capability and regression suites separately. Regression runs report pass^k (consistency) for safety-relevant behaviours; capability runs may report pass@k. | S5 | An **eval report schema** plus a **CI gate** on regression pass^k. |
| H32 | No eval score is accepted without a transcript review sample, recorded per release. | S5, S3 | **CI release checklist** requires `eval-review.md` with the transcript IDs reviewed. |
| H33 | Each harness component (agent, hook, loop stage) records the model limitation it assumes. On a model change, components are removed one at a time and kept only if evals show a loss without them. | S7, S1 | A **`harness-components.yaml`** with an `assumption:` field. An **eval ablation CI job** triggers on model change. |
| H34 | New agents or pipeline stages are added only with an eval delta showing improvement over the simpler configuration. | S1, S7, S10 | An **ADR template** field `eval_evidence`, checked by **CI** for new `agents/*.md`. |
| H35 | Planners write product/requirements-level specs (what and why, acceptance criteria), not implementation details. | S7, S11 | The **planner agent prompt** plus a **lint** that flags code blocks or low-level parameters in `specs/`. |
| H36 | The repo is the system of record. Decisions, specs, active/completed plans and tech debt are versioned in `docs/`. Anything the agent needs but can't reach in-repo counts as missing. | S11, S12 | A **docs lint** (index files, cross-links, owners, a freshness date). A scheduled **doc-gardening routine** opens fix-up PRs. |
| H37 | Design artefacts are legible to agents: each worktree can build, simulate and check its own design, with numeric outputs in JSON. | S11, S6, S7 | A `forge verify` **CLI** emitting JSON metrics. **Worktree isolation**. An **eval** on end-to-end self-verification. |
| H38 | Recurring garbage collection: scheduled cleanup agents scan for violations of golden principles and open small, single-purpose refactor PRs. | S11, S10 | A **scheduled routine** (`/schedule`) plus a `QUALITY_SCORE.md` updated by CI. |
| H39 | Compaction/handoff preserves the modified-file list, active contract and check commands. Long work is resumable from files alone. | S2, S7, S9 | **CLAUDE.md compaction instruction** [V S9] plus a **resume eval**: a fresh session must continue from files alone. |
| H40 | Machine-edited state files are JSON/YAML with schemas, not free Markdown. | S6 | **JSON-schema CI** check on `.forge/**/*.json`. |
| H41 | Subproject context is nested (mech/, elec/, fw/ each have their own context file); the nearest file wins; user instructions override. | S12 | **Lint**: each domain dir has a context file ≤ N lines. An **eval** checks domain rules are applied only in that domain. |

---

## Conflicts between sources and how Forge should resolve them
1. **Merge gates and human review.** OpenAI runs minimal blocking gates, re-runs flakes and needs no human PR review, because at their throughput fixing things later is cheap and waiting is costly (S11). Anthropic says human review stays crucial for system fit (S1). Forge requires human signatures on safety, money and fabrication. **Resolution:** tier the gates by reversibility. Software, docs and simulation-only changes may use OpenAI-style fast agent-reviewed merges behind checker plus CI. Anything that crosses into the physical world (fab release, part orders, production flashing, safety claims) gets a blocking human gate (H25). The "corrections are cheap" premise does not hold for fabrication. S11 itself calls its approach irresponsible outside high-throughput settings.
2. **Compaction vs context reset.** S2 calls compaction the first lever. S6 found compaction insufficient. S7 needed resets for Sonnet 4.5 but not for Opus 4.5 or 4.6. **Resolution:** make work resumable from files regardless of strategy (H12–H14, H39). Choose compaction or reset per model with an eval, and don't hard-code either.
3. **Complexity budget.** S1 and S10 say start simple. S7 shows a 20x-cost multi-agent harness producing clearly better output. **Resolution:** maker ≠ checker is a Forge principle and always applies to acceptance (H7). Heavier structure (planner, sprint loops, multi-round QA) needs eval evidence (H34) and is ablated on model upgrades (H33).
4. **Self-verification vs separate evaluator.** S9 and S10 encourage Claude to run its own checks. S7 shows self-*evaluation* is lenient. **Resolution:** self-run *deterministic* checks (numbers, exit codes) are welcome as maker-side feedback. Judgement-based acceptance always comes from the separate checker (H5, H7).
5. **Reviewer bias in both directions.** S9 warns reviewers over-report gaps and drive over-engineering. S7 warns evaluators under-report and approve bugs. **Resolution:** use explicit criteria with thresholds, a blocking/advisory split (H8, H10), and human-labelled calibration (H9).
6. **Grade outcome vs path.** S5 advises against grading tool sequences, yet its own example YAML has a `tool_calls` grader, and S3 optionally specifies expected tools. **Resolution:** outcome graders by default. Process checks only where the process is a stated requirement, e.g. DRC must run before Gerber export (H29).
7. **Emphasis in instructions.** S6 used strongly worded instructions forbidding test edits. S9 says to emphasise sparingly, and S11 says when everything is important nothing is. **Resolution:** keep emphasis rare in prose and use mechanisms for invariants (H3, H12). The S6 JSON-edit rule becomes a hook.
8. **Frameworks vs thin harness.** S1 warns that frameworks hide prompts and add abstraction. Forge is effectively a framework (a plugin). **Resolution:** keep Forge transparent. Hooks and scripts are plain files in the repo, prompts are readable, and there are no hidden layers. Every component must be explainable in `harness-components.yaml` (H33).
9. **AGENTS.md vs CLAUDE.md.** agents.md is the cross-tool standard (S12). Claude Code's docs centre on CLAUDE.md with `@` imports (S9). **Resolution:** a canonical short map in one file imported by the other. Native AGENTS.md support in Claude Code was not checked here [U]; see R1a.
10. **Tool consolidation vs code-API exposure.** S3 favours fewer consolidated tools. S4 favours exposing many tools as code files for progressive disclosure, at the cost of sandbox overhead. **Resolution:** a few consolidated MCP tools for common high-level workflows, plus a sandboxed Python/build123d code path for heavy data work (H17, H20).

---

## Not found / discrepancies
- **Title differences.** The brief's "Writing effective tools for agents" is actually titled "Writing effective tools for agents — with agents"; the body links it as "Writing tools for AI agents – with AI agents". "Code execution with MCP" is actually "Code execution with MCP: Building more efficient agents". [V]
- **Claude Code best practices.** `anthropic.com/engineering/claude-code-best-practices` ("Claude Code: Best practices for agentic coding", Apr 18, 2025 in the listing) now **308-redirects** to `code.claude.com/docs/en/best-practices` ("Best practices for Claude Code"), a living doc with no publication date. Its content (e.g. `/goal`, auto mode, agent view) is newer than 2025. Findings S9 reflect the current doc. [V]
- **"Harness design … generator–evaluator (Mar 2026)"** is confirmed as "Harness design for long-running application development", Mar 24, 2026, by Prithvi Rajasekaran. It covers a generator–evaluator loop and a three-agent planner/generator/evaluator design. [V]
- **"Claude Code team guidance on loops (Jun 2026)"** is on **claude.com/blog**, not the Anthropic Engineering blog: "Loop engineering: Getting started with loops", June 30, 2026. The Engineering index has no loops post. [V]
- **OpenAI post.** The live URL returned HTTP 403 to both curl and WebFetch. Content was read from a Wayback snapshot of the same URL dated 2026-09-13. Title, author (Ryan Lopopolo) and date (Feb 11, 2026) were confirmed in OpenAI's RSS feed. Tagged [V-arch]. It could not be confirmed whether the live page has changed since that snapshot [U].
- **Hashimoto.** The post is "My AI Adoption Journey", February 5, 2026. The term appears in "Step 5: Engineer the Harness". He explicitly says he doesn't know whether an industry term exists, so it is not a claim of coinage. The linked Ghostty AGENTS.md example was not fetched [U].
- **Building effective agents** now carries an editor's note that the tooling landscape has changed since Dec 2024 and points to Managed Agents. [V]
- The **Claude Code 25,000-token tool-response cap** is stated in S3 (Sep 2025). Its current value was not re-checked [U].
- **Related OpenAI posts seen only in RSS (not read):** "Unrolling the Codex agent loop" (Jan 23, 2026), "Unlocking the Codex harness: how we built the App Server" (Feb 4, 2026), "Codex-maxxing for long-running work" (Jun 22, 2026), "OpenAI co-founds Agentic AI Foundation, donates AGENTS.md" (Dec 9, 2025). Titles and dates [V] from RSS; content [U].
- The WebSearch result summary said the loops post "became a foundational reference". That is a secondary characterisation [R] and is not used here.

---

## Sources
| # | Title | URL | Published | Type | Accessed |
|---|---|---|---|---|---|
| S1 | Building effective agents | https://www.anthropic.com/engineering/building-effective-agents | 2024-12-19 | Anthropic Engineering blog | 2026-09-25 |
| S2 | Effective context engineering for AI agents | https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents | 2025-09-29 | Anthropic Engineering blog | 2026-09-25 |
| S3 | Writing effective tools for agents — with agents | https://www.anthropic.com/engineering/writing-tools-for-agents | 2025-09-11 | Anthropic Engineering blog | 2026-09-25 |
| S4 | Code execution with MCP: Building more efficient agents | https://www.anthropic.com/engineering/code-execution-with-mcp | 2025-11-04 | Anthropic Engineering blog | 2026-09-25 |
| S5 | Demystifying evals for AI agents | https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents | 2026-01-09 | Anthropic Engineering blog | 2026-09-25 |
| S6 | Effective harnesses for long-running agents | https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents | 2025-11-26 | Anthropic Engineering blog | 2026-09-25 |
| S7 | Harness design for long-running application development | https://www.anthropic.com/engineering/harness-design-long-running-apps | 2026-03-24 | Anthropic Engineering blog | 2026-09-25 |
| S8 | Engineering at Anthropic (index) | https://www.anthropic.com/engineering | n/a (listing) | Blog index | 2026-09-25 |
| S9 | Best practices for Claude Code | https://code.claude.com/docs/en/best-practices (redirect target of https://www.anthropic.com/engineering/claude-code-best-practices, orig. 2025-04-18) | living doc, undated | Official product docs | 2026-09-25 |
| S10 | Loop engineering: Getting started with loops | https://claude.com/blog/getting-started-with-loops | 2026-06-30 | Claude (Anthropic) product blog | 2026-09-25 |
| S11 | Harness engineering: leveraging Codex in an agent-first world | https://openai.com/index/harness-engineering/ (read via https://web.archive.org/web/20260913183535/https://openai.com/index/harness-engineering/; metadata via https://openai.com/news/rss.xml) | 2026-02-11 | OpenAI Engineering blog | 2026-09-25 |
| S12 | AGENTS.md | https://agents.md/ | living site, undated | Open-format spec site (AAIF / Linux Foundation) | 2026-09-25 |
| S13 | My AI Adoption Journey | https://mitchellh.com/writing/my-ai-adoption-journey | 2026-02-05 | Personal blog (Mitchell Hashimoto) | 2026-09-25 |
