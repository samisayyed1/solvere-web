# NodeLink power board rev A -- test plan

| ID | Covers | Method | Pass criterion |
|---|---|---|---|
| TP-01 | REQ-ELEC-001, REQ-ELEC-002 | Electronic load, 12 V +/-10 % | rails within 3 % |
| TP-02 | REQ-ELEC-003 | Thermal analysis + IR camera at 60 C | Tj < 125 C |
| TP-04 | REQ-ELEC-005 | IEC 61000-4-2 contact, +/-8 kV, J2 pins | no damage, comms OK |
| TP-05 | REQ-MECH-001 | 20 N pull on pigtail, 10 s | joints intact |
