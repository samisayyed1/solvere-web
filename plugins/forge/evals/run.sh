#!/usr/bin/env bash
# Forge eval runner (brief §6, ADR-001 §10). Runs the smoke tier or the full
# suite with pinned models and a hard cost ceiling, then computes pass@k /
# pass^k (forge passk), seeded-defect recall and precision, and appends the
# spend to SPEND.md.
#
#   plugins/forge/evals/run.sh smoke --max-cost-usd 60
#   plugins/forge/evals/run.sh full  --max-cost-usd 200 [--runs 3] [--concurrency 2] [--case <glob>]
#   plugins/forge/evals/run.sh check          # free: load every case, spend nothing
#
# Always: --model/--judge-model claude-opus-5-5 (owner decision, 2026-09-25),
# --trust-plugin --scaffold --no-publish --json, --allow-tools Bash Write Edit,
# --keep-temp (the seeded-defect findings files are harvested from the kept
# workspaces, then the temp dirs are deleted), results in
# plugins/forge/evals/results/<UTC timestamp>/.
set -euo pipefail

EVALS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN="$(cd "$EVALS/.." && pwd)"
MODEL="claude-opus-5-5"
JUDGE="claude-opus-5-5"
FORGE_HOME="${FORGE_HOME:-$HOME/.forge}"

usage() { sed -n '2,16p' "$0" | sed 's/^# \{0,1\}//'; exit 2; }

TIER="${1:-}"; [ -n "$TIER" ] || usage; shift || true
COST=""; RUNS=3; CONC=1; CASE=""; THRESH="0.0"
while [ $# -gt 0 ]; do
  case "$1" in
    --max-cost-usd) COST="$2"; shift 2 ;;
    --runs) RUNS="$2"; shift 2 ;;
    --concurrency|-j) CONC="$2"; shift 2 ;;
    --case) CASE="$2"; shift 2 ;;
    --threshold) THRESH="$2"; shift 2 ;;
    -h|--help) usage ;;
    *) echo "run.sh: unknown option $1" >&2; usage ;;
  esac
done

# Forge's toolchain must be visible to the run: $FORGE_HOME/bin on PATH gives
# the sandbox its bwrap/socat and lets each scaffold find forge-python (the
# scaffold links the run's throwaway $HOME/.forge to it). $FORGE_HOME itself
# is on PATH too: the harness grants sandboxed Bash read access to PATH
# entries under the (otherwise unreadable) real home, and forge-python execs
# $FORGE_HOME/envs/cad/bin/python, so the whole toolchain tree must be readable.
[ -x "$FORGE_HOME/bin/forge-python" ] || { echo "run.sh: no Forge toolchain at $FORGE_HOME (set FORGE_HOME)" >&2; exit 2; }
export PATH="$FORGE_HOME/bin:$FORGE_HOME:$PATH"
export EVAL_FORGE_HOME="$FORGE_HOME"

COMMON=(--model "$MODEL" --judge-model "$JUDGE" --trust-plugin --scaffold --no-publish
        --allow-tools Bash Write Edit)
FILTER=()
case "$TIER" in
  smoke) FILTER=(--tag smoke) ;;
  full) ;;
  check)
    out="$(mktemp -d)"
    claude plugin eval "$PLUGIN" "${COMMON[@]}" --runs 1 --max-cost-usd 0 --output-dir "$out" 2>&1 \
      | grep -v '^Note: --scaffold' || true
    python3 - "$out/aggregate-result.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
print(f"load check: partial={d.get('partial')} ({d.get('partialReason')}), cost ${d.get('costUsd', 0):.2f}")
PY
    rm -rf "$out"; exit 0 ;;
  *) usage ;;
esac
[ -n "$CASE" ] && FILTER+=(--case "$CASE")

[ -n "$COST" ] || { echo "run.sh: --max-cost-usd is required (owner budget ~US\$250 for ALL eval runs)" >&2; exit 2; }
python3 -c "import sys; c=float(sys.argv[1]); sys.exit(0 if c > 0 else 1)" "$COST" \
  || { echo "run.sh: --max-cost-usd must be > 0" >&2; exit 2; }
[ "$RUNS" -ge 3 ] 2>/dev/null || { echo "run.sh: --runs must be >= 3 (brief §6)" >&2; exit 2; }

TS="$(date -u +%Y-%m-%dT%H-%M-%SZ)"
OUT="$EVALS/results/$TS"
mkdir -p "$OUT"
echo "run.sh: $TIER tier, runs=$RUNS, ceiling \$$COST, model $MODEL / judge $JUDGE -> $OUT"

set +e
claude plugin eval "$PLUGIN" "${COMMON[@]}" "${FILTER[@]}" \
  --runs "$RUNS" -j "$CONC" --threshold "$THRESH" --max-cost-usd "$COST" \
  --keep-temp --output-dir "$OUT" --json "$OUT/results.json" 2> "$OUT/stderr.log"
EVAL_RC=$?
set -e
echo "run.sh: claude plugin eval exit $EVAL_RC (0 pass, 1 below threshold, 2 partial/ceiling)"
[ -f "$OUT/aggregate-result.json" ] || cp "$OUT/results.json" "$OUT/aggregate-result.json" 2>/dev/null || {
  echo "run.sh: no result document written; see $OUT/stderr.log" >&2; exit 1; }

# pass@k / pass^k per case and arm (partial documents allowed, and marked)
python3 "$PLUGIN/bin/forge" passk "$OUT/aggregate-result.json" --k "1,$RUNS" --allow-partial \
  --out "$OUT/passk.json" | tee "$OUT/passk.txt" || true

# seeded-defect recall/precision (reads the kept workspaces, archives findings under $OUT/findings/)
python3 "$EVALS/_tools/seeded_score.py" --results "$OUT" --min-recall 0.8 | tee "$OUT/seeded.txt" || true

# delete the kept temp dirs (their findings are archived); only harness-made claude-eval-* dirs
python3 - "$OUT/aggregate-result.json" <<'PY'
import json, os, shutil, stat, sys
from pathlib import Path
d = json.load(open(sys.argv[1]))
roots = set()
for c in d.get("cases", []):
    for runs in (c.get("arms") or {}).values():
        for r in runs:
            tp = r.get("tracePath")
            if tp:
                root = Path(tp).parent.parent
                if root.name.startswith("claude-eval-"):
                    roots.add(root)
def onerr(func, path, _):
    os.chmod(path, stat.S_IRWXU); func(path)
for root in sorted(roots):
    for p, dirs, files in os.walk(root):
        for x in dirs + files:
            try: os.chmod(os.path.join(p, x), stat.S_IRWXU, follow_symlinks=False)
            except (OSError, NotImplementedError): pass
    shutil.rmtree(root, onerror=onerr)
print(f"run.sh: removed {len(roots)} kept temp dir(s)")
PY

# spend log
python3 - "$OUT/aggregate-result.json" "$EVALS/SPEND.md" "$TIER" "$RUNS" "$TS" <<'PY'
import json, re, sys
agg, spend, tier, runs, ts = sys.argv[1:6]
d = json.load(open(agg))
cost = float(d.get("costUsd") or 0.0)
n_runs = sum(len(v) for c in d.get("cases", []) for v in (c.get("arms") or {}).values())
text = open(spend).read()
totals = [float(m) for m in re.findall(r"\|\s*([0-9]+\.[0-9]{2})\s*\|\s*$", text, re.M)]
total = (totals[-1] if totals else 0.0) + cost
row = (f"| {ts[:10]} | run.sh {tier} ({ts}){' PARTIAL: ' + str(d.get('partialReason')) if d.get('partial') else ''} "
       f"| {len(d.get('cases', []))} cases x {runs} runs x arms | claude-opus-5-5 / claude-opus-5-5 "
       f"| {n_runs} | {cost:.2f} | {total:.2f} |\n")
with open(spend, "a") as f:
    f.write(row)
print(f"run.sh: spent ${cost:.2f} (running total ${total:.2f}); logged in SPEND.md")
PY
exit "$EVAL_RC"
