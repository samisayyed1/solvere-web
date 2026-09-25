# Verification plan (G0 draft)

Planned tests, one per requirement in `requirements/requirements.md`. **None of these tests has been run.** Each entry names the gate by which it is expected, the method, and the pass criterion. Evidence is recorded in `evidence/manifest.json` as each test runs; `requirements/trace.json` points here until real test scripts or reports replace these entries.

Numbers here come from the requirements and `params/params.toml`; see those for sources and assumptions.

## TP-SYS-001

- Requirement: REQ-SYS-001
- Method: test
- Planned by: G3/G4
- Procedure and pass criterion: Mount pod at 2.2 m and at 3.0 m. Stage a fall with a test person or fall dummy at each corner and at the centre of a 3.0 m x 3.0 m square centred below the pod, one person in the room. Pass: the fall-event output is set for every position at both heights. If a corner fails, repeat on a 2 m radius circle (Owner round 2 fallback). Protocol (repeats, dummy, room furnishing) to be agreed with the owner.

## TP-SYS-002

- Requirement: REQ-SYS-002
- Method: test
- Planned by: G2/G3
- Procedure and pass criterion: A/B test: bare MR60FDA2 kit vs the kit inside the assembled pod (FDM PETG, then demo material). Same room, same test points on a grid out to 6 m. Pass: the pod reports presence at every point where the bare kit does. Before G2, run the same A/B on flat radome coupons of each candidate material at thicknesses N x c/(2 f sqrt(er)) (MDS §8), to find er and the best N; this sets `radome.thickness` (REQ-MECH-013).


## TP-SYS-003

- Requirement: REQ-SYS-003
- Method: test
- Planned by: G3
- Procedure and pass criterion: Install two pods in one room at 2.2 m and 3.0 m heights, at a series of spacings. At each spacing, run the TP-SYS-001 fall points and the TP-SYS-002 presence points with the second pod on and then off. Also log false fall events over the same session with nobody falling. Pass: identical fall-event and presence outputs, on and off, at every point; the smallest spacing that passes becomes the minimum spacing in the instructions (REQ-MNT-006).

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
- Procedure and pass criterion: Clip the T-bar adapter to a 15 mm and a 24 mm drop-ceiling grid sample. Pass: pod held, tile not drilled or cut.

## TP-MECH-004

- Requirement: REQ-MECH-004
- Method: test
- Planned by: G3
- Procedure and pass criterion: Weigh the installed pod (g). Apply a static downward pull of 4 x that weight to the installed pod for 60 s on drywall, concrete and T-bar samples. Pass: no detachment. Load factor and hold time per placeholder A-001 at G0; from G2 the load per REQ-MECH-015.

## TP-MECH-005

- Requirement: REQ-MECH-005
- Method: test
- Planned by: G3
- Procedure and pass criterion: Weigh shell plus sensor kit. Apply 4 x that weight (placeholder A-001; REQ-MECH-015 from G2) downward on the shell for 60 s. Pass: shell stays attached.

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
- Procedure and pass criterion: Check the CAD for metal parts inside the 60 deg half-angle cone about the antenna boresight; check material and pigment declarations. Pass: none found.

## TP-MECH-011

- Requirement: REQ-MECH-011
- Method: test
- Planned by: G3
- Procedure and pass criterion: Pull the USB cable at the raceway exit with the load set under REQ-MECH-015 while monitoring power at the kit. Pass: no disconnection, no movement at the connector.

## TP-MECH-012

- Requirement: REQ-MECH-012
- Method: demo
- Planned by: G3
- Procedure and pass criterion: Install a pod with cable and raceway on a ceiling-and-wall mock-up. Pass: cable leaves at the ceiling plane into the raceway end.

## TP-MECH-013

- Requirement: REQ-MECH-013
- Method: analysis
- Planned by: G2
- Procedure and pass criterion: From the coupon result (TP-SYS-002) take er of the chosen radome material; compute T = N x c/(2 f sqrt(er)) with f = 60 GHz (MDS p.12); measure the CAD radome thickness over the 60 deg half-angle cone. Pass: thickness equals the computed T within the tolerance set from the coupon test.

## TP-MECH-014

- Requirement: REQ-MECH-014
- Method: inspection
- Planned by: G2/G3
- Procedure and pass criterion: Measure antenna face to radome inner surface in CAD and on a printed assembly. Pass: an integer multiple of 2.5 mm (MDS p.12) within the tolerance set at G2.


## TP-MECH-015

- Requirement: REQ-MECH-015
- Method: inspection
- Planned by: before G2 (G2 entry)
- Procedure and pass criterion: Check `params/params.toml`: retention loads for REQ-MECH-004, -005 and -011 are computed from measured weights times a safety factor, and the safety factor param has a value and a cited source (standard clause or named qualified human). Pass: all three present and sourced.

## TP-MECH-016

- Requirement: REQ-MECH-016
- Method: demo
- Planned by: G3
- Procedure and pass criterion: Fit and remove the pod on the base plate by hand 10 times on each ceiling type, with the USB cable connected. Pass: removal and refit by hand with no tool; cable and connector undamaged; REQ-MECH-005 still passes afterwards.

## TP-MECH-017

- Requirement: REQ-MECH-017
- Method: analysis
- Planned by: G2
- Procedure and pass criterion: Compare the CAD groove against ARSDG Table A (PDF p.20) for the chosen cord cross-section: gland depth, groove width and squeeze range; check corner radius at least 3 x cross-section if the groove is non-round (ARSDG p.90) and gland volume above O-ring volume at worst-case tolerances (ARSDG p.113). Pass: all within the guide.

## TP-MECH-018

- Requirement: REQ-MECH-018
- Method: test
- Planned by: bathroom variant (post-v1)
- Procedure and pass criterion: IPX4 test on an assembled bathroom-variant pod with gasket and cable fitted, by a lab using the test method a qualified human confirms. Pass: IPX4 met.

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
- Procedure and pass criterion: Measure steady-state input power with a USB power meter in standby and active detection, no Grove accessory. Pass: 1.4 W or less. Also retires A-007 and A-008.

## TP-ELEC-001

- Requirement: REQ-ELEC-001
- Method: inspection
- Planned by: G1
- Procedure and pass criterion: Inspect the BOM and assembly: no mains conductor, terminal or connector.

## TP-ENV-001

- Requirement: REQ-ENV-001
- Method: test
- Planned by: G3
- Procedure and pass criterion: Run the pod in a climate chamber at 0 C and at 40 C for 2 h each. Pass: presence and fall-event outputs work at both.

## TP-ENV-002

- Requirement: REQ-ENV-002
- Method: test
- Planned by: G1/G3
- Procedure and pass criterion: Draft analysis in docs/budgets.md (G0). Test: pod at 40 C ambient, active mode, thermocouple at the kit, until stable. Pass: at or below the kit rated maximum, 85 C per A-004 until Seeed confirms.

## TP-SAFE-001

- Requirement: REQ-SAFE-001
- Method: inspection
- Planned by: G2
- Procedure and pass criterion: Check each enclosure material's UL iQ listing at the as-built wall thickness and colour against the class set by a qualified human.

## TP-SAFE-002

- Requirement: REQ-SAFE-002
- Method: test
- Planned by: G3
- Procedure and pass criterion: Measure outer surface temperatures at 40 C ambient, active mode, until stable. Pass: at or below the limit set by a qualified human.

## TP-SAFE-003

- Requirement: REQ-SAFE-003
- Method: inspection
- Planned by: G4
- Procedure and pass criterion: Claims review by safety-compliance-engineer of label, packaging, instructions and marketing text before release.


## TP-SAFE-004

- Requirement: REQ-SAFE-004
- Method: inspection
- Planned by: G3 (firmware entity names), G4 (all text)
- Procedure and pass criterion: Search every user-facing text, including ESPHome / Home Assistant entity and device names, for the deny-list terms in `compliance/claims-wording.md`. Pass: no hit.

## TP-EMC-001

- Requirement: REQ-EMC-001
- Method: test
- Planned by: G4
- Procedure and pass criterion: Pre-scan per compliance/pre-scan-plan.md, then accredited-lab radiated and conducted emissions to FCC Part 15 Subpart B Class B.

## TP-EMC-002

- Requirement: REQ-EMC-002
- Method: inspection
- Planned by: G4
- Procedure and pass criterion: Check that FCC grants cover every intentional radiator in the pod as built (60 GHz radar; XIAO ESP32C6 Wi-Fi, Bluetooth LE and 802.15.4).

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


## TP-FW-004

- Requirement: REQ-FW-004
- Method: test
- Planned by: G3
- Procedure and pass criterion: Run the pod through boot into normal operation with no fault for 1 h; observe the light pipe and read the LED state from the firmware. Pass: LED off throughout after setup ends.

## TP-FW-005

- Requirement: REQ-FW-005
- Method: test
- Planned by: G3
- Procedure and pass criterion: Enter setup mode, pairing mode and each injected fault state (for example Wi-Fi loss, radar UART loss) with the LED enabled. Pass: LED lit in each state and off again when the state ends.

## TP-FW-006

- Requirement: REQ-FW-006
- Method: test
- Planned by: G3
- Procedure and pass criterion: Disable the LED in settings; repeat TP-FW-004 and TP-FW-005. Pass: LED off in every state.

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


## TP-UX-004

- Requirement: REQ-UX-004
- Method: inspection
- Planned by: G3
- Procedure and pass criterion: Inspect the assembled pod: light pipe flush with the shell surface (feel and straight-edge), same matte warm white as the shell; confirm the light-pipe part prints with no supports on its show face (TP-MFG-001) and adds no visible screw (TP-UX-002).

## TP-UX-005

- Requirement: REQ-UX-005
- Method: inspection
- Planned by: G2/G3
- Procedure and pass criterion: Inspect CAD and the printed shell: no light-sensor window and no reset pinhole on the room-facing side.

## TP-UX-006

- Requirement: REQ-UX-006
- Method: demo
- Planned by: G3
- Procedure and pass criterion: Twist the pod off the base plate and press the kit reset button with a finger. Pass: reached and pressed with no tool.

## TP-MNT-001

- Requirement: REQ-MNT-001
- Method: inspection
- Planned by: G4
- Procedure and pass criterion: Review the instructions text.

## TP-MNT-002

- Requirement: REQ-MNT-002
- Method: inspection
- Planned by: G4
- Procedure and pass criterion: Review the instructions text against the seven Wiki keep-outs. Pass: all seven are listed.

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

## TP-MNT-005

- Requirement: REQ-MNT-005
- Method: inspection
- Planned by: G4
- Procedure and pass criterion: Review the instructions text. Pass: it states that the fall-event output is specified for one person, matching the TP-SYS-001 configuration.


## TP-MNT-006

- Requirement: REQ-MNT-006
- Method: inspection
- Planned by: G4
- Procedure and pass criterion: Review the instructions text. Pass: states at most two pods per room and the minimum spacing found in TP-SYS-003.

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
- Procedure and pass criterion: costing-bom roll-up of shell parts, kit and fixings at 10+ unit pricing (Owner round 2).

## TP-COST-003

- Requirement: REQ-COST-003
- Method: inspection
- Planned by: G1
- Procedure and pass criterion: costing-bom check on bom/bom.csv: every line priced with a check date.
