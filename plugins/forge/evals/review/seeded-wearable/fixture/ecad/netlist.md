# PulseBand rev B -- netlist (from the tscircuit source, abridged)

| Net | Connections |
|---|---|
| VBUS | J2.1 (charging pogo contact, exposed on band underside), U1.VIN, U2.VIN (via Q1 path switch), U3.VIN, C1 (10 uF 0402) |
| GND | J2.2 (charging pogo contact), U1.GND, U2.GND, U3.GND, C1, C2, C3 |
| VBAT | U1.BAT, BT1+, Q1 |
| 3V3 | U2.VOUT, C2 (22 uF), U4.VDD (nRF52832), U5.VDD |
| 1V8 | U3.VOUT, C3 (1 uF), U5.VLED (MAX86141 optical AFE) |
| SDA/SCL | U4.P0.26/P0.27, U5.SDA/SCL, R1/R2 4.7 k pull-ups to 3V3 |

Notes: J2 pins route directly to U1.VIN and GND through 0.3 mm traces; no other parts on the J2 nets.
