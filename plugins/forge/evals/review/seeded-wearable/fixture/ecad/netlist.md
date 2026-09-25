# PulseBand rev B -- netlist (from the tscircuit source, abridged)

| Net | Connections |
|---|---|
| VBUS | J2.1 (charging pogo contact, exposed on band underside), U1.VIN, Q1.INA, C1 (10 uF 0402) |
| GND | J2.2 (charging pogo contact), U1.GND, Q1.GND, U2.GND, U3.GND, U4.GND, U5.GND, C1, C2, C3, C4 |
| VBAT | U1.BAT, BT1+, Q1.INB |
| VSYS | Q1.OUT, U2.VIN, U3.VIN, C4 (10 uF) |
| 3V3 | U2.VOUT, C2 (22 uF), U4.VDD (nRF52832) |
| 1V8 | U3.VOUT, C3 (1 uF), U5.VDD (optical AFE module) |
| SPI | U4.P0.23-P0.26 to U5.SCK/SDO/SDI/CS |

Notes: J2 pins route directly to U1.VIN and GND through 0.3 mm traces; no other parts on the J2 nets. U4 and U5 SPI levels: U5 I/O is 3.3 V tolerant (module datasheet p.5).
