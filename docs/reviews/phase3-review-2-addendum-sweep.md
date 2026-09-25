Addendum to phase3-review-2 (the can't-fail sweep): 14 checks pass clearly wrong input, 19 majors (S1–S5, S7–S19) plus K1 and K2 are open; Phase 3 stays FAIL.

# Addendum to phase3-review-2: the "can a check fail?" sweep

- **What was probed:** 17 of the 19 skill `verify.py` entrypoints and the `forge` check subcommands. mapping-compliance was skipped (a fixer is working on it) and `passk` was skipped (still under construction).
- **How:** each probe fed a realistic wrong input of the kind an honest but sloppy agent might produce. Probes and projects are in `/tmp/claude-0/review2/sweep/`. The harness `run.sh` prints the exit code and the status of every `forge.check/1` file.
- **Tree moved during the sweep.** HEAD advanced from 7a7bfa5 to 846cf31 (committed 09:56). Two skill scripts changed in that window: releasing-designs and mapping-compliance. I re-checked the releasing-designs finding (N7) on 846cf31; no other probed skill script changed.
- **Threat model (owner update):** hooks are guardrails against a sloppy agent, not a boundary against a malicious one. Findings that need deliberate evasion are marked **residual (evasion)**.

## Re-rating of review-2 findings under the new threat model, and fixes since
| ID | New status |
|---|---|
| N1 (`rm forge.toml` turns off every hook) | residual (evasion). Still worth an `ask`, since an honest cleanup could delete it. |
| N2 (`git update-index --assume-unchanged`) | residual (evasion) |
| N4 (judge runs commands via `git grep -O`) | residual (evasion) |
| N8 (`cp -l` hard link into `evidence/`) | residual (evasion) |
| N3 (`.gitignore` hides new design files) | residual (evasion); minor at most |
| N5 (hooks find the project only from the payload `cwd`) | minor. The platform normally resets `cwd` into the project. |
| N6 (an agent can mark a param `verified` itself) | stays **major**. An honest agent may well mark a value verified after running checks. |
| N11 (`git commit --amend` on the fresh scaffold commit empties the gate's diff) | raised to **major**. `--amend` is an ordinary habit, and the gate then silently loses the change. |
| N7, N10, N13 | **FIXED at 846cf31**. p9's superseded fail entry now gives `clean`. The template `trace.json` placeholders are waived with a reason. INSTALL-LOG has 0 `samisayyed` hits. |

## Per-skill results
In the "Can fail?" column, "Yes" means every wrong input I tried was caught; "No" means at least one was not.

| Skill / command | Probe | Expected | Actual | Can fail? | Severity |
|---|---|---|---|---|---|
| all 19 skill entrypoints | empty project | explicit SKIP | `[SKIP] …`, exit 0, no check file | Yes | — (roll-up is known K2) |
| checking-ecad | garbage `ecad/x.kicad_sch` (kicad-cli: "Failed to load schematic", rc 3) | ERROR | **PASS** with erc_errors = 0 | No | major (S1) |
| writing-requirements | "at least 300 g and at most 200 g" | FAIL | **PASS** | No | major (S2) |
| writing-requirements | heading `## REQ-mech-5` (bad ID) | FAIL | **SKIP**: "no requirements found" | No | major (S2) |
| writing-requirements | duplicate ID, unit typo `gg`, `Verify: tets`, vague words, no Rationale | FAIL | FAIL | Yes | — |
| tracing-requirements | `tests` names a file that does not exist; `design` names `cad/nope.py` | FAIL | **PASS** | No | major (S3) |
| tracing-requirements | `status = "verified"` with `evidence = []`; `status = "failed"` | FAIL | **PASS** | No | major (S3) |
| tracing-requirements | `waived` with no reason; trace entry for a requirement not in requirements.md | FAIL | **PASS** | No | minor (S3) |
| modeling-systems | empty `system.sysml`, or comment only | SKIP | **PASS** | No | major (S4) |
| modeling-systems | syntax error; unresolved type | FAIL | FAIL | Yes | — |
| gardening-docs | broken reference-style link `[b][ref]`; missing image `![x](img/missing.png)` | FAIL | **PASS** | No | major (S5) |
| gardening-docs | broken inline link, anchor, wrong case, missing directory | FAIL | FAIL | Yes | — |
| verifying-geometry | family typo; key typo `min_mn`; missing module; min_wall set 0.001 mm above the real wall | ERROR / FAIL | ERROR / FAIL | Yes | — |
| verifying-geometry | `requirement = "REQ-MECH-999"` (no such requirement) | FAIL | PASS | No | minor (S6) |
| checking-dfm | process typo `fmd`; rule typo; material typo; negative thickness; taper typo; unmapped rule | ERROR | ERROR (rc 2) | Yes | — |
| stacking-tolerances | direction 2, distribution typo, negative tolerance, 0.001 past the worst case, no contributors | ERROR / FAIL | ERROR / FAIL | Yes | — |
| stacking-tolerances | `unit = "mn"` or `"in"`; contributor nominals disagree with params.toml | FAIL | **PASS** (never checked against params) | No | major (S7) |
| running-fea | ν = 0.6, E < 0, force 0, one mesh level, missing yield | ERROR | ERROR | Yes | — |
| running-fea | `min_safety_factor = 0.5`; `deflection_tolerance_pct = 500`; `convergence_tol_pct = 100` | FAIL (out of sane bounds) | **PASS** | No | major (S8) |
| running-fea | E = 210 while the material is named steel (GPa/MPa slip) | FAIL | PASS | No | minor (S8) |
| designing-circuits | no limits file; empty limits; name typo; no bound; key typo `maxx`; 0.0001 past the limit | ERROR / FAIL | ERROR / FAIL | Yes | — |
| designing-circuits | `unit = "mV"`, `max = 40` against a 50 mV (0.05 V) ripple | FAIL | **PASS**, recorded as "0.0499923 mV" | No | major (S9) |
| building-firmware | `firmware/src/main.c` has a syntax error and there are no tests | FAIL (compile rung) | **SKIP** | No | major (S10) |
| inspecting-renders | all 10 answers `"no"`, deviations `"none found"` | FAIL | **PASS** | No | major (S11) |
| inspecting-renders | renders are always a hard-coded demo plate and pin, never `cad/` (`render.py:57-75`) | FAIL | PASS | No | major (S11) |
| inspecting-renders | half the questions answered; question-id typo; no answers file | FAIL | FAIL | Yes | — |
| rendering-products | renders `_build_part` (a parametric box), never the project's part; not disclosed in SKILL.md | FAIL | PASS | No | major (S12) |
| intaking-datasheets | "Length: 2.56 in" with pattern `([\d.]+)` and `unit = "mm"` | FAIL | **PASS**, param written as 2.56 mm | No | major (S13) |
| intaking-datasheets | no page marker; would overwrite a verified param | FAIL | FAIL; the verified value is kept | Yes | — |
| drafting-drawings | `tol_minus_mm = -0.10`; `scale = "1:0"` | FAIL | **PASS** | No | major (S14) |
| drafting-drawings | dimension 81 vs a real 80 | FAIL | FAIL | Yes | — |
| exploring-concepts | the file sets `minimum_concepts = 1` and has 1 concept; score 50 on a −2…+2 scale | FAIL | **PASS** | No | major (S15) |
| exploring-concepts | no datum; duplicate concept names | FAIL | PASS | No | minor (S15) |
| analyzing-risk | S = O = D = 10 with action `TBD`, owner `?`, due `someday`; due date 2001 | FAIL | **PASS** | No | major (S16) |
| analyzing-risk | S = 11, blank S, whitespace action | FAIL | FAIL | Yes | — |
| costing-bom | price −0.30; blank MPN; alternate equals its own MPN | FAIL | **PASS** | No | major (S17) |
| costing-bom | duplicate ref_des; blank lead time; risk_note `x` | FAIL | PASS | No | minor (S17) |
| `forge params lint` | `datasheet` source with no page; unit `mmm`; value `"2.0mm"` (a string); verified with evidence `EV-9999` that does not exist | FAIL | **rc 0, 0 errors** | No | major (S18) |
| `forge params lint` | status typo; negative tolerance; no source; bare value | FAIL | rc 1 | Yes | — |
| `forge evidence status` | mech: verifying-geometry FAIL, then checking-dfm N/A | mech FAIL | **"mech: pass L0 VERIFIED"** | No | major (S19) |
| `forge lint agents` / `skills` | judge given Write; judge on haiku; model typo; `disable-model-invocation: false` | FAIL | FAIL | Yes | — |
| `forge lint skills` | `context: frok` | FAIL | PASS | No | minor (S20) |
| `forge lint claudemd` | 150-line CLAUDE.md | FAIL | FAIL | Yes | — |
| `forge lint wording` | "validated" or "Certified" without a level | FAIL | FAIL | Yes | — |
| `forge lint wording` | "prod-ready", "ready for production" | FAIL | PASS | No | minor (S20) |
| `forge ears` / `forge trace` | wrap the skill scripts | as the skill rows | same as S2 and S3 | — | — |

## Findings
| ID | Sev | file:line | Defect | Fix |
|---|---|---|---|---|
| S1 | major | `checking-ecad/scripts/verify.py:137-138,179-181` | `run_kicad_cli` ignores the exit code. When no report file is written, `report = {}` gives 0 errors and a PASS. | Treat any exit other than 0 or 5 (violations), or a missing report, as ERROR. |
| S2 | major | `writing-requirements/scripts/verify.py` | A min above its max is not checked. A heading that does not match the ID pattern drops the requirement silently, which can end in SKIP. | Flag contradictory bounds. Treat any `## REQ…`-like heading that fails the pattern as an error. |
| S3 | major | `tracing-requirements/scripts/verify.py:204` | `tests[]` and `design[]` paths are never checked to exist. `verified` needs no evidence and `failed` passes. `waived` needs no reason. Ghost requirement IDs are accepted. | Check that paths exist; require evidence for `verified`; fail on `failed`; require a reason on `waived`; reject IDs not in requirements.md. |
| S4 | major | `modeling-systems/scripts/verify.py` | An empty model, or one with only a comment, passes. | No definitions should give SKIP or FAIL. |
| S5 | major | `gardening-docs/scripts/verify.py` | Reference-style links and images are not checked. | Resolve both kinds. |
| S7 | major | `stacking-tolerances/scripts/stack_math.py:123` | `unit` is free text. Contributor nominals are typed by hand and never compared with params.toml, although SKILL.md:13 says "tolerances come from params/params.toml". | Add a unit vocabulary and a `param = "a.b"` binding that is checked against params.toml. |
| S8 | major | `running-fea/scripts/verify.py` | The maker sets its own acceptance bounds with no ceiling or floor (SF 0.5, tolerance 500 %, convergence 100 %). | Hard floor SF ≥ 1 and ceilings (hand-calc ≤ 10 %, convergence ≤ 5 %) unless a signed waiver exists. Add a material E plausibility band. |
| S9 | major | `designing-circuits/scripts/verify.py:182-199` | The limit's `unit` is only a label. A limit written in mV is compared with a value in volts. | Normalise SI prefixes, or require the base unit. |
| S10 | major | `building-firmware/scripts/verify.py` | When there are no tests, nothing under `firmware/src` is ever compiled. The brief says `firmware/` → compile. | Always compile `src/`; only the test rung should SKIP. |
| S11 | major | `inspecting-renders/scripts/verify.py:126-144`; `render.py:57-75` | A `"no"` answer (a deviation) passes alongside "none found". The renders are never of the project's part. | FAIL when an answer is `"no"` and there is no matching deviation note. Render the spec's `cad/` module or STEP file, and refuse the demo geometry. |
| S12 | major | `rendering-products/scripts/render_pack.py:33-58`; `verify.py:168` | The render pack draws a box, not the design, and SKILL.md does not say so. | Load the part named in the spec. |
| S13 | major | `intaking-datasheets` scripts | The unit is taken from the spec, never from the datasheet text. | Capture the unit from the text and compare it. |
| S14 | major | `drafting-drawings/scripts/drawspec.py` | Negative tolerances and a degenerate scale are accepted. The legacy `[part]` spec draws dimensions typed by hand, not the design. | Validate tolerance ≥ 0 and the scale; require `[model]`. |
| S15 | major | `exploring-concepts/scripts/verify.py:63` | The input can lower its own minimum below the brief's N. Score range, datum and duplicate names are not checked. | Floor `minimum_concepts` at 3 (2 for the tournament). Validate the score scale, require a datum, require unique names. |
| S16 | major | `analyzing-risk/scripts/verify.py:88-90` | The action, owner and due date only need to be non-empty. | Parse the due date as ISO; reject placeholders (TBD, ?, n/a); flag overdue dates. |
| S17 | major | `costing-bom/scripts/verify.py:101` | A negative price, a blank MPN, and an alternate equal to the part's own MPN (which hides single-sourcing) all pass. | Validate each. Also flag duplicate ref_des and blank lead time (minor). |
| S18 | major | `schemas/params.schema.json`; `commands/params.py` lint | A `datasheet` param needs no page ref (CONTRACTS §2 requires one). `value` can be a string. There is no unit vocabulary. Evidence IDs are not checked against the manifest. | Add each rule to the schema or lint. |
| S19 | major | `lib/forge/commands/evidence.py:114-119` | `status` shows only the newest entry per domain, so a later N/A or pass hides a failing sibling. Judges use this command. | Report per (domain, entrypoint) and roll up as the worst result. |
| S6, S20 | minor | `verifying-geometry` spec loader; `lintlib/skills.py`, `lintlib/wording.py` | Requirement IDs in specs are not cross-checked. `context:` values are not validated. Phrasings like "ready for production" and "prod-ready" are missed. | Cross-check IDs, validate enums, extend the phrase list. |
| K1 | major | `mapping-compliance` (known) | Unknown market `EUU` passes. A radio mismatch passes. UK rows, RED core, EN 301 489 and harmonised spectrum standards are missing. IEC 62368-1 is triggered on mains only. | Fixer in progress. |
| K2 | major | `lib/forge/commands/verify.py` (known) | `forge verify` claimed PASS and recorded last-green with zero check files. On 7a7bfa5, `cad/bracket.py` = "not python (((" gave `[PASS] mech/*` and Stop 0. On 846cf31 this shows `[N/A]`, so it is partly addressed. | Record N/A with no last-green; the Stop gate should say "nothing verified". |
| K3 | minor | new-project scaffolder (known) | Copies gitignored template artefacts such as `out/verify/gardening.docs.json`. | Skip gitignored template files. `template_files.py` was added at 846cf31; re-check it. |

## Addendum verdict
- **Can fail:** 6 skill entrypoints held on every probe: checking-dfm, verifying-geometry (except the minor ID cross-check), stacking-tolerances (except the unit/params gap), designing-circuits (except the unit gap), building-firmware (when tests exist), and the agent and skill lint rules.
- **Pass wrong input:** 14 checks pass at least one clearly wrong input, in the major findings S1–S5 and S7–S19.
- **Overall:** Phase 3 stays FAIL. S1–S19 add to the open majors N6 and N11 and the known K1 and K2.

Verdict: FAIL
