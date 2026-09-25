# Interfaces (G0 draft)

Status: DRAFT, evidence level L0 (nothing here is measured). The structure is modelled in `model/system.sysml` (ports and interfaces named below); every number lives in `params/params.toml`, and this page only points at it. Open questions (Q-xx) are listed in `reviews/G0.md`; assumptions (A-xxx) in `ASSUMPTIONS.md`.

System boundary: the pod is the base plate, shell, radome, sensor kit, cable strain relief, gasket groove and the optional T-bar clip. Outside it: the ceiling, the drop-ceiling grid, the USB cable, the adhesive raceway and the USB wall adapter (whether the cable and adapter ship in the box is Q-09).

## IF-01 Ceiling to base plate (mechanical)

| Item | Value / status | Source |
|---|---|---|
| Model element | `CeilingFixPort` on `BasePlate` | `model/system.sysml` |
| Ceilings | drywall (anchors), concrete (plugs), one screw-on base plate | Owner; REQ-MECH-001, -002 |
| Mount height | 2.2 m to 3.0 m above floor | `mount.height_min`, `mount.height_max` |
| Retention | static pull of 4 x installed weight for 60 s | `mount.retention_load_factor`, `mount.retention_hold_time` (A-003); REQ-MECH-004 |
| Screw, anchor and hole pattern | open | Q-10 |
| Orientation | antenna face parallel to ceiling within 5 deg, facing floor | `sensor.level_tolerance` (A-004); REQ-MECH-009 |

The base plate's ceiling face must be flat so the level tolerance holds on a flat ceiling; ceiling flatness itself is outside the pod.

## IF-02 T-bar clip adapter (mechanical, optional)

| Item | Value / status | Source |
|---|---|---|
| Model element | `TBarClipAdapter` [0..1], `TBarPort` | `model/system.sysml` |
| Function | holds the base plate on a drop-ceiling T-bar without drilling or cutting the tile | Owner; REQ-MECH-003 |
| Grid widths to fit | open | Q-11 |
| Retention | same test as IF-01 | REQ-MECH-004 |

## IF-03 Base plate to shell (mechanical, hidden fastening)

| Item | Value / status | Source |
|---|---|---|
| Model element | `ShellBaseInterface` (`BasePlate.toShell` to `Shell.toBase`) | `model/system.sysml` |
| Constraint | no screw passes through the shell; no screw head visible from the room | REQ-MECH-006, REQ-UX-002 |
| Concept | not chosen (candidates: twist-lock/bayonet, snap-fit); decided in the G1 concept tournament | G1 |
| Tool-free removal | open | Q-08 |
| Retention | static pull of 4 x (shell + kit) weight for 60 s | A-003; REQ-MECH-005 |
| Mating clearance | 0.5 mm FDM, 0.2 mm SLA, 0.6 mm MJF | `mfg.fdm.clearance_connecting`, `mfg.sla.clearance_connecting`, `mfg.mjf.clearance_connecting`; REQ-MFG-005 |
| Snap-fit strain (if a snap is chosen) | from R5d per chosen material; PETG has no row in R5d | R5d; material choice at G1 |

## IF-04 Gasket groove (mechanical, designed now, used by the bathroom variant)

| Item | Value / status | Source |
|---|---|---|
| Model element | `GasketGrooveInterface` (`BasePlate.groove` to `Shell.rim`), `GasketGroove`, `Gasket` [0..1] | `model/system.sysml` |
| v1 | groove present and continuous around the full shell-to-base perimeter; no gasket fitted | Owner; REQ-MECH-007 |
| Bathroom variant | gasket compressed around the full perimeter with the shell attached | REQ-MECH-008 |
| Groove width, depth, gland fill, compression | open: set from the chosen gasket's datasheet | Q-12 |
| Ingress target (IP code) | open | Q-12 |
| Consequence for IF-03 | the fastening must hold the gasket compression load in the bathroom variant without changing the shell | design note for G1 |

The groove sits on the base-plate side so the same shell serves both variants (Owner: "same shell plus a gasket").

## IF-05 Sensor kit to enclosure (mechanical and RF)

| Item | Value / status | Source |
|---|---|---|
| Model element | `SensorKit.antenna` to `Radome.window` (`rfPath`) | `model/system.sysml` |
| Kit | Seeed MR60FDA2 kit, SKU 114993388: radar module + XIAO ESP32C6 | DS p.1, p.7; A-009 |
| Board outline | about 47 mm x 29 mm (+/- 1 mm), estimated from a Seeed ruler photo; stack height with the XIAO unknown | `sensor.board_length`, `sensor.board_width` (A-008) |
| Mounting holes | 2 holes visible in the Seeed photo; diameter and position not published | measure with A-008 |
| Metal keep-out | no metal, metallic pigment or conductive coating inside the 120 deg x 100 deg FoV | `sensor.fov_horizontal`, `sensor.fov_vertical`; REQ-MECH-010; R-013 (FoV conflict) |
| Radome thickness | not set; depends on material permittivity at 60 GHz, unsourced. Half-wave rule: t = n x 4.997 mm / (2 x sqrt(er)), er to be sourced or measured | `sensor.wavelength_free_space` (A-015); acceptance by A/B test REQ-SYS-002 |
| Radome finish | matte warm white, no metallic pigment | REQ-UX-001, REQ-MECH-010 |
| Radome guidance from Seeed | none found in DS or Wiki (searched 2026-09-25); ask Seeed | R-004 |
| Light sensor (BH1750) and RGB LED (WS2812) | whether a light window or visible LED is needed is open | Q-07 |
| Reset button | access requirement open | Q-07 |

## IF-06 USB-C power (electrical)

| Item | Value / status | Source |
|---|---|---|
| Model element | `UsbCPowerPort`, `UsbPowerInterface` (`adapter.usbOut` to `pod.sensor.usbC.power`) | `model/system.sysml` |
| Voltage / current | 5 V, 1 A rated | `power.usb_voltage`, `power.usb_current_max`; Owner; DS p.6 |
| Pod draw | at most 1 A peak (REQ-PWR-002), at most 1.4 W steady (REQ-PWR-005) | `power.pod_power_max` |
| Connector | the kit's own on-board USB-C receptacle (use as-is, pending Q-01) | A-009 |
| C-to-C source compatibility | must start from a USB Type-C wall adapter over a C-to-C cable; kit behaviour not published | REQ-PWR-004; R-012 |
| Battery | none | REQ-PWR-003 |
| Mains | none inside the v1 pod; hardwired variant out of scope | REQ-ELEC-001 |
| Strain relief | clamps the cable jacket; pull does not reach the connector | REQ-MECH-011 |
| Cable exit | at the ceiling plane into the end of the adhesive raceway | REQ-MECH-012; raceway product, size and route Q-09 (A-018) |

## IF-07 Radio and data

| Item | Value / status | Source |
|---|---|---|
| Radios in the kit | 60 GHz radar; XIAO ESP32C6 Wi-Fi and Bluetooth | DS p.2, p.6 |
| Firmware | XIAO pre-flashed with ESPHome; radar firmware closed source | DS p.2; Wiki "Customised Service Description" |
| Network use (Home Assistant local only, or internet) | open | Q-02 |
| Other compute or radio (e.g. "Voice PE") | not assumed; the DS p.8 FCC statement forbids co-location without reassessment | Q-01; REQ-EMC-005 |
| Credentials | no blank-credential mode; no universal default password | REQ-FW-002, REQ-FW-003 |
| Commissioning | installer's measured height written to the radar | REQ-FW-001 |

## IF-08 Installer and user

Instructions content: REQ-UX-003, REQ-MNT-001 to REQ-MNT-004. Appearance: REQ-UX-001, REQ-UX-002.
