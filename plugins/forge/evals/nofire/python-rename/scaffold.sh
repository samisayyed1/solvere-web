#!/usr/bin/env bash
# Plain Python repo, NOT a Forge project (no template) -- Forge must stay out of the way.
CASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$CASE_DIR/../../_lib/scaffold.sh"
forge_eval_scaffold "$CASE_DIR" --bare
