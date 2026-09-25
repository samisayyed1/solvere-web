---
name: modeling-systems
description: Write and validate a SysML v2 textual systems model (structure, interfaces, requirements linkage, budgets) at model/system.sysml, checked by the spec42 parser/validator. Use when the user asks for a systems model, architecture diagram as code, interface definition, part/port/connection structure, or when model/**/*.sysml needs validation. Also fires from the systems.md path rule on model/**. Do NOT use this for EARS requirement text (see writing-requirements) or for CAD geometry (see modeling-cad-parts) — SysML here is structural/architectural, not dimensioned.
paths:
  - "model/**"
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(${CLAUDE_SKILL_DIR}/scripts/verify.py:*), Bash(forge-python ${CLAUDE_SKILL_DIR}/scripts/verify.py:*), Bash(spec42:*)
---

# Modeling systems

**Non-negotiable rules, read first:**
1. `model/**/*.sysml` is the single source of truth for system structure (parts, ports, connections, interfaces, item flows) and budgets (power, mass, thermal, cost, link margin as `attribute` values or `calc`/`constraint` blocks) — never duplicate this structure as prose in CLAUDE.md or a doc.
2. Every model file must pass `spec42 check --warnings-as-errors` with zero errors and zero warnings before it is considered done. A model that "looks right" but has an unresolved reference is not validated — the parser is the check that can fail.
3. Requirements referenced from the model (via `satisfy`/`requirement` usages) must use the exact `REQ-<AREA>-<NNN>` IDs from `requirements/requirements.md` — never invent a parallel ID scheme.
4. Build stepwise: model a feature, run the checker, then add the next feature. Never write a large model blind and check it once at the end.

## Workflow

1. Sketch the system boundary and top-level parts as `part def` / `part` declarations.
2. Add `port def`/`port` and `connection`/`interface` usages for every interface the requirements or the industrial-designer/electrical-engineer need.
3. Add budgets as `attribute` values with units (SI; mm for geometry per CONTRACTS §10), sourced from `params/params.toml` where a concrete number already exists there — the model should reference or mirror `params.toml`, never contradict it.
4. Link requirements with `satisfy` relationships where the tooling/library supports it; otherwise record the linkage in `requirements/trace.json` (`tracing-requirements` owns that file).
5. Run:
   ```
   forge-python ${CLAUDE_SKILL_DIR}/scripts/verify.py --project <root>
   ```
   Fix every diagnostic — `spec42` prints the exact line, column and a `remediation`-wrapped message per finding. Re-run until it exits 0.

## Conventions

- One `package` per file, file name matches the package's primary concept in `snake_case.sysml`.
- Keep files under ~200 lines; split a growing model into multiple files under `model/` (spec42 resolves the whole directory).
- Never suppress a diagnostic by renaming or deleting the reference it complains about without checking whether something else in the model depended on it — re-run the full check, not just the file you touched.
- If `spec42` reports a library-resolution warning that looks spurious, do not add `--no-stdlib` or `--strict-diagnostics` to silence it without understanding why; ask if unsure. The check always runs with `--warnings-as-errors` — a model with warnings is not done.

## What this skill refuses

- Marking a model "validated" from a clean `spec42 check` alone — CONTRACTS' L0–L5 ladder puts a syntax/structure check at L1. Physical or simulated validation of the budgets it encodes needs `running-fea` or hardware evidence, and the word "validated" needs L4+ (CONTRACTS §4).
- Modeling geometry dimensions here — that is `cad/` and `modeling-cad-parts`'s job; SysML here stays structural and parametric via `params.toml` references, not a second CAD tool.

See `references/sysml-conventions.md` for a longer worked example and the tool's own diagnostic categories.
