# R1a — Claude Code core extension surfaces (memory, rules, skills, subagents, hooks)

- Date accessed: 2026-09-25 · Author: research agent (Phase 1) · Scope: CLAUDE.md/AGENTS.md memory, `.claude/rules`, auto memory, skills (SKILL.md), subagents (agent files), hooks (all events, I/O contract, plugin hooks), plus the platform Agent Skills authoring best-practices page — verified against live docs on 2026-09-25 and the local CLI (Claude Code 2.1.270).

Tag legend: [V] official/primary source read (URL given) · [L] verified locally (command given) · [R] secondary source · [U] could not confirm.

## Summary (≤10 bullets, each tagged)

1. **The local CLI is behind the docs.** Local is 2.1.270 [L: `claude --version`]; npm has `latest`=2.1.281, `stable`=2.1.273, `next`=2.1.282 [L: `npm view @anthropic-ai/claude-code version dist-tags`]. Several documented features need newer builds: `omitClaudeMd` in agent files needs 2.1.271, reading AGENTS.md natively needs 2.1.277 (fully fixed in 2.1.281), and the `opus` alias pointing at Opus 5.5 needs 2.1.280 [V: [changelog](https://code.claude.com/docs/en/changelog), [memory](https://code.claude.com/docs/en/memory#agents-md), [model-config](https://code.claude.com/docs/en/model-config)].
2. **Hooks fail open unless you design them not to.** Only exit code 2 blocks by itself. Exit 1, a script that is missing or not executable, bad JSON and a timed-out `PreToolUse` command hook all count as non-blocking, so the action goes ahead [V: [hooks#exit-code-output](https://code.claude.com/docs/en/hooks#exit-code-output), [hooks#timeouts](https://code.claude.com/docs/en/hooks#timeouts)].
3. **Stop/SubagentStop block cap.** If a Stop or SubagentStop hook blocks 8 times in a row, Claude Code overrides it and ends the turn with a warning. You can change the cap with `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`, and `0` turns it off. The input field `stop_hook_active` is `true` while the continuation was caused by a stop hook [V: [hooks#stop-input](https://code.claude.com/docs/en/hooks#stop-input), [env-vars](https://code.claude.com/docs/en/env-vars)]. The variable is present in the local 2.1.270 binary [L: `strings …/versions/2.1.270 | grep STOP_HOOK_BLOCK_CAP`].
4. **Plugin-shipped agents lose three security-relevant fields.** They ignore `hooks`, `mcpServers` and `permissionMode`, and they also ignore `initialPrompt`. Project/user agents keep all of these [V: [plugins-reference#plugin-agent-frontmatter](https://code.claude.com/docs/en/plugins-reference#plugin-agent-frontmatter)]. A plugin therefore has to enforce read-only checkers through its own `hooks/hooks.json`, matching on `agent_type` (the plugin-scoped name, e.g. `^forge:checker$`) [V: [hooks#subagentstart](https://code.claude.com/docs/en/hooks#subagentstart)].
5. **A subagent with `memory:` set automatically gets Read, Write and Edit** [V: [sub-agents#enable-persistent-memory](https://code.claude.com/docs/en/sub-agents#enable-persistent-memory)]. A "read-only reviewer with memory" is therefore not read-only by default. Whether those writes are confined to the memory directory is not documented [U].
6. **Plugins cannot ship CLAUDE.md or `.claude/rules/`.** A `CLAUDE.md` at the plugin root is not loaded. Plugins add context only through skills, agents and hooks. A plugin's own `settings.json` supports only the `agent` and `subagentStatusLine` keys [V: [plugins-reference](https://code.claude.com/docs/en/plugins-reference#plugin-directory-structure)].
7. **Path-scoped rules are guidance that loads lazily, not enforcement.** A rule with `paths:` loads when Claude *reads* a matching file. Compaction summarises it away, and it reloads only when a matching file is read again. `paths` is the only frontmatter field a rule reads [V: [memory#path-specific-rules](https://code.claude.com/docs/en/memory#path-specific-rules), [context-window](https://code.claude.com/docs/en/context-window#what-survives-compaction)].
8. **The skill frontmatter spec has grown to 20 fields** (list in §6), including `when_to_use`, `arguments`, `disallowed-tools`, `effort`, `context: fork` + `agent`, `background`, `hooks`, `paths` and `shell`. The listing text (`description` + `when_to_use`) is capped at 1,536 characters. The whole skill listing is budgeted at 1% of the context window [V: [skills#frontmatter-reference](https://code.claude.com/docs/en/skills#frontmatter-reference), [settings-reference](https://code.claude.com/docs/en/settings-reference)].
9. **`isolation: worktree` subagents branch from the repo's default branch, not your HEAD**, unless `worktree.baseRef: "head"` is set [V: [worktrees#choose-the-base-branch](https://code.claude.com/docs/en/worktrees#choose-the-base-branch)]. Subagents can nest 3 layers by default (`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`). The default concurrency cap is 20 (`CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`) [V: [sub-agents](https://code.claude.com/docs/en/sub-agents#let-subagents-spawn-their-own-subagents)].
10. **Workspace trust is uneven.** `claude -p`/SDK runs treat the folder as trusted, so hooks in the repo's `.claude/settings.json` run there. Hooks in a *project subagent's* frontmatter still need explicit trust, and `-p` does not count. A skill's `allowed-tools` is never gated by trust [V: [permissions#what-runs-before-you-trust-a-folder](https://code.claude.com/docs/en/permissions#what-runs-before-you-trust-a-folder)].

## Findings

### 0. Version baseline and local CLI cross-check

- Local version: `2.1.270 (Claude Code)` [L: `claude --version`]. The binary is at `~/.local/share/claude/versions/2.1.270` [L: `ls -la $(which claude)`].
- Latest changelog entry is 2.1.282, dated 2026-09-24 [V: [changelog](https://code.claude.com/docs/en/changelog)]. npm dist-tags: `latest` 2.1.281, `stable` 2.1.273, `next` 2.1.282 [L: `npm view @anthropic-ai/claude-code version dist-tags`].
- `claude agents` now manages **background sessions**. It has no subcommands for subagent definitions; its options include `--json`, `--agent`, `--model` and `--permission-mode` [L: `claude agents --help`]. The `/agents` interactive creation wizard was removed in v2.1.198. You now create agents by asking Claude or editing `.claude/agents/` directly [V: [sub-agents](https://code.claude.com/docs/en/sub-agents#quickstart-create-your-first-subagent)].
- Relevant CLI flags present locally [L: `claude --help`]:
  - `--agent <agent>` and `--agents <json>`.
  - `--bare`: skips hooks, LSP, plugin sync, auto-memory and CLAUDE.md auto-discovery; skills still resolve via `/skill-name`.
  - `--safe-mode`: disables CLAUDE.md, skills, plugins, hooks, MCP servers, agents and more.
  - `--restricted`, `--setting-sources`, `--plugin-dir`, `--plugin-url`, `--disallowedTools`, `--effort` (low|medium|high|xhigh|max).
  - `-w/--worktree`.
- `claude plugin` subcommands locally: `details`, `disable`, `enable`, `eval`, `init|new`, `install`, `list`, `marketplace`, `prune`, `tag`, `uninstall`, `update`, `validate` [L: `claude plugin --help`]. `claude plugin validate` supports `--json` and `--strict`. `--strict` turns warnings into errors, which is meant for CI [L: `claude plugin validate --help`].
- Feature strings in the local binary [L: `strings -n 6 ~/.local/share/claude/versions/2.1.270 | grep -F <s>`]:
  - Present: `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`, `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`, `asyncRewake`, `continueOnBlock`, `reloadSkills`, `disallowed-tools`, `when_to_use`, `skillListingMaxDescChars`, `PostToolBatch`, `MessageDisplay`, `PreModelSwitch`, `UserPromptExpansion`, `agent-memory-local`.
  - Absent: `agents-md@builtin`, which is consistent with AGENTS.md support arriving in 2.1.277.
  - `omitClaudeMd` appears, but only in internal built-in-agent code. The changelog says user frontmatter support was added in 2.1.271 [V: [changelog](https://code.claude.com/docs/en/changelog)], so treat it as unavailable on 2.1.270.

### 1. Memory — CLAUDE.md hierarchy, imports, size

**Locations**, in load order from broadest to most specific [V: [memory#choose-where-to-put-claude-md-files](https://code.claude.com/docs/en/memory#choose-where-to-put-claude-md-files)]:

| Scope | Location |
|---|---|
| Managed policy | macOS `/Library/Application Support/ClaudeCode/CLAUDE.md`; Linux/WSL `/etc/claude-code/CLAUDE.md`; Windows `C:\Program Files\ClaudeCode\CLAUDE.md`. Can also be supplied as the `claudeMd` string key in managed settings. Cannot be excluded. |
| User | `~/.claude/CLAUDE.md` (plus `~/.claude/rules/`) |
| Project | `./CLAUDE.md` or `./.claude/CLAUDE.md` |
| Local | `./CLAUDE.local.md` (personal; gitignore it) |

**Load behaviour** [V: [memory#how-claude-md-files-load](https://code.claude.com/docs/en/memory#how-claude-md-files-load)]:
- Files are concatenated, not overridden. The order runs from the filesystem root down to the cwd, and `CLAUDE.local.md` comes after `CLAUDE.md` at each level.
- Files in ancestors of the cwd load at launch. Files in subdirectories load on demand, when Claude reads files in that subdirectory.
- Block-level HTML comments are stripped before injection. Comments inside code blocks are kept.
- CLAUDE.md is delivered as a user message after the system prompt, not as part of the system prompt [V: [memory#claude-isnt-following-my-claudemd](https://code.claude.com/docs/en/memory#troubleshoot-memory-issues)].
- `--add-dir` directories do not load CLAUDE.md unless `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1` is set.
- `claudeMdExcludes` takes glob patterns matched against absolute paths. It can be set at any settings layer, and arrays merge [V: [memory#exclude-specific-claude-md-files](https://code.claude.com/docs/en/memory#exclude-specific-claude-md-files)].

**@imports** [V: [memory#import-additional-files](https://code.claude.com/docs/en/memory#import-additional-files)]:
- Syntax is `@path/to/file`. Relative paths resolve against the *importing file*, and absolute paths and `~` also work.
- Imports nest to a maximum depth of four hops.
- `@` inside code spans or fences is not treated as an import.
- Imported files still load at launch, so they do not save context.
- An import that resolves outside the working directory, when it appears in a project file, triggers a one-time approval dialog. If the user declines, it stays disabled.

**Size** [V: [memory#write-effective-instructions](https://code.claude.com/docs/en/memory#write-effective-instructions), [memory#my-claudemd-is-too-large](https://code.claude.com/docs/en/memory#my-claudemd-is-too-large)]:
- Target under 200 lines per CLAUDE.md.
- A CLAUDE.md up to 4 MiB loads in full; a larger file is skipped.
- `/doctor` proposes trims (v2.1.206+).
- Compaction: the project-root CLAUDE.md and unscoped rules are re-injected from disk. Nested CLAUDE.md files and path-scoped rules reload only when matching files are read again [V: [context-window#what-survives-compaction](https://code.claude.com/docs/en/context-window#what-survives-compaction)].

### 2. AGENTS.md support status

- **Native, from v2.1.277**, through a built-in plugin `agents-md@builtin` [V: [memory#agents-md](https://code.claude.com/docs/en/memory#agents-md); [changelog 2.1.277](https://code.claude.com/docs/en/changelog)].
- **Default behaviour.** Claude reads AGENTS.md only when there is no `CLAUDE.md`, `.claude/CLAUDE.md` or `CLAUDE.local.md` in the cwd or any ancestor. `~/.claude/CLAUDE.md`, managed CLAUDE.md and `.claude/rules/` do *not* count for this check [V: same].
- **Files read.** At session start it reads `AGENTS.md` and `.claude/AGENTS.md` in the cwd and its ancestors. A subdirectory's AGENTS.md loads on Read if that subdirectory has no CLAUDE.md files. `AGENTS.local.md`, `AGENTS.override.md` and anything under `.agents/` are never read [V: same].
- **The "Project instructions" setting** takes four values: `claude-md-or-agents-md` (default), `claude-md-and-agents-md`, `claude-md` and `managed-only` [V: same].
  - It is set via `/config` or `pluginConfigs["agents-md@builtin"].options.instructionFiles` in user, `--settings` or managed settings.
  - It is ignored in project and local settings [V: same].
- **Differences from CLAUDE.md** [V: same]:
  - `InstructionsLoaded` hooks do not fire for AGENTS.md read through the setting.
  - `--add-dir` AGENTS.md files do not load.
  - External `@` imports load only if they were already approved.
- **Unavailable when** [V: same]:
  - the version is below 2.1.277;
  - the built-in plugin is disabled;
  - it is the first session after upgrading;
  - on versions before v2.1.281, some sessions (Bedrock, telemetry disabled) could not load it.
- **Portable fallback:** a `CLAUDE.md` containing `@AGENTS.md`. This never double-reads, whatever the setting value is [V: [memory#share-one-file-with-other-coding-tools](https://code.claude.com/docs/en/memory#share-one-file-with-other-coding-tools)].
- **On this machine (2.1.270) AGENTS.md is not read natively.** Use the import [L+V: version above; binary lacks `agents-md@builtin`].

### 3. `.claude/rules/*.md` with `paths:`

[V: [memory#organize-rules-with-claude/rules/](https://code.claude.com/docs/en/memory#organize-rules-with-claude/rules/), [memory#path-specific-rules](https://code.claude.com/docs/en/memory#path-specific-rules), [memory#rules-frontmatter-reference](https://code.claude.com/docs/en/memory#rules-frontmatter-reference)]

- **Discovery.** Rules are discovered recursively (all `.md` files under `.claude/rules/`, subfolders allowed). User rules live in `~/.claude/rules/` and load before project rules. Neither overrides the other.
- **Frontmatter.** `paths` is the *only* field read. It accepts a YAML list or a comma-separated string. Other fields are silently ignored. If the YAML does not parse, the rule loads as if unscoped, and `--debug` shows the error.
- **When a rule loads.**
  - A rule without `paths` loads at launch, with the same priority as `.claude/CLAUDE.md`.
  - A rule with `paths` triggers when Claude **reads** a matching file, not on every tool use. Since v2.1.198 this also works through symlinked project paths.
  - The directory page describes the trigger as a matching file "entering context" [V: [claude-directory](https://code.claude.com/docs/en/claude-directory)].
- **Glob semantics** [V]:
  - `**/*.ts`, `src/**/*`, and `*.md` (project root only).
  - Brace expansion works (`src/**/*.{ts,tsx}`).
  - A rule's whole `paths` list shares an expansion budget of 1,000 patterns / 4 MiB. Patterns over budget are used unexpanded, where their braces match nothing (v2.1.217 fixed crashes).
  - `[` starts a bracket expression; escape it as `\[`. An invalid pattern matches nothing (v2.1.207+).
- **Glob anchor.** Examples imply patterns are relative to the project root [V]. The anchor for rules in nested `.claude/rules/` directories is not documented [U].
- **Symlinks.** Supported. A target outside the working directory is treated like an external import: it needs approval, and only rules *without* `paths` load [V].
- **`--setting-sources` without `project`** skips project rules, including lazy ones, since v2.1.211 [V].
- **Observability.** The `InstructionsLoaded` hook fires on each load. Its `load_reason` is one of `session_start`, `nested_traversal`, `path_glob_match`, `include` or `compact`, and its `globs` and `trigger_file_path` fields are useful for debugging [V: [hooks#instructionsloaded](https://code.claude.com/docs/en/hooks#instructionsloaded)].
- **Unclear.** Whether creating a *new* file with Write (no prior Read) triggers a path rule [U].

### 4. Auto memory

[V: [memory#auto-memory](https://code.claude.com/docs/en/memory#auto-memory)]

- **What it is.** Notes Claude writes for itself. It is on by default. Each memory file's frontmatter has a `type` of `user`, `feedback`, `project` or `reference`, plus a `modified` ISO-8601 timestamp (v2.1.214+).
- **Where it lives.** `~/.claude/projects/<project>/memory/`, with a `MEMORY.md` index plus one topic file per memory.
  - `<project>` is derived from the git repo, so all worktrees share one directory. Memory is machine-local.
  - `autoMemoryDirectory` overrides the location. It must be an absolute path or start with `~/`, and it can be set at any scope, subject to trust rules.
- **What loads.** At session start, the first 200 lines or 25KB of `MEMORY.md`, whichever comes first. Topic files are read on demand. If the index goes over its limit, the write still succeeds but Claude gets an error telling it to rewrite the index.
- **How to disable.** Use the `/memory` toggle (it writes `autoMemoryEnabled` to user settings), `"autoMemoryEnabled": false` in project settings, or `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`. Setting that variable to `0` forces memory on even under `--bare` [V: [env-vars](https://code.claude.com/docs/en/env-vars)].
- **Subagents.** Subagents do not receive the main session's auto memory; forks are the exception. Subagent `memory:` is a separate directory [V].

### 5. Skills — locations, precedence, naming, legacy commands

[V: [skills#where-skills-live](https://code.claude.com/docs/en/skills#where-skills-live), [skills#resolve-skills-that-share-a-name](https://code.claude.com/docs/en/skills#resolve-skills-that-share-a-name)]

- **Locations:**
  - Enterprise: `.claude/skills/<name>/SKILL.md` in the managed settings directory.
  - Personal: `~/.claude/skills/<name>/SKILL.md`.
  - Project: `.claude/skills/<name>/SKILL.md`, walked up to the repo root. In a linked worktree the walk stops at the worktree root. From v2.1.277, if the worktree has no `.claude/skills`, the main checkout's skills load instead.
  - Nested: `<subdir>/.claude/skills/`, loaded the first time Claude reads or edits a file there.
  - `--add-dir` directories.
  - Plugin: `<plugin>/skills/<name>/SKILL.md`, exposed as `/plugin-name:skill-name`.
  - claude.ai synced skills, exposed as `/anthropic-skills:<name>`. Terminal sync needs v2.1.273.
- **Precedence on name clash:**
  - enterprise > personal > project;
  - a user skill replaces a bundled skill, but not its aliases;
  - a skill beats a `.claude/commands/` file;
  - a plugin skill never clashes, because it is namespaced;
  - a nested skill clashing with a root skill: both load, and the nested one is reachable as `/apps/web:deploy`.
- **Command name source** [V: [skills#how-a-skill-gets-its-command-name](https://code.claude.com/docs/en/skills#how-a-skill-gets-its-command-name)]:
  - For personal and project skills, the **directory name** is the command. The `name` field is only a display label.
  - In a **plugin** skill, `name` replaces the last segment: `my-plugin/skills/review/` with `name: fancy` becomes `/my-plugin:fancy`. A bare `/fancy` also works if no other command uses it.
  - Since v2.1.246 the prefix is not doubled if `name` already contains it.
- **Legacy `commands/`.** Custom commands have been merged into skills. `.claude/commands/deploy.md` and `.claude/skills/deploy/SKILL.md` both create `/deploy`. A command file accepts all skill fields **except `name` and `paths`**. Subfolders become namespaces (`commands/frontend/component.md` becomes `/frontend:component`). Prefer skills for new work [V: [skills](https://code.claude.com/docs/en/skills)].
- **Reserved folder name:** `synced` (any case) [V].
- **Hot reload.** SKILL.md text reloads live. For a skill-folder plugin, changes to `hooks/`, `.mcp.json`, `agents/` and so on need `/reload-plugins` [V: [skills#live-change-detection](https://code.claude.com/docs/en/skills#live-change-detection)].
- **Validation.** `claude plugin validate .claude/skills` finds unparsable frontmatter (v2.1.233+) [V: [skills#skill-not-triggering](https://code.claude.com/docs/en/skills#troubleshooting)].

### 6. Skills — SKILL.md frontmatter (complete list as of 2026-09-25)

[V: [skills#frontmatter-reference](https://code.claude.com/docs/en/skills#frontmatter-reference); cross-checked with the field list on [claude-directory#frontmatter-fields-by-file](https://code.claude.com/docs/en/claude-directory)]

General rules [V]:
- All fields are optional; `description` is recommended.
- Field names are kebab-case, except `when_to_use`.
- Unknown fields are ignored silently.
- Frontmatter is read only if `---` is the very first line.
- If the YAML does not parse, the skill loads with no fields set.
- Booleans also accept `yes/no/on/off/1/0` (v2.1.218+).

| Field | Allowed values / semantics |
|---|---|
| `name` | Display label. Defaults to the directory name. In plugins, sets the last command segment. |
| `description` | What and when. If absent, the first non-empty body line is used. `description` + `when_to_use` are truncated at **1,536 chars** in the listing (`skillListingMaxDescChars`, default 1536). |
| `when_to_use` | Extra trigger text, appended to the description; counts toward the 1,536 cap. |
| `argument-hint` | Autocomplete hint, e.g. `[issue-number]`. |
| `arguments` | Named positional arguments (space-separated string or YAML list) for `$name` substitution. |
| `disable-model-invocation` | `true`: only the user can invoke it. Its description is removed from Claude's context, it cannot be preloaded into subagents, and (v2.1.196+) it will not run as a scheduled-task prompt. Default `false`. |
| `user-invocable` | `false`: hidden from the `/` menu, and the user cannot run it; Claude still can. Default `true`. |
| `allowed-tools` | Tools pre-approved **for the invoking turn only**; the grant clears on the next user message. Does not restrict other tools. Space- or comma-separated string, or YAML list. **Not gated by workspace trust.** |
| `disallowed-tools` | Tools removed while the skill is active; clears on the next user message. Cannot remove `EndConversation`. |
| `model` | Same values as `/model`, or `inherit`. Applies for the rest of the turn. With `context: fork`, sets the forked subagent's model. Subject to the `availableModels` allowlist. |
| `effort` | `low`, `medium`, `high`, `xhigh`, `max` (model-dependent). |
| `context` | `fork`: runs the skill as a fresh subagent. This is *not* a fork of the conversation. |
| `agent` | Subagent type for `context: fork`: `Explore`, `Plan`, `general-purpose`, or a custom agent. Default `general-purpose`. |
| `background` | Only with `context: fork`. Default `true`; `false` makes the invoking turn wait for the result (v2.1.218+). |
| `hooks` | Hooks registered when the skill is invoked; they **persist for the rest of the session**. `once: true` is honoured here only. |
| `paths` | Globs (string or list). When set, the skill auto-loads only when working with matching files. Same format as rules. |
| `shell` | `bash` (default) or `powershell`, for `` !`cmd` `` and ```` ```! ```` blocks. |
| `metadata` | Free-form map; Claude Code does not act on it. |
| `license` | Accepted, not acted on (Agent Skills spec field). |
| `compatibility` | String ≤500 chars; accepted, not acted on. |

- **Portability** [V: [skills#using-skill-frontmatter-outside-claude-code](https://code.claude.com/docs/en/skills#using-skill-frontmatter-outside-claude-code)]:
  - claude.ai uploads, the Skills API and `package_skill.py` accept only `name`, `description`, `license`, `compatibility`, `metadata` and `allowed-tools`.
  - Any other key is a hard error on those paths.
  - Claude Code accepts all fields.
- **Name and description limits (Agent Skills spec / platform):**
  - `name`: 1–64 characters; lowercase `a-z0-9` and `-` only; no leading, trailing or double hyphen; must match the parent directory.
  - `description`: 1–1,024 characters.
  - Platform docs add: no XML tags, and no reserved words "anthropic" or "claude".
  - Sources: [V: [agentskills.io/specification](https://agentskills.io/specification), [platform best-practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)]. Whether Claude Code itself enforces the 64/1,024 limits for local skills is not stated [U].

### 7. Skills — substitutions, dynamic context, lifecycle, budgets

**Substitutions** [V: [skills#available-string-substitutions](https://code.claude.com/docs/en/skills#available-string-substitutions)]:

| Variable | Meaning |
|---|---|
| `$ARGUMENTS` | All arguments. If no placeholder consumes them, Claude Code appends `ARGUMENTS: <value>`. |
| `$ARGUMENTS[N]`, `$N` | 0-based positional argument, using shell-style quoting. An unfilled `$N` stays literal. |
| `$name` | Named argument from `arguments:`. Expands to an empty string if missing. |
| `${CLAUDE_SESSION_ID}` | Session ID. |
| `${CLAUDE_EFFORT}` | Current effort level. |
| `${CLAUDE_SKILL_DIR}` | Directory containing this SKILL.md. For plugin skills, this is the skill's subdirectory. |
| `${CLAUDE_PROJECT_DIR}` | Project root (v2.1.196+). |
| `${CLAUDE_PLUGIN_ROOT}` | Plugin install directory. Plugin skills only. |
| `${CLAUDE_PLUGIN_DATA}` | Persistent plugin data directory. Plugin skills only. |

- **Where substitution happens.** `${CLAUDE_SKILL_DIR}` and `${CLAUDE_PROJECT_DIR}` (and the plugin variables, in plugin skills) are substituted in the body and in Bash rules inside `allowed-tools`. Using the same path in both places lets a bundled script run without a prompt [V].
- **Escaping.** Use `\$1` to write a literal `$1`. Backslash escaping does not stop `${CLAUDE_*}` substitution [V].
- **Environment gap.** The plugin path variables are exported to hook, MCP and LSP processes, but **not** to Bash tool commands. Skills must use the inline placeholders instead [V: [plugins-reference#environment-variables](https://code.claude.com/docs/en/plugins-reference#environment-variables)].

**Dynamic context injection** [V: [skills#inject-dynamic-context](https://code.claude.com/docs/en/skills#inject-dynamic-context)]:
- A line starting with `` !`cmd` ``, or a ```` ```! ```` block, runs *before* Claude sees the skill.
- A non-zero exit aborts the entire invocation. Exit 1 from search/compare commands is tolerated. Use `|| true` for check scripts.
- Each command gets a 2-minute timeout.
- The command is checked against permission rules. Outside auto mode, any result other than allow aborts the invocation, unless `allowed-tools` pre-approves it.
- Can be disabled with `disableSkillShellExecution`.
- Never runs for claude.ai-synced skills on a local machine.

**Lifecycle** [V: [skills#skill-content-lifecycle](https://code.claude.com/docs/en/skills#skill-content-lifecycle)]:
- The rendered SKILL.md enters the conversation as one message and stays. It is not re-read on later turns.
- After compaction, each invoked skill is re-attached up to its first 5,000 tokens, within a combined 25,000-token budget, newest first. Put critical instructions at the top.

**Budgets and visibility** [V: [skills#skill-descriptions-are-cut-short](https://code.claude.com/docs/en/skills#skill-descriptions-are-cut-short), [settings-reference](https://code.claude.com/docs/en/settings-reference)]:
- The skill listing is budgeted at `skillListingBudgetFraction` (default `0.01` = 1% of the context window). `SLASH_COMMAND_TOOL_CHAR_BUDGET` sets a fixed character count instead; the fallback is 8,000 chars [V: [env-vars](https://code.claude.com/docs/en/env-vars)].
- On overflow, descriptions of the least-used skills are dropped first.
- `skillOverrides` states: `on`, `name-only`, `user-invocable-only`, `off`. It does not apply to plugin skills.
- `/skill-doctor` (v2.1.252+) reports cost and usage.
- Permission rules: `Skill(name)` matches exactly; `Skill(name *)` matches by prefix [V: [skills#restrict-claudes-skill-access](https://code.claude.com/docs/en/skills#restrict-claudes-skill-access)].

**Progressive disclosure** [V: [skills](https://code.claude.com/docs/en/skills#add-supporting-files), [agentskills.io](https://agentskills.io/specification)]:
- Three levels: metadata (~100 tokens) is always listed; the body (recommended under 5,000 tokens) loads when invoked; resources load only when read.
- Keep SKILL.md under 500 lines.

### 8. Skills — `context: fork`

[V: [skills#run-skills-in-a-subagent](https://code.claude.com/docs/en/skills#run-skills-in-a-subagent)]

- **What it does.** Starts a *new* subagent of type `agent`. The SKILL.md content becomes its prompt, and it has **no conversation history**.
- **What loads with it.** The system prompt comes from the agent type. CLAUDE.md loads according to that agent's startup rules; Explore and Plan skip it.
- **Background by default** since v2.1.218. The turn waits for the result when:
  - `background: false` is set;
  - the session is `-p` or the SDK;
  - `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` is set;
  - the same skill is already running;
  - it fires as a scheduled task.
- **Reduced tools when backgrounded.** A backgrounded forked skill gets the narrower background tool set (§10).
- **Edits bypass checkpoints.** A background fork's edits happen outside checkpoints, so `/rewind` does not undo them.
- **Only for explicit tasks.** Don't use it for pure guideline skills; the subagent receives no task and returns nothing useful.
- **Inverse pattern.** A subagent's `skills:` field *preloads* full skill content into the subagent.

### 9. Subagents — scopes, precedence, file rules

[V: [sub-agents#choose-the-subagent-scope](https://code.claude.com/docs/en/sub-agents#choose-the-subagent-scope)]

- **Priority, highest first:**
  1. managed settings `.claude/agents/`;
  2. the `--agents` JSON flag;
  3. project `.claude/agents/` (walked up; the definition closest to the cwd wins);
  4. `~/.claude/agents/`;
  5. plugin `agents/`.
- **Scanning.** Directories are scanned recursively. For project and user agents, identity comes only from `name`; subfolders don't matter. For plugins, subfolders become part of the ID: `agents/review/security.md` loads as `my-plugin:review:security`.
- **Skipped files (project/user/managed).** A file is skipped silently if:
  - it has no `name`;
  - `---` is not on line 1;
  - `name` starts with `-` or contains `:` (v2.1.218+);
  - it has `name` but no `description`;
  - its YAML is unparsable.
  - A **plugin** agent still loads in these cases, under its filename.
- **Live reload.** File changes are hot-reloaded. Exceptions: a brand-new `agents` directory, `--add-dir` agents, and `--disable-slash-commands` sessions.
- **Description budget.** If custom agent descriptions total more than 15,000 tokens combined, a startup warning appears [V].

### 10. Subagents — frontmatter (complete list as of 2026-09-25)

[V: [sub-agents#supported-frontmatter-fields](https://code.claude.com/docs/en/sub-agents#supported-frontmatter-fields)]

- Only `name` and `description` are required.
- Multi-word keys are camelCase.
- Unknown keys are ignored silently.
- The body becomes the system prompt. It *replaces* the Claude Code system prompt; environment details are appended.

| Field | Allowed values / semantics | Plugin agents? |
|---|---|---|
| `name` | Unique ID; no `:`, must not start with `-`. Hooks see it as `agent_type`. | ✓ |
| `description` | When to delegate; "use proactively" encourages auto-delegation. | ✓ |
| `tools` | Allowlist (comma string or YAML list). Inherits all tools if omitted. Supports `mcp__server` / `mcp__server__*`. `Agent(type,…)` restricts spawnable types **only when running as the main thread via `--agent`**; inside a subagent definition the list in parentheses is ignored. | ✓ |
| `disallowedTools` | Denylist, applied before `tools`. An entry with a specifier such as `Bash(git push *)` removes the **whole** tool. `mcp__*` removes all MCP tools. | ✓ |
| `model` | `sonnet`, `opus`, `haiku`, `fable`, a full ID (e.g. `claude-opus-5-5`), or `inherit`. | ✓ |
| `permissionMode` | `default`, `acceptEdits`, `auto`, `dontAsk`, `bypassPermissions`, `plan`, and `manual` (= `default`, v2.1.200+). Ignored when the parent is in `bypassPermissions`, `acceptEdits` or auto. A subagent's `bypassPermissions` is refused (v2.1.267+). | ✗ ignored |
| `maxTurns` | Integer; output is marked partial when reached (v2.1.246+). | ✓ |
| `skills` | Skill names whose full content is preloaded. Cannot include `disable-model-invocation` skills. | ✓ |
| `mcpServers` | Names of existing servers, or inline configs (`stdio`, `http`, `sse`, `ws`). Inline servers from project agents need folder trust (v2.1.238+). | ✗ ignored |
| `hooks` | Hooks scoped to this agent's lifetime; `Stop` becomes `SubagentStop`. Project agents need explicit folder trust, and `-p` does not count. | ✗ ignored |
| `memory` | `user`, `project`, or `local` (§12). | ✓ |
| `background` | `true` always runs it in the background. | ✓ |
| `omitClaudeMd` | `true` skips user, project and local CLAUDE.md; managed still loads. **v2.1.271+**. Ignored under `--agent`. | ✓ |
| `effort` | `low`, `medium`, `high`, `xhigh`, `max`. | ✓ |
| `isolation` | `worktree` is the only value. | ✓ |
| `color` | `red`, `blue`, `green`, `yellow`, `purple`, `orange`, `pink`, `cyan`. | ✓ |
| `initialPrompt` | Auto-submitted first turn when the agent is the main session (`--agent` or the `agent` setting). | ✗ not supported |
| `experimental` | Map; only `cacheTtl: 5m` or `1h` is recognised (v2.1.248+). | ✓ |

Plugin column source: [V: [plugins-reference#plugin-agent-frontmatter](https://code.claude.com/docs/en/plugins-reference#plugin-agent-frontmatter)]. `--agents` JSON accepts `prompt` plus every field above except `color` and `experimental` [V].

**Model resolution order** [V: [sub-agents#choose-a-model](https://code.claude.com/docs/en/sub-agents#choose-a-model)]:
1. The per-invocation `model` parameter.
2. The frontmatter `model`.
3. `CLAUDE_CODE_SUBAGENT_MODEL`.
4. The main conversation's model.

- A family alias that matches the main model's family resolves to the main model exactly, including any `[1m]` suffix.
- `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` (v2.1.257+) forces one model on all subagents.
- Subagents inherit the parent's extended-thinking setting (v2.1.198+).
- Whether the frontmatter `model` also accepts `best`, `opusplan` or `[1m]` variants is not documented [U].

**Tools available to subagents** [V: [sub-agents#available-tools](https://code.claude.com/docs/en/sub-agents#available-tools)]:
- **Always removed:** `AskUserQuestion`, `EndConversation`, `EnterPlanMode`, `ExitPlanMode` (unless `permissionMode: plan`), `ScheduleWakeup`, `WaitForMcpServers`, `Workflow`. `Agent` is also removed at the depth limit.
- **Background subagents** keep all MCP tools, but only these built-ins: `Read`, `Grep`, `Glob`, `LSP`, `Bash`, `PowerShell`, `Edit`, `Write`, `NotebookEdit`, `WebFetch`, `WebSearch`, `TodoWrite`, `Skill`, `ToolSearch`, `EnterWorktree`, `ExitWorktree`, `Monitor`, `TaskStop`, `SendMessage`, `Artifact` (plus `SubagentHandback`).
- **Zero tools.** A `tools` list that resolves to nothing makes the launch fail (v2.1.208+).

**Nesting** [V: [sub-agents#let-subagents-spawn-their-own-subagents](https://code.claude.com/docs/en/sub-agents#let-subagents-spawn-their-own-subagents)]:
- Allowed by default, down to **3 layers** below main.
- Set with `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`; `1` disables nesting.
- To keep one agent from spawning, omit `Agent` from its `tools` or add it to `disallowedTools`.
- `Task` was renamed `Agent` in v2.1.63; `Task(...)` still works as an alias.
- **Concurrency.** The default is 20 running subagents (`CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`, v2.1.217+). There is no limit on the total over a session.

**Foreground vs background** [V: [sub-agents#run-subagents-in-foreground-or-background](https://code.claude.com/docs/en/sub-agents#run-subagents-in-foreground-or-background)]:
- **Fork mode is on by default in interactive sessions** (v2.1.232+). There, every Agent-tool subagent runs in the background and Claude cannot request the foreground.
- `-p` and the SDK default to fork mode off. Override with `CLAUDE_CODE_FORK_SUBAGENT=0|1`.
- Background subagents surface permission prompts in the main session. In `-p`, a prompt that no hook answers is denied.
- Results arrive in a later turn as a completion notification.

**Deny specific agents** with `permissions.deny: ["Agent(name)"]`. Parameter rules also exist: `Agent(model:opus)` and `Agent(isolation:worktree)` [V: [permissions](https://code.claude.com/docs/en/permissions)].

### 11. Subagents — what loads, forks, output scanning

[V: [sub-agents#what-loads-at-startup](https://code.claude.com/docs/en/sub-agents#what-loads-at-startup)]

- **Non-fork subagent initial context:**
  - its own system prompt plus environment details;
  - the delegation message;
  - the **full CLAUDE.md hierarchy**, including rules, CLAUDE.local.md, managed files and AGENTS.md. Explore/Plan skip this, and `omitClaudeMd` skips everything except managed files;
  - a git status snapshot;
  - preloaded skills;
  - a sibling roster (when it has `SendMessage`).
- **Never passed to a non-fork subagent:** conversation history, output style, main auto memory.
- **Forks** (`/subtask`, or Agent type `fork`) inherit the whole conversation, system prompt, tools and model, and share the prompt cache. A fork cannot fork further [V: [sub-agents#fork-the-current-conversation](https://code.claude.com/docs/en/sub-agents#fork-the-current-conversation)].
- **Output scanning (v2.1.210+).** Before a subagent's report reaches Claude, Claude Code escapes text that imitates harness tags or `Human:`/`Assistant:` turns. It adds a marker line when the report mentions permission-bypass settings, and wraps the report under a header saying it carries no user authority [V: [sub-agents#subagent-output-scanning](https://code.claude.com/docs/en/sub-agents#subagent-output-scanning)].
- **Resume.** Use `SendMessage` with the agent's ID or name. Explore and Plan are one-shot and cannot be resumed. Transcripts are stored at `~/.claude/projects/{project}/{sessionId}/subagents/agent-{agentId}.jsonl` [V].

### 12. Subagents — `memory:` scopes

[V: [sub-agents#enable-persistent-memory](https://code.claude.com/docs/en/sub-agents#enable-persistent-memory)]

| Scope | Directory |
|---|---|
| `user` | `~/.claude/agent-memory/<name-of-agent>/` |
| `project` | `.claude/agent-memory/<name-of-agent>/` (shareable via VCS; the recommended default) |
| `local` | `.claude/agent-memory-local/<name-of-agent>/` (not committed) |

- When enabled:
  - The agent's prompt gets memory instructions plus the first 200 lines / 25KB of its `MEMORY.md`.
  - **Read, Write and Edit are auto-enabled.**
- The field does nothing if auto memory is disabled (`autoMemoryEnabled: false` or `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`).
- Not documented [U]:
  - the directory name for plugin-scoped agents (e.g. whether `forge:review:checker` becomes a path containing colons);
  - whether auto-enabled writes are limited to the memory directory.

### 13. Subagents — `isolation: worktree`

[V: [sub-agents#write-subagent-files](https://code.claude.com/docs/en/sub-agents#write-subagent-files), [worktrees](https://code.claude.com/docs/en/worktrees#isolate-subagents-with-worktrees)]

- **Creation.** A temporary worktree under `.claude/worktrees/`, **branched from the default remote branch** (`worktree.baseRef: "fresh"`, the default). Use `"head"` to branch from the current HEAD; a branch name cannot be given.
- **Cleanup.** The worktree is removed automatically if the subagent makes no changes. Otherwise a sweep removes it after `cleanupPeriodDays` (default 30), but only if it holds no work. While the agent runs, a `git worktree lock` is held.
- **Command confinement.** Bash and PowerShell commands whose cwd resolves to the main checkout fail. Bash commands that redirect git into the main checkout are blocked, and so are commands whose git target can't be verified (v2.1.203/2.1.210 hardening).
- **Replacing git.** `WorktreeCreate`/`WorktreeRemove` hooks can replace git behaviour entirely.
- **Sparse checkouts.** `worktree.sparsePaths` checks out only the listed directories. Add `.claude` to the list if rules or settings are needed inside the worktree [V: [large-codebases](https://code.claude.com/docs/en/large-codebases)].

### 14. Hooks — event catalogue

[V: [hooks#hook-lifecycle](https://code.claude.com/docs/en/hooks#hook-lifecycle), [hooks#matcher-patterns](https://code.claude.com/docs/en/hooks#matcher-patterns), [hooks#exit-code-2-behavior-per-event](https://code.claude.com/docs/en/hooks#exit-code-2-behavior-per-event), [hooks#prompt-based-hooks](https://code.claude.com/docs/en/hooks#prompt-based-hooks)]

There are 33 events. "All 5" means the handler types `command`, `http`, `mcp_tool`, `prompt` and `agent`. "c/h/m" means `command`, `http`, `mcp_tool`.

| Event | Matcher filters on | Exit 2 effect | Handler types |
|---|---|---|---|
| SessionStart | `source`: `startup`,`resume`,`clear`,`compact`,`fork` | stderr to user only | `command`, `mcp_tool` (mcp_tool skipped at launch) |
| Setup | `init`,`maintenance` | ignored | `command` (mcp_tool always skipped) |
| UserPromptSubmit | — | blocks and erases the prompt | all 5 |
| UserPromptExpansion | `command_name` | blocks the expansion | all 5 |
| PreToolUse | `tool_name` | blocks the tool call | all 5 |
| PermissionRequest | `tool_name` | **not honoured**; use the `decision` object | c/h/m + prompt (no agent) |
| PermissionDenied | `tool_name` | ignored (auto mode only) | all 5 (prompt/agent output discarded) |
| PostToolUse | `tool_name` | stderr shown to Claude | all 5 |
| PostToolUseFailure | `tool_name` | stderr shown to Claude | all 5 |
| PostToolBatch | — | stops the agentic loop | all 5 |
| Notification | type (`permission_prompt`,`idle_prompt`,… ) | ignored | c/h/m |
| MessageDisplay | — | original text is displayed | c/h/m |
| SubagentStart | `agent_type` | stderr to user only | c/h/m |
| SubagentStop | `agent_type` | prevents the subagent from stopping | all 5 |
| TaskCreated | — | rolls back the task | all 5 |
| TaskCompleted | — | prevents completion | all 5 |
| Stop | — | prevents stopping | all 5 |
| StopFailure | error type (`rate_limit`,`overloaded`,…) | ignored | c/h/m |
| TeammateIdle | — | keeps the teammate working | all 5 |
| InstructionsLoaded | `load_reason` | ignored | c/h/m |
| ConfigChange | `user_settings`,`project_settings`,`local_settings`,`policy_settings`,`skills` | blocks (except policy) | c/h/m |
| CwdChanged | — | stderr to user | c/h/m |
| DirectoryAdded | `slash_command`,`register_repo_root` | debug log | c/h/m |
| FileChanged | literal filenames (the watch list) | stderr to user | c/h/m |
| WorktreeCreate | — | any non-zero fails creation | c/h/m |
| WorktreeRemove | — | any non-zero fails removal if the directory remains | c/h/m |
| PreCompact | `manual`,`auto` | blocks compaction | c/h/m |
| PostCompact | `manual`,`auto` | stderr to user | c/h/m |
| PreModelSwitch | canonical `to_model` | blocks the switch (v2.1.251+) | c/h/m |
| PostModelSwitch | canonical `to_model` | stderr to user | c/h/m |
| Elicitation | MCP server name | denies | c/h/m |
| ElicitationResult | MCP server name | blocks (becomes decline) | c/h/m |
| SessionEnd | `clear`,`resume`,`logout`,`prompt_input_exit`,`other` | stderr to user | c/h/m |

**Matcher syntax** [V: [hooks#matcher-patterns](https://code.claude.com/docs/en/hooks#matcher-patterns)]:
- `"*"`, `""` or an omitted matcher matches everything.
- A matcher using only letters, digits, `_`, `-`, spaces, `,` and `|` is an exact match or a list. The `,` form needs v2.1.191+ and hyphens need v2.1.195+.
- Any other character makes it an **unanchored JS regex**. Anchor it (`^Edit$`) when you mean an exact match.
- FileChanged and StopFailure use a narrower exact-match set (no `-`, space or `,`).
- Matchers are case-sensitive [V: [hooks-guide](https://code.claude.com/docs/en/hooks-guide#hook-not-firing)].
- A matcher on an event without matcher support is ignored silently.
- **MCP tools:** use `mcp__server__.*`. A bare `mcp__server` matches nothing. Plugin-bundled servers use `mcp__plugin_<plugin>_<server>__<tool>`.
- **Plugin agents in SubagentStart/Stop:** match `^plugin:agent$`. The colon forces the regex path.

### 15. Hooks — configuration and handler types

[V: [hooks#configuration](https://code.claude.com/docs/en/hooks#configuration), [hooks#hook-handler-fields](https://code.claude.com/docs/en/hooks#hook-handler-fields)]

- **Shape:** `{"hooks": {"<Event>": [{"matcher": "...", "hooks": [ {handler}, … ]}]}}`.
- **Locations:**
  - `~/.claude/settings.json`, `.claude/settings.json`, `.claude/settings.local.json`;
  - managed policy;
  - a plugin's `hooks/hooks.json` (or inline or a path in `plugin.json` `hooks`);
  - skill frontmatter (lasts the rest of the session);
  - agent frontmatter (lasts while the agent runs).
- **Merging and running:**
  - Entries merge across levels.
  - **All matching handlers run in parallel.**
  - An identical handler defined in several settings files runs once. Plugin and skill copies stay separate.
  - All handlers run to completion even if one denies.
  - When several hooks return `updatedInput`, the last to finish wins, which is non-deterministic [V: [hooks-guide#combine-results-from-multiple-hooks](https://code.claude.com/docs/en/hooks-guide#combine-results-from-multiple-hooks)].
- **Common handler keys:**
  - `type`: `command` | `http` | `mcp_tool` | `prompt` | `agent`.
  - `if`: **one** permission-rule string, only evaluated on tool events; best-effort for Bash.
  - `timeout` in seconds. Defaults: 600 for command/http/mcp_tool; 30 for prompt; 60 for agent. It drops to 30 on UserPromptSubmit and Pre/PostModelSwitch, and to 10 on MessageDisplay. SessionEnd has a 1.5 s budget, which can be raised to 60 s.
  - `statusMessage`.
  - `once`: skill frontmatter only.
- **`command`:**
  - `command` (required).
  - `args`: *exec form*, with no shell; placeholders are substituted per element. This is recommended for path placeholders.
  - `async`.
  - `asyncRewake`: runs in the background and wakes Claude on exit 2.
  - `shell`: `bash` | `powershell`.
  - Shell form uses `sh -c` on macOS/Linux.
- **`http`:** `url`, `headers` (`$VAR` interpolation limited to `allowedEnvVars`), `allowedEnvVars`. A non-2xx response or connection failure is non-blocking. **An HTTP hook blocks only through a 2xx JSON body** [V: [hooks#http-response-handling](https://code.claude.com/docs/en/hooks#http-response-handling)]. Governed by the `allowedHttpHookUrls` and `httpHookAllowedEnvVars` settings.
- **`mcp_tool`:** `server`, `tool`, `input` (with `${tool_input.file_path}`-style substitution). For plugin servers, `server` is `plugin:<plugin>:<server>`. It never triggers connect or OAuth. An unconnected server or an `isError` result is non-blocking.
- **`prompt`:**
  - `prompt` (with the `$ARGUMENTS` placeholder), `model` (defaults to a fast model, Haiku), `timeout`, `continueOnBlock`.
  - The LLM replies `{"ok": bool, "reason": str, "impossible": bool}`.
  - On PreToolUse, `ok:false` **by default ends the turn**; with `continueOnBlock: true` the reason goes back to Claude as a tool error.
  - On Stop/SubagentStop, `ok:false` continues the turn unless `impossible: true`.
- **`agent`:** marked **experimental**. A multi-turn verifier with Read/Grep/Glob, up to 50 turns, 60 s default timeout, no `continueOnBlock`. `ok:false` is handled like a prompt hook with `continueOnBlock: true`. Not supported on PermissionRequest [V: [hooks#agent-based-hooks](https://code.claude.com/docs/en/hooks#agent-based-hooks)].
- **Async hooks:**
  - Only `type: command`.
  - Output is delivered on the next turn.
  - Decision fields have no effect.
  - The timeout is not enforced for `async`, but is for `asyncRewake`.
  - Killed at `-p` teardown.
  - No dedupe across firings [V: [hooks#run-hooks-in-the-background](https://code.claude.com/docs/en/hooks#run-hooks-in-the-background)].
- **Disabling.** `disableAllHooks: true`, which respects the managed hierarchy. You cannot disable a single hook [V].
- **`/hooks` is read-only.** It shows the source labels User/Project/Local/Plugin/Session [V].

### 16. Hooks — input (stdin) fields

[V: [hooks#common-input-fields](https://code.claude.com/docs/en/hooks#common-input-fields)]

- **Common to every event:**
  - `session_id`
  - `prompt_id` (v2.1.196+)
  - `transcript_path`, which may lag; use `last_assistant_message` instead
  - `cwd`, which follows `cd` and worktree entry
  - `scratchpad_dir` (v2.1.257+)
  - `permission_mode`: `default`, `plan`, `acceptEdits`, `auto`, `dontAsk` or `bypassPermissions`. "Manual" arrives as `default`, and not every event includes this field.
  - `effort.level`
  - `hook_event_name`
- **Inside a subagent or under `--agent`:** `agent_id` and `agent_type` are added. For subagents, the subagent's own type takes precedence.
- **Model:** only SessionStart may get `model`. There is no `$CLAUDE_MODEL`.
- **Tool events** add `tool_name`, `tool_input` and `tool_use_id`. For MCP tools, `mcp_server` `{name, source}` is added (v2.1.274+).
- **File paths.** For file tools, `tool_input.file_path` is always absolute, and `~`/relative paths are expanded before the hook runs.
- **Per-tool `tool_input` shapes** are documented for Bash, PowerShell, Write, Edit, Read, Glob, Grep, WebFetch, WebSearch, Agent, AskUserQuestion and ExitPlanMode [V: [hooks#pretooluse-input](https://code.claude.com/docs/en/hooks#pretooluse-input)].
- **PostToolUse:**
  - adds `tool_response` and `duration_ms`;
  - for `Agent`, the response carries `status`, `agentId`, `content`, `resolvedModel`, `totalTokens`, `totalDurationMs`, `totalToolUseCount` and `usage` (foreground only);
  - Bash can carry `tool_response.bashEditDiff` (public beta, v2.1.269+; not for enforcement).
- **Stop:** `stop_hook_active`, `last_assistant_message`, `background_tasks[]`, `session_crons[]`.
- **SubagentStop** adds `agent_id`, `agent_type`, `agent_transcript_path` and `last_assistant_message`. SubagentStop also fires for internal agents (prompt suggestions, `/btw`); those have an empty `agent_type`.
- **PreCompact:** `trigger`, `custom_instructions`. **PostCompact:** `trigger`, `compact_summary`.
- **SessionStart:** `source`, optionally `model`, `agent_type`, `session_title`. On resume or fork, cost fields are also included (v2.1.251+).

### 17. Hooks — output contract

[V: [hooks#exit-code-output](https://code.claude.com/docs/en/hooks#exit-code-output), [hooks#json-output](https://code.claude.com/docs/en/hooks#json-output), [hooks#decision-control](https://code.claude.com/docs/en/hooks#decision-control)]

**Exit codes:**
- **0:** success. Stdout is parsed as JSON if it starts with `{` and ends with `}`; otherwise it is plain text.
  - Plain stdout is added to Claude's context only for UserPromptSubmit, UserPromptExpansion, SessionStart and PostModelSwitch. For other events it goes to the debug log.
  - Stderr on exit 0 goes to the debug log only.
- **2:** blocking error on events that can block. The message is the JSON reason if there is one, otherwise stderr. **JSON cannot override an exit-2 block**, and even `permissionDecision: allow` does not undo it. Since v2.1.214, exit 2 with schema-invalid JSON still blocks.
- **Anything else (including 1):** non-blocking. A *valid* JSON object on stdout still takes full effect for standard-decision events. Otherwise the action proceeds with a "hook error" notice.
- **Launch failures** (missing or non-executable script, exit 127) are in the non-blocking bucket too, so **a typo leaves the gate silently disabled**.
- **Timeouts.** A timed-out command/http/mcp_tool hook is cancelled and yields no decision. On PreToolUse that means the tool call **proceeds**. Exception: on PreModelSwitch, a timeout blocks. (SDK callback hooks that time out *do* block.)
- **Output size.** `additionalContext`, `systemMessage`, `initialUserMessage` and plain stdout are each capped at 10,000 chars. Longer output is saved to a file and replaced by a path plus a 2,000-char preview. This cap cannot be configured.

**Universal JSON fields:**

| Field | Default | Meaning |
|---|---|---|
| `continue` | `true` | `false` stops Claude entirely; takes precedence over decisions. |
| `stopReason` | — | Shown to the user when `continue:false`. |
| `suppressOutput` | `false` | **Accepted but has no effect** (per current docs). |
| `systemMessage` | — | Warning shown to the user. Some events discard it. |
| `terminalSequence` | — | Allow-listed OSC 0/1/2/9/99/777 or BEL, for notifications. |

**Decision fields per event:**
- **Top-level `decision: "block"` + `reason`:** UserPromptSubmit, UserPromptExpansion, PostToolUse, PostToolUseFailure, PostToolBatch, Stop, SubagentStop, ConfigChange, PreCompact. TaskCreated also accepts it.
- **PreToolUse** uses `hookSpecificOutput`:
  - `hookEventName`
  - `permissionDecision`: `allow` | `deny` | `ask` | `defer`
  - `permissionDecisionReason`: shown to Claude on deny, to the user on allow/ask
  - `updatedInput`: replaces the whole input
  - `additionalContext`
  - Precedence across hooks: deny > defer > ask > allow.
  - `allow` does **not** override deny/ask rules. `deny` works even under `bypassPermissions` [V: [hooks-guide#hooks-and-permission-modes](https://code.claude.com/docs/en/hooks-guide#hooks-and-permission-modes)].
  - `defer` applies only in `-p` with a single tool call.
  - Deprecated top-level `approve`/`block` map to allow/deny.
- **PermissionRequest:** `hookSpecificOutput.decision` = `{behavior: allow|deny, updatedInput, updatedPermissions[], message, interrupt}`. `updatedPermissions` entries have types `addRules`, `replaceRules`, `removeRules`, `setMode`, `addDirectories`, `removeDirectories`, with destination `session`, `localSettings`, `projectSettings` or `userSettings`.
- **PostToolUse:** adds `additionalContext`, `updatedToolOutput` (must match the tool's output shape), `updatedMCPToolOutput` and `classifierContext` (v2.1.236+, auto-mode classifier only).
- **Stop/SubagentStop:** `decision:"block"` requires a `reason`. `hookSpecificOutput.additionalContext` also continues the turn, but as non-error feedback.
- **SessionStart:** `additionalContext`, `initialUserMessage` (`-p`), `sessionTitle`, `watchPaths`, `reloadSkills`.
- **SubagentStart:** `additionalContext` is injected into the subagent. It cannot block.
- **PermissionDenied:** `retry: true`.
- **Elicitation/ElicitationResult:** `action` + `content`.
- **MessageDisplay:** `displayContent`.
- **WorktreeCreate:** a command hook prints the path; an HTTP hook returns `worktreePath`.
- **Rewrite scope.** `UserPromptSubmit` cannot rewrite the prompt; it can only add context.

**Where `additionalContext` lands.** It is wrapped as a system reminder:
- SessionStart/SubagentStart: at the conversation start;
- prompt events: alongside the prompt;
- tool events: next to the tool result;
- Stop: at the end of the turn, and the conversation continues.
- Write it as factual statements. Text phrased as imperative system commands can trip Claude's prompt-injection defences [V: [hooks#add-context-for-claude](https://code.claude.com/docs/en/hooks#add-context-for-claude)].

### 18. Hooks — Stop/SubagentStop, PreCompact, SessionStart specifics

- **When Stop fires.** Whenever the main agent finishes a response, not only when the task is complete. It does not fire on user interrupt. API errors fire `StopFailure`, whose output is ignored apart from `terminalSequence` [V: [hooks#stop](https://code.claude.com/docs/en/hooks#stop)].
- **Block cap:**
  - After **8 consecutive blocks**, Claude Code overrides the hook and ends the turn with a warning. The same applies to SubagentStop.
  - `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP` sets the cap; `0` disables it.
  - It was introduced in v2.1.143; before that, stop hooks could loop forever [V: [hooks#stop-input](https://code.claude.com/docs/en/hooks#stop-input), [hooks-guide#stop-hook-hits-the-block-cap](https://code.claude.com/docs/en/hooks-guide#stop-hook-hits-the-block-cap), [env-vars](https://code.claude.com/docs/en/env-vars), [changelog 2.1.143](https://code.claude.com/docs/en/changelog)].
  - The cap counts blocks "without progress" per the guide. Exactly what counts as progress is not specified [U].
  - `additionalContext` continuations count against the same cap [V].
- **SubagentStop "rejecting" output:**
  - `decision:"block"` + `reason` (or exit 2) **keeps the subagent running**, and the reason becomes its next instruction.
  - There is no field that rejects the result while stopping.
  - To inject context into the parent after a subagent returns, use a `PostToolUse` hook on `Agent` [V: [hooks#subagentstop](https://code.claude.com/docs/en/hooks#subagentstop)].
  - Whether `updatedToolOutput` on `Agent` can replace the subagent's report is not documented [U].
  - In auto mode (v2.1.271+), reports may arrive via the `SubagentHandback` tool; read `tool_input.message` on a PreToolUse/PostToolUse hook matched to `SubagentHandback` [V].
- **PreCompact:**
  - Matcher `manual` or `auto`.
  - Exit 2 or `decision:"block"` blocks compaction. If the compaction was recovering from a context-limit error, the request then fails.
  - `systemMessage` and `continue` are discarded.
  - PostCompact carries `compact_summary`.
  - To re-inject state, use a SessionStart hook with matcher `compact` [V: [hooks#precompact](https://code.claude.com/docs/en/hooks#precompact), [context-window](https://code.claude.com/docs/en/context-window#what-survives-compaction)].
- **SessionStart:**
  - Only `command` and `mcp_tool` handlers.
  - Runs in the background at interactive launch, but Claude's first response waits for it.
  - Plain stdout or `additionalContext` becomes context.
  - `CLAUDE_ENV_FILE` is available (also for Setup, CwdChanged and FileChanged) for persisting `export` lines into later Bash commands.
  - `reloadSkills: true` rescans skill directories after the hook [V: [hooks#sessionstart](https://code.claude.com/docs/en/hooks#sessionstart)].

### 19. Hooks — plugin hooks, frontmatter hooks, env vars, security

- **Plugin `hooks/hooks.json`:**
  - The same schema, plus an optional top-level `description` and `$schema`.
  - Plugin hooks merge with user and project hooks.
  - `${CLAUDE_PLUGIN_ROOT}` and `${CLAUDE_PLUGIN_DATA}` resolve anywhere in hook commands, and are also exported as env vars along with `CLAUDE_PROJECT_DIR` [V: [plugins-reference#hooks](https://code.claude.com/docs/en/plugins-reference#hooks), [hooks#exec-form-and-shell-form](https://code.claude.com/docs/en/hooks#exec-form-and-shell-form)].
  - `${user_config.*}` works only in exec form. In shell form, read `$CLAUDE_PLUGIN_OPTION_<KEY>` instead (v2.1.207 change) [V].
- **`CLAUDE_PLUGIN_DATA`:**
  - Resolves to `~/.claude/plugins/data/{id}/`, with non-`[A-Za-z0-9_-]` characters replaced by `-`.
  - It survives updates and is deleted on the last uninstall unless `--keep-data` is passed [V: [plugins-reference#persistent-data-directory](https://code.claude.com/docs/en/plugins-reference#persistent-data-directory)].
- **Plugin install location:**
  - Plugins from a **local-directory marketplace load in place**. `CLAUDE_PLUGIN_ROOT` then points at the source directory, and edits apply on `/reload-plugins` or at the next session.
  - Copied plugins get a new ROOT on each update [V: [plugins-reference#plugin-caching-and-file-resolution](https://code.claude.com/docs/en/plugins-reference#plugin-caching-and-file-resolution)].
- **`bin/`.** A plugin's `bin/` directory is added to the Bash tool's `PATH` [V: [plugins-reference#file-locations-reference](https://code.claude.com/docs/en/plugins-reference#file-locations-reference)].
- **Env vars in the hook process** [V: [hooks](https://code.claude.com/docs/en/hooks), [env-vars](https://code.claude.com/docs/en/env-vars)]:
  - the inherited parent environment, minus `OTEL_*`, and minus credentials when `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1`;
  - `CLAUDE_PROJECT_DIR` (stays at the session root even inside worktrees; read `cwd` for the live directory);
  - `CLAUDE_PLUGIN_ROOT` and `CLAUDE_PLUGIN_DATA`;
  - `CLAUDE_ENV_FILE` (4 events only);
  - `CLAUDE_EFFORT`;
  - `CLAUDE_CODE_REMOTE` (`"true"` on web);
  - `CLAUDE_CODE_BRIDGE_SESSION_ID`;
  - `CLAUDE_PLUGIN_OPTION_<KEY>`.
- **Hooks in frontmatter:**
  - Skill hooks persist for the rest of the session once the skill is invoked.
  - Agent hooks last only while the agent runs, and `Stop` becomes `SubagentStop`.
  - When a hook returns `ask`, the prompt is labelled `[settings]`, `[plugin:<name>]` or `[skill]` [V: [hooks#hooks-in-skills-and-agents](https://code.claude.com/docs/en/hooks#hooks-in-skills-and-agents)].
  - Plugin *agents* ignore frontmatter hooks. No restriction is documented for plugin *skills'* frontmatter hooks [V absence; behaviour U].
- **Security and trust** [V: [hooks#security-considerations](https://code.claude.com/docs/en/hooks#security-considerations), [permissions#what-runs-before-you-trust-a-folder](https://code.claude.com/docs/en/permissions#what-runs-before-you-trust-a-folder)]:
  - Command hooks run with full user permissions.
  - Interactive sessions hold back all settings-file hooks, even the user's own, until the workspace trust dialog is accepted.
  - `-p` and SDK runs treat the folder as trusted.
  - Project subagent frontmatter hooks and inline `mcpServers` need exact-folder trust. A parent folder's trust or a `-p` run does not count.
  - Safe `-p` in a repo you didn't write: pass `--setting-sources user`, use `--bare`, or pass `--settings '{"disableAllHooks": true}'`.
  - `allowManagedHooksOnly` (managed settings) blocks user, project, local and plugin hooks, except plugins force-enabled by policy.
  - Best practice: quote variables, reject `..`, use absolute paths, skip `.env` and keys.
  - PreToolUse does not fire for `@`-referenced files; use `Read` deny rules for those.
  - `PostToolUse` on `Edit|Write` misses edits made through Bash. Use `FileChanged` or a git diff in a Stop hook [V: [hooks#pretooluse](https://code.claude.com/docs/en/hooks#pretooluse), [hooks#posttooluse](https://code.claude.com/docs/en/hooks#posttooluse)].
- **Debugging.** Use `claude --debug-file <path>`, or `--debug` (log at `~/.claude/debug/<session-id>.txt`). `CLAUDE_CODE_DEBUG_LOG_LEVEL=verbose` adds more detail. Misplaced JSON keys show up as `Hook JSON output had unrecognized keys`, and a shell profile that echoes text breaks JSON parsing [V: [hooks#debug-hooks](https://code.claude.com/docs/en/hooks#debug-hooks), [hooks-guide#hook-json-has-no-effect](https://code.claude.com/docs/en/hooks-guide#hook-json-has-no-effect)].

### 20. Agent Skills authoring best practices (platform.claude.com)

[V: [best-practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)]

- **Concise is key.** At startup only metadata is preloaded, and the body loads when relevant. Assume Claude already knows general concepts, and justify every paragraph's token cost.
- **Degrees of freedom.** Match specificity to how fragile the task is:
  - high freedom: prose heuristics;
  - medium: pseudocode or parameterised scripts;
  - low: an exact script with "do not modify" instructions, for fragile or strictly sequential operations.
  - The page's analogy: a narrow bridge with cliffs needs guardrails; an open field needs only direction.
- **Test across models** (Haiku, Sonnet, Opus). Haiku may need more detail; Opus should not be over-explained.
- **Naming.** Gerund form is *recommended* (`processing-pdfs`); noun phrases and action forms are acceptable. Avoid vague names (`helper`, `utils`), overly generic ones, reserved words and inconsistent patterns.
- **Descriptions:**
  - Always third person.
  - State both what the skill does and when to use it, with key trigger terms.
  - One description per skill.
  - Claude may choose among 100+ skills.
  - The page contains **no explicit "when not to use" guidance** (see Discrepancies).
- **Progressive disclosure:**
  - Keep the SKILL.md body under 500 lines.
  - Split files by domain.
  - **Keep references one level deep from SKILL.md.** Nested references get partial reads (e.g. `head -100`).
  - Reference files over 100 lines get a table of contents.
- **Workflows.** Numbered steps and copyable checklists, plus **feedback loops**: run the validator, fix, repeat. For batch or destructive work, use plan → validate plan (script) → execute → verify, with verbose validator errors.
- **Content:**
  - No time-sensitive statements; use an "Old patterns" collapsible section instead.
  - Consistent terminology.
  - Template and examples patterns.
  - A conditional-workflow pattern.
- **Scripts vs prose:**
  - "Solve, don't defer": handle errors in scripts.
  - Justify constants ("no voodoo constants").
  - Prefer pre-made utility scripts, which are reliable, cheap and consistent.
  - Say explicitly whether a script should be *executed* or *read*.
  - List dependencies; don't assume they are installed.
  - Forward-slash paths.
  - Descriptive file names.
- **Evaluation-driven development:**
  1. Find gaps without the skill.
  2. Build **3 evaluations**.
  3. Measure the baseline.
  4. Write the minimum instructions.
  5. Iterate.
  - The page's example eval JSON has `skills`, `query`, `files` and `expected_behavior[]`, and it says there is no built-in runner.
  - Iterate with "Claude A" (author) and "Claude B" (tester), and observe how skills are navigated.
- **Anti-patterns:** Windows paths, offering too many options (give a default plus an escape hatch), deep nesting, magic numbers, assuming tools are installed.
- **Checklist.** Core quality, code/scripts, and testing: at least 3 evals, tested on Haiku/Sonnet/Opus, real scenarios.
- **Claude Code's own eval tooling** [V: [skills#evaluate-and-iterate-on-a-skill](https://code.claude.com/docs/en/skills#evaluate-and-iterate-on-a-skill)]:
  - `claude plugin eval` gates CI.
  - The `skill-creator` plugin uses `evals/evals.json`, `grading.json` and `benchmark.json`.
  - The two formats are not interchangeable.

### 21. Copy-pasteable examples (written for Forge; every field tagged)

**(a) Path-scoped rule** — `.claude/rules/mech/cad-build123d.md`

```markdown
---
paths:                         # [V] only field read; YAML list or comma string
  - "cad/**/*.py"              # [V] glob; ** recursive
  - "mech/**/*.{py,toml}"      # [V] brace expansion (1,000-pattern budget)
---

# build123d CAD conventions
- Every part module exposes `build() -> Part` and `PARAMS: dict` (units: mm).
- Never edit exported STEP/STL under `out/`; regenerate with `uv run forge-cad export`.
- Mass/volume/bbox claims must cite `out/<part>/metrics.json`, not a screenshot.
```

Loads when Claude reads a matching file. It is guidance only; enforcement belongs in hooks [V].

**(b) SKILL.md with `context: fork`** — `skills/checking-drc/SKILL.md` (plugin skill, so it is invoked as `/forge:checking-drc`)

```yaml
---
name: checking-drc                         # [V] plugin skill: sets last command segment
description: Runs KiCad DRC/ERC on the current board and reports violations with evidence paths. Use when a PCB layout or schematic changed, before fab release, or when asked to verify a board.   # [V] ≤1,536 listing cap (≤1,024 spec)
when_to_use: "verify board", "run DRC", "is the PCB clean"   # [V]
argument-hint: "[board.kicad_pcb]"         # [V]
context: fork                              # [V] fresh subagent, no chat history
agent: forge-checker                       # [V] custom agent type (plugin-scoped naming here is [U])
background: false                          # [V] caller waits for verdict (v2.1.218+)
effort: high                               # [V] low|medium|high|xhigh|max
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/bin/forge-drc *) Read   # [V] turn-scoped pre-approval; placeholder substituted
disable-model-invocation: false            # [V] default
---

Run `${CLAUDE_PLUGIN_ROOT}/bin/forge-drc $ARGUMENTS --json out/evidence/drc.json`.   <!-- [V] substitutions -->
Report PASS only if the JSON has zero errors. Quote counts from the file; never infer.
```

**(c) Read-only checker agent with `memory: project`** — `.claude/agents/forge-checker.md` (project scope; see the caveats below)

```yaml
---
name: forge-checker                        # [V] required; no ":"
description: Independent read-only verifier. Use after any design/code change to re-run checks and judge evidence; never edits sources.   # [V] required
tools: Read, Grep, Glob, Bash              # [V] allowlist; no Agent => cannot spawn; no Edit/Write listed
disallowedTools: Agent                     # [V] belt-and-braces
model: opus                                # [V] alias (sonnet|opus|haiku|fable|full id|inherit)
permissionMode: dontAsk                    # [V] auto-deny anything not pre-allowed; honoured only for project/user agents, and only if parent is default|dontAsk|plan
memory: project                            # [V] .claude/agent-memory/forge-checker/ — NOTE auto-enables Read/Write/Edit
maxTurns: 40                               # [V]
effort: high                               # [V]
omitClaudeMd: true                         # [V] needs v2.1.271+ (local 2.1.270 lacks it)
color: cyan                                # [V]
hooks:                                     # [V] ignored if this file ships in a plugin
  PreToolUse:
    - matcher: "Write|Edit"
      hooks:
        - type: command
          command: "${CLAUDE_PROJECT_DIR}/.claude/hooks/only-memory-writes.sh"   # [V] placeholder; script is Forge's to write
---
You verify; you never fix. Re-run the checks named in the task, cite evidence file paths, and return PASS/FAIL per check.
```

Caveats:
- `memory:` grants Write and Edit, and the docs do not say whether they are limited to the memory directory [U]. The `PreToolUse` hook above is there to deny writes outside `.claude/agent-memory/forge-checker/`.
- `Bash` can mutate files, so pair it with a PreToolUse `Bash` allowlist hook.
- For a **plugin-shipped** checker, `hooks`, `permissionMode` and `mcpServers` are ignored. Put the equivalent hook in the plugin's `hooks/hooks.json`, keyed on `agent_type` (the anchored matcher `^forge:checker$` applies to SubagentStart/Stop; for tool events, test `agent_type` inside the script) [V].

**(d) Plugin `hooks/hooks.json` with PreToolUse + PostToolUse + Stop**

```json
{
  "description": "Forge gates: protected paths, post-edit checks, verification-before-stop",
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/guard-paths.py",
            "args": [],
            "timeout": 10,
            "statusMessage": "Forge: checking protected paths"
          }
        ]
      },
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "if": "Bash(git push *)",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/require-signoff.py",
            "args": [],
            "timeout": 10
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          { "type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/lint-changed.py", "args": [], "timeout": 120 }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          { "type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/verify-before-stop.py", "args": [], "timeout": 300 }
        ]
      }
    ]
  }
}
```

Field provenance:
- top-level `description` [V: hooks#reference-scripts-by-path]. An optional top-level `$schema` key is also accepted and ignored [V: plugins-reference#hooks]. It is omitted here because no schema URL for *hooks.json* was found; the documented schemastore URL is for plugin.json manifests [U].
- `matcher` exact-list `Write|Edit` [V]; `type`, `command`, `args` (exec form, recommended with placeholders) [V]; `timeout` in seconds [V]; `statusMessage` [V]; `if` with permission-rule syntax, tool events only [V].
- Stop has no matcher support [V].

**(e) Hook script JSON output that blocks with a reason**

PreToolUse deny, printed to stdout with exit 0:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "fab/ is release-controlled. Use /forge:release-fab, which needs a human sign-off file."
  }
}
```

- `hookEventName`, `permissionDecision` and `permissionDecisionReason` [V: [hooks#pretooluse-decision-control](https://code.claude.com/docs/en/hooks#pretooluse-decision-control)].
- On `deny`, the reason is shown to Claude [V].

Stop block, from `verify-before-stop.py`, exit 0:

```json
{ "decision": "block", "reason": "Evidence missing: out/evidence/drc.json not newer than board file. Run /forge:checking-drc, then stop." }
```

- `decision: "block"` needs a `reason` [V: [hooks#stop-decision-control](https://code.claude.com/docs/en/hooks#stop-decision-control)].
- The script must first read stdin and **exit 0 with no output when `stop_hook_active` is true** after N retries, or else record "UNVERIFIED" in a ledger. Otherwise the 8-block cap ends the turn anyway [V: cap].

## Implications for Forge

1. **Pin a minimum Claude Code version and check it.**
   - Recommended floor: **≥2.1.281** (npm `latest`). That covers `omitClaudeMd` (2.1.271), `mcp_server` provenance in hook input (2.1.274), native AGENTS.md without the Bedrock/telemetry caveat (2.1.281), and worktree skill read-through (2.1.277).
   - The local 2.1.270 has to be upgraded by the human. Until then, design must degrade gracefully: import AGENTS.md via `@AGENTS.md`, and don't depend on `omitClaudeMd`.
   - A `SessionStart` hook should print a warning via `systemMessage` if `claude --version` is below the floor.
2. **Keep the root context small.** Root `CLAUDE.md` stays at ≤100 lines (the docs' ceiling is 200). Put the cross-tool content in `AGENTS.md`, imported by `@AGENTS.md`. Use HTML comments for maintainer notes, since they are stripped. Add a CI check that fails over the line limit.
3. **Plugins cannot ship CLAUDE.md or rules, so Forge must deliver domain guidance differently:**
   - (a) Plugin skills with `paths:`, e.g. `paths: "**/*.ato"` for atopile.
   - (b) An `/forge:init` skill that scaffolds `.claude/rules/<domain>/*.md` into the project.
   - (c) SessionStart `additionalContext` for dynamic state.
   - Rules are *guidance*. Every "must" gets a hook or permission counterpart.
4. **Every gate hook must fail closed on its own errors,** because the platform fails open on exit 1, a missing script or bad JSON:
   - wrap gate logic so that any exception exits **2** (or prints a `deny` decision);
   - build JSON with an encoder;
   - use exec form (`args: []`) with `${CLAUDE_PLUGIN_ROOT}`;
   - keep `PreToolUse` gates fast, with an explicit `timeout` (a timeout means "proceed");
   - put slow checks at Stop/SubagentStop or in `asyncRewake`.
5. **Test the harness itself:**
   - CI pipes fixture stdin JSON into every hook and asserts exit code and stdout.
   - A SessionStart self-check verifies that every hook script exists and is executable, and warns via `systemMessage`.
   - `claude plugin validate --strict` runs on the plugin, `.claude/skills` and `.claude/agents`.
   - `claude plugin eval` runs with `tool_used: Skill` graders.
   - An `InstructionsLoaded` logging hook measures whether rules actually load.
6. **Verification is the product: stop only with evidence.**
   - The Stop and SubagentStop hooks (command type, not the experimental `agent` type) check for evidence files newer than the changed sources (from `git status --porcelain`, which also catches edits made through Bash).
   - They block with a precise `reason`, and honour `stop_hook_active` together with Forge's own retry counter.
   - When the 8-block cap forces a stop, the hook records `UNVERIFIED` in the evidence ledger. Downstream gates such as fab release refuse to proceed on it.
   - Do **not** set `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP=0`.
7. **Maker ≠ checker, enforced mechanically:**
   - Checkers are non-fork subagents with a fresh context, `tools` without `Edit`/`Write`/`Agent`, and `omitClaudeMd: true` once ≥2.1.271.
   - Checkers should not use `memory:` by default, because it grants Write and Edit. If a checker needs memory, pair it with a hook that denies writes outside `.claude/agent-memory/<name>/`.
   - Because plugin agents ignore `hooks`/`permissionMode`/`mcpServers`, Forge's plugin `hooks.json` enforces checker read-only-ness on tool events. The hook branches on `agent_type` (`forge:…`) in the stdin JSON, denies Write/Edit, and allowlists Bash commands.
   - Makers and checkers never share a context. The parent passes paths to evidence, not conclusions.
8. **Subagent orchestration settings:**
   - Set `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=2` in project `env` so reviewers can dispatch per-finding verifiers but no deeper.
   - Leave concurrency at the default of 20.
   - Anchor plugin agent names in matchers (`^forge:review:mech$`).
   - Use `permissions.deny: ["Agent(fork)"]` wherever a checker must never inherit maker context.
9. **Worktree isolation.** Maker agents with `isolation: worktree` need project `worktree.baseRef: "head"`; otherwise they branch from `main` and miss in-progress work. Include `.claude` in any `worktree.sparsePaths`.
10. **Skills conventions** (lint in CI):
    - `name` in gerund kebab-case, ≤64 chars, equal to the directory name, with no "claude" or "anthropic".
    - A third-person `description`, with what + when + trigger terms first, ≤1,024 chars; any `when_to_use` still fits the 1,536 listing cap.
    - Body ≤500 lines.
    - Reference files one level deep, with a table of contents over 100 lines.
    - Deterministic work goes in bundled scripts invoked through `${CLAUDE_SKILL_DIR}`/`${CLAUDE_PLUGIN_ROOT}`, with a matching narrow `allowed-tools` rule.
    - Put the most important instructions first, because only the first 5,000 tokens survive compaction.
11. **Humans sign safety, money and fabrication:**
    - Such skills use `disable-model-invocation: true`, so Claude cannot trigger them.
    - A `UserPromptExpansion` hook, matched on those command names, blocks the command unless a signed approval file exists. This covers the direct `/command` path, which PreToolUse doesn't see.
    - A `PreToolUse` deny covers the underlying tool calls (e.g. `Bash(git push *)`, writes under `fab/`).
12. **Supply-chain and least privilege:**
    - A skill's `allowed-tools` is **not gated by trust**, so CI forbids bare `Bash` or wildcard grants in Forge skills.
    - Gate hooks read `mcp_server.source` (≥2.1.274) rather than the tool-name prefix.
    - Set `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1` for sessions that fetch untrusted content.
    - For CI `-p` runs over external repos, use `--setting-sources user` or `--bare`.
13. **Prefer settings and plugin hooks to agent-frontmatter hooks for anything that must run in CI.** Project-agent frontmatter hooks are skipped in `-p` unless the folder is explicitly trusted.
14. **Compaction resilience:**
    - A `PreCompact` hook writes a state checkpoint (open tasks, evidence status).
    - A `SessionStart` hook with matcher `compact` re-injects a ≤2,000-char summary as `additionalContext`, well under the 10,000-char cap.
    - Treat path rules and hook-added context as lost after compaction.
15. **Budget the listing:**
    - Keep Forge's skill count and descriptions lean; the listing is 1% of context.
    - Keep the combined agent descriptions far below 15,000 tokens.
    - Use `skillOverrides: "name-only"` for rarely used local skills. It doesn't apply to plugin skills; there, Forge controls verbosity at the source.
16. **Pin models by full ID** in agent and skill frontmatter where results must be reproducible (e.g. `claude-opus-5-5`), because aliases move between versions (`opus` means Opus 5 before 2.1.280 and Opus 5.5 from 2.1.280). Record the resolved model from PostToolUse `tool_response.resolvedModel` in the evidence.

## Not found / discrepancies

- **`claude agents --help` does not manage subagent definitions.** It manages *background sessions* [L]. The `/agents` creation wizard was removed in v2.1.198 [V].
- **AGENTS.md is not read natively on the local 2.1.270.** It needs v2.1.277+, and some session types need 2.1.281+ [V/L].
- **`omitClaudeMd` is documented as v2.1.271+.** The string exists in the 2.1.270 binary only in built-in agent code [L]. Treat it as unavailable locally.
- **`suppressOutput`** is still an accepted JSON field but is documented as **having no effect** [V].
- **Hook handler type** is `mcp_tool`, not `mcp` [V].
- **`agent`-type hooks** are marked **experimental** [V].
- **`once`** is honoured only in *skill* frontmatter; it is ignored in settings and agent frontmatter [V].
- **`Agent(type,…)` in `tools`** restricts spawnable types **only for an agent running as the main thread via `--agent`**. In a subagent definition the parenthesised list is ignored [V]. `Task` was renamed `Agent` in 2.1.63 [V].
- **Skill `name`** in personal and project skills is only a display label; the command comes from the directory name [V]. The 64/1,024-character limits come from the Agent Skills spec and platform docs. Claude Code's own enforcement for local skills is undocumented [U].
- **Platform best-practices page has no explicit "when not to use" guidance** for descriptions (searched; not found) [V]. Claude Code's docs only say to make descriptions more specific or set `disable-model-invocation` when a skill over-triggers [V].
- **MCP tool naming mismatch.** Platform best practices recommend `ServerName:tool_name` in skill text. Claude Code tool IDs are `mcp__<server>__<tool>` (plugin servers: `mcp__plugin_<plugin>_<server>__<tool>`) [V]. Forge should use Claude Code names.
- **Undocumented or unconfirmed behaviour** [U]:
  - whether subagent `memory:` Write/Edit is confined to the memory directory;
  - the memory directory name for plugin-scoped agents;
  - whether path-scoped rules trigger on Write of a new file (the docs say "reads");
  - whether a skill's `agent:` accepts plugin-scoped agent names;
  - whether the subagent `model` accepts `best`, `opusplan` or `[1m]`;
  - whether PostToolUse `updatedToolOutput` can replace an `Agent` result;
  - what counts as "progress" when the Stop block cap counts consecutive blocks.
- **Rule `paths` glob anchor** for nested `.claude/rules/` directories is not documented [U].
- **Plugin skill frontmatter `hooks`:** no restriction is documented, unlike plugin agents [V absence]. Actual behaviour not tested [U].
- **Correct `$schema` URL for `hooks/hooks.json`** not found. Docs show only that the key is accepted and ignored [U].
- **The skill-creator eval format (`evals/evals.json`) and the `claude plugin eval` format are explicitly not interchangeable** [V]. This matters for Forge's harness evals.

## Sources

| # | Title | URL | Type | Accessed |
|---|---|---|---|---|
| 1 | Claude Code docs index (llms.txt) | https://code.claude.com/docs/llms.txt | official | 2026-09-25 |
| 2 | How Claude remembers your project (memory, AGENTS.md, rules, auto memory) | https://code.claude.com/docs/en/memory | official | 2026-09-25 |
| 3 | Extend Claude with skills | https://code.claude.com/docs/en/skills | official | 2026-09-25 |
| 4 | Create custom subagents | https://code.claude.com/docs/en/sub-agents | official | 2026-09-25 |
| 5 | Hooks reference | https://code.claude.com/docs/en/hooks | official | 2026-09-25 |
| 6 | Automate actions with hooks (guide, troubleshooting) | https://code.claude.com/docs/en/hooks-guide | official | 2026-09-25 |
| 7 | Plugins reference | https://code.claude.com/docs/en/plugins-reference | official | 2026-09-25 |
| 8 | Explore the .claude directory | https://code.claude.com/docs/en/claude-directory | official | 2026-09-25 |
| 9 | Explore the context window (what survives compaction) | https://code.claude.com/docs/en/context-window | official | 2026-09-25 |
| 10 | Environment variables | https://code.claude.com/docs/en/env-vars | official | 2026-09-25 |
| 11 | All settings (settings-reference) | https://code.claude.com/docs/en/settings-reference | official | 2026-09-25 |
| 12 | Configure permissions (trust table, Agent()/Skill() rules) | https://code.claude.com/docs/en/permissions | official | 2026-09-25 |
| 13 | Run parallel sessions with worktrees | https://code.claude.com/docs/en/worktrees | official | 2026-09-25 |
| 14 | Model configuration (aliases) | https://code.claude.com/docs/en/model-config | official | 2026-09-25 |
| 15 | Claude Code changelog | https://code.claude.com/docs/en/changelog | official | 2026-09-25 |
| 16 | Extend Claude Code (features overview) | https://code.claude.com/docs/en/features-overview | official | 2026-09-25 |
| 17 | Set up Claude Code in a monorepo or large codebase | https://code.claude.com/docs/en/large-codebases | official | 2026-09-25 |
| 18 | Skill authoring best practices (platform) | https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices | official | 2026-09-25 |
| 19 | Agent Skills specification | https://agentskills.io/specification | primary (spec) | 2026-09-25 |
| 20 | npm registry: @anthropic-ai/claude-code (via `npm view`) | https://www.npmjs.com/package/@anthropic-ai/claude-code | primary | 2026-09-25 |
| 21 | Local CLI: `claude --version`, `claude --help`, `claude agents --help`, `claude plugin --help`, `claude plugin validate --help`, `strings` on `~/.local/share/claude/versions/2.1.270` | local | local verification | 2026-09-25 |
