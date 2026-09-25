#!/usr/bin/env bash
# Seeds the run's workspace: Forge project template + this case's fixture/ (see ../../_lib/scaffold.sh).
CASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$CASE_DIR/../../_lib/scaffold.sh"
forge_eval_scaffold "$CASE_DIR" --template
