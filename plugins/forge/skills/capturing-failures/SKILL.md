---
name: capturing-failures
description: Turn a caught defect into a permanent mechanism -- root cause via five whys, a new rule/hook/check/eval, and proof that the new check fails on the original artifact. Use whenever a review, a human, or a check catches something Forge should have caught earlier -- a wrong CAD dimension, a missed ERC violation, a firmware regression, an untested requirement. Do NOT use this for routine check failures that the existing checks already catch correctly (that's just "fix the design"); use it when the *check itself* was missing or too weak.
allowed-tools: Read, Grep, Glob, Write, Edit, Bash(~/.forge/bin/forge-python *)
---

# Capturing failures

**Non-negotiable rules:**

1. **Every failure capture ends with a mechanism that can fail** — a new or tightened rule, hook, check or eval case. A capture that ends only in prose ("we'll be more careful") hasn't fixed anything (brief §0).
2. **Prove the new check catches the original failure.** Run it against the original (unfixed) artifact and show it fails, then against the fix and show it passes. A check only ever run against the fixed version proves nothing.
3. **One `docs/failures/<id>.md` per failure**, scaffolded by `scripts/new_failure.py` so ids never collide.

## Workflow

1. **Scaffold the record**: `~/.forge/bin/forge-python scripts/new_failure.py --project <root> --title "<short description>"`. It allocates the next `FAIL-NNNN` id and writes the template.
2. **Root-cause it with five whys** — write real answers, not restatements of the symptom. Stop when the answer is something a mechanism can actually prevent (not "someone should be more careful").
3. **Build the mechanism**: a tightened rule (with its enforcing hook/lint/check named), a new PostToolUse check, a new `scripts/verify.py` measurement, or a new eval case under `plugins/forge/evals/`. Prefer pushing it to the fastest layer that can hold it (brief §0: hook < pre-commit < CI < human review).
4. **Prove it**: run the new/changed check against the original artifact (or a reconstruction of it) and confirm it fails with a remediation that would have caught the original mistake; then run it against the fix and confirm it passes. Record both `out/verify/*.json` paths in the failure doc.
5. **Add or update an eval case** if the failure is the kind an agent could plausibly repeat (brief §6, §7) — link it in the failure doc's "Eval case" section.

## What this skill refuses

- Closing a failure capture with no new or tightened mechanism.
- Marking the proof step done without actually running the new check against the original failing artifact.

## References

- `plugins/forge/CONTRACTS.md` §3 — the check-result format the proof step's `out/verify/*.json` must follow.
- `docs/decisions/ADR-001-forge-architecture.md` §13 point 6 — "every failure message says how to fix it," the standard this skill's new checks must meet.
