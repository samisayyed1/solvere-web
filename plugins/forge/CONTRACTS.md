# Forge contracts

These are the interfaces every Forge component must honour. Skills, hooks, agents, workflows and evals are built in parallel by different agents, and this file is what makes them fit together. A change here needs an ADR. The schemas live in `schemas/`, and `forge` tooling validates against them.

## 1. Paths

**Plugin** (`plugins/forge/`):

| Path | Contents |
|---|---|
| `.claude-plugin/plugin.json` | The manifest. Use the default component folders, and don't declare `hooks` or `agents` keys (ADR-001 §3). |
| `agents/<name>.md` | Agents, referred to as `forge:<name>` in hooks and matchers. |
| `skills/<gerund-name>/SKILL.md` | One skill per folder, with `references/` and `scripts/`. |
| `hooks/hooks.json` and `hooks/*.py` | Hook scripts, all run through `hooks/_failclosed.py`. |
| `workflows/<name>.js` | Workflows, invoked as `/forge:<meta.name>`. |
| `output-styles/engineering-report.md` | The report output style. |
| `bin/forge`, `bin/forge-mcp-guard` | CLIs. Shared library code lives in `lib/forge/`. |
| `schemas/*.schema.json` | JSON Schema, draft 2020-12. |
| `toolchain/` | Pinned tools; `manifest.json` is what `forge doctor` checks. |
| `evals/` | The `claude plugin eval` suite. |
| `tests/` | Pytest for everything with logic. |

**Product repo** (scaffolded from `templates/project/` by `/forge:new-project`):

```
CLAUDE.md (TOC, ≤100 lines)  AGENTS.md  ASSUMPTIONS.md  RISKS.md  Makefile  .claude/{settings.json,rules/}
requirements/  requirements.md (EARS) + trace.json          model/     *.sysml
params/params.toml  (single source of truth for every dimension/value)
cad/  ecad/  firmware/  app/  analysis/  mfg/  bom/  compliance/  tests/
evidence/manifest.json   reviews/  (G0.md … G6.md, verdicts are in the gate records)
docs/decisions/   release/   out/  (build + check outputs; gitignored except out/verify/*.json when promoted to evidence)
```

## 2. Params (`params/params.toml`)

Every dimension and value that appears in CAD, ECAD, firmware or analysis comes from here. Nothing is hard-coded in the source.

```toml
[enclosure.wall_thickness]
value = 2.0
unit = "mm"
tol = { minus = 0.1, plus = 0.1 }
status = "assumed"            # assumed | datasheet | measured | verified
source = "R5d FDM min wall 0.8–1.2 mm; chosen 2.0 for stiffness"   # required, with a page ref for datasheets
verified_by = ""              # human name, required when status = "verified"
evidence = []                 # evidence entry ids, required when status = "verified"
```

- Changing a `verified` value requires a sourced justification (`--justification "…"` via `forge params set`), and the PreToolUse hook blocks direct edits.
- Units must be explicit. Unitless values use `unit = "1"`.

## 3. Check result (`schemas/check-result.schema.json`)

- Every check script writes `out/verify/<check_id>.json` and prints a short human summary.
- **Exit codes:** `0` pass, `1` fail, `2` internal error. Errors must never print "pass".
- Use `lib/forge/checkresult.py`; don't hand-roll the format.
- Every failing measurement carries a `remediation` string: the rule, measured vs required with units, and how to fix it.
- Every new check ships with a test proving it fails on a seeded-wrong input.

```json
{"schema": "forge.check/1", "check_id": "geometry.min_wall", "target": "cad/enclosure.py",
 "status": "fail", "level": "L1",
 "measurements": [{"name": "min_wall", "value": 1.62, "unit": "mm", "limit": {"min": 2.0},
   "pass": false, "requirement": "REQ-MECH-004",
   "remediation": "Wall at lid lip is 1.62 mm < 2.0 mm (params enclosure.wall_thickness, FDM rule R5d). Thicken the lip or reduce the fillet offset."}],
 "tool_versions": {"build123d": "0.11.1"}, "git_sha": "…", "started": "2026-09-25T10:00:00Z", "duration_s": 1.4}
```

## 4. Evidence manifest (`evidence/manifest.json`, `schemas/evidence.schema.json`)

- It is append-only, written through `lib/forge/evidence.py` (`forge evidence add …`).
- Each entry records: `id` (EV-0001…), `artifact`, `domain` (mech|elec|fw|sw|sys|sim|mfg|compliance), `claim`, `check_ids[]`, `result` (pass|fail), `level` (L0–L5), `evidence_files[]`, `inputs_sha256`, `tool_versions{}`, `git_sha`, `model`, `timestamp`, and `status` (VERIFIED|UNVERIFIED).

| Level | Meaning |
|---|---|
| L0 | claimed |
| L1 | computed or measured in CAD/ECAD |
| L2 | simulated, with a hand-calc and a convergence check |
| L3 | independently reviewed (evaluator verdict PASS) |
| L4 | physically tested, with data attached |
| L5 | certified, or signed by a qualified human |

**Wording rule:** "validated" needs L4 or higher, and "certified" or "production-ready" needs L5. `forge lint wording` enforces it on `reviews/`, `docs/`, `release/` and reports.

## 5. Reviewer verdict (`schemas/verdict.schema.json`)

- Reviewer agents (`forge:verification-evaluator`, `forge:red-team` and specialist reviews) end their final message with exactly one fenced `json` block holding this object.
- The SubagentStop hook parses `last_assistant_message` and blocks with the schema errors if it's missing or invalid.

```json
{"schema": "forge.verdict/1", "reviewer": "verification-evaluator", "gate": "G2", "subject": "enclosure rev B",
 "criteria": [{"id": "REQ-MECH-004", "verdict": "FAIL", "evidence": ["out/verify/geometry.min_wall.json"],
   "finding": "Lid lip wall 1.62 mm below 2.0 mm minimum.", "severity": "major",
   "affects": ["manufacturability", "function"]}],
 "overall": "FAIL", "summary": "1 major defect; 11 criteria PASS.", "not_checked": ["thermal (no analysis yet)"]}
```

- `verdict` is one of PASS, FAIL or BLOCKED. BLOCKED means evidence is missing and the reviewer can't judge. `overall` is PASS only if every criterion is PASS.
- `severity` is one of critical, major or minor.
- `affects` must contain at least one of: requirements, safety, fit, function, manufacturability, cost. Style-only notes go in `summary`, never in `criteria`.

## 6. Requirements (`requirements/requirements.md`, `requirements/trace.json`)

- **Format:** each requirement is one EARS sentence with an ID `REQ-<AREA>-<NNN>`, plus `Rationale:` and `Verify:` lines. `Verify:` is one of inspection, analysis, demo or test.
- **`trace.json`** maps each requirement to its `design[]`, `tests[]`, `evidence[]` and `status` (open|verified|failed|waived).
- **Who may change what:** outside the systems-engineer role, agents may change only `status`, `evidence` and `tests`. Requirement text and IDs belong to systems-engineer and humans (enforced by a diff lint).
- **Lints:** `forge lint ears` checks EARS form, and `forge trace` fails on orphans, untested requirements and dangling evidence.

## 7. Gates (`reviews/Gx.md`)

- Each gate record contains: criteria, evidence links, the evaluator verdict (the JSON), red-team findings, open risks, and a sign-off block:
  ```
  Human sign-off: ____________  Name: ____  Date: ____  Decision: PASS / FAIL
  ```
- The sign-off is always left blank by Claude. Only a human fills it in, and the PreToolUse hook blocks agent edits to a filled sign-off line.

## 8. Hooks

- **Scripts:** Python 3 standard library only, invoked as `python3 "${CLAUDE_PLUGIN_ROOT}/hooks/<name>.py"` through the `_failclosed.py` wrapper.
- **Failure:** any exception exits 2 with a reason.
- **Timeouts:** every hook sets a timeout. PreToolUse runs in ≤ 1 s, and PostToolUse checks in ≤ 30 s.
- **Identity:** `agent_type` values for Forge agents look like `forge:<name>`.
- **Tests:** every hook has fixture tests in `tests/hooks/` that pipe JSON to stdin and assert the exit code and output. That includes a sabotaged input that must block.
