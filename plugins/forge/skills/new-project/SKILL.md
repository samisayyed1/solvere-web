---
name: new-project
description: Scaffold a brand-new Forge product-engineering project from templates/project/ into an empty or new directory -- CLAUDE.md, AGENTS.md, .claude/rules, .claude/settings.json, .mcp.json, forge.toml, params, requirements, the SysML model, evidence, reviews and every gate directory. Use only on explicit user request ("start a new Forge project", "/forge:new-project"); refuses a non-empty target directory. Do not use this on an existing repository that already has files in it, and do not use it to add Forge onto an existing project -- use /forge:init instead.
when_to_use: ["start a new project", "new forge project", "scaffold a project", "/forge:new-project"]
argument-hint: "<target-dir> [project name]"
disable-model-invocation: true
allowed-tools: "Bash(python3 ${CLAUDE_PLUGIN_ROOT}/skills/new-project/scripts/scaffold.py *)"
---

Scaffolding a project has side effects (writes many files to disk), so this skill never fires on its own -- only on an explicit `/forge:new-project` invocation.

## Non-negotiable rules

1. **Never run against a non-empty directory.** The script itself refuses this (exit 1); do not work around it by deleting files first.
2. **Never invent the project name silently.** If `$ARGUMENTS` gives a target directory but no name, ask the user for one, or fall back to the directory's basename and say so explicitly -- don't guess a product name.
3. **Report `forge doctor --quick` results, but never fail the scaffold on them.** A doctor warning (e.g. a missing optional toolchain tier) is not a scaffold failure.

## Steps

1. Parse `$ARGUMENTS` for a target directory (required) and an optional project name (everything after the directory).
2. Run:
   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/new-project/scripts/scaffold.py" <target-dir> --name "<name>"
   ```
   The script always leaves a git repository with one baseline commit of the scaffold (it runs `git init` if needed). The Stop hook's evidence gate diffs against that commit until the first green `forge verify`. Pass `--no-commit` only if the user explicitly refuses git.
3. Report the script's output verbatim: files written, the `forge doctor --quick` summary, and the next-steps list.
4. Tell the user explicitly that `.claude/settings.json` and `.mcp.json` were written with a strict default policy (deny/ask rules, sandbox baseline) and should be reviewed, not blindly trusted, before any fab/flash/release command runs in the new project.
5. Do not start filling in `requirements/requirements.md`, `params/params.toml` or `model/system.sysml` unless the user asks -- scaffolding and requirements-gathering are separate steps (see `interviewing-stakeholders`, `writing-requirements`).
