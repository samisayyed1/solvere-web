# Requirements -- NodeLink RS-485 sensor node, power board rev A

## REQ-ELEC-001

While supplied from 12 V DC +/-10 %, the 3.3 V rail shall supply 300 mA continuous within 3.3 V +/-3 %.

Rationale: radio module plus sensor bridge.
Verify: test

## REQ-ELEC-002

While the 3.3 V rail is up, the 1.8 V rail shall supply 50 mA within 1.8 V +/-3 %.

Rationale: sensor core.
Verify: test

## REQ-ELEC-003

While operating at 60 C ambient and full load, every regulator junction temperature shall stay below 125 C.

Rationale: regulator absolute maximum rating.
Verify: analysis

## REQ-ELEC-004

When the supply is connected with reversed polarity at up to 30 V, the board shall suffer no damage.

Rationale: field wiring mistakes.
Verify: test

## REQ-ELEC-005

When a +/-8 kV contact discharge (IEC 61000-4-2) is applied to any pin of the RS-485 connector J2, the board shall suffer no damage.

Rationale: J2 is an external M12 field connector.
Verify: test

## REQ-MECH-001

The 12 V input pigtail shall withstand a 20 N pull without stressing its solder joints.

Rationale: installers tug the pigtail.
Verify: test
