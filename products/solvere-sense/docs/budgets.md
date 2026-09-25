# Budgets (G0 draft)

Status: DRAFT, evidence level L0 (nothing measured). Every number comes from `params/params.toml`, which cites its source; this page shows the arithmetic. A value with no source is written as "not sourced" and is never estimated here. Source short names are in `docs/sources/README.md`.

## Power (5 V USB-C input)

| Line | Value | Param / source |
|---|---|---|
| Supply available | 5.0 V x 1.0 A = 5.0 W | `power.usb_voltage`, `power.usb_current_max` (Owner; DS p.6) |
| Kit, standby mode | 0.5 W | `sensor.power_standby` (DS p.6; A-007) |
| Kit, activation mode | 0.8 W | `sensor.power_active` (DS p.6; A-007) |
| Kit, with Grove relay | 1.4 W | `sensor.power_with_relay` (DS p.6) |
| Other loads in the pod | none (no battery, no other board) | REQ-PWR-003; A-006, Q-01 |
| **Pod cap** | **1.4 W** (REQ-PWR-005) | `power.pod_power_max` (A-008) |
| Margin to supply | 5.0 W - 1.4 W = 3.6 W | computed |
| Peak current | not sourced for the kit; must be at most 1 A (REQ-PWR-002) | measure, TP-PWR-002 |

Conflict to resolve by measurement (R-014): MDS p.4 gives a radar-module operating current of 600 mA at 3.1 V to 3.5 V (about 2 W at 3.3 V if that is a steady value), and MDS p.11 asks for a supply of at least 1 A with at most 50 mV ripple, while DS p.6 gives 0.8 W for the whole kit active.

## Thermal

All input power ends up as heat inside the enclosure.

| Line | Value | Param / source |
|---|---|---|
| Heat to dissipate | 1.4 W | `power.pod_power_max` (A-008) |
| Maximum room ambient | 35 °C | `env.ambient_max` (A-003, Q-09) |
| Kit maximum operating temperature | 85 °C | `sensor.kit_temp_max` (A-004; radar module MDS p.4, XIAO) |
| Allowed rise, kit air over room | 85 °C - 35 °C = 50 K | `thermal.kit_rise_allowed` |
| **Allowed thermal resistance, kit air to room** | **50 K / 1.4 W = 35.7 K/W** | `thermal.max_thermal_resistance` |
| Accessible surface temperature limit | set by a qualified human under IEC 62368-1 | REQ-SAFE-002; Q-17 |

The enclosure geometry that meets 35.7 K/W is not estimated at G0 (no sourced convection data); it is checked by analysis at G1/G2 and by test (TP-ENV-002, TP-SAFE-002).

## Mass

No mass is published for the kit (DS, MDS, Wiki and XIAO searched 2026-09-25), and no part is designed yet, so every mass line is **not sourced**. Mass matters for the retention tests (REQ-MECH-004, -005), which scale with measured weight, so no mass number is needed at G0.

| Line | Value | How it is obtained |
|---|---|---|
| Sensor kit (radar module + XIAO) | not sourced | weigh a kit at G1 |
| Base plate, shell, radome, strain relief | not sourced | CAD mass at G2 (material density from supplier datasheet), then weigh at G3 |
| T-bar clip (optional) | not sourced | as above |
| Installed pod | not sourced | weigh at G3; drives TP-MECH-004 load |

## Cost (US$ per unit)

| Line | Value | Param / source |
|---|---|---|
| Sensor kit, DS price | 26.90 (excl. VAT, 2026-07-30) | `sensor.unit_price_ds` (DS p.1) |
| Sensor kit, product page, 1 unit | 28.99 (2026-09-25) | `sensor.unit_price_web_qty1` (Web) |
| Sensor kit, product page, 10+ | 28.99 (2026-09-25) | `sensor.unit_price_web_qty10` (Web) |
| Printed parts, fixings, strain relief | not sourced | `bom/bom.csv` with dated quotes (REQ-COST-003) |
| USB cable, adapter, raceway | not sourced; in scope only if they ship in the box | Q-13, A-009 |
| **Prototype ceiling** | **50.00** | `cost.prototype_max` (Owner) |
| Prototype room after the kit | 50.00 - 28.99 = 21.01 | computed |
| **Production BOM ceiling** | **30.00** | `cost.production_bom_max` (Owner; A-016) |
| Production room after the kit | 30.00 - 28.99 = 1.01 | computed; R-002 |

The production line is at risk (R-002): with the kit bought at the only published tier, US$1.01 is left for everything else. The owner's volume tier and BOM scope (Q-10) decide whether a volume quote or a custom board is needed.

## RF / radome

The radar-to-person path is set by the sensor, not by Forge. The pod's part of it is the radome loss, which is not published for any material the owner named (PETG, SLA resin, PA nylon), so it is measured.

| Line | Value | Param / source |
|---|---|---|
| Frequency band | 58 GHz to 62 GHz; design centre 60 GHz | `sensor.freq_min`, `sensor.freq_max`, `sensor.freq_centre` (MDS p.4, p.12) |
| Free-space wavelength at 60 GHz | 4.997 mm | `sensor.wavelength_free_space` (computed) |
| Transmit power, antenna gain | 12 dBm, 4 dBi | `sensor.tx_power`, `sensor.antenna_gain` (MDS p.4) |
| Beam (-3 dB) | -60° to 60°, both planes | `sensor.beam_half_angle` (MDS p.4); R-013 |
| Antenna to radome inner surface | N x 2.5 mm | `radome.antenna_gap_step` (MDS p.12) |
| Radome thickness | N x 4.997 mm / (2 x sqrt(εr)) | MDS p.12; εr not sourced for the owner's materials |
| Radome insertion loss allowed | no degradation against the bare kit (A/B) | REQ-SYS-002; TP-SYS-002 |
| Reference εr / tan δ (materials not chosen) | PC 2.9 / 0.012; ABS 2.0-3.5 / 0.005-0.019; PE 2.3 / 0.0003; PBT 2.9-4.0 / 0.002 (others in MDS) | MDS p.11-12 |

## Link (Wi-Fi / Bluetooth)

Not budgeted at G0: which radios are enabled and where the pod sends data are open (Q-01, Q-02). The XIAO has an on-board ceramic antenna and an optional U.FL connector (XIAO). The metal keep-out (REQ-MECH-010) also keeps the 2.4 GHz antenna clear of metal in practice; a link check is planned once Q-02 is answered.
