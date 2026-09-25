# Interfaces (G0 draft)

Status: DRAFT, evidence level L0 (nothing here is measured). The structure is modelled in `model/system.sysml` (ports and interfaces named below); every number lives in `params/params.toml`, and this page only points at it. Owner decisions are cited as "Owner round 2" (`docs/intake/G0-owner-answers-2.md`); remaining open questions (Q-xx) are in `reviews/G0.md`; assumptions (A-xxx) in `ASSUMPTIONS.md`; source short names (DS, MDS, Wiki, XIAO, FDA1, Web) in `docs/sources/README.md`.

System boundary: the pod is the base plate, shell, radome, sensor kit, cable strain relief, gasket groove and the optional T-bar clip. Outside it: the ceiling, the drop-ceiling grid, the ceiling fixings (Forge proposes them; not in the box), the USB cable, the adhesive raceway, the USB wall adapter (whether cable and raceway ship in the box is open, Q-13), the home network (local Wi-Fi to Home Assistant, Owner round 2), a possible second pod in the same room, and the installer and occupants.

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
| IF-09 | Status LED light pipe | optical, mechanical | `LightPipe`, `LedLightPort` (`ledPath`) |
| IF-10 | Pod to pod (radar-to-radar) | RF | `Room.pods` [1..2] |

## IF-01 Ceiling to base plate (mechanical)

| Item | Value / status | Source |
|---|---|---|
| Ceilings | drywall (anchors), concrete (plugs), one screw-on base plate | Owner; REQ-MECH-001, -002 |
| Mount height | 2.2 m to 3.0 m above floor | `mount.height_min`, `mount.height_max` (Owner; Wiki; MDS p.10) |
| Retention | G0 placeholder: static pull of 4 x installed weight for 60 s; before G2: measured weight x a sourced safety factor | `mount.retention_load_factor`, `mount.retention_hold_time` (A-001); REQ-MECH-004, REQ-MECH-015 |
| Screw, anchor, plug type, size, count and hole pattern | Forge proposes at G1 from the anchor makers' datasheets; not in the box; named in the instructions | Owner round 2 (Q-05); REQ-MNT-003 |
| Orientation | antenna face parallel to the ceiling within 5°, facing the floor | `sensor.level_tolerance` (A-002); REQ-MECH-009 |

The base plate's ceiling face must be flat so the level tolerance holds on a flat ceiling; ceiling flatness itself is outside the pod.

## IF-02 T-bar clip adapter (mechanical, optional)

| Item | Value / status | Source |
|---|---|---|
| Function | holds the base plate on a drop-ceiling T-bar without drilling or cutting the tile | Owner; REQ-MECH-003 |
| Grid profile widths to fit | 15 mm and 24 mm | `tbar.grid_width_narrow`, `tbar.grid_width_wide` (Owner round 2, Q-07) |
| Retention | same test as IF-01 | REQ-MECH-004 |

## IF-03 Base plate to shell (mechanical, hidden fastening)

| Item | Value / status | Source |
|---|---|---|
| Constraint | no screw passes through the shell; no screw head visible from the room | REQ-MECH-006, REQ-UX-002 |
| Concept | hand twist-off (twist-lock or bayonet), detailed in the G1 concept tournament | Owner round 2 (Q-05/Q-06); REQ-MECH-016 |
| Tool-free removal | yes, by hand, no tools, no visible screws | Owner round 2; REQ-MECH-016, REQ-UX-002 |
| Kit location and cable | if the kit rides in the twisting part, the USB cable or connector must survive the twist; if it sits in the base plate, the reset button must still be reachable with the shell off (REQ-UX-006). G1 decides | R-017 |
| Retention | G0 placeholder 4 x (shell + kit) weight for 60 s; before G2 from REQ-MECH-015 | A-001; REQ-MECH-005 |
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
| Ingress target (IP code) | IPX4 (bathroom variant) | `gasket.ip_code` (Owner round 2, Q-08); REQ-MECH-018 |
| Gasket type | O-ring cord | `gasket.type` (Owner round 2, Q-08) |
| Sizing rule | gland depth, groove width and squeeze per ARSDG Table A (PDF p.20) for the chosen cross-section; general static squeeze 10 % to 40 % (ARSDG p.113); non-round groove inside corner radius at least 3 x cross-section and O-ring centreline length = groove centreline length (ARSDG p.90); O-ring volume never above minimum gland volume (ARSDG p.113) | REQ-MECH-017; `gasket.*` |
| Cord cross-section | **open parameter**, chosen at G1 (A-017). ARSDG Table A candidates (inches as published, mm = in x 25.4), axial (face) gland: 0.070 in (1.78 mm): depth 0.049-0.054 in (1.24-1.37 mm), squeeze 19-33 %, groove width 0.105 in (2.67 mm); 0.103 in (2.62 mm): depth 0.075-0.081 in (1.91-2.06 mm), squeeze 19-29 %, width 0.146 in (3.71 mm); 0.139 in (3.53 mm): depth 0.100-0.108 in (2.54-2.74 mm), squeeze 20-30 %, width 0.195 in (4.95 mm) | ARSDG p.20; column order in `docs/sources/apple-rubber-seal-design-guide-excerpt.txt` |
| Material | **open parameter** (chemical and temperature fit per ARSDG Section 6) | G1 |
| Cord splice | **open parameter**: ARSDG gives no rule for spliced cord | A-017 |
| Fastening compression load | **open parameter**: from the cord's durometer and squeeze; carried by the twist-lock (IF-03) | R-016 |
| Cable exit sealing | **open parameter**: the cable exit (IF-06) is a leak path in the bathroom variant | REQ-MECH-018; G1 |

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
| Light sensor window, LED visibility, reset-button access | no light-sensor window; LED only through the light pipe (IF-09); reset reached with the pod twisted off | Owner round 2 (Q-14); REQ-UX-004..006 |

## IF-06 USB-C power (electrical)

| Item | Value / status | Source |
|---|---|---|
| Voltage / current | 5 V, 1 A rated | `power.usb_voltage`, `power.usb_current_max`; Owner; DS p.6 |
| Pod draw | at most 1 A peak (REQ-PWR-002), at most 1.4 W steady (REQ-PWR-005) | `power.pod_power_max` (A-008); R-014 |
| Connector | the XIAO's on-board USB-C receptacle, used as-is | Owner round 2 (Q-01: kit as-is) |
| C-to-C source compatibility | must start from a USB Type-C wall adapter over a C-to-C cable; behaviour not published | REQ-PWR-004; R-012 |
| Battery | none (the XIAO battery pads are left unused) | REQ-PWR-003 |
| Mains | none inside the v1 pod; hardwired variant out of scope | REQ-ELEC-001 |
| Strain relief | clamps the cable jacket; pull does not reach the connector | REQ-MECH-011 |
| Cable exit | at the ceiling plane into the end of the adhesive raceway | REQ-MECH-012 |
| Cable, raceway and adapter in the box | **open product decision**: a 2.2 m to 3.0 m ceiling needs a long USB-C cable plus raceway; prices to be quoted (cost note in `docs/budgets.md`) | Owner round 2; Q-13; A-009 |

## IF-07 Radio and data

| Item | Value / status | Source |
|---|---|---|
| Radar | 60 GHz FMCW, 58 GHz to 62 GHz, 12 dBm transmit power, 4 dBi antenna | MDS p.3, p.4 |
| XIAO radio | 2.4 GHz Wi-Fi 6, Bluetooth LE (5.0 in the spec table, 5.3 in the introduction), IEEE 802.15.4 (Thread, Zigbee); on-board ceramic antenna, optional U.FL | XIAO; Wiki "Features" (Wi-Fi and Bluetooth) |
| Radar to XIAO | UART, 115200 baud default | MDS p.7 |
| Firmware | XIAO pre-flashed with ESPHome for Home Assistant; radar firmware and algorithms closed source | DS p.2, p.3; Wiki "Customised Service Description"; R-011 |
| Which radios are enabled; local or cloud | Wi-Fi to a local Home Assistant only | Owner round 2 (Q-02) |
| Other compute or radio | none: the XIAO is the only compute and radio | Owner round 2 (Q-01); REQ-EMC-005; R-010 |
| Credentials | no blank-credential mode; no universal default password | REQ-FW-002, REQ-FW-003 |

## IF-08 Installer and user

| Item | Value / status | Source |
|---|---|---|
| Installation | drill and fix base plate (IF-01) or clip to T-bar (IF-02); fit shell; route cable in raceway (IF-06) | REQ-MNT-003, REQ-MNT-004 |
| Commissioning | installer measures mounting height; firmware writes it to the radar (`setInstallationHeight`) | REQ-FW-001 |
| Placement rules | height range, coverage, seven Wiki keep-outs, room types, one person, up to two pods per room with minimum spacing | REQ-MNT-001, -002, -005, -006; REQ-UX-003 |
| Appearance | matte warm white, colour matched at the demo stage; no visible screw heads; only opening is the flush light pipe | REQ-UX-001, -002, -004, -005; Owner round 2 |
| Pod removal (cleaning, reset) | hand twist-off; reset button reachable once removed | REQ-MECH-016, REQ-UX-006 |
| Claims and UI wording | neutral terms only ("fall event", "presence"); deny-list applies to all user-facing text and Home Assistant entity names | REQ-SAFE-003, REQ-SAFE-004; `compliance/claims-wording.md` |
| Status LED behaviour | off in normal use; lit in setup, pairing and fault states; can be disabled in settings | REQ-FW-004..006 |

## IF-09 Status LED light pipe (optical and mechanical)

Owner round 2 (Q-14): "A tiny flush light pipe in the same matte warm white, OFF in normal use."

| Item | Value / status | Source |
|---|---|---|
| Light source | the kit's WS2812 RGB LED on the radar module board (the Wiki shows it on the right side of the module) | DS p.6; Wiki "Blink RGB LED" |
| Path | LED to shell surface through a light pipe; the pipe's room end is flush with the shell | REQ-UX-004 |
| Finish | same matte warm white as the shell; no metallic pigment | REQ-UX-004, REQ-UX-001, REQ-MECH-010 |
| Other constraints | adds no visible screw (REQ-UX-002); its show face prints on 0.4 mm FDM with no supports (REQ-MFG-001); passes the A/B sensing test (REQ-SYS-002) | R-018 |
| Placement | **open parameter**: the LED sits on the same board as the antenna, so the pipe probably crosses the 60° keep-out cone and breaks the uniform radome thickness (REQ-MECH-013). G1 routes it outside the cone or shows no degradation in TP-SYS-002 | R-018 |
| LED position on the board, pipe length and diameter | **open parameters**: measured on a kit at G1 | A-005 |
| Behaviour | off in normal use; lit in setup, pairing and fault states; disable option in settings | REQ-FW-004, -005, -006 |
| Not present | no light-sensor window (the BH1750 is unused); no reset pinhole | REQ-UX-005 |

## IF-10 Pod to pod (radar-to-radar)

Owner round 2 (Q-12): up to 2 pods per room, with a check for interference between them.

| Item | Value / status | Source |
|---|---|---|
| Pods per room | at most 2 | `pods.max_per_room`; REQ-MNT-006 |
| What the sources say | the Wiki lists "Multiple radars installed too close together" as a keep-out, with no distance; DS p.8 says the transmitter "must not be co-located or operating in conjunction with any other antenna or transmitter" (applicability to two separate pods is for a qualified human, Q-17); MDS says nothing | Wiki; DS p.8 |
| Minimum spacing | **open parameter**: found by TP-SYS-003 and asked of Seeed | REQ-SYS-003; R-007 |
| Acceptance | each pod gives the same outputs with the other pod on and off | REQ-SYS-003 |
