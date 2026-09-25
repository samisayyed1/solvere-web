# Requirements

Ladder fixture (plugins/forge/tests/ladder): a mounting plate with a resistor
divider board, a clamp firmware module and a cantilever arm. Every automatable
rung of the verification ladder (docs/standards/verification-ladder.md) has at
least one requirement here. Not a real product.

## REQ-MECH-001

The mounting plate shall be a valid, watertight solid with an outline of 60.0 mm by 40.0 mm ±0.1 mm.

Rationale: params plate.length and plate.width set the footprint of the mating chassis.
Verify: analysis

## REQ-MECH-002

The mounting plate shall be at least 2.9 mm thick everywhere sampled.

Rationale: params plate.thickness is 3.0 mm with a 0.1 mm lower tolerance.
Verify: analysis

## REQ-MECH-003

The mounting plate shall keep every mounting hole at least 3.0 mm from the outer edge.

Rationale: params plate.hole_inset leaves a 4.4 mm web; below 3.0 mm the web cracks under screw torque.
Verify: analysis

## REQ-MECH-004

When the lid is assembled on the plate, the lid-to-plate gap shall stay between 2.5 mm and 3.5 mm.

Rationale: the gap houses the divider board; the stack in analysis/stacks/lid_gap.toml carries the tolerances.
Verify: analysis

## REQ-MFG-001

The mounting plate shall meet the FDM unsupported-wall and minimum hole-diameter rules of the checking-dfm process table.

Rationale: the plate is printed on FDM; the rule table cites R5d.
Verify: analysis

## REQ-MFG-002

The bill of materials shall list an alternate part or a recorded risk note for every line item.

Rationale: single-source parts without a mitigation stop production when a supplier drops them.
Verify: inspection

## REQ-SIM-001

When a 100 N tip load is applied to the cantilever arm, the arm shall keep its peak bending stress at or below 166 MPa.

Rationale: 166 MPa is the 250 MPa yield of the generic structural steel divided by a 1.5 safety factor.
Verify: analysis

## REQ-ELEC-001

While the divider board is powered from 5.0 V, the divider shall hold its output at 2.5 V ±0.05 V.

Rationale: the downstream ADC reference expects half the supply rail.
Verify: analysis

## REQ-ELEC-002

The divider schematic shall pass the KiCad electrical rules check with no errors and no warnings.

Rationale: an unconnected pin or a dangling net on the divider changes its output.
Verify: analysis

## REQ-FW-001

The firmware shall clamp every commanded setpoint to the configured range before the setpoint is used.

Rationale: an out-of-range setpoint drives the actuator past its end stop.
Verify: test

## REQ-SYS-001

The system model shall parse with no errors and no warnings under the spec42 checker.

Rationale: the model is the single source for the product breakdown and budgets.
Verify: inspection

## REQ-COMP-001

The product profile shall be mapped to its applicable standards, test plan and pre-scan plan before gate G2.

Rationale: the compliance map is a G2 input; a qualified human signs the determination.
Verify: inspection
