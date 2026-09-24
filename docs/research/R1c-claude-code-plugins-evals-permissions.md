# R1c — Claude Code plugins, marketplaces, plugin evals, permissions, auto mode, sandboxing

- Date accessed: 2026-09-25 · Author: research agent (Phase 1) · Scope: how to package Forge as a plugin in a repo-local marketplace, validate it, measure it with `claude plugin eval`, and constrain it with permissions, auto mode and the Bash sandbox.

Tag legend: **[V]** read in an official/primary source (linked) · **[L]** verified locally by a command (given) · **[R]** secondary source only · **[U]** could not confirm.
Local environment for every [L]: Claude Code **2.1.270** (`claude --version`), macOS 15.3 arm64. Scratch experiments lived only under `…/scratchpad/r1c-scratch/`.

---

## Summary

1. **Version drift is real.** The live docs describe behaviour up to v2.1.280+, npm's latest is **2.1.282** (24 Sep 2026), and this machine runs **2.1.270**. Several documented features are missing locally: `install --accept-command`, and `userConfig.options`, which local `validate` rejects. Forge must declare a minimum Claude Code version. [L] (`npm view @anthropic-ai/claude-code version`; `claude plugin install --help`; validate test in §3) [V][pr]
2. **A plugin can't ship permission rules or sandbox policy.** A plugin's root `settings.json` honours only `agent` and `subagentStatusLine`, and ignores other keys without warning. Least privilege therefore has to come from committed project `.claude/settings.json`, from plugin **hooks**, or from managed settings. [V][pl]
3. **Plugin agents ignore `permissionMode`, `hooks` and `mcpServers`.** They do honour `tools`, `disallowedTools`, `model`, `effort`, `maxTurns`, `skills`, `memory`, `background`, `omitClaudeMd`, `isolation` (`worktree` only), `color` and `experimental`. Read-only checkers are built with `tools:` allowlists, not with permission modes. [V][pr] [V][sa]
4. **`claude plugin eval` exists (GA in v2.1.269).** A case is `prompt.md` (or `case.yaml`) plus `graders/*.md`. There are **6 grader types**: `regex`, `tool_used`, `tool_order`, `file_exists`, `llm`, `baseline`. There are **no custom-code or command graders** and **no pass@k / pass^k**: the score is a weighted fraction of graders passed, averaged over runs (default 3). A no-plugin baseline arm reports Δ. [V][ev] [L] (`claude plugin eval --help`)
5. **Eval CI contract.** Exit codes are 0 (all cases ≥ `--threshold`, default 1.0), 1 (failure, load error, untrusted dir or bad option), 2 (partial: cost ceiling hit or auth rejected), 130 (interrupted) and 143 (terminated). Pin `--model` and `--judge-model`, and pass `--trust-plugin`, `--no-publish`, `--max-cost-usd` and `--json`. [V][ev] [L] (untrusted dir → exit 1)
6. **`claude plugin validate` catches manifest schema and frontmatter errors, but misses real load failures.** Locally it passed a plugin that then failed to load its hooks (duplicate `hooks/hooks.json` declaration) and had an unsatisfied dependency. It also passed a plugin agent carrying ignored `permissionMode`/`hooks`. `claude --plugin-dir <p> plugin list --json` did report the load failures. [L]
7. **Rule precedence.** Rules are evaluated deny → ask → allow, and the first match wins. Settings precedence is managed > CLI args > local > project > user, and list keys *merge* across scopes. Content-scoped **ask** rules still prompt in auto mode and even in `bypassPermissions`. That makes them the mechanism for "humans sign". [V][perm] [V][set] [V][pm]
8. **Auto mode is the built-in default on Pro/Max/Team** (not for `claude -p`, SDK, Enterprise or API-key accounts). A classifier (Sonnet 5 by default) reviews actions. Neither `auto` nor `bypassPermissions` takes effect as `defaultMode` from project or local settings, and the classifier ignores `autoMode` in project settings. Anthropic's own write-up reports a ~17% false-negative rate on real over-eager actions, so auto mode is not a safety boundary. [V][pm] [V][amc] [R][blog]
9. **The Bash sandbox (macOS Seatbelt, Linux/WSL2 bubblewrap+socat) covers only Bash, PowerShell and Monitor commands and their children.** Read/Edit/WebFetch, **MCP servers and hooks run unsandboxed on the host**. By default it can read the whole disk (including `~/.ssh`, `~/.aws`) and has no domains pre-allowed. `failIfUnavailable` and `allowUnsandboxedCommands:false` make it a hard gate. [V][sb] [V][se]
10. **In a git worktree, a repo-local marketplace path resolves to the main checkout**, not the worktree. This matters for Forge's worktree workflow; use `--plugin-dir` when working in a worktree. [V][mk]

---

## Findings

### 0. Environment and version drift

- The local CLI is 2.1.270. The npm registry lists 2.1.271–2.1.282 published between 14 and 24 Sep 2026, with 2.1.282 as `latest`. [L] (`claude --version`; `npm view @anthropic-ai/claude-code version time --json`)
- `claude plugin eval` requires v2.1.269 or later and shipped in the week-37 release (v2.1.263–v2.1.269). [V][ev] [V][w37]
- Documented features newer than the local build include:
  - `--accept-command <sha256>` (v2.1.271). Absent from local `claude plugin install --help`. [V][pr] [L]
  - `userConfig.*.options` (v2.1.271). Local validate reports `userConfig.units: Invalid input`. [V][pr] [L]
  - Per-command allowed domains in auto mode (v2.1.271). [V][sb]
  - Synced claude.ai plugins in terminal sessions (v2.1.273). [V][pr]
  - `/plugin install … --marketplace` (v2.1.275). [V][disc]
  - Server-side classifier review by default (v2.1.278). [V][pm]
  - `CLAUDE_CODE_PLUGIN_DIRS` (v2.1.280). [V][pl]

### 1. Plugin structure

#### 1.1 Manifest `.claude-plugin/plugin.json`: every field

The manifest is optional; without it, components are auto-discovered and the name is taken from the directory. If a manifest exists, **`name` is the only required field** (kebab-case, no spaces or control/bidi characters). [V][pr]

| Field | Type | Notes | Tag |
|---|---|---|---|
| `name` | string | Namespace for components, e.g. `plugin:agent`. A marketplace entry's name overrides it for `enabledPlugins` and `/plugin`. | [V][pr] |
| `$schema` | string | Ignored at load. | [V][pr] |
| `displayName` | string | UI label only. A marketplace entry value wins. | [V][pr] |
| `version` | string | Semver. Pins the cache key: users update only when it changes (except command sources and plugins loaded in place). `plugin.json` beats the marketplace entry. | [V][pr] |
| `description`, `author` {name, email, url}, `homepage`, `repository`, `license`, `keywords` (array) | metadata | A wrong type (e.g. `keywords` as a string) is a **load error**. | [V][pr] [L] |
| `metadata` | object | Free-form; not read by Claude Code. | [V][pr] |
| `defaultEnabled` | boolean | Default `true`. The user's `enabledPlugins` entry or a dependency requirement wins. | [V][pr] |
| `skills` | string\|array | **Adds to** the default `skills/` scan. `"."` or `"./"` means the plugin root. | [V][pr] |
| `commands` | string\|array | **Replaces** the default `commands/`. | [V][pr] |
| `agents` | string\|array | **Replaces** the default `agents/`. Listed files load without subfolder names. | [V][pr] |
| `workflows` | string\|array | **Replaces** the default `workflows/`. A missing path is a validate error. | [V][pr] [L] |
| `hooks` | string\|array\|object | Path(s) or inline config. See the duplicate-load pitfall in §3. | [V][pr] [L] |
| `mcpServers` | string\|array\|object | Path(s) or inline config. | [V][pr] |
| `outputStyles` | string\|array | **Replaces** the default `output-styles/`. | [V][pr] |
| `lspServers` | string\|array\|object | LSP configs. | [V][pr] |
| `experimental.themes`, `experimental.monitors` | string\|array | Experimental. Top-level `monitors` still loads, with a validate warning. | [V][pr] [L] |
| `experimental.evals` | string\|array | Eval directory below the plugin root. Default `evals/`; `--eval-dir` overrides. A **top-level `evals` key is unknown** (validate warning). | [V][pr] [L] |
| `userConfig` | object | Values the user is prompted for at enable time (§1.6). | [V][pr] |
| `channels` | array | Message channels bound to a plugin MCP server (`server` required). | [V][pr] |
| `dependencies` | array | Other plugins, optionally semver-constrained (§1.7). | [V][pr] |
| `settings` | object | Mentioned only in the plugins guide (plugin `settings.json` overrides it). Accepted by local validate without warning. **Absent from the reference "complete schema".** | [V][pl] [L] |

- Unrecognized top-level fields are ignored at load. Validate reports them as **warnings**, with near-miss suggestions (locally, `homepge` → "did you mean `homepage`"). `--strict` turns warnings into exit 1. [V][pr] [L]
- A non-object `experimental` or `metadata` is ignored with a warning. Most other wrong types fail the load. [V][pr]

#### 1.2 Default layout

- The component directories sit at the **plugin root**. Only `plugin.json` goes inside `.claude-plugin/`. [V][pr]
- The defaults are:
  - `skills/<name>/SKILL.md`
  - `commands/*.md` (legacy)
  - `agents/` (recursive; subfolders become part of the name, e.g. `forge:review:security`)
  - `workflows/`, `output-styles/`, `themes/`
  - `monitors/monitors.json`, `hooks/hooks.json`, `.mcp.json`, `.lsp.json`
  - `bin/` (added to the Bash tool's PATH)
  - `settings.json` [V][pr]
- A `CLAUDE.md` at the plugin root is **not loaded**. Validate warns about it; use a skill instead. [V][pr] [L]
- A root `SKILL.md` with no `skills/` directory and no `skills` field loads as a single-skill plugin. [V][pr]
- A top-level `bin/` is rejected for plugins distributed via claude.ai organization settings. [V][mk]

#### 1.3 Path rules

- All paths are relative to the plugin root and start with `./`. `skills` also accepts `"."`. [V][pr]
- Paths that resolve outside the root (`../x`, or symlinks out of the marketplace) are rejected with `path escapes plugin directory`. Local validate reports `Path contains ".."` as an error. [V][pr] [L]
- Backslashes in paths are rejected on macOS and Linux. [V][pr]
- Copied (cached) plugins don't get files from outside their directory. Symlinks within the same marketplace are dereferenced at copy time; symlinks outside it are skipped. [V][pr]
- When a manifest key and the default folder both exist, the folder is ignored and a note is shown. Locally, `claude plugin list --json` noted that the default `agents/` folder was ignored because the manifest sets `"agents"`. [V][pr] [L]

#### 1.4 `${CLAUDE_PLUGIN_ROOT}`, `${CLAUDE_PLUGIN_DATA}`, `${CLAUDE_PROJECT_DIR}`

- **ROOT** is the absolute install directory. For copied plugins it changes on every update, so treat it as ephemeral and never write state there. For in-place local-directory marketplace plugins it points at the source directory. [V][pr]
- **DATA** is `~/.claude/plugins/data/{id}/`. The id is sanitized to `[a-zA-Z0-9_-]`, e.g. `formatter-my-marketplace`. It is created on first reference and survives updates. It is deleted on uninstall from the last scope unless you pass `--keep-data`. [V][pr]
- Where they resolve:
  - All three are exported to hook processes and MCP/LSP subprocesses. They are **not** set for commands Claude runs via Bash. [V][pr]
  - They are substituted inline in skill/agent content and in hook/monitor commands.
  - For MCP stdio servers they are substituted in `command`, `args` and `env`; for http/sse/ws in `url`, `headers` and `headersHelper`; for LSP in `command`, `args`, `env` and `workspaceFolder`. [V][pr]
- Quoting: prefer exec-form hooks (`args`). In shell form, quote the variable: `"\"${CLAUDE_PLUGIN_ROOT}\"/scripts/x.sh"`. [V][pr]
- The recommended dependency pattern is a `SessionStart` hook that diffs the bundled manifest against the copy in `${CLAUDE_PLUGIN_DATA}` and reinstalls when they differ. [V][pr]

#### 1.5 Fields plugin-shipped agents may not use

- **Ignored for security:** `hooks`, `mcpServers`, `permissionMode`. **Not supported:** `initialPrompt`. **The only valid `isolation` value** is `"worktree"`. [V][pr] [V][sa]
- Unlike project and user agents, a plugin agent with no `name`, or with unparseable frontmatter, still loads under its filename. [V][pr]
- Agent names can't contain `:` (it is reserved for plugin scoping). [V][sa]
- In auto mode, `permissionMode` in any subagent's frontmatter is ignored anyway. The classifier also vets the spawn, each action, and the final report. [V][pm]

#### 1.6 `userConfig`

- Each field takes:
  - `type`: one of `string`, `number`, `boolean`, `directory`, `file`
  - `title` and `description` (both required)
  - optional `sensitive`, `required`, `default`, `options` (v2.1.271+), `multiple`, `min`/`max`

  [V][pr]
- Where values are available:
  - Every value can be substituted as `${user_config.KEY}` in MCP/LSP configs and hook commands.
  - Non-sensitive values can also be substituted in skill and agent content.
  - Every value is exported to hooks as `CLAUDE_PLUGIN_OPTION_<KEY>`. [V][pr]
- Shell-form hooks, monitor commands and MCP `headersHelper` **reject** `${user_config.*}`. [V][pr]
- Storage:
  - Non-sensitive values go in user `pluginConfigs[<id>].options`.
  - Sensitive values go in the macOS Keychain (about a 2 KB total limit).
  - Project and local `pluginConfigs` are ignored. [V][pr] [V][sr]
- The non-interactive equivalent is `claude plugin install … --config key=value` (repeatable). [L] (`claude plugin install --help`)

#### 1.7 Dependencies

- Entries are either a bare string (`"audit-logger"`) or `{ "name", "version": "<semver range>", "marketplace"? }`. [V][dep]
- By default, resolution stays within the same marketplace. A cross-marketplace dependency needs the **root** marketplace to list the target in `allowCrossMarketplaceDependenciesOn`. [V][dep]
- Version resolution:
  - Ranges resolve against git tags named `{plugin-name}--v{version}` on the hosting repo; `claude plugin tag [--push]` creates them.
  - Pre-releases are excluded unless the range opts in.
  - When several plugins constrain one dependency, the ranges are intersected.
  - npm, archive and command sources are only checked at load time. [V][dep]
- Error codes are `dependency-unsatisfied`, `range-conflict`, `dependency-version-unsatisfied` and `no-matching-tag`. Locally, an unsatisfied dependency **disabled the plugin** (`"enabled": false`, `errorDetails.type: dependency-unsatisfied`). [V][dep] [L]
- Local development: `claude --plugin-dir ./dep --plugin-dir ./plugin` satisfies the dependency with no version check. [V][dep]

#### 1.8 Caching, loading in place, Node dependencies

- Marketplace plugins are copied to `~/.claude/plugins/cache`. The exceptions are relative-path sources in a **local-directory** marketplace and link-mode command sources, which load **in place**. Edits to an in-place plugin apply at the next session start or on `/reload-plugins`, with no version bump needed. [V][pr]
- Old copied versions are swept about 14 days after they are orphaned. [V][pr]
- When a copied plugin contains `package.json` plus a lockfile, Claude Code runs:
  - `bun install --frozen-lockfile --ignore-scripts` for `bun.lock`/`bun.lockb`, or
  - `npm ci --ignore-scripts` for `npm-shrinkwrap.json`/`package-lock.json`

  The install has a 60 s timeout and can't be disabled. yarn/pnpm-only plugins are skipped. In-place plugins get **no** install. [V][pr]
- Python dependencies must be installed from a hook into `${CLAUDE_PLUGIN_DATA}`. [V][pr]

#### 1.9 Local CLI surface (help text, v2.1.270)

- `claude plugin` subcommands: `details`, `disable`, `enable`, `eval`, `init|new`, `install|i`, `list`, `marketplace`, `prune|autoremove`, `tag`, `uninstall|remove`, `update`, `validate`. [L] (`claude plugin --help`)

| Command | Flags (local) |
|---|---|
| `validate <path>` | `--json`, `--strict` |
| `install <plugin>` | `--config <k=v>`, `--json`, `-s/--scope user\|project\|local` (default user), `-y/--yes` |
| `uninstall <plugin>` | `--json`, `--keep-data`, `--prune`, `-s/--scope`, `-y` |
| `enable <plugin>` | `--json`, `-s/--scope` (auto-detected) |
| `disable [plugin]` | `-a/--all`, `--json`, `-s/--scope` |
| `update <plugin>` | `--json`, `-s/--scope user\|project\|local\|managed`, `-y` |
| `list` | `--available` (requires `--json`), `--json` |
| `details <name>` | none |
| `prune` | `--dry-run`, `-s/--scope`, `-y` |
| `tag [path]` | `--dry-run`, `-f/--force`, `-m/--message`, `--push`, `--remote` (default origin) |
| `init <name>` | `--author`, `--author-email`, `--description`, `-f/--force`, `--with skills\|agents\|hooks\|mcp\|lsp\|output-style\|channel` |
| `marketplace add <source>` | `--claudeai`, `--scope user\|project\|local`, `--sparse <paths...>` |
| `marketplace list` | `--json` |
| `marketplace remove\|rm <name>` | `--scope` (omit to remove from every scope) |
| `marketplace update [name]` | none |

[L] (`claude plugin <sub> --help` for each)

- `plugin init` scaffolds into `~/.claude/skills/<name>/`, which loads as `<name>@skills-dir`. That is the wrong location for Forge, whose plugin lives in the repo. [V][pr] [L]
- `--json` results print one object on the last stdout line, with `command`, `outcome` (`ok`/`failed`) and `message`. [V][pr]

### 2. Marketplaces

#### 2.1 `.claude-plugin/marketplace.json`

- **Required:**
  - `name` (kebab-case)
  - `owner`: an object with `name` required; `email` and `url` optional
  - `plugins[]` [V][mk]
- **Optional:**
  - `$schema`, `description`, `version`
  - `metadata.pluginRoot` (v2.1.239+; lets entries use bare names)
  - `allowCrossMarketplaceDependenciesOn`
  - `renames` (maps an old name to a new name or `null`; append-only) [V][mk]
- **Reserved names.** You can't use:
  - `claude-plugins-official`, `claude-code-plugins`, `anthropic-plugins`, `agent-skills` and 13 others
  - impersonations of official names
  - `npm`, `pip`, `uv`, `cargo`, `github`, `gh` (v2.1.275+)

  Claude Desktop additionally rejects `org`, `org-provisioned` and `unknown`. [V][mk]
- **Plugin entries.** `name` and `source` are required. Entries may also carry:
  - any manifest field
  - `category`, `tags`, `strict`, `relevance`, `defaultEnabled`
  - `headers` and `headersHelper` (for archive sources)

  [V][mk]
- **`strict`** (default `true`):
  - `true`: `plugin.json` is authoritative and the entry can add components on top.
  - `false`: the entry *is* the whole definition, and a `plugin.json` that also declares components is a load conflict. [V][mk]
- Set `version` in only one place. `plugin.json` silently wins over the entry; local validate warns when they differ. [V][mk] [L]

#### 2.2 Plugin source types

| `source` | Fields | Notes |
|---|---|---|
| relative string | `"./plugins/x"` | Resolved against the marketplace root (the directory that contains `.claude-plugin/`). No `..`. **Fails for URL-added marketplaces.** |
| `github` | `repo`, `ref?`, `sha?` (40 chars) | `sha` wins when both are set. |
| `url` | `url` (https or `git@`), `ref?`, `sha?` | Any git host. |
| `git-subdir` | `url`, `path`, `ref?`, `sha?` | Sparse clone. |
| `npm` | `package`, `version?`, `registry?` | Install scripts never run. |
| `archive` | `url`, `sha256?` | https zip, v2.1.224+. |
| `command` | `command`, `timeout?` (60–600), `mode? copy\|link` | Runs a local command. The user must accept the exact command. Never auto-installed as a dependency. |

[V][mk]

- Git clones never fetch **Git LFS** content, so files arrive as pointers. [V][mk]

#### 2.3 Adding a local marketplace and installing

- Interactive: `/plugin marketplace add ./my-marketplace`, then `/plugin install <plugin>@<marketplace>`. The install opens a scope picker. [V][mk] [V][disc]
- Non-interactive: `claude plugin marketplace add ./path [--scope project]`, then `claude plugin install forge@<mkt> --scope project` (default scope `user`). [V][mk] [V][pr] [L]
- The shell `install` command does **not** activate the plugin in a running session. It loads at the next start or on `/reload-plugins`. [V][disc]
- Refreshing:
  - A named install (`x@mkt`) refreshes git/URL marketplaces first. Local-directory marketplaces are not refreshed.
  - A bare-name `claude plugin install x` reads cached catalogs only. [V][disc]
- Project scope:
  - `extraKnownMarketplaces` plus `enabledPlugins` in `.claude/settings.json` apply only after the workspace trust dialog.
  - From v2.1.195, project-enabled plugins from **external** sources (GitHub, npm) are not installed for teammates until each user installs them. [V][disc] [V][sr]
- **Worktree caveat.** For a `directory` or `file` marketplace with a relative path, the path resolves against the repo's **main checkout** even from a git worktree. Marketplace state is stored once per user in `~/.claude/plugins/known_marketplaces.json`. [V][mk]
- Development without installing: `claude --plugin-dir ./plugins/forge` (session only; also accepts a `.zip`, or a folder of plugins on v2.1.265+). It overrides a same-name installed plugin except where managed settings force it. [V][pl] [L] (`claude --help`)

#### 2.4 Scopes and settings keys

- The `user`, `project` and `local` scopes map to `~/.claude/settings.json`, `.claude/settings.json` and `.claude/settings.local.json`. The `managed` scope is read-only. [V][pr]
- `enabledPlugins`:
  - Maps `"plugin@marketplace": bool`. Project beats user.
  - To opt out of a project-enabled plugin, set `false` in `settings.local.json`.
  - A managed `false` blocks installation at every scope. [V][sr]
- `extraKnownMarketplaces`:
  - Maps a name to `{ source: {...}, autoUpdate?: bool }`.
  - Source types: `github` (repo), `git` (url), `url` (url, headers?, headersHelper?), `file` (path), `directory` (path, "for development only"), `settings` (inline `name` plus `plugins`).
  - Alias: `additionalMarketplaces` (v2.1.232+).
  - When the same name is defined at several scopes, the highest-precedence entry replaces the others **whole** (fields don't merge). [V][sr]
- Managed-only keys:
  - `strictKnownMarketplaces` (alias `allowedMarketplaces`): an allowlist. `[]` is a total lockdown, including the official marketplace. It also supports `hostPattern`/`pathPattern` regex entries and `owner/*` wildcards.
  - `blockedMarketplaces`: also accepts `{ "source": "skills-dir" }`.
  - `disableCommandPluginSources`, `pluginSuggestionMarketplaces`, `pluginTrustMessage`.
  - `strictPluginOnlyCustomization`: `true` or a subset of `["skills","agents","hooks","mcp"]`.
  - `pluginConfigs` (user or managed). [V][sr] [V][mk]

#### 2.5 Versioning and auto-update

- The version comes from the first of these that is set: `plugin.json` `version`, the entry `version`, the git commit SHA, the archive SHA-256 (first 12 characters), or `unknown`. Command sources always use a content hash. [V][pr]
- Auto-update:
  - It runs after startup with a random delay of up to 10 minutes, and asks you to `/reload-plugins`.
  - It is on by default for `claude-plugins-official` and most official marketplaces, and **off by default for third-party and local marketplaces**.
  - It can be enabled per marketplace via `extraKnownMarketplaces.<name>.autoUpdate`.
  - `DISABLE_AUTOUPDATER` stops it; add `FORCE_AUTOUPDATE_PLUGINS=1` to keep plugin updates only. [V][disc] [V][sr]
- Release channels are two marketplaces pinned to different refs. Each channel must resolve to a different version. [V][mk]
- Containers and CI can pre-seed with `CLAUDE_CODE_PLUGIN_SEED_DIR` (read-only, no auto-update) and `CLAUDE_CODE_PLUGIN_CACHE_DIR`. The git timeout defaults to 120 s (`CLAUDE_CODE_PLUGIN_GIT_TIMEOUT_MS`). [V][mk]

#### 2.6 Official marketplace

- `claude-plugins-official` is added automatically on the first interactive start. The manual command is `/plugin marketplace add anthropics/claude-plugins-official`. Inclusion is curated by Anthropic; the in-app submission form goes to the community marketplace. [V][disc]
- Repo inspection:
  - `anthropics/claude-plugins-official` is public and was last pushed 2026-09-24.
  - Its `marketplace.json` lists 313 plugins: `url` source 163, `git-subdir` 98, relative 52. It uses `renames`.
  - None of its plugins ships a `claude plugin eval` suite (`evals/*/prompt.md`). `skill-creator` uses its own `evals/evals.json` format, which is not interchangeable. [L] (`gh api repos/anthropics/claude-plugins-official …`, `git/trees/main?recursive=1`) [V][sk]

### 3. `claude plugin validate`

- **Documented checks:**
  - For a plugin path: `plugin.json`, `hooks/hooks.json` JSON, and the frontmatter of the default `skills/`, `agents/` and `commands/`.
  - For a marketplace path: the schema, duplicate names, `..` traversal, and each local-path entry's `plugin.json`, with a version-mismatch warning.
  - It also runs against bare component directories, such as `.claude/agents` (v2.1.233+).
  - It does **not** follow symlinks, and does not check a root `SKILL.md` unless you name the parent `skills` directory. [V][mk] [V][pr]
- **Exit codes (documented):** 0 pass, 1 fail, 2 when the validation run itself fails (e.g. an unreadable path). `--json` exits with the same codes. `--strict` makes warnings fail. [V][pr]
- **JSON shape:** `{ success, strict, target, manifest: {file,type,errors[],warnings[],notes[]} | null, contents: [{file,type,errors[],warnings[],notes[]}] }`. Each issue is `{path, message, code}`. [V][pr] [L]

What validate did locally (`claude plugin validate <dir> [--strict] [--json]`):

| Input | Result | Tag |
|---|---|---|
| Clean manifest using most fields (no `workflows`, no `userConfig.options`) | exit 0, including with `--strict` | [L] |
| Typo `homepge` | warning with a "did you mean" suggestion | [L] |
| Top-level `evals` | warning: unknown field | [L] |
| `experimental.evals` | accepted | [L] |
| `keywords: "string"` | **error** `Invalid input`, exit 1 | [L] |
| `agents: "../outside/agent.md"` | **error**: path traversal | [L] |
| `workflows: "./workflows/"`, missing | **error**: path not found | [L] |
| `userConfig.*.options` (2.1.271 feature) | **error** `Invalid input` on 2.1.270 | [L] |
| Broken SKILL.md YAML | **error**. Frontmatter is silently dropped at runtime. It was only reported once manifest errors were fixed. | [L] |
| Root `CLAUDE.md` | warning: not loaded | [L] |
| Marketplace entry `version` ≠ `plugin.json` | warning: `plugin.json` wins | [L] |
| Nonexistent path | error "File not found", **exit 1** (not 2) | [L] |
| Unreadable manifest (chmod 000) | error EACCES, **exit 1** (docs imply 2) | [L] |
| Plugin agent with `permissionMode: bypassPermissions` plus `hooks:` | **passes** (no warning that they are ignored) | [L] |
| `dependencies` on nonexistent plugins | **passes** | [L] |
| `"hooks": "./hooks/hooks.json"` alongside the default file | **passes**. At load time the hooks fail with "Duplicate hooks file detected". | [L] |
| Hook command pointing at a missing script | passes | [L] |

- **A load-level check that catches more:** `claude --plugin-dir <plugin> plugin list --json`. Each plugin row carries `enabled`, `errors[]`, `errorDetails[{type,…}]` and `notes[]`. Locally it showed:
  - `hook-load-failed`
  - `dependency-unsatisfied`
  - the ignored-folder note

  [L] [V][pr]
- **`claude plugin details <name>`** prints the component inventory and a token-cost estimate (always-on vs on-invoke). It uses the `count_tokens` API and falls back to a character estimate. Locally a one-skill plugin showed about 19 always-on tokens. It reported **Agents (0)** whenever the manifest `agents` key was set, and Agents (1) with the default `agents/` folder. [V][pr] [L] (`claude --plugin-dir … plugin details toy`)

### 4. `claude plugin eval`: reference

#### 4.1 Full local flag list

`claude plugin eval [options] [command] [target]`. The target is a plugin directory, a single `prompt.md` or `case.yaml`, an installed `name` or `name@marketplace`, or `name@skills-dir`; it defaults to `.`. Put the target **before** `--tag`, `--allow-tools` and `--json`. [L] (`claude plugin eval --help`) [V][ev]

| Flag | Meaning / default |
|---|---|
| `--ablation <none\|with-without>` | Default `with-without` when a plugin resolves, else `none`. Under two arms, graders marked with-only (including `tool_used: Skill`) become non-scored "plugin-fired indicators". |
| `--allow-real-servers` | With `--mocks record`, also start real plugin MCP servers that have no mock. They run as you, outside the OS sandbox. |
| `--allow-tools <tools...>` | Operator grant for gated tools (Bash, Write, Edit, WebFetch, WebSearch, `mcp__*`). Accepts `Tool(pattern:*)` syntax. |
| `--case <glob>` | Filter by case name. |
| `-j, --concurrency <n>` | 1–8, default 1. Runs share one rate limit. |
| `--eval-dir <dir>` | Relative directory below the plugin. Absolute paths and `..` are rejected. Default: `experimental.evals`, else `evals/`. |
| `--json [path]` | Full result to stdout, or to a `.json` path. Suppresses progress and the table. |
| `--judge-model <model>` | Model for `llm`/`baseline` graders. Default **haiku**. |
| `--keep-temp` | Keep the sandbox and scaffold directories. |
| `--max-cost-usd <usd>` | List-price ceiling, checked before each run launches. Overrun is limited to runs already in flight. When hit, exit 2 with partial results, and paid graders are skipped on breaching runs. |
| `--mocks <record\|off>` | Default `record`. |
| `--model <model>` | Model for the agent under test. Order: case `model`, then `ANTHROPIC_MODEL`, then the default. |
| `--no-publish` / `--publish-report` | Keep the HTML report local, or force publishing to claude.ai. |
| `--no-scaffold` / `--scaffold` | Scaffold scripts are **off** by default. |
| `--output-dir <dir>` | Default `<evaldir>/results/<timestamp>/`. |
| `--report <path>` | HTML report path. |
| `--runs <n>` | Overrides the per-case `runs` (default 3). |
| `--tag <tag...>` | Keep cases with any matching tag. |
| `--threshold <0..1>` | Default **1.0**. Any case below it means exit 1. |
| `--trust-plugin` | Skip the first-run trust prompt (for CI). Does **not** imply `--scaffold`, `--allow-tools` or `--mocks off`. |
| `--verbose` | Per-message trace events in the debug log. |

`claude plugin eval init [name]` takes `--bare` (blank `prompt.md` plus `graders/criteria.md`), `--eval-dir <dir>` and `-i/--interactive`. [L] (`claude plugin eval init --help`)

#### 4.2 What `eval init` writes

- **In a terminal:** an interview that reads the plugin, proposes cases and graders, pilots them, and writes the files. [V][ev]
- **With `--bare <name>`:** writes `evals/<name>/prompt.md` and `evals/<name>/graders/criteria.md`. Locally, the template `prompt.md` had `max_turns: 10` and `allowed_tools: [Read, Glob, Grep, Skill]`; the grader had `type: llm` and `weight: 1`; both bodies were TODO placeholders. [L] (`claude plugin eval init --bare first-case </dev/null` in scratch)
- **From inside a Claude Code session** (even run through a non-interactive Bash tool), `eval init` without `--bare`, and also with `-i`, **printed interview instructions for the host session to follow** instead of failing or writing a template. That printed spec, read as data rather than acted on, adds the following. [L]
  - Floor invariants: ≥1 should-NOT-fire case, ≥1 outcome grader per case, `runs: 3` minimum, and ablation kept on.
  - Guidance: grade outcomes rather than trajectories; `tool_used: Skill` alone is never enough; the judge should be sonnet-tier and not the agent's own model.
  - The runner prints a warning when a case "cannot pass with the granted tools".
  - `aggregate-result.json` has `suite.plugins[]` entries with `problem` codes: `manifest_invalid`, `disabled_by_default` and `will_not_load` block; `identity_unverified` and `archive_not_probed` don't.
- `--eval-dir /abs` and `--eval-dir ../x` are rejected with exit 1. [L]

#### 4.3 Case layouts and fields

- A case is a directory containing `prompt.md`, `case.yaml`, or both. Cases can be grouped under a non-case directory. `evals/results/` should be gitignored. [V][ev]
- **Each run starts in an empty workspace.** `@path` mentions in the prompt are not expanded. [V][ev]
- **`prompt.md` frontmatter.** An unknown key is an **error**. [V][ev]

  | Key | Default | Notes |
  |---|---|---|
  | `schema_version` | `"1.1"` | |
  | `name` | directory name | |
  | `description` | | for humans |
  | `tags` | `[]` | |
  | `plugins` | nearest enclosing plugin | set to e.g. `["../.."]` if not detected |
  | `runs` | `3` | range 1–50 |
  | `expected_outcome` | | for humans |
  | `model` | | |
  | `max_turns` | `10` | up to 200 |
  | `timeout_seconds` | `300` | up to 3600 |
  | `allowed_tools` | `[]` | |
  | `append_system_prompt` | | |
  | `env` | `{}` | keys must match `EVAL_[A-Z0-9_]*` |

  The local loader's accepted-key list also included undocumented **`artifact_publish`** and **`growthbook_overrides`**. [L] (loader error message, §4.12)
- **`case.yaml`** requires `schema_version: "1.1"` and `name`.
  - `description`, `tags`, `plugins`, `runs` and `expected_outcome` go at the top level.
  - `model`, `max_turns`, `timeout_seconds`, `allowed_tools`, `append_system_prompt`, `env` and `prompt` go under `execution:`.
  - Keys that exist only here: `context.scaffold_script`, `context.history_file` (a `.jsonl` to resume), `context.add_dirs` (read-only fixture dirs), and `graders:` (a list of `{name, type, …, criteria}`).
  - When both files exist, `prompt.md` frontmatter overrides, its body is the prompt, and `graders/*.md` are appended. [V][ev]

#### 4.4 Graders

- **Common frontmatter:**
  - `type` (required)
  - `weight` (default 1; any positive number)
  - `arm`: `with-only` excludes the grader from the score in two-arm runs; `both` forces a `tool_used: Skill` grader to score in both arms

  The grader's name is its filename. [V][ev]
- **`target` / `focus` values:**
  - `last_message` (default)
  - `trace`: JSON lines; an `llm` judge sees the first 12 and last 12 messages; quotes are escaped as `\"`
  - `files`: a list of **created** paths only
  - `{ source: file, path: <p> }`: file contents; PNG/JPEG/GIF/WebP go to an `llm` judge as images; other binaries are refused
  - `mock_calls` [V][ev]

| Type | Options | Passes when |
|---|---|---|
| `regex` | `pattern`, `flags` (e.g. `i`; no inline `(?i)`), `match` (`contains` default, `not_contains`, `count:N`), `target` | The JavaScript regex is found, absent, or matched exactly N times. |
| `tool_used` | `tool`, `input_match` (regex over the JSON-encoded input), `min` (default 1), `max` | Matching call count is within [min, max]. "Never called" is `min: 0, max: 0`. |
| `tool_order` | `before`, `after` (a tool name or `{tool, input_match}`) | The first matching `before` call precedes the first matching `after` call. |
| `file_exists` | `path` (glob), `exists` | A file **created during the run** matches (or doesn't, with `exists: false`). |
| `llm` | `criteria` (the `.md` body), `focus` | The judge votes PASS in **≥2 of 3** votes. |
| `baseline` | `baseline_file` (`.jsonl` in the case directory), `criteria` | The judge rates the run at least as good as the reference transcript. |

[V][ev]

- `regex`, `tool_used`, `tool_order` and `file_exists` are free. `llm` and `baseline` cost roughly **3 judge calls per grader per run**. The docs state there are **no custom-code graders**. [V][ev]
- **Outcome vs path.** The docs recommend one grader on the result (final message or produced file) and one on how Claude got there (`tool_used`/`tool_order`). To check a build or test, have the prompt tell Claude to run it and **write the outcome to a file**, grade that file, and assert the command with `tool_used` and `input_match`. [V][ev]
- For long outputs, prefer `regex` over file contents; keep `llm` graders for short text. If a Skill grader passes but Δ<0, suspect the judge (try `--judge-model sonnet`). [V][ev]

#### 4.5 Repetitions, scoring, baseline

- Scoring:
  - Run score = the weighted fraction of graders passed.
  - Case score = the mean over with-arm runs.
  - A case passes if its score ≥ `--threshold`.
  - Cost is about cases × runs × 2 arms, plus judge calls. [V][ev]
- **pass@k / pass^k are not reported.** The closest things are the report's "Perfect runs" share (the fraction of with-plugin runs where every grader passed) and per-run results in the JSON. [V][ev]
- Baseline and Δ:
  - The baseline arm uses the same runs with no plugin; Δ = WITH − W/OUT.
  - `tool_used: Skill` and `arm: with-only` graders are excluded from both arms' scores. If a case has *only* such graders, they are scored normally.
  - `--ablation none` scores everything, so absolute scores differ between modes.
  - In the baseline arm, the plugin's agents fail with "Agent type … not found"; this is expected. [V][ev]

#### 4.6 Tools, scaffolds, mocks, isolation, trust

- **Default tools:**
  - Runs never prompt. Built-in tools that need a grant you didn't give are **removed**.
  - The grantable read-only set is `Read`, `Glob`, `Grep`, `NotebookRead`, `Skill`, `Agent`, `TodoWrite` and `Task*`, via `allowed_tools`.
  - Everything else needs `--allow-tools`, e.g. `Write Edit "Bash(npm test *)"`.
  - Neither a case's `allowed_tools` nor a skill's `allowed-tools` can widen operator grants. [V][ev]
- **Bash in evals:**
  - Any Bash grant runs under the **OS sandbox**: writes are confined to the workspace, home and Claude config are unreadable, and network is limited to `--allow-tools "WebFetch(domain:…)"`.
  - With no sandbox backend (e.g. native Windows), the run is refused and usually scores 0. Linux needs `bubblewrap` and `socat`. [V][ev]
- **Isolation per run:** a throwaway home, cwd and config, running `claude -p` with only the plugin loaded. The run excludes:
  - user/project settings, hooks, `CLAUDE.md`, personal MCP servers and other plugins
  - most of the environment (only an allowlist plus `EVAL_*` pass through)
  - the Artifact tool, which is off
  - the eval directory, which the agent can't read

  Managed policy **still applies**. [V][ev]
- **Not isolated:** the plugin's own **hooks** and any real MCP servers you start run outside the sandbox and can reach any host. Treat scores from third-party hooks or servers as advisory unless you ran them in a container. [V][ev]
- **Scaffold:** `context.scaffold_script` is bash that runs as you, outside the sandbox, only with `--scaffold`. [V][ev]
- **Mocks:**
  - Files live in `evals/mocks/<server>/<tool>.md` (suite-wide) or a case's `mocks/`. The body is the result, with `{{input.x}}` and `{{file:fixtures/...}}` substitutions.
  - Frontmatter: `type fixed|agent`, `expect` (an input guard; a violation aborts the run with score 0), `error`, `abort_when` (agent only).
  - Optional `_server.md` and `_tools.json`. Agent-mock answers can be adopted into `.replay/<server>/` for deterministic CI.
  - Mocked tools need no grant. Real plugin MCP tools are named `mcp__plugin_<plugin>_<server>__<tool>`. [V][ev]
- **Trust:**
  - The first run in a directory asks `Trust this plugin directory?`. Inside git, the answer trusts the whole repo.
  - Non-TTY or `--json` without `--trust-plugin` gives exit 1. Locally, an untrusted scratch directory was refused with exit 1 before any model call.
  - Named installed targets skip the prompt. [V][ev] [L] (`claude plugin eval . --case zz… </dev/null` → exit 1)

#### 4.7 Outputs, CI and exit codes

- Every run writes `results/<timestamp>/aggregate-result.json` and a self-contained `report.html` (no external requests). The report is also published as a private claude.ai artifact when the account supports it; use `--no-publish` to keep it local. Runs started by a Claude session stay local by default. [V][ev]
- JSON fields (`schemaVersion: 1`, camelCase, additive):
  - `partial` and `partialReason` (`cost_ceiling` | `interrupted` | `auth_failed`)
  - `aggregates.overallScore`, `aggregates.casesPassed`, `aggregates.casesTotal`, `aggregates.meanDelta`
  - `cases[].name`, `cases[].aggregates.score`, `cases[].aggregates.delta`
  - `cases[].arms.with[].error`, `cases[].arms.with[].aborted`, `cases[].arms.with[].skippedPaidGraders`
  - `cases[].arms.without`
  - `costUsd`, `durationSeconds`, `claudeVersion` [V][ev]
- Exit codes: **0** means all cases met the threshold and every case file loaded. **1** means a case below threshold, a load error, no cases found, a run couldn't start, an untrusted directory, or a bad option. **2** means a partial run (cost ceiling hit, or credential rejected). **130** means interrupted. **143** means terminated. Report publish or write failures never change the exit code. [V][ev]
- Rate or usage limits mid-suite make the affected runs error and score about 0 **without** `partial`. Check `arms.with[].error`. [V][ev]
- CI recipe from the docs, in shape: `claude plugin eval . --trust-plugin --json results.json --threshold 0.8 --model <pinned> --judge-model <pinned> --no-publish --max-cost-usd 20`. In CI, `eval init` needs `--bare`. [V][ev]

#### 4.8 Minimal working example (own words)

Plugin `toy` with one skill, `skills/unit-check/SKILL.md` (frontmatter `name: unit-check` and a description saying it checks SI units in a spec line). The suite:

```text
evals/
├── units-flagged/
│   ├── prompt.md
│   └── graders/{verdict-fail.md, names-offender.md, skill-fired.md}
└── no-fire-poem/
    ├── prompt.md
    └── graders/{skill-not-fired.md, no-verdict.md}
```

`evals/units-flagged/prompt.md`
```markdown
---
description: Skill should flag the unitless number in a spec line
tags: [smoke, units]
runs: 3
max_turns: 5
timeout_seconds: 120
allowed_tools: [Skill]
---
Can you sanity-check this spec line for missing units? "Bracket thickness 3 mm, bolt preload 12, operating temperature 85 °C"
```

`graders/verdict-fail.md` (outcome, weight 2)
```markdown
---
type: regex
target: last_message
pattern: '\bFAIL\b'
weight: 2
---
```

`graders/names-offender.md` (outcome)
```markdown
---
type: regex
target: last_message
pattern: 'preload[^\n]{0,40}12|12[^\n]{0,40}preload'
flags: i
---
```

`graders/skill-fired.md` (path; a non-scored indicator under ablation)
```markdown
---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:[\w-]+:)?unit-check"'
---
```

`evals/no-fire-poem/prompt.md` (the negative case)
```markdown
---
description: Unrelated request must not invoke the skill
tags: [smoke, negative]
max_turns: 3
timeout_seconds: 60
allowed_tools: [Skill]
---
Write a two-line poem about autumn.
```

`graders/skill-not-fired.md`
```markdown
---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:[\w-]+:)?unit-check"'
min: 0
max: 0
arm: both
---
```

`graders/no-verdict.md`
```markdown
---
type: regex
target: last_message
pattern: '\b(PASS|FAIL)\b'
match: not_contains
---
```

Run: `claude plugin eval . --tag smoke --model <pinned> --judge-model <pinned> --threshold 1.0 --no-publish --max-cost-usd 2`.

Validation status:
- The `prompt.md` frontmatter of both cases was **parsed by the real loader without error**. [L] Method: an unfiltered-cost probe `claude plugin eval . --case zz-no-such-case --max-cost-usd 0 --runs 1 --ablation none --no-publish --trust-plugin` reported `0 case(s) · $0.00`. In the same probe, a deliberately bad sibling case (`bogus_key`) *was* reported, which shows prompt files are parsed before filtering.
- **Grader files were not validated by the runner.** A bogus grader `type` in a filtered-out case produced no error, so graders are only checked for selected cases, and checking them would start paid runs. [U]
- The docs list `pattern` as a regex option key. The init interview spec said the `.md` body carries the pattern. It is unconfirmed which of the two forms the loader accepts. [U]

#### 4.9 `/skill-doctor`

- `/skill-doctor` (v2.1.252+) reports each skill's context cost and usage, flags skills that were never invoked, and lists plugins not used recently.
  - Interactively it opens as the `/plugin` **Stats** tab; with `-p` it prints text.
  - It is unavailable when feature-flag fetching is off, and over Remote Control. [V][sk]
- It is unrelated to `plugin eval` scoring. Use it together with `claude plugin details` to keep root context small. [V][sk] [V][pr]

### 5. Permissions

#### 5.1 Rule syntax

- Form: `Tool` or `Tool(specifier)`. `Bash` and `Bash(*)` are equivalent. [V][perm]

| Rule | Meaning | Tag |
|---|---|---|
| `Bash(npm run build)` | exact command | [V][perm] |
| `Bash(npm run *)` | prefix. `*` matches any text including spaces. A trailing ` *` also matches the bare command. `Bash(ls*)` also matches `lsof`. | [V][perm] |
| `Bash(ls:*)` | same as `Bash(ls *)`. `:*` is recognised only at the end. | [V][perm] |
| `Read(path)` / `Edit(path)` | gitignore-style: `//abs`, `~/home`, `/relative-to-settings-source`, `./` or bare = relative to cwd. `Edit` covers Edit, Write and NotebookEdit. `Read` covers Read, Grep, Glob and LSP. `Write(...)` path rules are never consulted (startup warning). | [V][perm] [V][tr] |
| `WebFetch(domain:host)` | case-insensitive. `*.example.com` covers subdomains only. A bare `WebFetch` differs from `WebFetch(domain:*)`: only the `domain:` form feeds the sandbox lists. | [V][perm] |
| `mcp__server`, `mcp__server__*`, `mcp__server__tool` | allow globs only after a literal `mcp__<server>__`. `mcp__…(…)` rules with parentheses are **skipped** when loaded from settings. | [V][perm] |
| `Agent(Explore)`, `Agent(my-agent)` | subagent type | [V][perm] |
| `Skill(name)`, `Skill(name *)` | exact or prefix. A deny rule also matches aliases and unqualified names. | [V][sk] [V][tr] |
| `Tool(param:value)` | **deny/ask only**. Matches a top-level scalar input, e.g. `Agent(model:opus)`, `Bash(run_in_background:true)`, `Bash(dangerouslyDisableSandbox:true)`. Primary content fields such as `command` are not matchable. | [V][perm] [V][sb] |
| `Cd(path)` | limits user `/cd` targets | [V][perm] |
| `"*"`, `"mcp__*"` | tool-name globs, deny/ask only | [V][perm] |

- **Bash matching details:**
  - Rules split on `&&`, `||`, `;`, `|`, `|&`, `&` and newlines. Every subcommand must match an allow rule. A deny or ask rule hits any subcommand, including inside `$()` and loops.
  - A fixed set of wrappers is stripped: `timeout`, `time`, `nice`, `nohup`, `stdbuf`, `command`, `builtin`, `noglob` and bare `xargs`.
  - `npx`, `docker exec` and `devbox run` are **not** stripped. [V][perm]
- **Bash rule limits.** `Bash(git push *)` doesn't stop `git -C . push`, `/usr/bin/…` or `sh -c '…'`. Use the sandbox or a PreToolUse hook for real enforcement. [V][perm]
- **Read/Edit deny scope.** They also cover recognised Bash file commands (`cat`, `head`, `sed`, `tee`) and redirect targets, but not `grep -r` or arbitrary scripts. [V][perm]

#### 5.2 Precedence and hierarchy

- Rules are evaluated deny → ask → allow, and the first match wins regardless of specificity. An allow rule can't carve an exception out of a deny rule. A bare-tool deny removes the tool from context entirely. [V][perm]
- Settings precedence: **managed > command-line args > `.claude/settings.local.json` > `.claude/settings.json` > `~/.claude/settings.json`**. Environment variables are not a level. [V][set]
- Lists such as `permissions.allow` and the sandbox arrays **merge** across files. A deny at any level wins. [V][set] [V][perm]
- Some keys honour a stricter value from a lower scope, e.g. `useAutoModeDuringPlan:false`, `maxEffortLevel` and `syncClaudeAiPlugins:false`. [V][set]
- **Workspace trust:** project `permissions.allow` and `additionalDirectories` apply only after the trust dialog. `claude -p` and the SDK never show that dialog, so these rules are not used there (a stderr warning is printed). `deny` and `ask` always apply. [V][perm]
- **Location of the local file:** `.claude/settings.local.json` is read and written at the **git repo root**; in a worktree, at the main checkout's root. Rules anchored with `/` still anchor at the session's primary working directory. [V][set] [V][perm]
- `allowManagedPermissionRulesOnly` (managed only) ignores all non-managed allow, ask and deny rules. [V][sr]

#### 5.3 Permission modes

| Mode | Runs without asking | Notes |
|---|---|---|
| `default` (alias `manual`, v2.1.200+) | reads only | |
| `acceptEdits` | reads, edits, `mkdir`/`touch`/`mv`/`cp` inside working directories | |
| `plan` | reads (plus classifier-approved commands when auto mode is available) | blocks source edits |
| `auto` | everything, reviewed by the classifier | |
| `dontAsk` | reads and pre-approved tools. **Ask-rule matches are denied.** | for CI; never in the Shift+Tab cycle |
| `bypassPermissions` | everything except the "never auto-approved" set | refused as root; refused with `--restricted`; containers or VMs only |

[V][pm] [L] (`claude --help`: `--permission-mode` choices `acceptEdits, auto, bypassPermissions, manual, dontAsk, plan`)

- **Never auto-approved in any mode**, bypass included:
  - explicit ask-rule matches
  - org `ask` connector tools
  - `AskUserQuestion` and `requiresUserInteraction` MCP tools
  - `rm`/`rmdir` on critical paths
  - cross-session messaging safeguards
  - reads outside working directories while `blockReadsOutsideWorkingDirectories` is on

  [V][pm]
- Deny rules apply in every mode, bypass included. Allow rules have no effect in bypass. [V][pm]
- **`permissions.defaultMode`:**
  - `auto` and `bypassPermissions` **do not take effect from project or local settings**. Put them in `~/.claude/settings.json`.
  - Cloud sessions honour only `acceptEdits`, `plan`, `default` and `auto`. [V][sr] [V][pm]
- `permissions.disableBypassPermissionsMode: "disable"` works from any file (managed is typical). It rejects `--dangerously-skip-permissions` and ignores an agent's `permissionMode: bypassPermissions`. `disableAutoMode: "disable"` (also `permissions.disableAutoMode`) removes auto mode. [V][sr]
- **Protected paths.** Writes are never auto-approved except in bypass, and allow rules don't pre-approve them. The set covers:
  - `.git`, `.claude` (except `.claude/worktrees`), `.vscode`, `.idea`, `.husky`, `.devcontainer`
  - shell rc files, `.npmrc`, `.pre-commit-config.yaml`, `.mcp.json`, `.claude.json`, and others

  [V][pm]
- **Critical paths.** `rm`/`rmdir` targeting root, top-level directories, home, the working directory or its parents, or an unguarded `"$VAR"/*` is never approved by allow rules or hooks. [V][pm]

#### 5.4 Auto mode

- **What it is.** A separate classifier model reviews actions before they run. Explicit ask rules still prompt. [V][pm]
- **Availability:**
  - All plans. On Team/Enterprise, admins can disable it.
  - Models: Opus 4.6+/Sonnet 4.6+/Fable on the Anthropic API; Sonnet 5, Opus 4.7+ or Fable on Bedrock, Vertex and Foundry.
  - It is the **built-in default** on Pro/Max/Team in a terminal or VS Code. `claude -p`, the SDK, Enterprise, API keys and 3P providers default to `default`. [V][pm]
  - Auto mode became the default permission mode in week 32 (Aug 2026). [V][llms]
- **Decision order:**
  1. Allow, ask and deny rules resolve first. Protected-path writes, critical-path removals and per-command-domain shells still go to the classifier.
  2. Reads and working-directory edits are auto-approved.
  3. Everything else goes to the classifier.

  On entering auto mode, broad allow rules are **dropped**: `Bash(*)`, interpreter wildcards, package-manager run commands, `Agent` and `Monitor` allows. `autoMode.classifyAllShell: true` suspends every shell allow rule. [V][pm] [V][amc]
- **Classifier inputs.** It sees user messages, tool calls and CLAUDE.md, but **not tool results**. It runs on Sonnet 5 by default. Enterprise, API and 3P accounts pay for classifier tokens unless server-side review applies. [V][pm]
- **Fallback.** Three consecutive or 20 total blocks pause auto mode and fall back to prompts. In `-p` without `--permission-prompt-tool`, the blocked action simply doesn't run. [V][pm]
- **Configuration:**
  - `autoMode.{environment, allow, soft_deny, hard_deny}` are prose rule arrays. Include `"$defaults"` or you **replace** the built-in list.
  - The classifier reads `autoMode` from user, managed and `--settings` only, **never from project or local settings**.
  - Precedence inside the classifier: hard_deny > soft_deny > allow > explicit user intent.
  - CLI: `claude auto-mode defaults [--label]`, `config`, `critique [--model]`, `reset`. [V][amc] [L] (`claude auto-mode --help`)
- **Default blocks** include `curl | bash`, force push, production deploys, IAM grants, `git reset --hard`, merging unapproved PRs, disabling CI or security tests, and routing installs around internal registries. **Default allows** include pushes to any branch of the working repo and PR creation. [V][pm]
- **Measured reliability (dated).** Anthropic reported a two-stage classifier (fast filter, then reasoning). It had a 0.4% false-positive rate but a **17% false-negative rate** on real over-eager actions, and the write-up names the Sonnet 4.6 model. Treat the numbers as indicative. [R][blog]

#### 5.5 `additionalDirectories` and working directories

- Working directories can be extended with `--add-dir`, `/add-dir` or `permissions.additionalDirectories`. The settings form grants **file access only**. `--add-dir` also loads skills, agents and commands, and `enabledPlugins`/`extraKnownMarketplaces` from that directory. [V][perm]
- `permissions.blockReadsOutsideWorkingDirectories: true` (v2.1.257+; `true` from any source wins) fences Read, Grep, Glob and LSP in every mode. [V][sr]

#### 5.6 Hooks vs rules

- PreToolUse hooks run before the permission prompt. **Deny and ask rules still apply whatever the hook returns.** A hook that exits 2 blocks the call even when an allow rule matches. [V][perm]
- Plugin hooks that target the plugin's own MCP tools must use the scoped names `mcp__plugin_<plugin>_<server>__<tool>`. [V][pr]

### 6. Sandboxing

#### 6.1 What it is

- It is built into Claude Code and uses **Seatbelt on macOS** (nothing to install) and **bubblewrap plus socat on Linux/WSL2**; an optional seccomp filter blocks Unix sockets. Native Windows and WSL1 are unsupported. [V][sb]
- It confines **Bash, PowerShell and Monitor commands and their child processes**. [V][sb]
- The same primitives ship standalone as `@anthropic-ai/sandbox-runtime` (beta), which wraps the whole Claude process. [V][se]
- `/sandbox` opens a panel with three tabs plus a conditional one:
  - **Mode**: auto-allow vs regular permissions
  - **Overrides**: `allowUnsandboxedCommands`, shown as "Strict sandbox mode"
  - **Config**: resolved settings, including protected paths
  - **Dependencies**: appears on Linux when something is missing

  Choosing a mode writes to `.claude/settings.local.json`. [V][sb]
- `/sandbox` **is not a permission mode.** Auto-allow approves sandboxed Bash without prompting. Deny rules, content-scoped ask rules and critical-path `rm` still apply. In plan mode, auto-allow does not widen approvals. [V][sb]
- **Escape hatch.** A blocked command can be retried with `dangerouslyDisableSandbox`, which goes through the normal permission flow. `allowUnsandboxedCommands: false` ignores that parameter; an ask rule `Bash(dangerouslyDisableSandbox:true)` forces a prompt. [V][sb]

#### 6.2 Exact settings keys

| Key | Default | Scope note |
|---|---|---|
| `sandbox.enabled` | `false` | any file |
| `sandbox.failIfUnavailable` | `false` | any file. `true` means exit at startup if the sandbox can't start; otherwise commands silently run **unsandboxed** after a warning. |
| `sandbox.autoAllowBashIfSandboxed` | `true` | any file |
| `sandbox.excludedCommands` | unset | `Bash(...)`-style patterns. Excluded commands still go through permissions. Some shapes stay sandboxed (`cd`, redirects, subshells, `sudo`/`eval`/`xargs`). Merges with **no managed lock**. |
| `sandbox.allowUnsandboxedCommands` | `true` | any file |
| `sandbox.filesystem.allowWrite` / `denyWrite` / `denyRead` / `allowRead` | unset | merged. Prefixes: `/` absolute, `~/`, `./` = project root (project settings) or `~/.claude` (user settings). Write-list wildcards work on macOS only. |
| `sandbox.filesystem.allowManagedReadPathsOnly` | `false` | managed |
| `sandbox.filesystem.disabled` | `false` | user/managed, v2.1.216+. Keeps network isolation only. |
| `sandbox.ignoreViolations` | unset | map of command substring to violation substrings |
| `sandbox.enableWeakerNestedSandbox` | `false` | Linux, for unprivileged Docker |
| `sandbox.enableWeakerNetworkIsolation` | `false` | macOS `trustd`, for MITM proxies |
| `sandbox.allowAppleEvents` | `false` | user/managed. Removes code-execution isolation. |
| `sandbox.ripgrep` | unset | user/managed |
| `sandbox.bwrapPath`, `sandbox.socatPath` | unset | managed, Linux |
| `sandbox.credentials.files[]` / `envVars[]` `{path\|name, mode: deny\|mask, injectHosts?…}`, `allowPlaintextInject`, `awsPairs`, `sigv4` | unset | `mask`-related entries are honoured only from user, managed and `--settings`. **There is no built-in credential deny list.** |
| `sandbox.network.allowedDomains` / `deniedDomains` | unset | merged. `*.x.com`, `host:port`, bracketed IPv6. Deny wins. |
| `sandbox.network.strictAllowlist` | `false` | user/managed/`--settings`. **No effect from repo files.** |
| `sandbox.network.allowManagedDomainsOnly` | `false` | managed |
| `sandbox.network.allowUnixSockets` (macOS) / `allowAllUnixSockets` / `allowLocalBinding` (macOS) / `allowMachLookup` | unset/`false` | any file |
| `sandbox.network.httpProxyPort` / `socksProxyPort` | unset (built-in proxy) | any file |
| `sandbox.network.tlsTerminate` | unset | user/managed. Experimental; needed for `mask`. |

[V][sr] [V][sb]

#### 6.3 Domain allowlisting

- Outbound traffic goes through a proxy outside the sandbox. **No domains are pre-allowed.**
  - The first connection to a new host prompts. "Yes" allows it for the session; "Yes, and don't ask again" saves a `WebFetch(domain:…)` allow rule to local settings.
  - `allowedDomains` and `WebFetch(domain:…)` allow rules pre-allow hosts.
  - `strictAllowlist` or managed `allowManagedDomainsOnly` deny instead of prompting. [V][sb]
- In **auto mode** (v2.1.271+), each command names the hosts it needs. The classifier reviews them together with the command, and the hosts open for that command only. [V][sb]
- The proxy decides on the hostname and **does not inspect TLS** by default. Broad domains such as `github.com` allow exfiltration and domain fronting. A custom proxy (`httpProxyPort`) is needed for inspection. [V][sb]

#### 6.4 Filesystem defaults and protected paths

- Default write access: the cwd, added directories and the session `$TMPDIR`. Default read access: **the whole machine, including `~/.ssh` and `~/.aws`**. [V][sb]
- **Worktrees:** writes to the main repo's shared `.git` are allowed, but not `hooks/` or `config`. [V][sb]
- **Sandbox-protected paths** can't be exempted by `allowWrite`:
  - `.claude` settings files and `skills`/`agents`/`commands`/`hooks` directories, and `.mcp.json`, in the working directory and its parents
  - rc files, `.gitconfig`, `.vscode`, `.idea` and `.git/hooks`/`config` in the working directory
  - bare-repo markers
  - most of `~/.claude`

  [V][sb]

#### 6.5 What the sandbox does NOT cover

- Built-in Read, Edit and Write are governed by permission rules only. WebFetch runs in-process. **MCP servers and command hooks run unconstrained on the host.** [V][sb] [V][se]
- Computer use and plugin monitors run unsandboxed. [V][sb] [V][pr]
- Environment variables, including credentials, are inherited unless you set `sandbox.credentials` or `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB`. [V][sb]
- Commands the user types at the `!` prompt run unsandboxed, except in background sessions. [V][sb]
- Subagents share the parent's sandbox config. [V][sb]
- The docs say the sandboxed Bash tool alone is **not sufficient** for fully unattended runs. [V][se]

#### 6.6 Dev container and sandbox runtime

- Dev container reference setup:
  - Install via the feature `ghcr.io/anthropics/devcontainer-features/claude-code:1.0`. It installs the latest CLI; pin with an `npm install -g @anthropic-ai/claude-code@X.Y.Z` Dockerfile step plus `DISABLE_AUTOUPDATER=1`.
  - Policy goes in `/etc/claude-code/managed-settings.json`.
  - Persist a volume at `~/.claude` and set `CLAUDE_CONFIG_DIR` to that path.
  - The reference `init-firewall.sh` needs `NET_ADMIN`/`NET_RAW`.
  - It runs as a non-root `remoteUser`, which is required for `--dangerously-skip-permissions`. [V][dc]
- Tool compatibility:
  - `docker` is incompatible with the sandbox; use `excludedCommands`.
  - Go CLIs (`gh`, `terraform`) can fail TLS under Seatbelt.
  - `jest` needs `--no-watchman`. [V][sb]

---

## Implications for Forge

1. **Repo layout.**
   - Put the marketplace at the repo root as `.claude-plugin/marketplace.json`. The name must not be reserved or impersonate an official one (e.g. `forge-local`). Its single entry is `{ "name": "forge", "source": "./plugins/forge" }`.
   - Keep `version` **only** in `plugins/forge/.claude-plugin/plugin.json`, and release with `claude plugin tag --push` (`forge--vX.Y.Z` tags).
   - Supports: §2.1, §2.5.
2. **Dev loop.**
   - Develop with `claude --plugin-dir ./plugins/forge`, which loads in place, overrides installed copies and works in worktrees.
   - Don't rely on a project `directory` marketplace inside worktrees, because its relative path resolves to the main checkout.
   - Document `/reload-plugins` for picking up changes.
   - Supports: §2.3.
3. **Use default component folders only** (`skills/`, `agents/`, `hooks/hooks.json`, `.mcp.json`). Never declare `"hooks": "./hooks/hooks.json"`, which causes a duplicate-load failure that validate misses. Avoid the `agents` manifest key so `plugin details` inventories agents. Supports: §3 [L].
4. **Checker agents (maker ≠ checker).**
   - Express read-only reviewers as plugin agents with `tools: Read, Grep, Glob` (plus narrowly needed tools) and `disallowedTools: Write, Edit, NotebookEdit`.
   - Never rely on `permissionMode`, `hooks` or `mcpServers` in plugin agents; they are ignored.
   - Forge's own linter must reject those fields, because validate doesn't.
   - `omitClaudeMd: true` and `isolation: worktree` are available for fresh-context review.
   - Supports: §1.5.
5. **The plugin can't carry the permission policy.** Forge's least-privilege lives in three places:
   - (a) A committed product-repo `.claude/settings.json` with `deny`/`ask` rules, which apply without trust, and `allow` rules, which need trust.
   - (b) Plugin **PreToolUse hooks** (exit 2 blocks; returning `ask` forces a prompt) for semantic checks that text rules can't express, e.g. `git -C … push`.
   - (c) Managed settings for anything that must be unoverridable.
   - Supports: §1 (plugin `settings.json` limits), §5.2, §5.6.
6. **Humans sign safety, money and fabrication through `permissions.ask` content rules plus hooks, never through auto-mode prose.**
   - Examples: fabrication-order and quote-submit CLIs, `Bash(git push *)`, `Bash(gh pr merge *)`, and any vendor-upload command.
   - Ask rules prompt in auto and bypass modes, and are **denied** in `dontAsk`, which fails closed in CI.
   - Pair them with hook-based argument inspection, because Bash rule text is bypassable.
   - Supports: §5.1, §5.3, §5.4.
7. **Don't commit `defaultMode: auto` or `bypassPermissions`** (ignored from project files) or `autoMode` rules (ignored from project files). Treat auto mode as a convenience with a reported ~17% miss rate on over-eager actions, not a control. Unattended Forge runs need a container, VM or sandbox-runtime boundary. Supports: §5.3, §5.4, §6.5.
8. **Sandbox baseline for product repos** (project `.claude/settings.json`):
   - `sandbox.enabled: true`
   - `failIfUnavailable: true`
   - `allowUnsandboxedCommands: false`
   - an explicit `network.allowedDomains` per toolchain (e.g. PyPI and the GitHub API only)
   - `filesystem.denyRead` for `~/.ssh`, `~/.aws` and `~/.config/gh` (`credentials.*.mask` isn't honoured from project files)
   - Keep `excludedCommands` minimal (it has no managed lock); `docker *` is the only expected entry.
   - Users set `strictAllowlist: true` at user scope.
   - Supports: §6.2–6.4.
9. **Prefer sandboxed CLI tools over MCP servers.** MCP servers and hooks run unsandboxed, so each one Forge ships is host-level trusted code. When MCP is unavoidable, mock it in evals and require explicit enablement (`defaultEnabled: false` or `userConfig`). Supports: §6.5, §4.6.
10. **Every eval case gets at least two scored graders plus an indicator, and each suite has a negative case.**
    - (a) An outcome grader, usually `regex` over `{source: file, path: …}` evidence the agent wrote.
    - (b) A path grader, `tool_used` with `input_match` naming the verifier command.
    - (c) A `tool_used: Skill` indicator, which is non-scored.
    - At least one should-not-fire case per suite, with `min: 0, max: 0, arm: both`.
    - Because there are no code graders, "checks that can fail" means the *agent* runs the Forge checker, writes machine-readable results to a file, and the grader asserts on that file.
    - Supports: §4.4.
11. **Eval CI command, always:**
    ```
    claude plugin eval plugins/forge --trust-plugin --json results.json \
      --model <pinned> --judge-model <pinned, not the agent model> \
      --threshold <explicit> --max-cost-usd <budget> --no-publish \
      --allow-tools "Bash(<exact verifier> *)"
    ```
    - Fail on non-zero exit.
    - Drop `partial: true` runs and `skippedPaidGraders` runs from trend charts.
    - Check `arms.with[].error` for rate limits.
    - Use `--ablation none` only for cheap iteration.
    - Supports: §4.1, §4.7.
12. **Measure pass^k and pass@k in Forge tooling**, computed from the per-run results in `aggregate-result.json`, since the runner reports only means and the "Perfect runs" share. Pick runs ≥3 (the init floor) and a higher count for release gates, within the 1–50 limit. Supports: §4.5.
13. **Static CI gates run before any paid eval:**
    - (a) `claude plugin validate . --strict` at the marketplace root and on the plugin.
    - (b) `claude --plugin-dir plugins/forge plugin list --json`, failing on any `errors` or unexpected `enabled:false`.
    - (c) A Forge linter for agent frontmatter, hook-script existence and manifest-key hygiene.
    - (d) `claude plugin details forge`, with a token budget for always-on cost to keep root context small.
    - Supports: §3.
14. **Pin the Claude Code floor.**
    - Forge requires ≥2.1.269 for `plugin eval`.
    - Avoid `userConfig.options` and other post-2.1.270 features until the floor is raised.
    - Consider a `SessionStart` hook that checks `claude --version` and warns, since `requiredMinimumVersion` is managed-only.
    - Supports: §0.
15. **Supply chain.**
    - Pin any external plugin or dependency source by `sha`.
    - Never use `command` sources.
    - Ship an npm lockfile if there are Node deps (`npm ci --ignore-scripts`). Install Python toolchains (build123d, atopile) from a `SessionStart` hook into `${CLAUDE_PLUGIN_DATA}` with a `uv` lockfile and a manifest-diff check.
    - Never write state under `${CLAUDE_PLUGIN_ROOT}`.
    - Keep required files out of Git LFS.
    - Supports: §1.4, §1.8, §2.2.
16. **Evals run in an empty workspace with no user config.** Fixtures come from `case.yaml` `context.add_dirs` (read-only) or a `scaffold_script` (Forge-authored, run with `--scaffold`). Toolchain settings reach the run only as `EVAL_*` variables. CAD/EDA binaries must be on PATH for the sandboxed Bash in the eval child. Supports: §4.3, §4.6.
17. **Don't put `CLAUDE.md` in the plugin.** Ship context as skills and keep descriptions tight. Use `/skill-doctor` and `plugin details` as the numbers for small-root-context reviews. Supports: §1.2, §4.9.

---

## Not found / discrepancies

- **`skill_used` grader:** doesn't exist. Use `tool_used` with `tool: Skill` and an `input_match` on the skill name. [V][ev]
- **Command/script/custom-code graders:** don't exist; the docs state "There are no custom-code graders". [V][ev]
- **pass@k / pass^k:** not supported. Only the mean score, Δ and the report's "Perfect runs" share exist. [V][ev]
- **Top-level `evals` manifest field:** doesn't exist; it is `experimental.evals`. [L]
- **`workflows`:** exists as a component path field (replaces the default `workflows/`). [V][pr]
- **`settings` in `plugin.json`:** mentioned in the plugins guide and accepted by validate, but missing from the reference "Complete schema". Only `agent` and `subagentStatusLine` keys are honoured. [V][pl] [L]
- **Validate exit 2:** the docs promise exit 2 for an unreadable path, but local 2.1.270 returned **1** for both a missing path and an EACCES manifest. [V][pr] [L]
- **Validate gaps (local):**
  - ignored plugin-agent fields (`permissionMode`, `hooks`) aren't flagged
  - unresolvable `dependencies` aren't flagged
  - missing hook scripts aren't flagged
  - the duplicate `hooks/hooks.json` declaration isn't flagged, although it breaks loading
  - skill YAML errors are shown only after manifest errors are cleared

  [L]
- **`plugin details`:** shows Agents (0) when the manifest `agents` key is set. Whether those agents load at runtime was not confirmed (it would need a live session). [L] [U]
- **`eval init -i` without a TTY:** inside a Claude Code session it printed interview instructions instead of failing as documented. The docs do describe the in-session behaviour for plain `init`. [L] [V][pr]
- **Undocumented `prompt.md` keys:** the loader accepts `artifact_publish` and `growthbook_overrides`. [L]
- **Regex grader pattern location:** the docs list `pattern` as an option key, while the init interview spec says the `.md` body is the pattern. Not confirmed without a paid run. [U]
- **Per-run JSON field names** beyond `error`, `aborted` and `skippedPaidGraders` (per-grader `passed`, `scored`, explanations): only partially documented. [U]
- **Version drift:**
  - `--claudeai` appears in local 2.1.270 `marketplace add --help`, although the docs say it requires v2.1.273.
  - `--accept-command` (v2.1.271) is absent locally.
  - `userConfig.options` (v2.1.271) is rejected locally.

  [L] [V][mk]
- **`--permission-mode` choices:** local help lists `manual` but not `default`, while the docs treat `default` as the config value and `manual` as an alias. [L] [V][pm]
- **Auto mode classifier model:** the engineering blog says Sonnet 4.6, while current docs say Sonnet 5 by default. The blog's FP/FN figures may be stale. [R][blog] [V][pm]
- **SchemaStore manifest schema lags the docs.** It lacks `displayName`, `defaultEnabled`, `metadata`, `experimental` and `workflows`, and still has top-level `monitors`, `themes` and `settings`. Its marketplace schema has a `forceRemoveDeletedPlugins` key that is not in the official docs. Don't rely on it. [L] (`curl https://json.schemastore.org/claude-code-plugin-manifest.json`) [R][ss] [R][ssm]
- **`Bash(cmd:*)`:** valid, but only as a trailing form. It is equivalent to `Bash(cmd *)`. [V][perm]
- **MCP permission rules with a parameter**, `mcp__x__y(…)`, are skipped when loaded from settings files (CLI `--disallowedTools` only). [V][perm]
- **Not verified:**
  - Whether macOS Seatbelt interferes with KiCad CLI, OpenCascade/build123d, ngspice or atopile under the Bash sandbox.
  - The actual token cost and wall time of a Forge-sized eval suite.
  - The behaviour of `claude plugin eval` with Bash grants on this Mac.

  None of these were run (no installs, no paid evals). [U]

---

## Sources

| # | Title | URL | Type | Accessed |
|---|---|---|---|---|
| 1 | Claude Code docs index (llms.txt) | https://code.claude.com/docs/llms.txt | official | 2026-09-25 |
| 2 | Plugins reference | https://code.claude.com/docs/en/plugins-reference.md | official | 2026-09-25 |
| 3 | Create plugins | https://code.claude.com/docs/en/plugins.md | official | 2026-09-25 |
| 4 | Create and distribute a plugin marketplace | https://code.claude.com/docs/en/plugin-marketplaces.md | official | 2026-09-25 |
| 5 | Constrain plugin dependency versions | https://code.claude.com/docs/en/plugin-dependencies.md | official | 2026-09-25 |
| 6 | Discover and install plugins | https://code.claude.com/docs/en/discover-plugins.md | official | 2026-09-25 |
| 7 | Test plugins with evals | https://code.claude.com/docs/en/plugin-evals.md | official | 2026-09-25 |
| 8 | Configure permissions | https://code.claude.com/docs/en/permissions.md | official | 2026-09-25 |
| 9 | Choose a permission mode | https://code.claude.com/docs/en/permission-modes.md | official | 2026-09-25 |
| 10 | Configure auto mode | https://code.claude.com/docs/en/auto-mode-config.md | official | 2026-09-25 |
| 11 | Configure the sandboxed Bash tool | https://code.claude.com/docs/en/sandboxing.md | official | 2026-09-25 |
| 12 | Choose a sandbox environment | https://code.claude.com/docs/en/sandbox-environments.md | official | 2026-09-25 |
| 13 | Settings files and precedence | https://code.claude.com/docs/en/settings.md | official | 2026-09-25 |
| 14 | All settings (reference) | https://code.claude.com/docs/en/settings-reference.md | official | 2026-09-25 |
| 15 | Development containers | https://code.claude.com/docs/en/devcontainer.md | official | 2026-09-25 |
| 16 | Subagents | https://code.claude.com/docs/en/sub-agents.md | official | 2026-09-25 |
| 17 | Skills | https://code.claude.com/docs/en/skills.md | official | 2026-09-25 |
| 18 | Tools reference | https://code.claude.com/docs/en/tools-reference.md | official | 2026-09-25 |
| 19 | What's new, week 37 (plugin eval launch) | https://code.claude.com/docs/en/whats-new/2026-w37.md | official | 2026-09-25 |
| 20 | Claude Code auto mode (engineering deep dive) | https://www.anthropic.com/engineering/claude-code-auto-mode | primary (dated) | 2026-09-25 |
| 21 | Official plugin marketplace repo | https://github.com/anthropics/claude-plugins-official | primary | 2026-09-25 |
| 22 | npm registry: @anthropic-ai/claude-code | https://registry.npmjs.org/@anthropic-ai/claude-code | primary | 2026-09-25 |
| 23 | SchemaStore plugin manifest schema | https://json.schemastore.org/claude-code-plugin-manifest.json | secondary | 2026-09-25 |
| 24 | SchemaStore marketplace schema | https://json.schemastore.org/claude-code-marketplace.json | secondary | 2026-09-25 |

Local commands used (all read-only, or confined to the scratch directory):
- `claude --version`, `claude --help`
- `claude plugin <sub> --help` for every subcommand
- `claude plugin marketplace <sub> --help`, `claude plugin eval init --help`
- `claude auto-mode <sub> --help`
- `claude plugin validate [--strict] [--json]` against scratch fixtures
- `claude --plugin-dir <scratch> plugin details|list --json`
- `claude plugin eval init --bare`
- Two zero-case `claude plugin eval` probes, both $0.00: an untrusted-directory refusal, and a `--case` filter that matched nothing
- `gh api repos/anthropics/claude-plugins-official/...`
- `npm view @anthropic-ai/claude-code`

[llms]: https://code.claude.com/docs/llms.txt
[pr]: https://code.claude.com/docs/en/plugins-reference.md
[pl]: https://code.claude.com/docs/en/plugins.md
[mk]: https://code.claude.com/docs/en/plugin-marketplaces.md
[dep]: https://code.claude.com/docs/en/plugin-dependencies.md
[disc]: https://code.claude.com/docs/en/discover-plugins.md
[ev]: https://code.claude.com/docs/en/plugin-evals.md
[perm]: https://code.claude.com/docs/en/permissions.md
[pm]: https://code.claude.com/docs/en/permission-modes.md
[amc]: https://code.claude.com/docs/en/auto-mode-config.md
[sb]: https://code.claude.com/docs/en/sandboxing.md
[se]: https://code.claude.com/docs/en/sandbox-environments.md
[set]: https://code.claude.com/docs/en/settings.md
[sr]: https://code.claude.com/docs/en/settings-reference.md
[dc]: https://code.claude.com/docs/en/devcontainer.md
[sa]: https://code.claude.com/docs/en/sub-agents.md
[sk]: https://code.claude.com/docs/en/skills.md
[tr]: https://code.claude.com/docs/en/tools-reference.md
[w37]: https://code.claude.com/docs/en/whats-new/2026-w37.md
[blog]: https://www.anthropic.com/engineering/claude-code-auto-mode
[off]: https://github.com/anthropics/claude-plugins-official
[npm]: https://registry.npmjs.org/@anthropic-ai/claude-code
[ss]: https://json.schemastore.org/claude-code-plugin-manifest.json
[ssm]: https://json.schemastore.org/claude-code-marketplace.json
