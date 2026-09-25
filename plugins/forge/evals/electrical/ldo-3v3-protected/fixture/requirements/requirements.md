# Requirements -- 3.3 V power stage

## REQ-ELEC-001

While supplied from USB 5.0 V (4.75 V to 5.25 V) and loaded with 300 mA, the 3.3 V rail shall stay within 3.3 V +/-3 %.

Rationale: MCU and radio supply tolerance.
Verify: analysis

## REQ-ELEC-002

If the 5 V input is connected with reversed polarity, then the power stage shall not pass reverse current to the 3.3 V rail.

Rationale: bench supplies get wired backwards.
Verify: analysis

## REQ-ELEC-003

The power stage shall clamp ESD and surge transients on the 5 V input with a TVS diode.

Rationale: external connector.
Verify: inspection

## REQ-ELEC-004

The schematic shall pass KiCad ERC with no unwaived errors or warnings.

Rationale: fabrication readiness.
Verify: inspection
