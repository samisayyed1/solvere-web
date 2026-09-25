---
name: reviewing-designs
description: Run a stage-gate review -- verification-evaluator, red-team and the relevant specialists, each in a fresh context -- and reconcile them into reviews/Gx.md with a blank human sign-off line. Use when asked to "review this for gate G<n>", "run the gate review", "is this ready for G2", or before any release. Never passes a gate itself, and never fills in a sign-off line -- only a human does that. Do not use this to build or fix a design -- that is the maker skills' job, not a reviewer's.
context: fork
allowed-tools: Read, Grep, Glob, Bash(git log *), Bash(git diff *), Bash(~/.forge/bin/forge-python *), Workflow
---

# Reviewing designs

**Non-negotiable rules:**

1. **This skill never passes a gate.** It produces a reconciled report and a recommendation; the `reviews/Gx.md` sign-off line is always left blank, and only a human fills it in (CONTRACTS.md §7). If asked to mark a gate PASS, decline and say what's missing.
2. **The maker is never the checker.** Every reviewer runs in a fresh context with read-only tools (`forge:verification-evaluator`, `forge:red-team`, and specialists in *review mode*) — never the agent that built the thing under review, and never with write access.
3. **Every criterion needs cited evidence.** A reviewer verdict that references a claim with no `out/verify/*.json` or `evidence/manifest.json` entry is `BLOCKED`, not `PASS` — see the verdict schema (CONTRACTS.md §5).
4. **Run the `gate-review` workflow from the main thread**, via the `Workflow` tool — never simulate the parallel review by hand in this skill's own context, and never call it from inside a subagent (it isn't available there).

## Workflow

1. **Confirm the gate and scope** with the user if not already clear: which gate (`G0`–`G6`), which project path, and whether any specialists beyond `verification-evaluator`/`red-team` should review (e.g. `mechanical-engineer`, `electrical-engineer`, `safety-compliance-engineer` — matched to what actually changed).
2. **Check the evidence gate first**: read `evidence/manifest.json` and `out/verify/*.json` for the domains that changed since the last review. If a domain changed with no fresh evidence, say so up front — the review will come back `BLOCKED` for those criteria, which is expected, not a bug.
3. **Run the workflow**:
   ```
   Workflow({ name: "gate-review", args: { project: "<path>", gate: "G2", specialists: ["mechanical-engineer"] } })
   ```
   It runs `forge:verification-evaluator` and `forge:red-team` (always) plus any named specialists, in parallel, each in a fresh context, each forced to end with exactly one `forge.verdict/1` JSON block (enforced by the SubagentStop hook — a reviewer that returns free-form prose is rejected upstream, not accepted here).
4. **The workflow reconciles the verdicts** into `reviews/Gx.md`, following `templates/project/reviews/_gate-template.md` if the target project has it, else `references/gate-record-template.md` in this skill. The sign-off line is always written blank.
5. **Report the result to the user**: overall recommendation (PASS/FAIL/BLOCKED), the count of criteria in each state, the most severe open finding, and exactly what a human needs to do to sign off (or what's missing before they can).

## What this skill refuses

- Filling in, or asking the user to let it fill in, the human sign-off line.
- Treating a maker agent's own summary of its work as a review.
- Accepting a reviewer's free-form text in place of the verdict JSON block.
- Running the review from inside a subagent context (the `Workflow` tool isn't available there — ADR-001 §7).

## References

- `references/gate-record-template.md` — the fallback gate-record template and why the sign-off line is always blank.
- `plugins/forge/workflows/gate-review.js` — the workflow this skill invokes.
- `plugins/forge/CONTRACTS.md` §5, §7 — the verdict schema and the gate-record contract.
