# Requirements -- dev-board enclosure

## REQ-MECH-001

The enclosure base and lid shall be FDM-printed in ABS.

Rationale: low-volume run on the lab printer.
Verify: inspection

## REQ-MECH-002

The enclosure shall contain the dev board (docs/board.md) with no interference between the board keep-out and the base or the lid.

Rationale: fit.
Verify: analysis

## REQ-MECH-003

The enclosure base walls shall be at least 1.6 mm thick.

Rationale: stiffness and FDM wall rule.
Verify: analysis

## REQ-MECH-004

The base and lid shall leave room for a mating USB-C plug to be fully inserted.

Rationale: the board is powered and programmed over USB-C.
Verify: analysis

## REQ-MECH-005

The lid shall close onto the base with a snap fit and no tools, with no interference between lid and base when closed.

Rationale: tool-free access.
Verify: analysis

## REQ-MECH-006

The snap-fit latch root strain shall stay within the material's single-assembly allowable.

Rationale: the latch must not crack on first assembly.
Verify: analysis
