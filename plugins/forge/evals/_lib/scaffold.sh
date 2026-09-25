#!/usr/bin/env bash
# Shared scaffold for Forge eval cases. Sourced by each case's scaffold.sh:
#
#   source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../_lib/scaffold.sh"
#   forge_eval_scaffold --template      # or --bare for a non-Forge workspace
#
# `claude plugin eval --scaffold` runs the case script in the run's empty
# workspace ($PWD) with a THROWAWAY $HOME, a minimal environment (PATH is
# inherited, EVAL_* variables are not) and no sandbox. Forge's toolchain lives
# in the REAL user's ~/.forge, and every skill script and hook finds it as
# ~/.forge (Path.home()/.forge, `~/.forge/bin/forge-python`). So this script
# links $HOME/.forge -> the real forge home. Resolution order:
#   1. $FORGE_HOME / $EVAL_FORGE_HOME, if the harness ever passes them;
#   2. the dir above a `forge-python` on PATH (run.sh puts $FORGE_HOME/bin there);
#   3. ~<login user>/.forge (tilde-user expansion reads the passwd db, not $HOME).
# It then copies templates/project/ (minus .claude/settings.json and .mcp.json,
# which would pull the user's sandbox/MCP config into a run) and the case's
# fixture/ over it, fills {{PROJECT_NAME}}, and commits the result as the
# scaffold commit the Stop hook diffs against. Answer keys (key/, reference/,
# selftest.json) are never copied.
set -euo pipefail

_FE_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FORGE_EVALS_DIR="$(cd "$_FE_LIB_DIR/.." && pwd)"
FORGE_PLUGIN_DIR="$(cd "$FORGE_EVALS_DIR/.." && pwd)"
FORGE_REPO_DIR="$(cd "$FORGE_PLUGIN_DIR/../.." && pwd)"

forge_eval_real_home() {
  local cand
  for cand in "${FORGE_HOME:-}" "${EVAL_FORGE_HOME:-}"; do
    if [ -n "$cand" ] && [ -x "$cand/bin/forge-python" ]; then echo "$cand"; return 0; fi
  done
  cand="$(command -v forge-python 2>/dev/null || true)"
  if [ -n "$cand" ]; then
    cand="$(cd "$(dirname "$cand")/.." && pwd -P)"
    if [ -x "$cand/bin/forge-python" ]; then echo "$cand"; return 0; fi
  fi
  local user; user="$(id -un)"
  cand="$(eval echo "~$user")/.forge"
  if [ -x "$cand/bin/forge-python" ]; then echo "$cand"; return 0; fi
  return 1
}

forge_eval_link_home() {
  local real
  if ! real="$(forge_eval_real_home)"; then
    echo "scaffold: WARNING no Forge toolchain found (FORGE_HOME, PATH, ~user/.forge); checks will exit 2" >&2
    return 0
  fi
  if [ "$(cd "$HOME" && pwd -P)" = "$(cd "$(dirname "$real")" && pwd -P)" ]; then
    return 0   # not a throwaway HOME (manual run): ~/.forge already is the real one
  fi
  if [ ! -e "$HOME/.forge" ]; then
    ln -s "$real" "$HOME/.forge"
  fi
}

forge_eval_seed_template() {
  local name="${1:-eval-project}"
  local tpl="$FORGE_REPO_DIR/templates/project"
  [ -d "$tpl" ] || { echo "scaffold: template not found at $tpl" >&2; exit 1; }
  (cd "$tpl" && tar cf - --exclude='./.claude/settings.json' --exclude='./.mcp.json' .) | tar xf -
  local f
  for f in forge.toml CLAUDE.md AGENTS.md; do
    [ -f "$f" ] && sed -i.bak "s/{{PROJECT_NAME}}/$name/g" "$f" && rm -f "$f.bak"
  done
  return 0
}

forge_eval_copy_fixture() {
  local case_dir="$1"
  if [ -d "$case_dir/fixture" ]; then
    (cd "$case_dir/fixture" && tar cf - .) | tar xf -
  fi
}

forge_eval_git_commit() {
  git init -q . 2>/dev/null || true
  git -c user.name=forge-eval -c user.email=eval@forge.invalid add -A >/dev/null 2>&1 || true
  git -c user.name=forge-eval -c user.email=eval@forge.invalid -c commit.gpgsign=false \
      commit -q -m "scaffold" >/dev/null 2>&1 || true
}

# forge_eval_scaffold <case_dir> [--template|--bare] [project-name]
forge_eval_scaffold() {
  local case_dir="$1" mode="${2:---template}" name="${3:-$(basename "$1")}"
  forge_eval_link_home
  if [ "$mode" = "--template" ]; then
    forge_eval_seed_template "$name"
  fi
  forge_eval_copy_fixture "$case_dir"
  forge_eval_git_commit
}
