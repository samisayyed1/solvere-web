---
name: init
description: Add Forge to an EXISTING repository non-destructively -- writes only the templates/project files that don't already exist, merges .gitignore lines, and never overwrites anything. Use only on explicit user request ("add forge to this repo", "/forge:init"); always prints a conflict report for files that already existed. Do not use this to start a brand-new, empty project -- use /forge:new-project instead.
when_to_use: ["add forge to this repo", "init forge here", "retrofit forge", "/forge:init"]
argument-hint: "[target-dir] [project name]"
disable-model-invocation: true
allowed-tools: "Bash(python3 ${CLAUDE_PLUGIN_ROOT}/skills/init/scripts/scaffold.py *)"
---

Adding files to an existing repository has side effects, so this skill never fires on its own -- only on an explicit `/forge:init` invocation.

## Non-negotiable rules

1. **Never overwrite a file that already exists.** The script enforces this; every existing file is left byte-for-byte untouched and reported as a conflict, never silently merged (except `.gitignore`, which is explicitly append-only).
2. **`.gitignore` is merged, not skipped and not overwritten.** Only lines missing from the existing file are appended, under a clearly marked `# --- added by /forge:init ---` section.
3. **Always show the full conflict report.** A conflict is not a failure -- it means the repo already had its own version of that file, and a human decides how to reconcile it.

## Steps

1. Parse `$ARGUMENTS` for a target directory (default: the current repo root) and an optional project name.
2. Run:
   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/init/scripts/scaffold.py" <target-dir> --name "<name>"
   ```
3. Report the script's output verbatim: files written, `.gitignore` lines merged, and the full conflict list.
4. For every conflicting file, tell the user what the template version would have contained (read it from `templates/project/<path>` in the Forge repo) so they can decide whether to merge it in by hand -- never merge it for them automatically.
5. If `.claude/settings.json` was a conflict (an existing project settings file), explicitly flag that Forge's permission/sandbox baseline (deny/ask rules, sandbox keys) was **not** applied, and point at `templates/project/.claude/settings.json` as the reference to merge in.
