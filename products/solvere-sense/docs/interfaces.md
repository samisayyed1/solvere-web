# Interfaces (G0 draft)

Status: DRAFT, evidence level L0 (nothing here is measured). The structure is modelled in `model/system.sysml` (ports and interfaces named below); every number lives in `params/params.toml`, and this page only points at it. Open questions (Q-xx) are in `reviews/G0.md`; assumptions (A-xxx) in `ASSUMPTIONS.md`; source short names (DS, MDS, Wiki, XIAO, FDA1, Web) in `docs/sources/README.md`.

System boundary: the pod is the base plate, shell, radome, sensor kit, cable strain relief, gasket groove and the optional T-bar clip. Outside it: the ceiling, the drop-ceiling grid, the USB cable, the adhesive raceway, the USB wall adapter (whether these ship in the box is Q-13), the home network (Q-02), and the installer and occupants.

| ID | Interface | Type | Model element |
|---|---|---|---|
| IF-01 | Ceiling to base plate | mechanical | `CeilingFixPort` |
| IF-02 | T-bar clip adapter to grid | mechanical, optional | `TBarClipAdapter`, `TBarPort` |
| IF-03 | Base plate to shell | mechanical, hidden | `ShellBaseInterface` |
| IF-04 | Gasket groove | mechanical, defined now, used by the bathroom variant | `GasketGrooveInterface`, `GasketGroove`, `Gasket` |
| IF-05 | Sensor kit to enclosure and radome | mechanical, RF | `SensorKit.antenna` to `Radome.window` (`rfPath`) |
| IF-06 | USB-C power | electrical | `UsbCPowerPort`, `UsbPowerInterface`, `CableExitPort` |
| IF-07 | Radio and data | data | `WirelessDataPort` |
| IF-08 | Installer and user | user | instructions, commissioning, appearance |

## IF-01 Ceiling to base plate (mechanical)

| Item | Value / status | Source |
|---|---|---|
| Ceilings | drywall (anchors), concrete (plugs), one screw-on base plate | Owner; REQ-MECH-001, -002 |
| Mount height | 2.2 m to 3.0 m above floor | `mount.height_min`, `mount.height_max` (Owner; Wiki; MDS p.10) |
| Retention | static pull of 4 x installed weight for 60 s | `mount.retention_load_factor`, `mount.retention_hold_time` (A-001, Q-17); REQ-MECH-004 |
| Screw, anchor, plug type, size, count and hole pattern | open | Q-05; REQ-MNT-003 |
| Orientation | antenna face parallel to the ceiling within 5°, facing the floor | `sensor.level_tolerance` (A-002); REQ-MECH-009 |

The base plate's ceiling face must be flat so the level tolerance holds on a flat ceiling; ceiling flatness itself is outside the pod.

## IF-02 T-bar clip adapter (mechanical, optional)

| Item | Value / status | Source |
|---|---|---|
| Function | holds the base plate on a drop-ceiling T-bar without drilling or cutting the tile | Owner; REQ-MECH-003 |
| Grid profile widths to fit | open | Q-07 |
| Retention | same test as IF-01 | REQ-MECH-004 |

## IF-03 Base plate to shell (mechanical, hidden fastening)

| Item | Value / status | Source |
|---|---|---|
| Constraint | no screw passes through the shell; no screw head visible from the room | REQ-MECH-006, REQ-UX-002 |
| Concept | not chosen (candidates: twist-lock/bayonet, snap-fit); decided in the G1 concept tournament | G1 |
| Tool-free removal | open | Q-06 |
| Retention | static pull of 4 x (shell + kit) weight for 60 s | A-001; REQ-MECH-005 |
| Mating clearance | 0.5 mm FDM, 0.2 mm SLA, 0.6 mm MJF | `mfg.fdm.clearance_connecting`, `mfg.sla.clearance_connecting`, `mfg.mjf.clearance_connecting`; REQ-MFG-005 |
| Snap-fit strain (if a snap is chosen) | from R5d per chosen material; PETG has no row in R5d | R5d; material choice at G1 |
| Bathroom load case | the fastening must also hold the gasket compression load without changing the shell | IF-04; R-016 |

## IF-04 Gasket groove (mechanical; defined now, used by the bathroom variant)

The groove is a defined interface in v1, even though v1 carries no gasket (Owner: "same shell plus a gasket. Design the gasket-groove interface now").

| Item | Value / status | Source |
|---|---|---|
| Location | on the base-plate side of the shell-to-base joint, mating with a rim on the shell, so one shell serves both variants | Owner; `BasePlate.groove` to `Shell.rim` |
| v1 | groove present and continuous around the full shell-to-base perimeter; no gasket fitted | REQ-MECH-007 |
| Bathroom variant | gasket held compressed around the full perimeter with the shell attached | REQ-MECH-008 |
| Ingress target (IP code) | **open parameter** | Q-08 |
| Gasket type (cord, moulded profile, foam) and material | **open parameter** | Q-08 |
| Groove width, depth, corner radius, gland fill, compression range | **open parameters**: set from the chosen gasket's datasheet | Q-08 |
| Fastening compression load | **open parameter**: from the gasket datasheet; carried by IF-03 | R-016 |
| Cable exit sealing | **open parameter**: the cable exit (IF-06) is a leak path in the bathroom variant | Q-08 |

## IF-05 Sensor kit to enclosure and radome (mechanical and RF)

| Item | Value / status | Source |
|---|---|---|
| Kit | Seeed MR60FDA2 kit, SKU 114993388: radar module with 3D-printed case + XIAO ESP32C6 with ESPHome | DS p.1, p.7 |
| On the radar module board | BH1750 light sensor, WS2812 RGB LED, reset button ("Rest"), Grove port (D0, D10), 2.54 mm headers | DS p.2, p.6 |
| Radar module outline | 25 mm x 31.5 mm | `sensor.radar_module_width`, `sensor.radar_module_length` (MDS p.3) |
| XIAO outline | 21 mm x 17.8 mm | `sensor.xiao_length`, `sensor.xiao_width` (XIAO) |
| Kit carrier-board outline, stack height, mounting holes | not published; measure a kit before CAD | A-005 |
| Radar frequency | 58 GHz to 62 GHz; design centre 60 GHz | `sensor.freq_min`, `sensor.freq_max`, `sensor.freq_centre` (MDS p.4, p.12) |
| Metal keep-out | no metal, metallic pigment or conductive coating inside a 60° half-angle cone about boresight | `radome.keepout_half_angle`; REQ-MECH-010; R-013 |
| Radome thickness | integer multiple of half the wavelength in the material, T = N·c/(2·f·sqrt(εr)); εr for the chosen material to be measured | MDS p.12 item 3; REQ-MECH-013; TP-SYS-002 coupons |
| Antenna to radome inner surface | integer multiple of 2.5 mm | `radome.antenna_gap_step` (MDS p.12 item 4); REQ-MECH-014 |
| Radome surface | smooth, uniform thickness; low εr and tan δ materials preferred | MDS p.12 item 2, p.11 item 1 |
| Radome finish | matte warm white, no metallic pigment | REQ-UX-001, REQ-MECH-010 |
| Light sensor window, LED visibility, reset-button access | open | Q-14 |

## IF-06 USB-C power (electrical)

| Item | Value / status | Source |
|---|---|---|
| Voltage / current | 5 V, 1 A rated | `power.usb_voltage`, `power.usb_current_max`; Owner; DS p.6 |
| Pod draw | at most 1 A peak (REQ-PWR-002), at most 1.4 W steady (REQ-PWR-005) | `power.pod_power_max` (A-008); R-014 |
| Connector | the XIAO's on-board USB-C receptacle, used as-is | A-006, Q-01 |
| C-to-C source compatibility | must start from a USB Type-C wall adapter over a C-to-C cable; behaviour not published | REQ-PWR-004; R-012 |
| Battery | none (the XIAO battery pads are left unused) | REQ-PWR-003 |
| Mains | none inside the v1 pod; hardwired variant out of scope | REQ-ELEC-001 |
| Strain relief | clamps the cable jacket; pull does not reach the connector | REQ-MECH-011 |
| Cable exit | at the ceiling plane into the end of the adhesive raceway | REQ-MECH-012; raceway product, size and route Q-13 (A-009) |

## IF-07 Radio and data

| Item | Value / status | Source |
|---|---|---|
| Radar | 60 GHz FMCW, 58 GHz to 62 GHz, 12 dBm transmit power, 4 dBi antenna | MDS p.3, p.4 |
| XIAO radio | 2.4 GHz Wi-Fi 6, Bluetooth LE (5.0 in the spec table, 5.3 in the introduction), IEEE 802.15.4 (Thread, Zigbee); on-board ceramic antenna, optional U.FL | XIAO; Wiki "Features" (Wi-Fi and Bluetooth) |
| Radar to XIAO | UART, 115200 baud default | MDS p.7 |
| Firmware | XIAO pre-flashed with ESPHome for Home Assistant; radar firmware and algorithms closed source | DS p.2, p.3; Wiki "Customised Service Description"; R-011 |
| Which radios are enabled; local or cloud | open (default: local Home Assistant only) | Q-02, A-014 |
| Other compute or radio (e.g. a voice board) | not assumed; the DS p.8 FCC statement forbids co-location without reassessment | Q-01; REQ-EMC-005; R-010 |
| Credentials | no blank-credential mode; no universal default password | REQ-FW-002, REQ-FW-003 |

## IF-08 Installer and user

| Item | Value / status | Source |
|---|---|---|
| Installation | drill and fix base plate (IF-01) or clip to T-bar (IF-02); fit shell; route cable in raceway (IF-06) | REQ-MNT-003, REQ-MNT-004 |
| Commissioning | installer measures mounting height; firmware writes it to the radar (`setInstallationHeight`) | REQ-FW-001 |
| Placement rules | height range, coverage, seven Wiki keep-outs, room types, number of people | REQ-MNT-001, -002, -005; REQ-UX-003 |
| Appearance | matte warm white; no visible screw heads | REQ-UX-001, REQ-UX-002; Q-04 |
| Shell removal (cleaning, reset) | tool-free or tool-needed open | Q-06 |
| Claims | no medical or emergency-alarm claims | REQ-SAFE-003; Q-15 |
