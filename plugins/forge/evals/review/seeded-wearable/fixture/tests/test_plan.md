# PulseBand rev B -- test plan

| ID | Covers | Method | Pass criterion |
|---|---|---|---|
| TP-01 | REQ-SYS-001 | 20 subjects at rest vs ECG reference | error <= 5 bpm |
| TP-02 | REQ-MECH-001 | Inspect print traveller | Tough 2000, SLA |
| TP-03 | REQ-MECH-002, REQ-MECH-003 | Stack-up analysis + CT scan of 3 EVT units | no cell contact; gap 0.05-0.40 mm |
| TP-04 | REQ-MECH-004 | 20 N axial pull on tether, 10 s, 5 units | continuity unchanged |
| TP-05 | REQ-ELEC-001, REQ-ELEC-003 | Bench load 180 mA at 40 C, thermocouple on regulators | 3.3 V within 3 %; Tj estimate < 105 C |
| TP-06 | REQ-SW-001 | 5 units, scripted usage profile | >= 5 days |
