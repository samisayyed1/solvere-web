---
name: tracing-requirements
description: Build and verify the requirement -> design -> test -> evidence traceability graph from requirements/requirements.md, requirements/trace.json and evidence/manifest.json. Use when the user asks "is everything traced", "what's untested", "check traceability", before a gate review, or after adding/removing a design file, test or evidence entry. Also fires from the systems.md path rule. Do NOT use this to write requirement text (see writing-requirements) or to change evidence levels (see the evidence CLI) — this skill only reads and cross-references, plus updates trace.json's status/design/tests/evidence links.
paths:
  - "requirements/**"
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(${CLAUDE_SKILL_DIR}/scripts/verify.py:*), Bash(forge-python ${CLAUDE_SKILL_DIR}/scripts/verify.py:*), Bash(forge trace:*)
---

# Tracing requirements

**Non-negotiable rules, read first:**
1. Every requirement in `requirements/requirements.md` must have an entry in `requirements/trace.json`. No entry means no design, no tests, no evidence — that is a gate blocker, not a formality.
2. A requirement with an empty `tests[]` is untested unless its `status` is `waived` (and a waiver needs a stated reason in `notes`, recorded by a human — never waive silently to make the check pass).
3. Every `evidence[]` id must exist in `evidence/manifest.json`. A dangling id is worse than no id — it is evidence that was never written.
4. Every design or test source file under `cad/`, `ecad/`, `firmware/`, `app/`, `analysis/`, `mfg/`, `tests/` must be referenced by some requirement's `design[]`/`tests[]`. An unreferenced file is either untraceable work or dead code — find out which, don't leave it silent.
5. Run `scripts/verify.py` (or `forge trace`) after every change to `trace.json`, and after adding or deleting a design/test file. Fix every finding.

## `trace.json` format

```json
{
  "schema": "forge.trace/1",
  "requirements": {
    "REQ-MECH-004": {
      "design": ["cad/enclosure.py#lid_lip"],
      "tests": ["tests/mech/test_wall_thickness.py"],
      "evidence": ["EV-0001"],
      "status": "verified"
    }
  }
}
```

- `design[]` / `tests[]` entries are repo-relative paths, optionally with a `#fragment` naming the specific feature/test inside the file (the orphan check matches on the file path).
- `status` is one of `open`, `verified`, `failed`, `waived`.
- **Who may change what** (CONTRACTS §6): outside the systems-engineer role, agents may change only `status`, `evidence` and `tests` here — never requirement text or IDs (that's `writing-requirements`'s and a human's job), and a diff lint enforces it.

## Workflow

1. After a requirement is added (`writing-requirements`), add its `trace.json` entry with empty `design`/`tests`/`evidence` and `status: "open"`.
2. As design and test files land, add their paths to the requirement's `design[]`/`tests[]`.
3. As checks pass and `forge evidence add` runs, append the returned `EV-####` id to `evidence[]` and flip `status` toward `verified` (or `failed`) once the evidence supports it.
4. Run:
   ```
   forge-python ${CLAUDE_SKILL_DIR}/scripts/verify.py --project <root>
   ```
   This writes `out/verify/trace.graph.json` (machine-readable graph) and `out/verify/trace.graph.mmd` (a Mermaid flowchart — paste into any Mermaid renderer to see the graph). Fix every failing measurement using its `remediation` string before calling the gate ready.
5. `forge trace` (CONTRACTS §11, the systems-team command) wraps step 4 for CI and hooks.

## What counts as an orphan

A source file under a conventional design/test directory that no requirement's `design[]`/`tests[]` mentions. Two honest fixes exist: add the missing trace reference, or delete the file if it truly isn't needed. Never add a fake reference just to silence the check — that breaks the graph's meaning for everyone downstream (gate reviews, red-team, evidence rollups).

## What this skill refuses

- Marking a requirement `verified` without a passing check behind it in `evidence/manifest.json`. Status must follow evidence, never the other way round.
- Silently deleting a `trace.json` entry to make an orphan or untested-requirement finding disappear. If a requirement is genuinely obsolete, that is a requirement-text change — flag it to `writing-requirements` and a human, don't erase the trace.
