# Requirements -- PulseBand wrist sensor, rev B

## REQ-SYS-001

While the band is worn, the PulseBand shall measure heart rate from 40 bpm to 200 bpm with an error of at most 5 bpm.

Rationale: core product promise.
Verify: test

## REQ-MECH-001

The housing and lid shall be printed by SLA in Formlabs Tough 2000 resin for the EVT build.

Rationale: EVT process decision, docs/decisions/ADR-0003.
Verify: inspection

## REQ-MECH-002

The housing shall hold the 402530 LiPo cell (40.0 x 25.0 x 5.0 mm nominal, 5.3 mm at end of life) with no part of the housing or PCB touching the cell.

Rationale: pressure on a pouch cell is a swelling and fire hazard.
Verify: analysis

## REQ-MECH-003

When the lid is closed, the gap between the top of the U5 optical AFE window and the underside of the lid window shall be between 0.05 mm and 0.40 mm.

Rationale: below 0.05 mm the lid presses on the AFE; above 0.40 mm stray light degrades the optical signal.
Verify: analysis

## REQ-MECH-004

The sensor tether cable shall withstand a 20 N axial pull without damage to its solder joints.

Rationale: users pull the tether when taking the band off.
Verify: test

## REQ-ELEC-001

While powered, the 3.3 V rail shall supply 180 mA peak.

Rationale: radio TX peak plus MCU.
Verify: analysis

## REQ-ELEC-002

When a user touches the charging contacts, the device shall survive a +/-8 kV contact discharge (IEC 61000-4-2 level 4) without damage.

Rationale: the charging contacts are exposed on the underside of the band.
Verify: test

## REQ-ELEC-003

While charging at 40 C ambient, the 1.8 V sensor-rail regulator junction temperature shall stay below 105 C.

Rationale: regulator absolute maximum 125 C, 20 C margin.
Verify: analysis

## REQ-SW-001

While in normal use, the PulseBand shall run for at least 5 days per charge.

Rationale: competitive benchmark.
Verify: test
