# Requirements -- smart plant pot

## REQ-SYS-001

The pot shall measure volumetric soil moisture within 3 % of a gravimetric reference.

Rationale: core feature. The 3 % figure is assumption A-001.
Verify: test

## REQ-SYS-002

When the measured soil moisture falls below the dry threshold, the app shall show a notification within 60 s.

Rationale: user value. 60 s is assumption A-002.
Verify: demo

## REQ-PWR-001

The pot shall run for at least 4380 h on one charge.

Rationale: users hate charging; six months of runtime is assumption A-003.
Verify: test

## REQ-MECH-001

If 200 mm3 of water is spilled on the top surface, then the pot shall continue to meet REQ-SYS-001.

Rationale: it lives on a windowsill; spill volume is assumption A-004.
Verify: test

## REQ-UX-001

When a first-time user follows the quick-start card, the user shall pair the pot with the app within 120 s.

Rationale: consumer product; replaces "easy to use"; 120 s is assumption A-005.
Verify: demo

## REQ-MECH-002

The pot shall hold a 12 cm nursery pot.

Rationale: standard size.
Verify: inspection
