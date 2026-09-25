# Requirements -- SensorHub enclosure, rev A

## REQ-MECH-001

The enclosure base and lid shall be printed by FDM in PETG with a 0.4 mm nozzle.

Rationale: low-volume build, no tooling budget.
Verify: inspection

## REQ-MECH-002

The enclosure shall house the 60.0 x 40.0 x 1.6 mm PCB, including every component on it, with at least 0.3 mm clearance to every enclosure surface.

Rationale: print tolerance and assembly without force.
Verify: analysis

## REQ-MECH-003

When the PCB is seated, the PCB-to-slot side gap shall be between 0.05 mm and 0.50 mm in the worst case.

Rationale: the board must drop in by hand and must not rattle.
Verify: analysis

## REQ-MECH-004

The DC input cable shall withstand a 30 N axial pull without load on the J3 terminal.

Rationale: field installers pull the cable during mounting.
Verify: test

## REQ-MECH-005

The lid shall be retained by four M3 x 6 screws passing through the lid into heat-set inserts in the base corners.

Rationale: serviceable, repeated opening.
Verify: inspection

## REQ-MECH-006

The assembled SensorHub shall survive 10 drops from 1.0 m onto concrete with no cracked part and no loose component.

Rationale: installation happens on ladders.
Verify: test

## REQ-SYS-001

While operating at 0 C to 50 C ambient, the PCB hot spot shall stay below 85 C.

Rationale: component rating.
Verify: analysis
