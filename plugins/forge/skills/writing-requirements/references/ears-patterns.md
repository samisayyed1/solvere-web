# EARS pattern reference and common lint failures

Source of the six-pattern taxonomy: Mavin, Wilkinson, Harwood & Novak, "Easy
Approach to Requirements Syntax (EARS)", RE'09, DOI 10.1109/RE.2009.9 (see
`docs/research/R5b-standards-safety-risk-se.md`). Examples below are original
to Forge, for a fictional handheld soil-moisture sensor "HydroSense" and the
DripGuard puck used in SKILL.md.

## Worked examples, one per pattern

**Ubiquitous** (always active, no trigger keyword):
```
## REQ-SYS-001

The HydroSense sensor shall store each moisture reading with a UTC timestamp.

Rationale: field agronomists need a defensible time series for irrigation
scheduling decisions.
Verify: test
```

**Event-driven** (`When <trigger>`):
```
## REQ-SYS-002

When the user presses the Measure button, the HydroSense sensor shall
display a moisture reading within 2 s.

Rationale: stakeholder interview SPEC.md §3.2 — a slow response was the top
complaint about the previous generation.
Verify: test
```

**State-driven** (`While <state>`):
```
## REQ-ELEC-010

While battery charge is below 10 %, the HydroSense sensor shall disable the
display backlight.

Rationale: preserves 48 h of runtime margin per the power budget in
model/system.sysml.
Verify: analysis
```

**Unwanted behaviour** (`If <trigger>, then`):
```
## REQ-SYS-015

If the probe temperature is outside -20 degC to +60 degC, then the
HydroSense sensor shall mark the reading as invalid.

Rationale: probe accuracy is unspecified by the vendor datasheet outside
this range (params/params.toml probe.temp_range).
Verify: test
```

**Optional feature** (`Where <variant>`):
```
## REQ-SYS-020

Where the Bluetooth module is fitted, the HydroSense sensor shall send
stored readings to a paired phone on request.

Rationale: BLE is a build option per the product family SPEC.md; the base
SKU has no radio.
Verify: demo
```

**Complex** (combined keywords):
```
## REQ-FW-030

While field-logging mode is active, when the sampling interval elapses, the
HydroSense sensor shall record a reading to flash memory.

Rationale: continuous logging must not depend on a live BLE connection.
Verify: test
```

## Common lint failures and how to fix them

| Finding | Bad | Fixed |
|---|---|---|
| Two `shall` clauses | "The puck shall detect leaks and shall alert the user." | Split into REQ-...-010 (detect) and REQ-...-011 (alert). |
| Vague word | "The UI shall be fast and user-friendly." | "When the Measure button is pressed, the sensor shall display a reading within 2 s." (drop the adjectives; state the number.) |
| Bare number | "The enclosure shall have a wall thickness of at least 2." | "...at least 2.0 mm." — every number needs a unit; use `unit = "1"` in params.toml for a genuinely unitless count, and spell it out in prose ("at least 3 retries"). |
| Missing Rationale | (sentence only, no Rationale: line) | Add one sentence: what stakeholder need, standard clause or system budget this traces to. |
| Wrong Verify value | `Verify: manual` | `Verify: inspection` (not manual/visual/other — only inspection, analysis, demo, test). |
| No EARS keyword | "The system is fast." | Not a requirement at all — restate as an event/state/ubiquitous EARS sentence with a measurable response. |
| Reused ID | Two blocks both headed `REQ-MECH-004` | Renumber the second one to the next free MECH id. |

## Choosing an area code

Use the domain the requirement is *owned by*, not where it happens to be
implemented: `SYS` (system-level, cross-domain), `MECH`, `ELEC`, `FW`, `SW`,
`SIM`, `MFG`, `COMPLY`. A requirement that constrains more than one domain
(e.g. a thermal budget that drives both mechanical and electrical choices)
is `SYS` and gets decomposed into domain-specific child requirements later,
each tracing back to it in `trace.json`.
