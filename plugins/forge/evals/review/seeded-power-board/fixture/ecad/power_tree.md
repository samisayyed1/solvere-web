# NodeLink power board rev A -- power tree

| Ref | Part | Input | Output | Load | Package |
|---|---|---|---|---|---|
| D1 | SS34 Schottky, series | J1 12 V | 11.6 V | 0.35 A | SMA |
| D2 | SMBJ28A TVS | J1 12 V to GND | clamp | -- | SMB |
| U1 | AMS1117-3.3 LDO | 11.6 V | 3.3 V | 300 mA | SOT-223, theta_JA 60 C/W |
| U2 | TLV70018 LDO | 3.3 V | 1.8 V | 50 mA | SOT-23-5, theta_JA 210 C/W |

## Thermal at 60 C ambient, full load

- U1: P = (11.6 - 3.3) x 0.03 = 0.25 W -> Tj = 60 + 0.25 x 60 = 75 C. PASS.
- U2: P = (3.3 - 1.8) x 0.05 = 0.075 W -> Tj = 60 + 0.075 x 210 = 76 C. PASS.

## Capacitors

- C1 22 uF 25 V X7R 1210 at U1 input.
- C3 1 uF 10 V X7R 0402 at U1 output (small, cheap, placed next to the tab).
- C4 1 uF at U2 input, C5 1 uF at U2 output (TLV700 datasheet: 1 uF ceramic minimum).
