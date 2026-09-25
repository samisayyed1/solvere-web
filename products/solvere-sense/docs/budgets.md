# Budgets (G0 draft)

Status: DRAFT, evidence level L0 (nothing measured). Every number comes from `params/params.toml`, which cites its source; this page shows the arithmetic. A value with no source is written as "not sourced" and is never estimated here. Source short names are in `docs/sources/README.md`.

## Power (5 V USB-C input)

| Line | Value | Param / source |
|---|---|---|
| Supply available | 5.0 V x 1.0 A = 5.0 W | `power.usb_voltage`, `power.usb_current_max` (Owner; DS p.6) |
| Kit, standby mode | 0.5 W | `sensor.power_standby` (DS p.6; A-007) |
| Kit, activation mode | 0.8 W | `sensor.power_active` (DS p.6; A-007) |
| Kit, with Grove relay | 1.4 W | `sensor.power_with_relay` (DS p.6) |
| Other loads in the pod | none (no battery, no other board; kit as-is, Owner round 2) | REQ-PWR-003; Q-01 closed |
| **Pod cap** | **1.4 W** (REQ-PWR-005) | `power.pod_power_max` (A-008) |
| Margin to supply | 5.0 W - 1.4 W = 3.6 W | computed |
| Peak current | not sourced for the kit; must be at most 1 A (REQ-PWR-002) | measure, TP-PWR-002 |

Conflict to resolve by measurement (R-014): MDS p.4 gives a radar-module operating current of 600 mA at 3.1 V to 3.5 V (about 2 W at 3.3 V if that is a steady value), and MDS p.11 asks for a supply of at least 1 A with at most 50 mV ripple, while DS p.6 gives 0.8 W for the whole kit active.

## Thermal

All input power ends up as heat inside the enclosure.

| Line | Value | Param / source |
|---|---|---|
| Heat to dissipate | 1.4 W | `power.pod_power_max` (A-008) |
| Maximum ambient | 40 °C (ceilings run hotter than rooms in summer) | `env.ambient_max` (Owner round 2, Q-09) |
| Ambient range checked against ratings | 0 °C to 40 °C lies inside radar module -20 °C to 85 °C (MDS p.4) and XIAO -40 °C to 85 °C (XIAO) | REQ-ENV-001 |
| Kit maximum operating temperature | 85 °C | `sensor.kit_temp_max` (A-004; radar module MDS p.4, XIAO) |
| Allowed rise, kit air over ambient | 85 °C - 40 °C = 45 K | `thermal.kit_rise_allowed` |
| **Allowed thermal resistance, kit air to ambient** | **45 K / 1.4 W = 32.1 K/W** | `thermal.max_thermal_resistance` |
| Accessible surface temperature limit | set by a qualified human under IEC 62368-1 | REQ-SAFE-002; Q-17 |

The enclosure geometry that meets 32.1 K/W is not estimated at G0 (no sourced convection data); it is checked by analysis at G1/G2 and by test (TP-ENV-002, TP-SAFE-002).

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
| Printed parts (base plate, shell, radome, light pipe, T-bar clip), strain relief | to be quoted | `bom/bom.csv` with dated quotes (REQ-COST-003) |
| Fixings (screws, drywall anchors, concrete plugs) | to be quoted; in the BOM scope per Owner round 2 although not in the box (Q-19) | Q-10 closed |
| USB-C cable, adapter, raceway | outside the US$30 scope (pod only, Owner round 2); in-box decision open; see cost note below | Q-13, A-009 |
| **Prototype ceiling** | **50.00** | `cost.prototype_max` (Owner) |
| Prototype room after the kit | 50.00 - 28.99 = 21.01 | computed |
| **Production BOM ceiling** | **30.00**, pod only (shell, kit, fixings) at 10+ unit pricing | `cost.production_bom_max` (Owner; Owner round 2, Q-10) |
| Production room after the kit | 30.00 - 28.99 = 1.01 | computed; R-002 |
| **Real production BOM (reported per Owner round 2)** | **at least 28.99 + printed parts + fixings**; the printed parts and fixings are not yet quoted, so the total is not known. With the kit at US$28.99 the target holds only if everything else costs at most US$1.01 | R-002 |

The production line is likely unreachable (R-002): with the kit bought at the only published tier (10+), US$1.01 is left for everything else. The owner chose "kit as-is" (Q-01), so the only levers are a Seeed volume quote (asked in `docs/seeed-questions-draft.md`) or a later change to the architecture.

**Cost note, in-box cable (open product decision, Q-13).** A pod mounted at 2.2 m to 3.0 m needs a USB-C cable long enough to run down the wall to a socket, plus an adhesive raceway (Owner round 2). No price is sourced for a long USB-C cable, a raceway kit or a wall adapter, so each is a to-be-quoted line (A-009). They sit outside the US$30 pod-only BOM either way; if they ship in the box they add to the unit cost and packaging, and the cable must then also pass TP-PWR-004 (C-to-C start-up).

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
