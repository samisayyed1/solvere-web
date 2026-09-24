# R1b — Claude Code orchestration, runtime and model features

- Date accessed: 2026-09-25 · Author: research agent (Phase 1) · Scope: /goal, /loop + Monitor + ScheduleWakeup, routines/scheduled tasks, channels, dynamic workflows, subagents/agent teams/agent view/SendMessage, advisor tool, model/effort/fast-mode config, output styles, CLI computer use, and the 2026 feature timeline (v2.0.77 → v2.1.282).

Tag legend: **[V]** read in an official/primary source (link given) · **[L]** verified locally by a command I ran (command given) · **[R]** secondary source only · **[U]** could not confirm. Source keys such as [S7] resolve to URLs in the Sources table and in the link definitions at the end of the file.

---

## Summary

1. **Version pinning comes first.** On this Mac the terminal `claude` is **2.1.270**, while the Desktop app runs its own bundled CLI at **2.1.280**. On npm, `latest` is 2.1.281, `stable` is 2.1.273 and `next` is 2.1.282. Opus 5.5 needs **v2.1.280 or later**, so the `stable` channel can't run it yet. [L] (`claude --version`; `ps -o command= -p $PPID`; `npm view @anthropic-ai/claude-code dist-tags`) [V][S12]
2. **`/goal` is a session-scoped, prompt-based Stop hook.** After each turn, a small fast model (Haiku by default) judges whether the condition holds. It reads only the transcript and never runs commands. It has no built-in turn or time cap: you write the bound into the condition, which can be up to 4,000 characters. It stops being available when `disableAllHooks` or `allowManagedHooksOnly` is set. [V][S1]
3. **Dynamic workflows** are JavaScript scripts run by the `Workflow` tool, built from `agent()`, `parallel()`, `pipeline()`, `phase()`, `log()`, `workflow()`, `args` and `budget`.
   - Where they live: saved in `.claude/workflows/` or `~/.claude/workflows/`. A plugin ships them from `workflows/` (or the manifest's `workflows` field) and they run as `/<plugin>:<meta.name>`.
   - How they start: the user opts in with the `ultracode` keyword, by asking for a workflow in their own words, or with `/effort ultracode`.
   - Limits: 1,000 agents per run, 4,096 items per `parallel`/`pipeline` call, and ≤16 concurrent agents (depends on CPU count). There is no mid-run user input.
   - Built-in workflow: `/deep-research` is bundled.
   - [V][S7] [V][S8] [L] (`/workflow-authoring` bundled skill)
4. **Subagents can't start workflows.** The `Workflow` tool is stripped from every subagent (as are `AskUserQuestion`, `ScheduleWakeup` and the plan-mode tools), so only the main thread orchestrates workflows.
   - Subagent nesting defaults to 3 levels (`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`).
   - At most 20 subagents run at once (`CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`).
   - Workflow `workflow()` calls nest only one level deep.
   - [V][S18] [L] (workflow-authoring skill)
5. **Plugin subagents ignore `hooks`, `mcpServers`, `permissionMode` and `initialPrompt`.** A read-only reviewer therefore has to be enforced through its `tools`/`disallowedTools` lists plus settings or hooks. For a fresh-context checker, `omitClaudeMd: true` (v2.1.271+) works for plugin subagents too. [V][S18] [V][S30]
6. **The advisor tool** is configured with `/advisor <model|off>`, the `advisorModel` setting, or the hidden `--advisor` flag.
   - Claude decides when to consult it. It can't be forced or capped in Claude Code, and it sees the same transcript as the main model.
   - Opus 5.5 as the main model accepts only Fable or Opus 5+ advisors. The API page doesn't list Opus 5.5 yet (see discrepancies).
   - It is second-opinion guidance, not an independent checker.
   - [V][S10] [V][S11]
7. **Model IDs are confirmed:** `claude-fable-5-1`, `claude-opus-5-5`, `claude-sonnet-5`, and `claude-haiku-4-5-20251001` (alias `claude-haiku-4-5`).
   - The `opus` alias means Opus 5.5 and `sonnet` means Sonnet 5 on the Anthropic API. `default` means Opus 5.5 on every paid plan.
   - Effort levels are `low|medium|high|xhigh|max`. **Opus 5.5 defaults to `medium`**, while other effort-capable models default to `high`, except Opus 4.7 (`xhigh`). `ultracode` is a Claude Code setting (xhigh plus automatic workflows), not an API effort level.
   - Haiku 4.5 retirement is "not sooner than Oct 15, 2026".
   - [V][S13] [V][S12]
8. **Scheduling options:**
   - `/loop` runs in-session: fixed cron, or self-paced through `ScheduleWakeup` at 60–3600 s. Recurring jobs expire after 7 days, and at most 50 tasks are allowed per session.
   - Desktop scheduled tasks run locally at intervals of ≥1 min, but only while the app is open and the machine is awake.
   - Cloud routines run at intervals of ≥1 h against a fresh clone, with no local files and no permission prompts, and each account has a daily run cap.
   - The Monitor tool streams background events. Each watch has a deadline of at most 30 minutes (10 minutes in `-p`).
   - [V][S2] [V][S3] [V][S4] [V][S9]
9. **Agent teams stay experimental.** They are enabled with `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`. Once they're on, any subagent Claude *names* becomes a teammate. Teams can't nest, there is one team per session, and in-process teammates don't come back on resume. Agent view (`claude agents`, `--bg`) runs background sessions under a supervisor, each in its own worktree. [V][S17] [V][S19]
10. **Auto mode is now the starting permission mode on Pro, Max and Team.** It drops broad allow rules: `Bash(*)`, wildcard interpreters, package-manager run commands, `Agent` and `Monitor` allow rules. Messages from other agents (SendMessage, teammates) never carry user authority. Forge's gates must therefore be narrow allow rules plus hooks, and a human sign-off can't be relayed through an agent. [V][S27] [V][S17]

---

## Findings

### 0. Versions and local environment

- **[L]** `claude --version` returns `2.1.270 (Claude Code)`. The binary is `/Users/samisayyed/.local/bin/claude` (`which -a claude`), and `~/.local/share/claude/versions` holds 2.1.211, 2.1.233 and 2.1.270.
- **[L]** The Desktop host process for this session is `.../Library/Application Support/Claude/claude-code/2.1.280/claude.app/...` with `CLAUDE_CODE_ENTRYPOINT=claude-desktop` (`ps -o command= -p $PPID`). Two CLI versions coexist on this machine.
- **[L]** npm dist-tags: `latest` 2.1.281, `stable` 2.1.273, `next` 2.1.282 (`npm view @anthropic-ai/claude-code dist-tags`).
- **[L]** Release months derived from npm `time`:
  | Month (2026) | Versions |
  | --- | --- |
  | Jan | 2.0.77–2.1.29 |
  | Feb | 2.1.30–2.1.63 |
  | Mar | 2.1.64–2.1.89 |
  | Apr | 2.1.90–2.1.126 |
  | May | 2.1.128–2.1.159 |
  | Jun | 2.1.160–2.1.197 |
  | Jul | 2.1.198–2.1.220 |
  | Aug | 2.1.221–2.1.252 |
  | Sep | 2.1.257–2.1.282 |
- **[V]** Release dates from the docs changelog: 2.1.0 Jan 7 · 2.1.32 Feb 5 · 2.1.71 Mar 7 · 2.1.80 Mar 19 · 2.1.98 Apr 9 · 2.1.139 May 11 · 2.1.154 May 28 · 2.1.219 Jul 24 · 2.1.224 Aug 7 · 2.1.257 Sep 1 · 2.1.269 Sep 11 · 2.1.271 Sep 14 · 2.1.273 Sep 15 · 2.1.280 Sep 22 · 2.1.281 Sep 23 · 2.1.282 Sep 24 ([S29]).
- **[L]** `sysctl -n hw.ncpu` returns `10`. The workflow skill states per-workflow concurrency as min(16, CPUs − 2), which gives **8 concurrent workflow agents** on this machine. The 8 is my inference from that formula.
- **[L]** `~/.claude/settings.json` contains a top-level `"effortLevel": "medium"`. Per [S12], a top-level user-settings `effortLevel` does **not** apply to Opus 5.5.
- **[V]** Several documented behaviours need versions newer than the local terminal CLI: the workflow pause at usage limits (2.1.271), `omitClaudeMd` (2.1.271), `SubagentHandback` (2.1.271), and Opus 5.5 (2.1.280). `TaskOutput` was removed in 2.1.277 ([S7], [S18], [S9], [S12], [S8]).

### 1. `/goal`

- **Syntax.** [V][S1] [V][S25]
  - `/goal <condition>` sets a goal and immediately starts a turn with the condition as the directive. Setting a new goal replaces the old one.
  - `/goal` on its own shows status: the condition, elapsed time, turns evaluated, token spend and the latest reason.
  - `/goal clear` removes the goal. `stop`, `off`, `reset`, `none` and `cancel` are aliases, and `/clear` also removes it.
  - One goal can be active per session. The condition can be up to **4,000 characters**.
- **How completion is judged.** [V][S1]
  - `/goal` wraps a *session-scoped prompt-based Stop hook*.
  - After each turn, Claude Code sends the condition plus the conversation to the configured small fast model: Haiku on the Claude API, overridable via `ANTHROPIC_DEFAULT_HAIKU_MODEL`, which also moves all other background work to that model.
  - There are three verdicts: *not yet met* (the reason is fed back as guidance), *met* (the goal clears and is logged as achieved), and *impossible* (the goal clears and is logged as failed).
  - The evaluator calls **no tools**. It judges only what Claude surfaced in the transcript. The docs advise writing the condition with one measurable end state, a stated check command, and the constraints that must not change.
- **Bounds.** [V][S1]
  - There is no built-in turn or time cap. The docs tell you to put a clause such as "or stop after 20 turns" into the condition, which the evaluator then judges from the conversation.
  - If Claude keeps answering the evaluator with no tool use for several turns, the loop stops with a warning and the goal stays set.
  - Unrecoverable errors clear the goal: auth failure when Claude Code owns the credentials, exhausted credits, context overflow that compaction can't fix, or an unavailable model.
  - Transient errors retry up to 3 times, then pause (v2.1.269+ interactive). Rate and usage limits, or a hook that ended the turn, pause the goal.
- **Background work.** [V][S1]
  - Evaluation is skipped while a subagent or background shell is still running.
  - After 30 minutes waiting on background work, a check-in fires. The interval then backs off (×2, capped at ×4), with at most 3 idle check-ins per goal (v2.1.246+).
  - `CLAUDE_CODE_GOAL_CHECKIN_MINUTES` changes the first interval, and `0` turns off both check-ins and retries.
- **Resume.** An active goal is restored on every resume route (all routes since v2.1.239). The turn count, timer and token baseline reset. [V][S1]
- **Headless.** `claude -p "/goal …"` runs to completion. Use `--output-format stream-json --verbose` to watch progress. [V][S1]
- **Interaction with Stop hooks.** [V][S1] [V][S21] [V][S24]
  - Both fire after every turn.
  - A Stop hook lives in settings and can be a script (deterministic) or a prompt.
  - Stop hooks receive `stop_hook_active`, `last_assistant_message`, `background_tasks` and `session_crons`.
  - Claude Code overrides a Stop/SubagentStop hook after **8 consecutive blocks** (`CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`, where `0` disables the cap).
  - Stop/SubagentStop hooks may return `hookSpecificOutput.additionalContext` to keep the turn going without an error (W23, v2.1.158–165) ([S28]).
- **Requirements.** The same workspace-trust rule as settings hooks applies. `/goal` is unavailable when `disableAllHooks` is true or managed `allowManagedHooksOnly` is set. [V][S1]
- **Introduced** in v2.1.139 (May 11, 2026). [V][S30] [V][S29]

### 2. `/loop`, `ScheduleWakeup`, cron tools, Monitor

- **`/loop` forms.** `/loop` is a bundled skill; `/proactive` is an alias. [V][S2] [V][S25]
  - `/loop 5m <prompt>` runs on a fixed cron schedule.
  - `/loop <prompt>` is self-paced: Claude picks a delay of 1 min–1 h each iteration.
  - `/loop` or `/loop 15m` with no prompt runs the built-in maintenance prompt, or `.claude/loop.md` (which wins over `~/.claude/loop.md`). The file is truncated after 25,000 bytes.
  - Interval units are `s|m|h|d`. Seconds round up to a whole minute, and odd intervals round to a clean cron step.
- **Skills as the loop prompt.** A skill can be the prompt (`/loop 20m /review-pr 1234`). The following reach Claude as plain text instead of running: built-in commands, skills with `disable-model-invocation: true`, skills blocked by `skillOverrides` or a deny rule, and MCP prompts. [V][S2]
- **Self-paced mechanics.** [V][S2] [V][S8] [V][S9]
  - Claude calls `ScheduleWakeup` with `{delaySeconds, reason, prompt, noop?, stop?}`. The runtime clamps the delay to **60–3600 s**.
  - `stop: true` ends the loop (v2.1.202+).
  - If an iteration neither reschedules nor stops, one fallback wakeup fires about 20 minutes later, and the loop ends if that iteration also fails to reschedule.
  - Esc cancels a pending self-paced wakeup.
  - The pending wakeup appears in the Stop hook's `session_crons`.
- **Cron tools.** [V][S2]
  - `CronCreate` takes a 5-field cron expression (vixie semantics, local time, no `L`/`W`/`?`/names), the prompt, and a recurring-or-once flag. `CronList` and `CronDelete` manage tasks by their 8-character IDs.
  - The limit is **50 tasks per session**. Recurring tasks **expire after 7 days**, firing one last time.
  - Jitter: recurring tasks fire up to 30 minutes late (or up to half the interval, for intervals under an hour), and one-shot tasks at :00 or :30 fire up to 90 s early.
  - There is no catch-up for missed fires. Tasks fire only while the session is idle.
  - `CLAUDE_CODE_DISABLE_CRON=1` disables all of this.
  - With feature-flag fetching off, persisted tasks go to `.claude/scheduled_tasks.json`.
- **Monitor tool.** [V][S9] [V][S8] [V][S30]
  - Input is `{description, timeout_ms, command? | ws?:{url, protocols?}}`. Every stdout line (or WebSocket text frame) is delivered to Claude as an event.
  - The deadline defaults to 5 minutes, is capped at 30 minutes, and at 10 minutes in `-p` runs. Since v2.1.271 there is always a deadline, and the old `persistent` option is gone.
  - Monitor follows Bash permission rules. In auto mode, `Monitor` allow rules are dropped and the classifier reviews commands instead.
  - It is unavailable on Bedrock, Vertex (Agent Platform) and Foundry, and when `DISABLE_TELEMETRY` or `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` is set.
  - Added in v2.1.98 (Apr 9); WebSocket source since v2.1.195.
- **Plugin monitors.** [V][S22]
  - Declared in `monitors/monitors.json` or under `experimental.monitors` in `plugin.json`, as entries of the form `{name, command, description, when?}`.
  - `when` is `"always"` (the default) or `"on-skill-invoke:<skill>"`.
  - They run unsandboxed, at hook trust level, only in interactive CLI sessions, and can't reference `${user_config.*}`.
  - This is an *experimental* component.

### 3. Scheduling compared: cloud routines, Desktop tasks, `/loop`

[V][S2] [V][S4] (the same comparison table appears on both pages):

| | Cloud routine | Desktop task | `/loop` |
|---|---|---|---|
| Runs on | Anthropic cloud (or self-hosted env) | your machine | your machine |
| Machine on / session open | no / no | yes / no | yes / yes |
| Local files | no (fresh clone) | yes | yes |
| Permission prompts | none (autonomous) | per-task mode | inherits session |
| Minimum interval | 1 h | 1 min | 1 min |

- **Routines (research preview).** [V][S3]
  - Plans: Pro, Max, Team and Enterprise.
  - Create them at claude.ai/code/routines, in Desktop (Routines → New routine → Cloud), or in the CLI with `/schedule` (alias `/routines`). The CLI creates schedule triggers, and GitHub triggers since v2.1.225. API triggers and tokens are web-only.
  - Triggers: schedule (presets, custom cron via `/schedule update`, ≥1 h, one-off timestamps), API, and GitHub `pull_request.*` or `release.*` events with filters.
  - API trigger call: `POST https://api.anthropic.com/v1/claude_code/routines/<trig_id>/fire` with the bearer token and header `anthropic-beta: experimental-cc-routine-2026-04-01`. The optional `text` field arrives wrapped in `<routine-fire-payload>` and is treated as untrusted.
  - Runs push only to `claude/`-prefixed branches by default, and routines act as the user's own GitHub and connector identities.
  - All connected connectors are included by default, with write access and no prompts.
  - Cost: routines draw on subscription usage, plus a **daily per-account run cap** (the number is shown in the UI, not the docs). One-off runs don't count toward the cap, and overage runs on usage credits if enabled.
  - Admins can disable routines. Since 2.1.280 the toggle lives under Admin settings → Capabilities → Remote sessions ([S30]).
  - `/schedule` needs a claude.ai subscription login. It is hidden with a Console API key or a 3P provider.
- **Desktop scheduled tasks.** [V][S4]
  - Local tasks run only while Desktop is open and the machine awake. After a gap, one catch-up run fires for the most recent miss within 7 days.
  - Each task has its own permission mode and model and an optional worktree.
  - Stored at `~/.claude/scheduled-tasks/<task-name>/SKILL.md`: frontmatter holds `name` and `description` and the body is the prompt. Schedule, folder, model and enabled state live elsewhere.
  - A running task can modify itself with the `update_scheduled_task` MCP tool.
  - Available from Desktop 1.1.5368.
- **GitHub Actions** is the fourth option for unattended cron. [V][S2]

### 4. Channels (research preview)

- **What they are.** [V][S5] [V][S6]
  - A channel is an MCP server, spawned over stdio, that *pushes* events into a running local session. It can be one-way (webhook or CI) or two-way (chat bridge with a reply tool).
  - Official plugins: Telegram, Discord and iMessage, plus the `fakechat` demo, all Bun-based, in `claude-plugins-official`.
- **Configuration.** [V][S5] [L]
  - Install the plugin, then start with `claude --channels plugin:<name>@<marketplace>` (space-separated for several). Being listed in `.mcp.json` is not enough.
  - Custom channels need `--dangerously-load-development-channels server:<name>` during the preview.
  - Neither flag appears in `claude --help`: `claude --help | grep -ci channels` returns 0.
- **Protocol.** [V][S6]
  - The server declares `capabilities.experimental['claude/channel']` and emits `notifications/claude/channel` with `{content, meta}`, which arrives as `<channel source=… …>`.
  - Opting into permission relay: `experimental['claude/channel/permission']: {}`. Requests go out as `notifications/claude/channel/permission_request`, and the reply is `notifications/claude/channel/permission` with `{request_id, behavior: 'allow'|'deny'}`.
  - Sender allowlists gate inbound messages.
- **Enterprise controls.** [V][S5]
  - Managed `channelsEnabled` is the master switch. On claude.ai Team/Enterprise channels are blocked until an Owner enables them.
  - `allowedChannelPlugins` takes `[{marketplace, plugin}]`.
  - Channels require claude.ai or Console auth and are unavailable on Bedrock, Vertex and Foundry.
  - In `-p` runs, AskUserQuestion and plan-approval tools are disabled.
- **Introduced** in v2.1.80 (Mar 19); permission relay in 2.1.81; `allowedChannelPlugins` in 2.1.84. [V][S30]

### 5. Dynamic workflows (`Workflow` tool)

**5.1 Availability and opt-in** [V][S7] [V][S23] [V][S12]
- Available on all paid plans, the Anthropic API, and Bedrock/Vertex/Foundry. **Off by default on Pro**: `enableWorkflows` is unset, which means off on Pro and on elsewhere. Workflows work in the CLI, Desktop, the IDE extensions, `-p` and the SDK.
- Opt-in routes:
  - the keyword **`ultracode`** in a prompt the user types (renamed from `workflow` in v2.1.160),
  - asking in your own words ("use a workflow"),
  - `/effort ultracode` or `claude --effort ultracode` (v2.1.203+), or `"ultracode": true` in settings.
- The keyword does **not** trigger a workflow from `-p` prompts, unstamped SDK prompts, scheduled-task prompts, or relayed webhook and PR text (since v2.1.210).
- Dismissing the keyword: Option+W on macOS, or turn off the "Ultracode keyword trigger" in `/config`.
- Ultracode means xhigh effort plus a workflow for every substantive task. It is unavailable when workflows are off, when the model lacks `xhigh`, or when an effort cap below xhigh applies. `effortLevel` and `CLAUDE_CODE_EFFORT_LEVEL` don't accept `ultracode`.

**5.2 Script API** [V][S7] [V][S8] [L] (bundled `/workflow-authoring` skill, loaded in this session)
- The file must start with `export const meta = { name, description, whenToUse?, phases?: [{title, detail?, model?}] }`. It must be a **pure literal**. A non-literal `meta` drops the command from `/` autocomplete.
- The body is plain JavaScript (no TypeScript) with top-level `await`. There is no filesystem or Node access and no `import()`. `Date.now()`, `Math.random()` and argument-less `new Date()` throw, to keep runs replayable.
- `agent(prompt, {label?, phase?, schema?, model?, effort?, isolation?: 'worktree', agentType?})`
  - Returns the agent's final text, or the validated JSON object when `schema` is passed.
  - Returns `null` if the agent was stopped or died.
  - Schema validation retries up to 5 times (`MAX_STRUCTURED_OUTPUT_RETRIES`). Self-contradictory schemas fail before launch.
- `pipeline(items, stage1, stage2, …)` has no barrier between stages. Each stage gets `(prev, item, index)`, and a stage that throws turns that item into `null`.
- `parallel(thunks)` is a barrier and never rejects; a failure becomes `null`.
- `phase(title)`, `log(msg)`, and the globals `args` and `budget` (`{total, spent(), remaining()}`, a hard ceiling tied to a "+500k"-style directive) are available.
- `workflow(nameOrRef, args)` runs a child workflow inline; nesting is one level only.
- The model for each agent follows the subagent order, with a script-specified model counting as the per-invocation model. `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` overrides it.
- Workflow agents get the same CLAUDE.md files, except built-in types such as Explore and Plan.
- Tool inputs are `{script? | name? | scriptPath?, args?, resumeFromRunId?}`; `title` and `description` are ignored. The tool is available in Agent SDK v0.3.149+.

**5.3 Where workflows live and how a plugin ships one** [V][S7] [V][S22]
- Save from `/workflows` with `s`, into `.claude/workflows/` (project) or `~/.claude/workflows/` (personal). They then run as `/<name>`.
- Project wins over personal. In a monorepo the nearest `.claude/workflows/` wins. Saving refuses to write through symlinks (since v2.1.216).
- Plugins ship workflows from **`workflows/` at the plugin root**, or from the `workflows` manifest field (string or array, which *replaces* the default dir). They are namespaced: `acme-tools` plus `meta.name: 'release-audit'` gives `/acme-tools:release-audit`.
- Every run's script is persisted under the session dir in `~/.claude/projects/`.
- After editing, `/reload-skills` re-reads the workflow dirs.

**5.4 Approval and permissions** [V][S7]
- Interactive CLI prompt options: Yes / Yes-and-don't-ask-again (offered only for named bundled, saved or plugin workflows) / View raw script / No. Ctrl+G opens the script in an editor.
- In auto mode the prompt shows on first launch only, and is skipped when ultracode is on. In Manual and acceptEdits it shows every run. In bypass mode, `-p` and the SDK there is no prompt.
- Headless allow routes: a `Workflow` or `Workflow(<name>)` allow rule, auto mode, bypass, a PreToolUse hook returning `allow`, or `--permission-prompt-tool`/`canUseTool`.
- Workflow agents use the session's permission rules. In auto mode, a script-computed `agent()` prompt is *not* treated as user intent.

**5.5 Limits, size guideline and cost** [V][S7] [V][S23] [V][S30]
- Runtime limits:
  - no mid-run user input (pauses happen only for permission prompts and usage-limit waits);
  - at most 16 concurrent agents, fewer with fewer CPUs, adjustable 1–256 via `CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS` (v2.1.269+);
  - at most 4,096 items per `parallel`/`pipeline` call;
  - at most **1,000 agents per run**.
- Size guideline (advice, not a cap), via the `workflowSizeGuideline` key (v2.1.219+) or `/config`:
  - `unrestricted` = no guideline;
  - `small` = fewer than 5 agents;
  - `medium` = fewer than 10;
  - `large` = fewer than 50.
- The default is `medium`, or `small` on Pro since v2.1.271, which also lowered medium from 15 to 10.
- A **"Large workflow"** warning appears above 25 agents or above 1.5M projected tokens. It is advisory only.
- Prompt cache: agents with the same prefix stagger their start by up to `CLAUDE_CODE_WORKFLOW_PREFIX_STAGGER_MS` (5000 ms by default). Cache TTL is 5 minutes unless `subagentPromptCacheTtl: "1h"`.
- Runs count against plan usage. Since v2.1.271 an interactive subscription run pauses at a usage limit and resumes afterwards (at most 2 waits, only resets within 24 h, only when `autoContinueAtUsageLimit` is on).

**5.6 Resume** [V][S7] [L] (skill)
- Paused runs resume with `p` in `/workflows`. Stopped runs relaunch with `Workflow({scriptPath, resumeFromRunId})`, and only in the same session. Backgrounding the session carries the run over.
- On relaunch, completed agents replay from cache up to the first agent whose prompt changed or that failed. Everything after that point reruns.
- `<transcriptDir>/journal.jsonl` records each agent's actual return value.
- If no saved results exist at all, the run fails with a `nothing to resume` error.

**5.7 `/deep-research`** [V][S7] [V][S30]
- Bundled workflow. It fans out WebSearch across several angles, fetches and cross-checks sources, **votes on each claim**, and returns a cited report with refuted claims filtered out. Claims it couldn't check are listed as unverified.
- Requires the WebSearch tool. Since v2.1.218 it runs **only when the user invokes it**.

**5.8 Turning workflows off** [V][S7]
- Per user: `/config`, `"disableWorkflows": true`, or `CLAUDE_CODE_DISABLE_WORKFLOWS=1`.
- Per organization: managed `disableWorkflows` or the admin toggle.
- Turning workflows off also removes the bundled workflow commands, `/workflow-authoring` and ultracode.

**Timeline.** [V][S30]
- v2.1.154: dynamic workflows introduced (May 28).
- v2.1.160: keyword renamed to `ultracode`.
- v2.1.202: size setting added.
- v2.1.248: script reference moved into the `/workflow-authoring` skill, cutting the tool description from about 5.7k to 1k tokens.
- v2.1.269: concurrency env var.
- v2.1.271: pause at usage limits; Pro default size `small`.

### 6. Subagents: model, effort, background, forks, nesting

- **Frontmatter fields** (camelCase; unknown fields are silently ignored). [V][S18]
  - Required: `name` (no `:`) and `description`.
  - Optional: `tools`, `disallowedTools`, `model` (`sonnet|opus|haiku|fable|<full id>|inherit`), `permissionMode`, `maxTurns`, `skills`, `mcpServers`, `hooks`, `memory` (`user|project|local`), `background`, `omitClaudeMd` (v2.1.271+), `effort` (`low…max`), `isolation: worktree`, `color`, `initialPrompt`, `experimental.cacheTtl` (`5m|1h`).
  - **Plugin subagents ignore `hooks`, `mcpServers` and `permissionMode`**, and `initialPrompt` is ignored for plugin subagents too.
- **Scope priority**: managed > `--agents` JSON > `.claude/agents/` > `~/.claude/agents/` > plugin `agents/`. Plugin subfolders become part of the ID, so `my-plugin:review:security` is valid. [V][S18]
- **Model resolution order**: per-invocation `model` → frontmatter `model` → `CLAUDE_CODE_SUBAGENT_MODEL` → main model. [V][S18]
  - A family alias that matches the main model's family resolves to the *exact* main model.
  - `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` (v2.1.257+) forces one model on subagents, teammates and workflow agents.
  - `availableModels` substitutes a blocked model.
- **Effort precedence.** Frontmatter `effort` overrides the session level, but not `CLAUDE_CODE_EFFORT_LEVEL`. `maxEffortLevel` or an org cap still applies. [V][S12] [V][S18]
- **Tools stripped from every subagent**: `Agent` (at the depth limit), `AskUserQuestion`, `EndConversation`, `EnterPlanMode`, `ExitPlanMode` (unless `permissionMode: plan`), `ScheduleWakeup`, `WaitForMcpServers` and **`Workflow`**. [V][S18]
- **Background subagents** additionally keep only these built-in tools: Read, Grep, Glob, LSP, Bash, PowerShell, Edit, Write, NotebookEdit, WebFetch, WebSearch, TodoWrite, Skill, ToolSearch, EnterWorktree, ExitWorktree, Monitor, TaskStop, SendMessage and Artifact, plus all MCP tools. [V][S18]
- **Foreground or background.** [V][S18]
  - Fork mode is on by default in interactive sessions (v2.1.232+), which makes spawned subagents run in the background.
  - In `-p` and the SDK, fork mode is off. Claude backgrounds by default there but uses the foreground when it needs the result.
  - `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` forces the foreground.
  - Background permission prompts surface in the main session (v2.1.186+).
- **Forks** (`/subtask`, or Agent type `fork`) inherit the full conversation, system prompt, tools and model, and share the prompt cache. A fork can't spawn forks. `CLAUDE_CODE_FORK_SUBAGENT=0|1` turns fork mode off or on. [V][S18]
- **Nesting and concurrency.** [V][S18] [V][S24]
  - Depth defaults to 3 layers (`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`; `1` disables nesting). History: 5 fixed in v2.1.172–216, 1 in 2.1.217–218, 3 from 2.1.219.
  - Concurrent subagents default to 20 (`CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`, v2.1.217+). Ultracode sessions are exempt.
  - The old 200-per-session total cap was removed in v2.1.224.
- **`Agent(type1, type2)` allowlists** in `tools` work only for an agent running as the main thread via `claude --agent`. [V][S18]
- **Result framing.** Since v2.1.277 subagent results are wrapped under a header marking them as subagent output. In auto mode, `SubagentHandback` (v2.1.271) routes reports through the classifier. [V][S30] [V][S9]

### 7. Agent teams (experimental)

- **Enabling.** [V][S17] [V][S24]
  - Set `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in the environment or in settings `env`.
  - Teams need an interactive session. In `-p` or the SDK, no teammates are spawned.
  - Once teams are on, any Agent call with a `name` (that isn't a fork and passes no `isolation`) launches a *teammate*. Claude may name subagents on its own, so teams can form unasked. Set the variable to `0` to prevent that.
- **Display.** `teammateMode` or `--teammate-mode` (hidden flag) takes `in-process` (default), `auto`, `tmux` or `iterm2` (v2.1.186+). [V][S17] [V][S23]
- **Internals.** [V][S17]
  - Team config: `~/.claude/teams/{team}/config.json`, runtime state only; don't author it.
  - Mailboxes: `~/.claude/teams/{team}/inboxes/{agent}.json`.
  - Tasks: `~/.claude/tasks/{team}/`, with file-locked claiming.
  - Hooks: `TeammateIdle`, `TaskCreated` and `TaskCompleted`, where exit code 2 blocks.
- **Teammate model order**: spawn prompt → the subagent definition's `model` → `CLAUDE_CODE_SUBAGENT_MODEL` → the lead's model. `teammateDefaultModel` was removed in v2.1.234. Teammates inherit the lead's effort and permission mode, except `dontAsk`. [V][S17]
- **Limits.** [V][S17]
  - One team per session.
  - **No nested teams.**
  - The lead is fixed.
  - `/resume` and `/rewind` don't restore in-process teammates.
  - An in-process teammate's own subagents run in the foreground only.
  - Plan approvals are auto-granted by the lead.
  - In-process teammates ignore a definition's `skills` and `mcpServers`.
- **Messages between agents** carry no user authority. In auto mode the classifier reviews each message before delivery. [V][S17]
- **Introduced** in v2.1.32 (Feb 5, 2026). [V][S30]

### 8. Agent view and background sessions

- **Commands.** [V][S19] [L] (`claude agents --help`, `claude --help`)
  - `claude agents` opens the view.
  - `claude --bg "<prompt>"` starts a background session. It can't be combined with `-p`.
  - `/bg` or `/background`, or ← on an empty prompt, sends the current session to the background.
  - `claude attach|logs|stop|rm|respawn <id>` manage sessions.
  - `claude agents --json [--all]` prints state for scripts.
  - Dispatch defaults: `--permission-mode`, `--model`, `--effort` (accepts `ultracode`), `--agent`, `--restricted`, `--settings`, `--plugin-dir`, `--mcp-config`, `--add-dir`.
- **Supervisor.** [V][S19]
  - A separate process runs the sessions. It stops an unattached idle session after about an hour; pinning with Ctrl+T keeps it alive.
  - Sessions survive sleep and auto-update, but not shutdown.
  - State lives in `~/.claude/jobs/<id>/`, with `CLAUDE_JOB_DIR` set for each session.
- **Isolation.** Every background session moves into a worktree under `.claude/worktrees/` before editing. `worktree.bgIsolation: "none"` turns that off. [V][S19]
- **Permission mode.** It is inherited from how the session was dispatched. A project `.claude/settings.json` `defaultMode` can't escalate beyond the originating session's mode, and `auto` or `bypassPermissions` as `defaultMode` count only from user, managed or `--settings` sources. [V][S19]
- **Turning it off**: `disableAgentView: true` or `CLAUDE_CODE_DISABLE_AGENT_VIEW`. [V][S19] [V][S23]
- **Status**: research preview, introduced in v2.1.139 (May 11). [V][S19] [V][S30]

### 9. SendMessage and cross-session messaging

- **Targets.** `SendMessage` reaches teammates, subagents to resume (by agent ID or name), and other local sessions (v2.1.224+), plus cloud and Remote Control sessions when connected. `ListAgents` discovers targets. [V][S9] [V][S20]
- **Message content.** Messages are plain text only: no files, and no `@` attachments (since v2.1.251). Each message carries an optional `summary` (the preview is truncated at 200 characters). [V][S9] [V][S20]
- **Idle notice.** `notify_when_idle` asks another session for one notice when it next goes idle (v2.1.236+). [V][S20] [V][S28]
- **Resume semantics.** The Agent tool's `resume` parameter was removed in v2.1.77, and `SendMessage({to: agentId})` resumes a stopped agent in the background. [V][S30]
- **Authority.** Relayed messages never grant approval or consent, and permissions stay per-session. [V][S17] [V][S20]

### 10. Advisor tool

- **What it is.** [V][S10] [V][S11]
  - A server-side tool: the executor emits `server_tool_use` with `name: "advisor"` and empty `input`, and the advisor model reads the *full transcript*.
  - The advisor runs without tools, and its thinking is dropped.
  - It is experimental and **Anthropic API only**; Claude Code docs say it is unavailable on Bedrock, Vertex, Foundry and Claude Platform on AWS.
  - It needs feature-flag fetching, so for example `DISABLE_TELEMETRY` turns it off.
- **Configuring it in Claude Code.** [V][S10] [V][S23] [V][S25] [L] (`claude --help | grep -ci advisor` → 0)
  - `/advisor [fable|opus|sonnet|<full id>|off]` (text form v2.1.260+). The choice is saved to **`advisorModel`** in `~/.claude/settings.json`.
  - `"advisorModel": "opus"` in any settings file.
  - `claude --advisor <model>`, which is hidden from `--help`.
  - `CLAUDE_CODE_DISABLE_ADVISOR_TOOL=1` disables it completely.
  - Subagents inherit the advisor, subject to their own pairing check.
  - There is **no setting to force or cap calls**. Claude decides when to consult.
- **Accepted pairings in Claude Code** [V][S10]:

| Main model | Accepted advisors | Rejected / refused |
|---|---|---|
| Haiku 4.5 | Fable, Opus, Sonnet | Haiku can't advise |
| Sonnet 4.6 | Fable, Opus, Sonnet | — |
| Sonnet 5 | Fable, Opus 4.7+, Sonnet 5 | Sonnet 4.6 rejected; Opus 4.6 refused by API |
| Opus 4.6 | Fable, Opus, Sonnet 5 | Sonnet 4.6 rejected |
| Opus 4.7 / 4.8 | Fable, Opus 4.7+ | Opus 4.6, Sonnet rejected |
| **Opus 5.5 / Opus 5** | **Fable, Opus 5+** | Opus 4.6, Sonnet rejected; Opus 4.7/4.8 refused by API |
| Fable 5 | Fable 5.1, Fable 5 | Opus, Sonnet rejected |
| Fable 5.1 | Fable 5.1 | Opus, Sonnet rejected; Fable 5 refused by API |

  - A "rejected" advisor is never attached. A "refused" one is attached, silently dropped for the rest of the conversation, and resets only after `/clear` or `/compact`.
  - Fable 5.1 needs v2.1.257+ and Fable access. A Fable advisor may need one-time usage-credits consent via `/model fable`.
- **API-level details.** [V][S11]
  - Beta header `advisor-tool-2026-03-01`. Tool definition: `{type: "advisor_20260301", name: "advisor", model, max_uses?, max_tokens? (≥1024), caching?: {type: "ephemeral", ttl: "5m"|"1h"}}`.
  - Result variants: `advisor_result` (plaintext, for example from an Opus 4.8 advisor) and `advisor_redacted_result` (encrypted; Fable 5.1, Mythos 5.1, Opus 5, Fable 5 and Mythos 5 advisors return this).
  - Error codes: `max_uses_exceeded`, `too_many_requests`, `overloaded`, `prompt_too_long`, `execution_time_exceeded`, `model_not_found`, `unavailable`.
  - The API requires the advisor to be Sonnet 4.6 or better and at least as capable as the executor. An invalid pair returns HTTP 400.
- **Cost.** [V][S10] [V][S11]
  - Advisor tokens are billed at the advisor model's rates. They appear in `usage.iterations[]` with `type: "advisor_message"` and are **excluded from top-level usage**.
  - The top-level `max_tokens` doesn't bound the advisor.
  - Typical advisor output is 400–700 text tokens, or 1,400–1,800 including thinking.
  - The advisor's own read of the transcript is uncached in Claude Code. Toggling the advisor doesn't break the main model's cache.
  - On subscriptions it counts toward plan limits, except that a Fable advisor bills to usage credits where Fable does.
- **Published results.** The Anthropic blog (Apr 9, 2026) reports Sonnet with an Opus advisor gaining about 2.7 points on SWE-bench at about 11.9% lower cost than Sonnet alone. I relayed this via WebFetch's summarizer and didn't re-check it. [V][S32]
- **History.** The earliest changelog entry is v2.1.117 (Apr 22, 2026), and it already refers to an existing advisor dialog. [V][S30]

### 11. Model configuration

- **Current IDs.** [V][S13]

| Model | Claude API ID | Alias | Price in/out per MTok | Context | Default effort | Retirement (not sooner than) |
|---|---|---|---|---|---|---|
| Fable 5.1 | `claude-fable-5-1` | same | $10 / $50 | 1M | high | 2027-09-01 |
| Opus 5.5 | `claude-opus-5-5` | same | $4 / $20 | 1M | medium | 2027-09-22 |
| Sonnet 5 | `claude-sonnet-5` | same | $2 / $10 | 1M | high | 2027-06-30 |
| Haiku 4.5 | `claude-haiku-4-5-20251001` | `claude-haiku-4-5` | $1 / $5 | 200K | n/a (extended thinking) | **2026-10-15** |

- **Claude Code aliases.** [V][S12]
  - `default` clears any override.
  - `best` means Fable where available, else `opus`.
  - `fable` means Fable 5.1 (Fable 5 in claude-apps-gateway sessions).
  - `opus` means Opus 5.5 on the Anthropic API, Claude Platform on AWS, Bedrock and Vertex, and Opus 4.6 on Foundry.
  - `sonnet` means Sonnet 5 on the API, Sonnet 4.6 on Claude Platform on AWS, and Sonnet 4.5 on Bedrock, Vertex and Foundry.
  - `haiku`, `sonnet[1m]`, `opus[1m]`, and `opusplan` (Opus in plan mode, Sonnet otherwise; also `opusplan[1m]`).
  - **`opusplan` is the only plan/execute split alias.**
  - Requirements: Opus 5.5 needs v2.1.280+, Opus 5 v2.1.219+, Sonnet 5 v2.1.197+, Fable 5.1 v2.1.257+.
- **`default` per plan.** Pro, Max, Team, Enterprise and the API default to **Opus 5.5**, and so do Claude Platform on AWS, Bedrock and Vertex. Foundry defaults to Sonnet 4.5. Before v2.1.280, Pro and Team Standard defaulted to Sonnet 5. Fable is never the default. [V][S12] [V][S30]
- **Setting the model.** [V][S12]
  - Precedence: `/model` → `--model` → `ANTHROPIC_MODEL` → settings `model` → `ANTHROPIC_DEFAULT_MODEL` (v2.1.236+).
  - Family pins: `ANTHROPIC_DEFAULT_{FABLE,OPUS,SONNET,HAIKU}_MODEL`.
  - Allowlist: `availableModels` (managed) with `enforceAvailableModels`.
  - Fallback chains: `--fallback-model a,b` or `fallbackModel: [..]`, with at most 3 entries.
- **Content-based fallback.** Classifier-flagged requests fall back automatically. On Fable 5.1, Fable 5 and Opus 5.5, biology flags go to Opus 5 and cybersecurity flags to Opus 4.8. `switchModelsOnFlag: false` asks first instead. [V][S12]
- **Effort.** [V][S12] [V][S23] [V][S26] [L] (`claude --help` lists `--effort` values low, medium, high, xhigh, max)
  - Levels: Fable 5.x, Opus 5.5, Opus 5, Sonnet 5, Opus 4.8 and Opus 4.7 support `low|medium|high|xhigh|max`. Opus 4.6 and Sonnet 4.6 support `low|medium|high|max`. An unsupported level falls back to the next lower one.
  - Resolution order: explicit choice (`CLAUDE_CODE_EFFORT_LEVEL`, `--effort` or `/effort`) → settings (`modelSettings.<model>.effortLevel` per model, v2.1.251+, else top-level `effortLevel`) → the model default.
  - `/effort [level|auto|status]`; `s` in the slider applies a level to this session only. `max` and `ultracode` apply to the session only (unless set via env or the `ultracode` key).
  - Skill and subagent frontmatter can set `effort:`.
  - `maxEffortLevel` (v2.1.267+) caps effort on every provider, including per model.
  - `ultrathink` in a prompt adds in-context instruction without changing the API effort.
  - Thinking can't be turned off on Opus 5.5 or Fable.
- **Fast mode.** [V][S14]
  - `/fast` or `"fastMode": true`. Supported on Opus 5.5 ($8/$40), Opus 5 and Opus 4.8 ($10/$50); Opus 5.5 is the default since v2.1.280. It reaches up to 2.5× speed.
  - Subscription plans pay for it from usage credits only. Team and Enterprise need an Owner to enable it.
  - Not available on Bedrock, Vertex, Foundry or Claude Platform on AWS.
  - Turning it on mid-conversation pays uncached input once for the whole context.
  - `fastModePerSessionOptIn` and `CLAUDE_CODE_DISABLE_FAST_MODE` control it.
- **Per-subagent model and effort**: see §6. Skills can also set `model:` for the current turn only. [V][S26]
- **Plan availability highlights.** [V][S12] [V][S10] [V][S14] [V][S16] [V][S7]
  - Fable may bill to usage credits on some plans, with one-time consent.
  - The advisor works on subscription and API accounts, API-only in terms of provider.
  - Fast mode runs on usage credits.
  - Computer use in the CLI is Pro/Max only.
  - Workflows are off by default on Pro.

### 12. Output styles

- **Built-in styles**: Default, `Proactive`, `Concise` (v2.1.237+), `Explanatory` and `Learning`. [V][S15]
- **Selecting a style.** [V][S15] [V][S23] [V][S25]
  - `/output-style <style>` (v2.1.269+; case-insensitive), or `/config` → Output style. Both write `.claude/settings.local.json`.
  - Or set `"outputStyle": "<Name>"` directly. That value is **case-sensitive**, and a mismatch silently falls back to Default.
  - A style change applies from the next message (since v2.1.251).
- **Files.** Markdown with YAML frontmatter, in `~/.claude/output-styles/`, `.claude/output-styles/` (nested dirs; the nearest wins), the managed-settings `.claude/output-styles`, or a plugin's `output-styles/` (or the manifest's `outputStyles` field). [V][S15] [V][S22]
- **Frontmatter** (all optional, kebab-case; unknown fields are ignored): [V][S15]
  - `name` (defaults to the file name) and `description`;
  - `keep-coding-instructions` (default `false`, which *drops* Claude Code's software-engineering instructions);
  - `force-for-plugin` (plugin styles only; overrides the user's `outputStyle`; the first loaded plugin wins).
- **Scope.** A style applies to the main thread and forks, **not to other subagents**. Terminal sessions read style files at startup, so a restart picks up edits. [V][S15]

### 13. Computer use in the CLI

- **Availability.** Research preview, **macOS only**, **Pro or Max only** (not Team or Enterprise), claude.ai auth only (no 3P providers), interactive sessions only (not `-p`). [V][S16]
- **Enabling.** Enable the built-in MCP server `computer-use` in `/mcp`; the setting is per project. macOS then prompts for Accessibility and Screen Recording. [V][S16]
- **Safety limits.** [V][S16]
  - Apps are approved per session.
  - Warnings flag apps equivalent to shell access (terminals, IDEs), Finder, and System Settings.
  - Browsers and trading apps are view-only, and terminals and IDEs click-only.
  - Other apps are hidden while Claude works, and the terminal is excluded from screenshots.
  - A global Esc aborts, and Esc can't be synthesized by an injection.
  - A single-session lock applies.
  - Screenshots are downscaled automatically, for example 3456×2234 to about 1372×887.
- **Introduced** in Week 14 (Mar 30–Apr 3, 2026). Since v2.1.243 on macOS, clicking the desktop or a Finder window requires a Finder grant. [V][S28] [V][S30]

### 14. 2026 timeline: notable features by month

The weekly "What's new" digests exist for W13–W37, but **W31 and W38 return 404** and nothing covers Jan 1–Mar 22. I built January to mid-March from the GitHub/docs changelog. [V][S28] [V][S29] [V][S30]

- **January (v2.0.77–2.1.29).**
  - 2.1.0 (Jan 7): skill hot-reload; `context: fork` and `agent` in skill frontmatter; hooks in agent and skill frontmatter; `once: true` hooks; plugins may ship prompt/agent hooks.
  - 2.1.3 (Jan 9): slash commands merged into skills; tool-hook timeout raised from 60 s to 10 min.
  - 2.1.9: PreToolUse `additionalContext`; `${CLAUDE_SESSION_ID}`.
  - 2.1.10: `Setup` hook event.
  - 2.1.14: plugin pinning to git SHAs.
- **February (2.1.30–2.1.63).**
  - 2.1.32 (Feb 5): **agent teams** research preview; the skill-description budget becomes 2% of context.
  - 2.1.33: `TeammateIdle` and `TaskCompleted` hooks; `Task(agent_type)` spawn allowlist; agent `memory`.
  - 2.1.47: `last_assistant_message` in Stop input.
  - 2.1.49/2.1.50: `isolation: worktree`, `background: true`, plugin `settings.json`, `ConfigChange` hook, `WorktreeCreate`/`WorktreeRemove` hooks.
  - 2.1.63 (Feb 28): **HTTP hooks**.
- **March (2.1.64–2.1.89).**
  - 2.1.69: `InstructionsLoaded` hook; `${CLAUDE_SKILL_DIR}`; `/reload-plugins`; `agent_id` and `agent_type` in hook input.
  - 2.1.71 (Mar 7): **`/loop`**.
  - 2.1.76: `/effort`; `PostCompact`; `Elicitation` hooks.
  - 2.1.77: SendMessage auto-resume; the Agent `resume` param removed; `claude plugin validate` checks frontmatter.
  - 2.1.78: `StopFailure` hook; `${CLAUDE_PLUGIN_DATA}`; plugin agents gain `effort`, `maxTurns` and `disallowedTools`.
  - 2.1.80 (Mar 19): **`--channels`**; skill `effort` frontmatter.
  - 2.1.81: `--bare`.
  - 2.1.83: `managed-settings.d/`; `CwdChanged` and `FileChanged` hooks; `sandbox.failIfUnavailable`; `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB`; plugin `userConfig` with keychain secrets.
  - 2.1.84: `TaskCreated` hook.
  - 2.1.85: conditional hook `if`.
  - W13 (Mar 23–27): **auto mode** research preview.
  - 2.1.89 (Apr 1): PreToolUse `defer`; `PermissionDenied` hook.
- **April (2.1.90–2.1.126).**
  - W14: **CLI computer use**; plugin executables on the Bash PATH; `disableSkillShellExecution`.
  - 2.1.98 (Apr 9): **Monitor tool**; W15 adds self-paced `/loop`.
  - Apr 9: advisor-strategy blog.
  - W16: **Routines**; Opus 4.7 with `xhigh`; plugin `monitors`; PreCompact can block; 2.1.111 drops the `--enable-auto-mode` requirement.
  - 2.1.117 (Apr 22): first **Advisor Tool (experimental)** changelog entry.
  - W17: hooks `type: "mcp_tool"`; `claude plugin tag`; auto-mode `$defaults`.
  - W18: PostToolUse `updatedToolOutput` for all tools; `claude plugin prune`.
- **May (2.1.128–2.1.159).**
  - W19: `--plugin-url`/zip plugins; `worktree.baseRef`; `autoMode.hard_deny`; hooks get `effort.level`/`$CLAUDE_EFFORT`.
  - 2.1.139 (May 11): **`/goal`** and **agent view**; hook `args` exec form; PostToolUse `continueOnBlock`; `claude plugin details` with token cost.
  - W21: auto mode on Pro; `/code-review`; `claude agents --json`.
  - 2.1.154 (May 28): **dynamic workflows**; W22 also brings Opus 4.8, `/reload-skills`, skill `disallowed-tools`, the `MessageDisplay` hook, and plugin `defaultEnabled: false`.
- **June (2.1.160–2.1.197).**
  - 2.1.160: `ultracode` keyword; Stop/SubagentStop `additionalContext`; 2.1.163 adds managed version requirements.
  - 2.1.172 (Jun 10): nested subagents; `--safe-mode`; `fallbackModel`; `disableBundledSkills`; agent messages lose user authority.
  - W25: Artifacts; `Tool(param:value)` rules; `/config key=value`.
  - W26: `claude mcp login`; `sandbox.credentials`; `autoMode.classifyAllShell`; background-subagent prompts surfaced (2.1.186).
- **July (2.1.198–2.1.220).**
  - 2.1.198: Sonnet 5; subagents background by default; `default` mode renamed "Manual".
  - 2.1.202/203: workflow size setting; `--effort ultracode`.
  - W29: `/fork` vs `/subtask`; MCP calls auto-background after 2 minutes.
  - 2.1.217–219: concurrent-subagent limit; depth default 3; `workflowSizeGuideline`; `/deep-research` manual-only (2.1.218); `sandbox.network.strictAllowlist`.
  - 2.1.219 (Jul 24): **Opus 5**; Claude Security plugin.
- **August (2.1.221–2.1.252).**
  - 2.1.224 (Aug 7): **cross-session messaging**; self-hosted environments; plugin zip `archive` source with SHA-256 pin; 200-subagent cap removed; **auto mode becomes the default** for Pro/Max/Team from Aug 14.
  - 2.1.232: fork mode default on (task tools dropped on newer models in W33).
  - 2.1.234: `/goal` check-ins.
  - 2.1.236: `ANTHROPIC_DEFAULT_MODEL`.
  - 2.1.237: Concise style.
  - 2.1.248: `--restricted`; `/workflow-authoring`; `modelPicker`.
  - 2.1.251: per-model effort (`modelSettings`).
- **September (2.1.257–2.1.282).**
  - 2.1.257 (Sep 1): **Fable 5.1**; `CLAUDE_CODE_SUBAGENT_MODEL_FORCE`.
  - W36 (2.1.251–261): `PreModelSwitch` and `PostModelSwitch` hooks; `/skill-doctor`; `managedMcpServers`; project-level `bypassPermissions` `defaultMode` ignored.
  - 2.1.260: `/advisor` text form.
  - 2.1.267: `maxEffortLevel`.
  - 2.1.269 (Sep 11): **`claude plugin eval`**; `/output-style`; workflow concurrency env.
  - 2.1.271 (Sep 14): workflows pause at usage limit; **`omitClaudeMd`**; `SubagentHandback`; Monitor deadlines; per-command `allowed_domains` in auto mode with sandbox.
  - 2.1.275: npm plugins fetched with `--ignore-scripts` and integrity-verified.
  - 2.1.277: subagent-output header; `TaskOutput` removed.
  - 2.1.278: server-side auto-mode classifier by default for API and Enterprise.
  - 2.1.280 (Sep 22): **Opus 5.5** default; Pro and Team Standard default to Opus; marketplaces imitating reserved names refused; agent-type `PermissionRequest` hooks rejected.
  - 2.1.281: `claude plugin validate` MCP checks and an unquoted-`${CLAUDE_PLUGIN_ROOT}` warning; `--agents` accepts a JSON file path.
  - 2.1.282: `anthropic-skills` and `claude-ai` names reserved.

---

## Implications for Forge

1. **Pin the Claude Code floor at v2.1.280, and check it in `forge doctor`.** Opus 5.5, `omitClaudeMd`, workflow usage-limit pauses and npm `--ignore-scripts` all need it. The `stable` channel (2.1.273) is too old. Check *both* CLIs (the terminal one and the Desktop-bundled one). Upgrading the local 2.1.270 is a human action. ([S12], [S30], [L])
2. **Forge's authoritative "done" gate is a command-type Stop/SubagentStop hook in the Forge plugin.** It runs the check scripts and writes evidence files, and must honour `stop_hook_active` and the cap of 8 blocks. Treat `/goal` "met" as a *convenience signal, never evidence*: its Haiku evaluator only reads the transcript. ([S1], [S21])
3. **When Forge suggests `/goal`, the condition must name the check command, the evidence path, and an explicit bound** ("…or stop after N turns"). Forge must warn that `disableAllHooks` or `allowManagedHooksOnly` disables `/goal`. ([S1])
4. **Checker agents ship as plugin subagents with an explicit `tools:` allowlist** (Read/Grep/Glob plus narrowly-scoped Bash only if needed), with `Agent` omitted to stop nesting.
   - Also set `omitClaudeMd: true` for independence from project steering, an explicit `model:` and `effort:`, and `maxTurns`.
   - Don't rely on `permissionMode`, `hooks` or `mcpServers` in plugin agents; they're ignored.
   - Read-only enforcement must also come from settings deny rules and PreToolUse hooks. ([S18])
5. **Fan-out verification (reviews, tolerance audits, BOM checks) should be plugin workflows** in `workflows/`, invoked as `/forge:<name>`.
   - Scripts need a literal `meta` and are deterministic: no clocks, and timestamps come in through `args`.
   - Every `agent()` call returns a `schema`-validated object, which becomes the saved evidence.
   - Use `agentType` to bind stages to Forge's reviewer subagents, and use `pipeline` by default.
   - Use `isolation: 'worktree'` only for parallel writers.
   - Expect about 8 concurrent agents on the reference M4. ([S7], [L])
6. **Workflows have no mid-run user input**, so human sign-off (safety, money, fabrication) happens *between* workflows. That gives one workflow per stage, with a hook- or file-based approval gate before the next stage. ([S7])
7. **Forge's project settings should set these explicitly** rather than inherit plan-dependent defaults: `"workflowSizeGuideline"` (e.g. `"medium"`), `"enableWorkflows": true` (off by default on Pro), and narrow allow rules such as `Workflow(forge:…)`. The exact rule string for a plugin-namespaced workflow is unverified; test it. ([S7], [S23])
8. **Only the main thread can run workflows**, because `Workflow` is stripped from subagents, and `workflow()` nests one level only. Forge's orchestration layer therefore lives in the root session or a `claude --agent forge-lead` main-thread agent, which is also the only place `Agent(type,…)` allowlists work. ([S18], [L])
9. **Treat the advisor as optional and never as the checker.** It sees the maker's full transcript, Claude decides when to call it, calls can't be forced, and its output is encrypted from Opus 5 / Fable-class advisors. If used with Opus 5.5 as main, the advisor must be `fable` or `opus` (Opus 5+). Surface in docs that advisor tokens bill at advisor rates and aren't cached. ([S10], [S11])
10. **Use aliases (`opus`, `sonnet`, `haiku`, `fable`) in shipped agent frontmatter; pin full IDs only in eval configs.** Record `modelUsage` for every eval run. Never pin `claude-haiku-4-5`: it may retire from Oct 15, 2026, and `/goal` plus agent-view summaries depend on the small fast model. ([S12], [S13])
11. **Set effort explicitly for each Forge agent**, because Opus 5.5 defaults to `medium`. Suggested defaults: verification and judging at `high` or `xhigh`, mechanical extraction at `low`. Respect `maxEffortLevel`, and don't depend on ultracode, which is a session-level user choice. ([S12], [S23])
12. **Pick the long-running mechanism by where the work runs:**
    - Monitor (≤30 min per watch, re-armed) for simulation, CAM or build logs inside a session;
    - Desktop scheduled tasks for overnight local CAD, EDA or sim regressions (the machine must stay awake);
    - `/loop` only for short-lived polling (7-day expiry);
    - cloud routines only for repo hygiene that needs no local toolchain.
    
    Note that Monitor, the advisor and some scheduling features vanish when `DISABLE_TELEMETRY` or `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` is set. ([S2], [S3], [S4], [S9], [S10])
13. **Don't make channels or agent teams core dependencies**; both are research previews. If a user enables agent teams, Forge's *named* Agent calls become teammates. Forge should avoid naming subagents or document `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=0`. ([S5], [S17])
14. **Approvals must reach the human directly** (permission prompts, hook `ask`, or signed files). Messages from other agents, subagent results and routine fire payloads are all framed as untrusted or non-user, so a "signed-off" message relayed between agents must never unlock a gate. ([S17], [S3], [S30])
15. **Assume auto mode is the default.** Ship narrow allow rules for Forge's own check commands, for example `Bash(uv run forge-check *)`, since broad `Bash(*)`, interpreter, `Agent` and `Monitor` rules are dropped in auto mode. Keep gates in hooks, which run in every mode. ([S27])
16. **Ship an optional plugin output style** (e.g. "forge-report", with `keep-coding-instructions: true`) but do **not** set `force-for-plugin`. It would override the user's style and still wouldn't reach subagents. Put report formats in skills and schemas instead. ([S15])
17. **Don't use computer use as a verification mechanism.** It is Pro/Max-only, macOS-only and interactive-only, and unavailable on Team/Enterprise. Forge's CAD/EDA checks stay headless and numeric ("numbers beat pictures"). ([S16])

---

## Not found / discrepancies

- **Brief's model IDs.** The Fable 5.1, Opus 5.5 and Sonnet 5 IDs are confirmed exactly. Haiku 4.5's pinned API ID is `claude-haiku-4-5-20251001`, with alias `claude-haiku-4-5`. [V][S13]
- **Advisor platform availability conflicts.** Claude Code docs say the advisor is unavailable on Claude Platform on AWS. The API advisor page says it *is* available there in beta. [V][S10] vs [V][S11]
- **Opus 5.5 is missing from the API advisor table.** The table as fetched lists no `claude-opus-5-5` row, as executor or advisor. The Claude Code docs include an "Opus 5.5 or Opus 5" row. The API page likely predates the Sep 22 release. [V][S11] [V][S10]
- **Claude Code is stricter than the API for Fable 5.** The API accepts Opus 5 (and Mythos) advisors for a Fable 5 executor, but Claude Code rejects Opus and Sonnet advisors on Fable mains. [V][S10] [V][S11]
- **`--effort` help omits `ultracode`.** `claude --help` lists low, medium, high, xhigh and max, while the docs say `--effort ultracode` works since v2.1.203. [L] [V][S12]
- **Hidden flags.** `--advisor`, `--channels`, `--dangerously-load-development-channels` and `--teammate-mode` are absent from `claude --help`, and the docs say they are intentionally hidden. [L] [V][S5] [V][S10] [V][S17]
- **No plan/execute alias besides `opusplan`.** For example, there is no `fableplan`. [V][S12]
- **Unpublished numbers.** The routine **daily run cap** and the GitHub-trigger **hourly caps** aren't given in the docs, which point to the UI. [U][S3]
- **Advisor introduction version isn't stated anywhere.** The earliest changelog mention (v2.1.117, Apr 22, 2026) already describes an existing dialog, the blog is dated Apr 9, 2026, and the API beta header is dated 2026-03-01. [V][S30] [V][S32] [V][S11]
- **Digest gaps.** The "What's new" digests start at W13 (Mar 23–27). W31 (Jul 27–31) and W38 (Sep 14–18) are 404, and no digest covers v2.1.270–2.1.282. Those were covered from the changelog. [V][S28] [L] (curl status codes)
- **`ScheduleWakeup` has no changelog entry of its own.** Its `stop` field is documented as v2.1.202+. [V][S8]
- **Workflow permission rule for plugin workflows.** The syntax for a plugin-namespaced workflow isn't documented; `Workflow(<name>)` is shown only for saved workflows. [U][S7]
- **Concurrency wording differs but agrees.** The docs say at most 16 concurrent workflow agents, fewer with fewer CPUs. The bundled skill gives min(16, CPUs − 2). They are consistent, and the local value of 8 is my inference. [V][S7] [L]
- **Docs are ahead of the local terminal CLI.** They describe behaviour from v2.1.271–2.1.282 while the terminal CLI is v2.1.270. For example, `TaskOutput` is documented as removed in v2.1.277 but still appears in older tool tables. [L] [V][S8] [V][S9]
- **Goal bounds.** The brief asked for turn/time caps. `/goal` has **no built-in caps**; the bound must go in the condition text. [V][S1]
- **Effort in `~/.claude/settings.json`.** The local file's `"effortLevel": "medium"` doesn't apply to Opus 5.5 (a legacy top-level user key). This is harmless, because Opus 5.5 defaults to medium anyway. [L] [V][S12]

---

## Sources

| # | Title | URL | Type | Accessed |
|---|---|---|---|---|
| S1 | Keep Claude working toward a goal (/goal) | https://code.claude.com/docs/en/goal | official | 2026-09-25 |
| S2 | Run prompts on a schedule (/loop, cron tools) | https://code.claude.com/docs/en/scheduled-tasks | official | 2026-09-25 |
| S3 | Automate work with routines | https://code.claude.com/docs/en/routines | official | 2026-09-25 |
| S4 | Schedule recurring tasks in Claude Code Desktop | https://code.claude.com/docs/en/desktop-scheduled-tasks | official | 2026-09-25 |
| S5 | Push events into a running session with channels | https://code.claude.com/docs/en/channels | official | 2026-09-25 |
| S6 | Channels reference | https://code.claude.com/docs/en/channels-reference | official | 2026-09-25 |
| S7 | Orchestrate subagents at scale with dynamic workflows | https://code.claude.com/docs/en/workflows | official | 2026-09-25 |
| S8 | Agent SDK reference – TypeScript (Workflow, Monitor, ScheduleWakeup, RemoteTrigger inputs) | https://code.claude.com/docs/en/agent-sdk/typescript | official | 2026-09-25 |
| S9 | Tools reference | https://code.claude.com/docs/en/tools-reference | official | 2026-09-25 |
| S10 | Escalate hard decisions with the advisor tool | https://code.claude.com/docs/en/advisor | official | 2026-09-25 |
| S11 | Advisor tool (Claude API) | https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool | official | 2026-09-25 |
| S12 | Model configuration | https://code.claude.com/docs/en/model-config | official | 2026-09-25 |
| S13 | Models overview (Claude API) | https://platform.claude.com/docs/en/about-claude/models/overview | official | 2026-09-25 |
| S14 | Speed up responses with fast mode | https://code.claude.com/docs/en/fast-mode | official | 2026-09-25 |
| S15 | Output styles | https://code.claude.com/docs/en/output-styles | official | 2026-09-25 |
| S16 | Let Claude use your computer from the CLI | https://code.claude.com/docs/en/computer-use | official | 2026-09-25 |
| S17 | Orchestrate teams of Claude Code sessions | https://code.claude.com/docs/en/agent-teams | official | 2026-09-25 |
| S18 | Create custom subagents | https://code.claude.com/docs/en/sub-agents | official | 2026-09-25 |
| S19 | Manage multiple agents with agent view | https://code.claude.com/docs/en/agent-view | official | 2026-09-25 |
| S20 | Message your other Claude Code sessions | https://code.claude.com/docs/en/cross-session-messaging | official | 2026-09-25 |
| S21 | Hooks guide / Hooks reference | https://code.claude.com/docs/en/hooks-guide ; https://code.claude.com/docs/en/hooks | official | 2026-09-25 |
| S22 | Plugins reference | https://code.claude.com/docs/en/plugins-reference | official | 2026-09-25 |
| S23 | All settings (settings reference) | https://code.claude.com/docs/en/settings-reference | official | 2026-09-25 |
| S24 | Environment variables | https://code.claude.com/docs/en/env-vars | official | 2026-09-25 |
| S25 | Commands | https://code.claude.com/docs/en/commands | official | 2026-09-25 |
| S26 | Extend Claude with skills | https://code.claude.com/docs/en/skills | official | 2026-09-25 |
| S27 | Choose a permission mode | https://code.claude.com/docs/en/permission-modes | official | 2026-09-25 |
| S28 | What's new (index + weekly digests W13–W37) | https://code.claude.com/docs/en/whats-new/index (e.g. /whats-new/2026-w37) | official | 2026-09-25 |
| S29 | Claude Code changelog (docs, dated) | https://code.claude.com/docs/en/changelog | official | 2026-09-25 |
| S30 | CHANGELOG.md (anthropics/claude-code) | https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md | primary | 2026-09-25 |
| S31 | npm package @anthropic-ai/claude-code (versions, dist-tags, publish times) | https://www.npmjs.com/package/@anthropic-ai/claude-code | primary | 2026-09-25 |
| S32 | The advisor strategy (Anthropic blog, Apr 9 2026) | https://claude.com/blog/the-advisor-strategy | official | 2026-09-25 |
| S33 | Claude Code docs index (llms.txt) | https://code.claude.com/docs/llms.txt | official | 2026-09-25 |

Local commands used (all read-only): `claude --version`; `claude --help`; `claude agents --help`; `claude plugin --help`; `which -a claude`; `ps -o command= -p $PPID`; `npm view @anthropic-ai/claude-code version dist-tags time --json`; `sysctl -n hw.ncpu hw.memsize`; `grep` of `~/.claude/settings.json`; `curl -sL <docs>.md` for raw pages; the bundled `/workflow-authoring` skill (loaded as reference only; no workflow was run).

[S1]: https://code.claude.com/docs/en/goal
[S2]: https://code.claude.com/docs/en/scheduled-tasks
[S3]: https://code.claude.com/docs/en/routines
[S4]: https://code.claude.com/docs/en/desktop-scheduled-tasks
[S5]: https://code.claude.com/docs/en/channels
[S6]: https://code.claude.com/docs/en/channels-reference
[S7]: https://code.claude.com/docs/en/workflows
[S8]: https://code.claude.com/docs/en/agent-sdk/typescript
[S9]: https://code.claude.com/docs/en/tools-reference
[S10]: https://code.claude.com/docs/en/advisor
[S11]: https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool
[S12]: https://code.claude.com/docs/en/model-config
[S13]: https://platform.claude.com/docs/en/about-claude/models/overview
[S14]: https://code.claude.com/docs/en/fast-mode
[S15]: https://code.claude.com/docs/en/output-styles
[S16]: https://code.claude.com/docs/en/computer-use
[S17]: https://code.claude.com/docs/en/agent-teams
[S18]: https://code.claude.com/docs/en/sub-agents
[S19]: https://code.claude.com/docs/en/agent-view
[S20]: https://code.claude.com/docs/en/cross-session-messaging
[S21]: https://code.claude.com/docs/en/hooks
[S22]: https://code.claude.com/docs/en/plugins-reference
[S23]: https://code.claude.com/docs/en/settings-reference
[S24]: https://code.claude.com/docs/en/env-vars
[S25]: https://code.claude.com/docs/en/commands
[S26]: https://code.claude.com/docs/en/skills
[S27]: https://code.claude.com/docs/en/permission-modes
[S28]: https://code.claude.com/docs/en/whats-new/index
[S29]: https://code.claude.com/docs/en/changelog
[S30]: https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md
[S31]: https://www.npmjs.com/package/@anthropic-ai/claude-code
[S32]: https://claude.com/blog/the-advisor-strategy
[S33]: https://code.claude.com/docs/llms.txt
