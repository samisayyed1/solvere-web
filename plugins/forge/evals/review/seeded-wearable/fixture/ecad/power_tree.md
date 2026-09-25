# PulseBand rev B -- power tree

| Ref | Part | Input | Output | Load | Package |
|---|---|---|---|---|---|
| U1 | BQ21080 Li-ion charger | VBUS 5.0 V (J2) | VBAT 3.0-4.2 V | 200 mA charge | WCSP-8 |
| U2 | TPS62840 buck, 90 % eff. | VBUS 5.0 V while charging, else VBAT | 3.3 V | 180 mA peak | SON-6 |
| U3 | TLV70018 LDO | VBUS 5.0 V while charging, else VBAT | 1.8 V | 150 mA (optical AFE LEDs) | SOT-23-5, theta_JA 210 C/W |

## Dissipation at 40 C ambient, charging (worst case)

- U2: P_loss = 3.3 V x 0.18 A x (1/0.9 - 1) = 0.066 W -> Tj = 40 + 0.066 x 70 = 45 C. OK.
- U3: P = (VIN - VOUT) x I = (5.0 - 1.8) x 0.015 = 0.048 W -> Tj = 40 + 0.048 x 210 = 50 C. OK, meets REQ-ELEC-003.
