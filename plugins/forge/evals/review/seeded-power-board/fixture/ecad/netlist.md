# NodeLink power board rev A -- netlist (abridged from the tscircuit source)

| Net | Connections |
|---|---|
| VIN_RAW | J1.1 (12 V pigtail, red), D1.A, D2.K |
| VIN | D1.K, U1.VIN, C1 |
| 3V3 | U1.VOUT, C3, U2.VIN, C4, U3.VCC (MAX3485), U4.VDD (radio) |
| 1V8 | U2.VOUT, C5, U5.VDD (sensor bridge) |
| GND | J1.2, D2.A, U1.GND, U2.GND, U3.GND, J2.3, C1, C3, C4, C5 |
| RS485_A | J2.1 (M12 field connector), U3.A |
| RS485_B | J2.2 (M12 field connector), U3.B |
| RS485_TERM | R7 120 R between RS485_A and RS485_B via JP1 |
