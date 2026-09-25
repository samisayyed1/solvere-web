# Ladder fixture overview

A tiny product that exercises every automatable rung of the Forge
verification ladder (see the plugin's `docs/standards/verification-ladder.md`).

- Requirements: [requirements.md](../requirements/requirements.md), e.g. [REQ-MECH-002](../requirements/requirements.md#req-mech-002).
- Mounting plate: [cad/plate.py](../cad/plate.py), params in [params.toml](../params/params.toml).
- Divider board: [schematic](../ecad/divider/divider.kicad_sch) and [SPICE netlist](../analysis/spice/divider.cir).
- Firmware: [clamp.c](../firmware/src/clamp.c).
- See [the design overview](#ladder-fixture-overview).
