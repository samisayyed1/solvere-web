# G0 check log

Sections 1-4: first G0 draft (53 requirements, 59 params). Section 5: re-run after the owner's round-2 answers; section 5 is the current state.

Commands run by systems-engineer on 2026-09-25 from the Forge repo root (`/home/user/solvere-web`), with outputs as printed. Tool: spec42 0.53.1 (`~/.forge/bin/spec42 --version`). `forge verify` and `forge evidence` were **not** run (the evidence system was being changed in parallel), so none of these results is in `evidence/manifest.json` yet; they are L1 check results, not recorded evidence.

`$SEED` is a scratch directory outside the repo that holds a copy of the project with one fault seeded; the real project files were not touched by the seeding.

## 1. EARS lint (53 requirements)

```
$ plugins/forge/bin/forge ears --project products/solvere-sense
[FORGE_CHECK_ID_PREFIX] requirements.ears_lint
[PASS] requirements.ears_lint (requirements/requirements.md)
exit 0
```

Seeded fault (copy of `requirements/`; REQ-PWR-003 changed to "The pod shall contain no battery and shall be robust."):

```
$ plugins/forge/bin/forge ears --project $SEED
[FAIL] requirements.ears_lint (requirements/requirements.md)
  - REQ-PWR-003@L145.one_shall = False ... REQ-PWR-003 has 2 'shall' clauses; split it into separate requirements, one 'shall' each.
  - REQ-PWR-003@L145.no_vague_words = False ... REQ-PWR-003 uses vague word(s) ['robust'] ...
exit 1
```

## 2. Trace graph

```
$ plugins/forge/bin/forge trace --project products/solvere-sense
[FORGE_CHECK_ID_PREFIX] requirements.trace_graph
[PASS] requirements.trace_graph (requirements/trace.json)
exit 0
```

Seeded fault (same copy; REQ-MECH-014 entry deleted from `trace.json`):

```
$ plugins/forge/bin/forge trace --project $SEED
[FAIL] requirements.trace_graph (requirements/trace.json)
  - REQ-MECH-014.has_trace_entry = False ... REQ-MECH-014 has no entry in requirements/trace.json. ...
  - REQ-MECH-014.valid_status = False ... REQ-MECH-014 status None is not one of ['failed', 'open', 'verified', 'waived'].
exit 1
```

## 3. SysML model (spec42)

```
$ ~/.forge/bin/spec42 check products/solvere-sense/model --warnings-as-errors
Checked 2 document(s): 0 error(s), 0 warning(s), 0 info(s)
exit 0

$ ~/.forge/bin/forge-python plugins/forge/skills/modeling-systems/scripts/verify.py --project products/solvere-sense
[FORGE_CHECK_ID_PREFIX] systems.sysml_check
[PASS] systems.sysml_check (model)
exit 0
```

Seeded fault A (copy of `model/`; in `system.sysml` `part sensor : SensorKit;` changed to `part sensor : SensorKitMissing;`):

```
$ ~/.forge/bin/spec42 check $SEED/model --warnings-as-errors
.../system.sysml:167:23: warning [unresolved_type_reference] This type reference does not resolve.
.../system.sysml:173:35: warning [unresolved_reference] This reference does not resolve.
.../requirements.sysml:108:26: warning [unresolved_reference] This reference does not resolve.
... (13 more unresolved_reference warnings on pod.sensor.* lines)
Checked 2 document(s): 0 error(s), 16 warning(s), 0 info(s)
exit 1

$ ~/.forge/bin/forge-python plugins/forge/skills/modeling-systems/scripts/verify.py --project $SEED
[FAIL] systems.sysml_check (model)
  - model/system.sysml.unresolved_type_reference.L167C23 = False ... spec42 warning [unresolved_type_reference] at model/system.sysml:167:23: This type reference does not resolve.. Fix the model (warning severity is treated as a failure -- --warnings-as-errors).
  ... (15 more)
exit 1
```

Seeded fault B (copy of `model/`; `satisfy antennaGap by pod.radome;` changed to `pod.radomeX`):

```
$ ~/.forge/bin/spec42 check $SEED2/model --warnings-as-errors
.../requirements.sysml:105:27: warning [unresolved_reference] This reference does not resolve.
Checked 2 document(s): 0 error(s), 1 warning(s), 0 info(s)
exit 1
```

## 4. Params

```
$ plugins/forge/bin/forge params --project products/solvere-sense lint
forge params lint: 59 param(s), 0 error(s)
exit 0
```

## 5. Re-run after the owner's round-2 answers (2026-09-25)

Package now: 66 requirements, 66 planned tests, 67 params, 2 model files. Same tools (spec42 0.53.1). Scratch copies in `$SP` hold the seeded faults; the project files were not touched by the seeding.

```
$ plugins/forge/bin/forge ears --project products/solvere-sense
[PASS] requirements.ears_lint (requirements/requirements.md)
exit 0
$ plugins/forge/bin/forge trace --project products/solvere-sense
[PASS] requirements.trace_graph (requirements/trace.json)
exit 0
$ plugins/forge/bin/forge params --project products/solvere-sense lint
forge params lint: 67 param(s), 0 error(s)
exit 0
$ ~/.forge/bin/spec42 check products/solvere-sense/model --warnings-as-errors
Checked 2 document(s): 0 error(s), 0 warning(s), 0 info(s)
exit 0
$ ~/.forge/bin/forge-python plugins/forge/skills/modeling-systems/scripts/verify.py --project products/solvere-sense
[PASS] systems.sysml_check (model)
exit 0
```

Seeded faults:

```
# A: system.sysml `port fromLed : LedLightPort;` -> `LedLightPortX`
$ ~/.forge/bin/spec42 check $SP/seedA/model --warnings-as-errors
.../seedA/model/system.sysml:157:24: warning [unresolved_type_reference] This type reference does not resolve.
Checked 2 document(s): 0 error(s), 1 warning(s), 0 info(s)
exit 1

# B: requirements.sysml `satisfy lightPipeFlush by pod.lightPipe;` -> `pod.lightPipeMissing`
$ ~/.forge/bin/spec42 check $SP/seedB/model --warnings-as-errors
.../seedB/model/requirements.sysml:123:31: warning [unresolved_reference] This reference does not resolve.
Checked 2 document(s): 0 error(s), 1 warning(s), 0 info(s)
exit 1

# R: REQ-MECH-016 given the word "quickly"; REQ-SYS-003 tests[] emptied
$ plugins/forge/bin/forge ears --project $SP/seedR
[FAIL] requirements.ears_lint -- REQ-MECH-016 uses vague word(s) ['quickly'] ...
exit 1
$ plugins/forge/bin/forge trace --project $SP/seedR
[FAIL] requirements.trace_graph -- REQ-SYS-003 has no tests[] and status is not 'waived' -- it is an untested requirement ...
exit 1

# P: first `status = "datasheet"` changed to "guessed"
$ plugins/forge/bin/forge params --project $SP/seedP lint
[FAIL] mount.height_min: $.status: value 'guessed' not in ['assumed', 'datasheet', 'measured', 'verified']
forge params lint: 67 param(s), 1 error(s)
exit 1
```

## 6. Compliance map via mapping-compliance (2026-09-25)

Profile: `compliance/product-profile.toml`. Generator and check, run as SKILL.md says (`forge-python ${CLAUDE_SKILL_DIR}/scripts/verify.py --project <root>`), from `plugins/forge/`:

```
$ ~/.forge/bin/forge-python skills/mapping-compliance/scripts/verify.py --project /home/user/solvere-web/products/solvere-sense
[FORGE_CHECK_ID_PREFIX] compliance.standards_map
[PASS] compliance.standards_map (compliance/product-profile.toml)
exit 0
# wrote compliance/standards-map.md (11 standards: ul94-flammability, ipc-2221c, eu-rohs, reach-scip,
# fcc-part15, ised-rss, eu-red-cyber, cispr32-35-emc, etsi-en303645, eu-cra, nist-ir8259),
# compliance/test-plan.md, compliance/pre-scan-plan.md
```

Seeded wrong profiles (copies in `$SP/<name>/compliance/product-profile.toml`; `V` = the command above with `--project $SP/<name>`):

```
# cMissing: target_markets line deleted
$ V --project $SP/cMissing
[FAIL] compliance.standards_map -- profile.required_fields: missing required field(s) ['target_markets'].
exit 1

# cBlank: allows_blank_password = true, no mitigation note
$ V --project $SP/cBlank
[FAIL] compliance.standards_map -- tripwire.no_blank_password_unmitigated: EN 18031-1 clause 6.2.5.1/6.2.5.2 gives NO presumption of conformity ...
exit 1

# cTypo: target_markets "EU" -> "EUU"            (requested seed)
$ V --project $SP/cTypo
[PASS] compliance.standards_map
exit 0        # silently maps 6 standards instead of 11: the check CANNOT fail on this

# cNoRadio: has_radio = false while REQ-EMC-002/-004 list radios   (requested seed)
$ V --project $SP/cNoRadio
[PASS] compliance.standards_map
exit 0        # 10 standards instead of 11 (ised-rss dropped): the check CANNOT fail on this
```

Finding: the skill's verify.py checks only the three required fields and the EN 18031 tripwires. It does not validate market codes, and it does not cross-check the profile against the requirements. The fix belongs in `plugins/forge/skills/mapping-compliance` (outside this product repo); until then a human reviews the profile against REQ-EMC-001..005 at each gate.
