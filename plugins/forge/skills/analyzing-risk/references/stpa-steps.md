# STPA walkthrough (MIT PSASS Handbook, Leveson & Thomas, March 2018)

Source: `docs/research/R5b-standards-safety-risk-se.md` §"STPA Handbook
(MIT, March 2018)". Free PDF at https://psas.scripts.mit.edu/home/get_file.php?name=STPA_Handbook.pdf.
This reference paraphrases the four steps in Forge's own words with an
original worked example (a fictional handheld soil-moisture sensor,
"HydroSense") — it does not reproduce handbook text.

## Step 1 — Define the purpose of the analysis

- **Losses**: state what stakeholders will not accept, in their language, not the system's. Example: "L-1: a field operator is injured by the probe," "L-2: crop irrigation decisions are made from corrupted data."
- **System boundary**: what's inside (the sensor, its firmware, the companion app) vs. outside (the irrigation controller it feeds, the operator).
- **System-level hazards**: states that could lead to a loss, e.g. "H-1: the probe delivers an electrical shock to the operator," "H-2: the sensor reports a moisture reading outside its calibrated accuracy without flagging it as invalid."
- **Safety constraints**: the inverse of each hazard, e.g. "SC-1: the probe shall never present a shock hazard to the operator during normal handling."

## Step 2 — Model the control structure

A hierarchical diagram of **controllers** (a person or component issuing commands), the **control actions** they send, the **controlled process**, and the **feedback** they receive back. Start with one box per major actor and refine only where a hazard analysis needs more detail.

```
[Operator] --(Measure command)--> [Firmware Controller] --(drive ADC, power probe)--> [Probe hardware]
    ^                                     |
    |<---(display reading, alarm)---------|
                                          [Feedback: probe temperature, battery voltage]
```

## Step 3 — Identify unsafe control actions (UCAs)

For each control action, check the four (sometimes five) ways it can be hazardous:

| Control action | Not given | Given | Given too early / late / out of order | Stopped too soon / applied too long |
|---|---|---|---|---|
| "Power the probe" | Sensor can't measure (not usually hazardous alone) | Powering while probe is submerged past its rated depth is hazardous (H-1) | Powering before a self-test completes could apply full voltage to a faulted probe (H-1) | Leaving power applied after a fault is detected keeps a shock path live (H-1) |

Each hazardous cell becomes a **controller constraint**, e.g. "C-1: the firmware controller shall not power the probe until self-test confirms no ground fault."

## Step 4 — Identify loss scenarios

For each UCA, ask two questions:
1. **Why might the controller issue the unsafe control action?** Bad feedback (a stuck sensor reads "dry" when wet), a wrong process model (firmware assumes the probe is always dry-mated), flawed logic (a race condition skips the self-test).
2. **Why might a *correct* command not be carried out?** Actuator fault (the power MOSFET welds closed), process fault (a cracked probe housing lets water bypass the intended seal).

Each scenario should point at a `writing-requirements` REQ id it drives (either an existing one it should trace to, or a new one to write), e.g.:

| Scenario | Derived requirement |
|---|---|
| Firmware's self-test can pass on a shorted ground-fault detector, masking the fault | REQ-FW-041 (self-test shall include a ground-fault-detector functional check, not just a presence check) |

## Recording STPA output

Write `analysis/stpa.md` with four sections matching the four steps above: Losses & Hazards, Control Structure, UCA Table, Loss Scenarios & Derived Requirements. There is no automated STPA checker — this is structured engineering judgement. The requirement IDs it derives are checked as normal by `writing-requirements` (EARS form) and `tracing-requirements` (traced to design/tests/evidence).
