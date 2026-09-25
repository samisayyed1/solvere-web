# Verification plan (G0 draft)

Planned tests, one per requirement in `requirements/requirements.md`. **None of these tests has been run.** Each entry names the gate by which it is expected, the method, and the pass criterion. Evidence is recorded in `evidence/manifest.json` as each test runs; `requirements/trace.json` points here until real test scripts or reports replace these entries.

Numbers here come from the requirements and `params/params.toml`; see those for sources and assumptions.

## TP-SYS-001

- Requirement: REQ-SYS-001
- Method: test
- Planned by: G3/G4
- Procedure and pass criterion: Mount pod at 2.2 m and at 3.0 m. Stage a fall with a test person or fall dummy at each corner and at the centre of a 3.0 m x 3.0 m square centred below the pod. Pass: a fall event is reported for every position at both heights. Protocol (repeats, dummy, room furnishing) to be agreed with the owner.

## TP-SYS-002

- Requirement: REQ-SYS-002
- Method: test
- Planned by: G2/G3
- Procedure and pass criterion: A/B test: bare MR60FDA2 kit vs the kit inside the assembled pod (FDM PETG, then demo material). Same room, same test points on a grid out to 6 m. Pass: the pod reports presence at every point where the bare kit does. Also run on radome coupons of candidate thickness before G2.

## TP-MECH-001

- Requirement: REQ-MECH-001
- Method: demo
- Planned by: G3
- Procedure and pass criterion: Install the base plate on a drywall test panel with the specified anchors; fit the pod. Pass: pod installed per instructions, base plate firm.

## TP-MECH-002

- Requirement: REQ-MECH-002
- Method: demo
- Planned by: G3
- Procedure and pass criterion: Install the base plate on a concrete test block with the specified plugs; fit the pod. Pass: installed per instructions.

## TP-MECH-003

- Requirement: REQ-MECH-003
- Method: demo
- Planned by: G3
- Procedure and pass criterion: Clip the T-bar adapter to a drop-ceiling grid sample of each width the owner names (Q-11). Pass: pod held, tile not drilled or cut.

## TP-MECH-004

- Requirement: REQ-MECH-004
- Method: test
- Planned by: G3
- Procedure and pass criterion: Weigh the installed pod (g). Apply a static downward pull of 4 x that weight to the installed pod for 60 s on drywall, concrete and T-bar samples. Pass: no detachment. Load factor per A-003.

## TP-MECH-005

- Requirement: REQ-MECH-005
- Method: test
- Planned by: G3
- Procedure and pass criterion: Weigh shell plus sensor kit. Apply 4 x that weight downward on the shell for 60 s. Pass: shell stays attached.

## TP-MECH-006

- Requirement: REQ-MECH-006
- Method: inspection
- Planned by: G1/G2
- Procedure and pass criterion: Inspect the CAD and the printed shell: no screw passes through the shell.

## TP-MECH-007

- Requirement: REQ-MECH-007
- Method: inspection
- Planned by: G2
- Procedure and pass criterion: Inspect CAD section views and a printed v1 part: groove continuous around the full shell-to-base perimeter.

## TP-MECH-008

- Requirement: REQ-MECH-008
- Method: inspection
- Planned by: post-v1
- Procedure and pass criterion: With the bathroom gasket fitted and the shell attached, inspect sections or a cut sample: gasket seated and compressed around the full perimeter within the gasket datasheet range.

## TP-MECH-009

- Requirement: REQ-MECH-009
- Method: inspection
- Planned by: G3
- Procedure and pass criterion: Measure the angle between the sensor PCB plane and the base-plate mounting face with an inclinometer or CMM. Pass: 5 deg or less.

## TP-MECH-010

- Requirement: REQ-MECH-010
- Method: inspection
- Planned by: G2
- Procedure and pass criterion: Check the CAD for metal parts inside the 120 x 100 deg FoV cone from the antenna face; check material and pigment declarations. Pass: none found.

## TP-MECH-011

- Requirement: REQ-MECH-011
- Method: test
- Planned by: G3
- Procedure and pass criterion: Pull the USB cable at the raceway exit with the load set per A-003 while monitoring power at the kit. Pass: no disconnection, no movement at the connector.

## TP-MECH-012

- Requirement: REQ-MECH-012
- Method: demo
- Planned by: G3
- Procedure and pass criterion: Install a pod with cable and raceway on a ceiling-and-wall mock-up. Pass: cable leaves at the ceiling plane into the raceway end.

## TP-PWR-001

- Requirement: REQ-PWR-001
- Method: test
- Planned by: G3
- Procedure and pass criterion: Power the pod from a bench supply at 5 V with a 1 A limit through USB-C. Pass: pod boots and reports presence.

## TP-PWR-002

- Requirement: REQ-PWR-002
- Method: test
- Planned by: G3
- Procedure and pass criterion: Log input current at 5 V with a current probe (1 ms resolution or better) through boot, standby, active detection and radio activity. Pass: peak current 1 A or less.

## TP-PWR-003

- Requirement: REQ-PWR-003
- Method: inspection
- Planned by: G1
- Procedure and pass criterion: Inspect the BOM and assembly: no battery or cell.

## TP-PWR-004

- Requirement: REQ-PWR-004
- Method: test
- Planned by: G3
- Procedure and pass criterion: Connect the pod with a USB-C to USB-C cable to at least two different USB Type-C wall adapters. Pass: 5 V present at the kit and the pod starts.

## TP-PWR-005

- Requirement: REQ-PWR-005
- Method: test
- Planned by: G3
- Procedure and pass criterion: Measure steady-state input power with a USB power meter in standby and active detection, no Grove accessory. Pass: 1.4 W or less. Also retires A-010.

## TP-ELEC-001

- Requirement: REQ-ELEC-001
- Method: inspection
- Planned by: G1
- Procedure and pass criterion: Inspect the BOM and assembly: no mains conductor, terminal or connector.

## TP-ENV-001

- Requirement: REQ-ENV-001
- Method: test
- Planned by: G3
- Procedure and pass criterion: Run the pod in a climate chamber at 0 C and at 35 C for 2 h each. Pass: presence reporting works at both.

## TP-ENV-002

- Requirement: REQ-ENV-002
- Method: test
- Planned by: G1/G3
- Procedure and pass criterion: Draft analysis in docs/budgets.md (G0). Test: pod at 35 C ambient, active mode, thermocouple at the kit, until stable. Pass: at or below the kit rated maximum (A-006).

## TP-SAFE-001

- Requirement: REQ-SAFE-001
- Method: inspection
- Planned by: G2
- Procedure and pass criterion: Check each enclosure material's UL iQ listing at the as-built wall thickness and colour against the class set by a qualified human.

## TP-SAFE-002

- Requirement: REQ-SAFE-002
- Method: test
- Planned by: G3
- Procedure and pass criterion: Measure outer surface temperatures at 35 C ambient, active mode, until stable. Pass: at or below the limit set by a qualified human.

## TP-SAFE-003

- Requirement: REQ-SAFE-003
- Method: inspection
- Planned by: G4
- Procedure and pass criterion: Claims review by safety-compliance-engineer of label, packaging, instructions and marketing text before release.

## TP-EMC-001

- Requirement: REQ-EMC-001
- Method: test
- Planned by: G4
- Procedure and pass criterion: Pre-scan per compliance/pre-scan-plan.md, then accredited-lab radiated and conducted emissions to FCC Part 15 Subpart B Class B.

## TP-EMC-002

- Requirement: REQ-EMC-002
- Method: inspection
- Planned by: G4
- Procedure and pass criterion: Check that FCC grants cover every intentional radiator in the pod as built (radar, Wi-Fi/Bluetooth).

## TP-EMC-003

- Requirement: REQ-EMC-003
- Method: test
- Planned by: G4
- Procedure and pass criterion: Accredited-lab EN 55032 emission and EN 55035 immunity tests; qualified human to confirm the radio EMC route.

## TP-EMC-004

- Requirement: REQ-EMC-004
- Method: inspection
- Planned by: G4
- Procedure and pass criterion: Check ISED approvals cover every licence-exempt radio in the pod as built.

## TP-EMC-005

- Requirement: REQ-EMC-005
- Method: inspection
- Planned by: G1
- Procedure and pass criterion: Inspect the architecture and BOM: no radio beyond the MR60FDA2 kit, or a signed human assessment exists.

## TP-FW-001

- Requirement: REQ-FW-001
- Method: demo
- Planned by: G3
- Procedure and pass criterion: Commission a pod at 2.5 m; read back the radar parameters with getRadarParameters. Pass: height equals the entered value.

## TP-FW-002

- Requirement: REQ-FW-002
- Method: test
- Planned by: G3
- Procedure and pass criterion: Attempt setup and operation with a blank credential, over every enabled network interface. Pass: refused in every case.

## TP-FW-003

- Requirement: REQ-FW-003
- Method: inspection
- Planned by: G3
- Procedure and pass criterion: Inspect the firmware build and two production units: no shared default password.

## TP-UX-001

- Requirement: REQ-UX-001
- Method: inspection
- Planned by: G3
- Procedure and pass criterion: Compare the printed or demo shell to the owner-approved colour sample under daylight; check matte finish.

## TP-UX-002

- Requirement: REQ-UX-002
- Method: inspection
- Planned by: G3
- Procedure and pass criterion: View the installed pod from the floor: no screw head visible.

## TP-UX-003

- Requirement: REQ-UX-003
- Method: inspection
- Planned by: G4
- Procedure and pass criterion: Review the instructions text.

## TP-MNT-001

- Requirement: REQ-MNT-001
- Method: inspection
- Planned by: G4
- Procedure and pass criterion: Review the instructions text.

## TP-MNT-002

- Requirement: REQ-MNT-002
- Method: inspection
- Planned by: G4
- Procedure and pass criterion: Review the instructions text.

## TP-MNT-003

- Requirement: REQ-MNT-003
- Method: inspection
- Planned by: G4
- Procedure and pass criterion: Review the instructions text.

## TP-MNT-004

- Requirement: REQ-MNT-004
- Method: inspection
- Planned by: G4
- Procedure and pass criterion: Review the instructions text and illustrations.

## TP-MFG-001

- Requirement: REQ-MFG-001
- Method: inspection
- Planned by: G2/G3
- Procedure and pass criterion: Slice each part at its chosen orientation (0.4 mm nozzle); inspect support placement; print and inspect show faces.

## TP-MFG-002

- Requirement: REQ-MFG-002
- Method: analysis
- Planned by: G2
- Procedure and pass criterion: checking-dfm overhang analysis on the CAD at print orientation.

## TP-MFG-003

- Requirement: REQ-MFG-003
- Method: analysis
- Planned by: G2
- Procedure and pass criterion: checking-dfm bridge analysis on the CAD at print orientation.

## TP-MFG-004

- Requirement: REQ-MFG-004
- Method: analysis
- Planned by: G2
- Procedure and pass criterion: verifying-geometry minimum-wall check on every part.

## TP-MFG-005

- Requirement: REQ-MFG-005
- Method: analysis
- Planned by: G2
- Procedure and pass criterion: stacking-tolerances on every mating interface for each process.

## TP-MFG-006

- Requirement: REQ-MFG-006
- Method: demo
- Planned by: G3
- Procedure and pass criterion: Print every part in PETG and assemble.

## TP-MFG-007

- Requirement: REQ-MFG-007
- Method: demo
- Planned by: G3
- Procedure and pass criterion: Order demo parts from a service in SLA or MJF and assemble.

## TP-COST-001

- Requirement: REQ-COST-001
- Method: analysis
- Planned by: G3
- Procedure and pass criterion: costing-bom roll-up at the prototype quantity.

## TP-COST-002

- Requirement: REQ-COST-002
- Method: analysis
- Planned by: G5
- Procedure and pass criterion: costing-bom roll-up at the production volume tier (Q-15).

## TP-COST-003

- Requirement: REQ-COST-003
- Method: inspection
- Planned by: G1
- Procedure and pass criterion: costing-bom check on bom/bom.csv: every line priced with a check date.
