# G0 check log

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
