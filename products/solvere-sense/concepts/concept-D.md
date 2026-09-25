# Concept D: two-part straight-pull pod, kit fixed in the base plate

- **Lens:** lowest cost and best manufacturability: FDM PETG for G3 fit checks, SLA/MJF demo units, and the easiest route to a future production process, with the cheapest BOM against the US$30 target.
- **Status:** G1 concept, L0. Nothing here is measured. Every number is cited to `params/params.toml`, a source or a requirement; everything else is "TBD at G2".
- **Author:** concept generator D (G1 tournament). Written without reading any other concept.
- **Revision 1 (2026-09-25), after the judges' gate review.** Two changes:
  - **GATE-S3:** the glow pocket in the radome is removed. The radome floor is now one uniform thickness over the whole footprint of the 60° cone, and the LED light path moves to the skirt, outside the cone (§2, light path).
  - **GATE-S1:** the bayonet now seats on flat bearing lands in a drop-in notch, with a hard stop. The 45° faces are kept only on non-bearing lead-ins and print chamfers, so an axial load has no back-drive or cam-out component. Release is push up, then twist (§2, attach).
  - The cost and manufacturability intent is unchanged: still two printed parts, no light-pipe part, and straight-pull geometry.

## 1. Summary

The pod is **two printed parts plus the kit**: a **base plate** that screws to the ceiling and carries the MR60FDA2 kit, the cable, the strain relief, the gasket groove and the fixed half of the bayonet, and a **one-piece shell-radome** (a shallow cup whose flat floor is the radome) that twists on and off by hand. The kit never moves when the shell twists, so the USB cable and connector are never twisted (this closes R-017 by architecture), and the reset button is exposed as soon as the shell comes off (REQ-UX-006). There is **no separate light pipe part**: the LED glows through a thinned groove in the **skirt**, which lies outside the 60° cone, so the radome floor stays uniform. The bayonet **seats in a notch on flat lands with a hard stop**; 45° faces are used only on lead-ins and print chamfers. Every show face of both parts prints on a 0.4 mm FDM printer with no support, and both parts are also **straight-pull mouldable** (no side actions) with draft designed in from G2. The strain relief is a **printed serpentine channel** in the base plate, not a bought part. The optional T-bar clip is one parametric CAD part printed in a 15 mm and a 24 mm variant. The concept deliberately minimises part count, bought parts and process steps; it does not make the US$30 target reachable, because the kit alone is US$28.99 (R-002), and the report below says so.

## 2. Architecture and part list

| # | Part | Function | G3 fit check | Demo units | Production path (future) |
|---|---|---|---|---|---|
| P1 | Shell-radome (one piece) | Room-facing cup; flat floor is the radome (IF-05); outward bayonet lugs at the rim with a drop-in foot; LED glow groove in the skirt, outside the cone (IF-09); rim seals on the gasket (IF-04) | FDM PETG, printed floor-down (radome outer face on the bed); fit-check only | SLA, Formlabs Flame Retardant Resin (smooth radome face, MDS §8 item 2; UL 94 listing in §8 below) | Straight-pull injection moulding; radome material chosen from the MDS §8 table (PC, ABS, PBT, PE have published εr/tan δ) |
| P2 | Base plate | Ceiling fixing (IF-01); kit cradle with integral snap arms; bayonet collar with inward lugs carrying a flat seat land, a notch and a hard stop; face gasket groove (IF-04); cable channel with serpentine strain relief and exit at the ceiling plane (IF-06) | FDM PETG, printed ceiling-face-down; fit-check only | MJF, HP 3D HR PA 12 FR (tougher snaps and lugs; UL 94 listing in §8) | Straight-pull moulding; lug undersides formed through shut-off windows in the hidden ceiling face |
| P3 | T-bar clip (optional) | Bridges a T-bar flange and presents the base-plate screw pattern (IF-02); one CAD, parameter `tbar.grid_width_*` selects 15 or 24 mm | FDM PETG; fit-check only | MJF, HP 3D HR PA 12 FR | Straight-pull moulding, one tool with two jaw inserts |
| K1 | Seeed MR60FDA2 kit, SKU 114993388 | Radar module + XIAO ESP32C6 (bought, used as-is; Owner round 2 Q-01). The kit's own 3D-printed case is not used in the pod | bought | bought | bought |
| F1 | Ceiling fixings: screws + drywall anchors, or screws + concrete plugs | IF-01, not in the box (Owner round 2 Q-05) | retail | retail | retail |
| F2 | Cable tie (fallback only) | Positive jacket clamp if the serpentine fails TP-MECH-011 | retail | retail | retail |
| G1 | O-ring cord gasket | Bathroom variant only; not fitted in v1 (REQ-MECH-007) | - | - | cord supplier |

Nothing else: no light-pipe part, no inserts, no metal hardware in the pod other than the ceiling screws and anchors, no adhesive, no labels on show faces.

### How it attaches and detaches (IF-03)
- **How the shell goes on:**
  - The base plate carries a downward collar with inward lugs. The shell rim carries outward lugs.
  - The shell lugs enter axially through the gaps between the collar lugs. The user pushes the shell up and twists it.
  - A short entry ramp, with a 45° lead-in, lifts each shell lug over a lip. The lug then drops into a **notch** in a **flat seat land**, whose face is perpendicular to the pod axis, and stops against a **hard-stop wall** at the end of travel.
- **Why it cannot back off:**
  - At the seat the load-bearing faces are flat-on-flat and perpendicular to the axis. Gravity and the axial pull load therefore make no torque that could rotate the shell back.
  - The notch walls run parallel to the axis. To rotate back, the shell must first be lifted by the notch depth against gravity, and in the bathroom variant also against the gasket preload.
  - The hard stop prevents over-rotation.
  - Release is therefore two deliberate actions: push the shell toward the ceiling, then twist. A knock or vibration supplies neither the lift nor the torque.
  - A small printed click detent is kept as tactile feedback only; retention does not rely on it.
- **Sizes:** lug count, notch depth, land width, ramp lead and twist angle are TBD at G2.
- **No cam-out:** the 45° faces now appear only on non-bearing surfaces: lead-ins, entry chamfers and print chamfers. The seat contact is flat, so an axial load has no radial component and cannot spread the collar. Radial location comes from the shell skirt's clearance fit in the collar bore, not from cones.
- **One locking angle:** one lug is wider than the others, so the shell seats at one angle only. That keeps the skirt glow groove on the LED side of the fixed kit.
- Clearance at the bayonet is a CAD parameter switched per process: 0.5 mm FDM, 0.2 mm SLA, 0.6 mm MJF (`mfg.fdm/sla/mjf.clearance_connecting`, REQ-MFG-005). For a mixed demo pair (SLA shell on an MJF base) the larger value, 0.6 mm, applies.
- No screw passes through the shell (REQ-MECH-006). The ceiling screw heads sit in the base plate, under the shell (REQ-UX-002).

### Kit mounting and radome geometry (IF-05, MDS §8)
- The kit sits in a cradle of posts and cantilever snap arms rising from the base plate's room face. The cradle seat is parallel to the base plate's ceiling face, which is the print-bed face, so the level requirement is set by the flattest surface of the part (REQ-MECH-009, 5° per `sensor.level_tolerance`, A-002).
- The antenna faces the floor. The antenna-to-radome gap is **N × 2.5 mm** (`radome.antenna_gap_step`, MDS p.12 item 4, REQ-MECH-014). N is TBD at G2 and is set from the stack: base-plate seat to kit board (kit stack height is unpublished, A-005) and base-plate lug face to shell floor. Gap tolerance: open (R-001).
- Radome thickness **T = N·c/(2·f·√εr)** (MDS p.12 item 3, REQ-MECH-013), with f = 60 GHz (`sensor.freq_centre`) and λ0 = 4.997 mm (`sensor.wavelength_free_space`), so T = N × 4.997/(2√εr) mm. εr for PETG, SLA resin and PA12 is not in the MDS table, so T is set per material from the TP-SYS-002 coupons. As a scale check only, PC from the MDS table (εr 2.9) gives 1.47 mm for N = 1 and 2.93 mm for N = 2. Numbers for the pod's materials: TBD at G2.
- The floor is flat, smooth and of uniform thickness across the whole 60° half-angle cone (`radome.keepout_half_angle`, MDS §8 item 2, REQ-MECH-010). The window diameter follows from the gap and the cone and is TBD at G2. Printing the floor on the bed gives the smoothest, flattest face for FDM.
- There is no metal in the cone. The only metal in the pod is the ceiling screws and anchors, which sit behind the antenna plane and so outside the forward cone. The finish has no metallic pigment (REQ-MECH-010, REQ-UX-001).

### Light path: skirt glow groove outside the cone (IF-09, R-018), Revision 1
- **Where the LED is:** the only source statement is the Wiki "Blink RGB LED" section: the "RGB LED on the right side of the mmWave Sensor Modules" (Wiki; DS p.6 names it as a WS2812). Its exact coordinates relative to the antenna are unpublished (A-005) and are measured on a kit at G1.
- **Uniform radome:** the radome floor has **one thickness, T(N)**, with no pocket, step or opening, over its whole inner face out to the skirt. The skirt's inner radius is at least r_ant + √3·d, where r_ant is the antenna's half-extent (measured, A-005) and d = N × 2.5 mm is the gap. That radius is where the 60° cone (`radome.keepout_half_angle`) meets the floor's inner face, so the whole cone footprint falls on the uniform floor, and the floor-to-skirt corner lies outside it (MDS §8 item 2).
- **Glow groove:** a vertical blind groove on the skirt's inner face, on the LED side (the single-angle lock places it), thins the skirt locally. The outer face stays unbroken, flush and matte warm white (REQ-UX-004, REQ-UX-005).
  - It sits between the antenna plane and the floor, which puts it outside the cone by construction: every skirt point shallower than the floor, at a radius of at least r_ant + √3·d, is more than 60° off boresight.
  - The wall left at the groove is at least the larger of 1.2 mm (`mfg.fdm.min_wall`) and the UL 94 listed thickness for the class the qualified human sets (GATE-S2).
  - The groove is open at the rim, so it is straight-pull in a mould and needs no support in FDM. It stops inside the seal band on the rim face, so the gasket contact stays continuous (IF-04).
  - It adds no part and no assembly step.
- **Unknown and tested:** whether the LED's sideways light makes a visible spot through that wall. It is checked by eye in TP-UX-004 once the LED position is measured. The cradle places the kit with its LED edge next to the skirt.
- **Fallbacks, in cost order:**
  1. A short horizontal clear light guide from the LED edge to the skirt, kept above the cone boundary (depth below the antenna plane less than its radial offset ÷ √3). It adds one part, to be quoted, and needs a UL 94-listed clear grade.
  2. A separate LED on the kit's Grove port, mounted at the skirt. This is not a radio, so REQ-EMC-005 is unaffected. It adds a part and a firmware change.

### Cable entry and strain relief (IF-06)
- The USB-C plug enters the kit's XIAO receptacle inside the base plate. The cable leaves through a hole in the base plate, inboard of the gasket groove, into a channel moulded into the **ceiling face**. It runs under the groove and exits at the base plate's outer edge at the ceiling plane, into the end of the raceway (REQ-MECH-012).
- The channel includes a serpentine of printed posts that grips the cable jacket by friction, so a pull on the raceway side does not reach the connector (REQ-MECH-011). Two slots beside the serpentine accept a cable tie as the fallback (F2).
- In print orientation the channel roof is a hidden bridge, limited to 10 mm (`mfg.fdm.max_bridge_hidden`). The cable diameter depends on the open cable decision (Q-13, A-009) and must fit within that. Serpentine geometry: TBD at G2.
- The cable never twists, because the kit is fixed (R-017).

### T-bar adapter, 15 mm and 24 mm (IF-02)
- P3 is a plate with two jaws that grip the T-bar flange edges without drilling or cutting the tile (REQ-MECH-003). It carries bosses at the base plate's screw pattern, so the same screws (F1) fix P2 to P3.
- A single CAD part with the jaw span driven by `tbar.grid_width_narrow` (15 mm) or `tbar.grid_width_wide` (24 mm) gives two printed variants and adds no new design. Flange thickness, bulb height and tile-edge clearance are not sourced (TBD at G2, measured on real grid samples).

### Gasket-groove provision (IF-04)
- A continuous face (axial) groove on the base plate's room face, inside the collar, mates with the shell rim, as IF-04 places it. It is present in every v1 part (REQ-MECH-007).
- Candidate cross-sections and gland sizes come from ARSDG Table A p.20 (listed in IF-04: 1.78, 2.62 and 3.53 mm cord). The inside corner radius is at least 3× the cross-section (`gasket.corner_radius_factor`, ARSDG p.90). A round groove avoids corners altogether. The cross-section choice is TBD at G2 (A-017).
- The groove opens upward in print orientation (no support) and is straight-pull in a mould.
- The notch depth and the entry-ramp lip set the squeeze: the ramp over-compresses the cord slightly, then the lug drops into the notch at the design squeeze. Twisting drags the rim across the cord only during the ramp (R-016).
- The cable hole inboard of the groove is a leak path in the bathroom variant. It needs a grommet or a potted cable exit then; not designed at G1.

### FDM printability (REQ-MFG-001..-004)
- **P1** prints floor-down. The show faces (outer floor and outer skirt) are on the bed or vertical. The glow groove is vertical and open at the rim. The rim lugs' flat bearing undersides are hidden faces: they are carried on a 45° gusset from the skirt, with a short flat band left as a hidden overhang. No supports, no show-face bridges.
- **P2** prints ceiling-face-down. The collar, cradle posts and snap arms are vertical. The flat seat lands and notch roofs face the bed and are printed as hidden bridges anchored on the collar wall and the hard-stop wall, span ≤ 10 mm (`mfg.fdm.max_bridge_hidden`). The gasket groove opens upward. The cable-channel roof is another hidden bridge. P2 has no show face apart from the collar's outer band.
- The hidden flat lands are a print-quality risk (sag lowers the bearing area), not a requirement breach: REQ-MFG-001 to -003 govern show faces. They are checked on the first FDM print, and in a mould they are straight-pull (the base lugs through shut-off windows in the hidden ceiling face).
- **P3** prints flat with 45° jaw lead-ins. Its jaw undersides are hidden faces.
- **Walls:** one nominal wall for P1 skirt, P2 and P3 of at least 2.5 mm, which meets both the 1.2 mm FDM minimum (`mfg.fdm.min_wall`, REQ-MFG-004) and the 2.5 mm MJF figure (`mfg.mjf.wall_min_pn`). That settles R-015 by taking the larger value. The radome floor is governed by REQ-MECH-013, not by this wall, and must still be at least 1.2 mm for FDM. The radome floor has one thickness, T(N), chosen to be at least 1.2 mm and at least the UL 94 listed thickness. The skirt groove keeps the same minimum.
- **Production:** from G2, add at least 2° draft to vertical walls (`injection_molding.toml` `draft_min_general_deg`) and inside radii of at least 0.5× wall. Neither harms FDM, so the G3 CAD becomes the tooling CAD without a redesign.

## 3. Requirement-by-requirement assessment (all 66)

M = meets (by concept), R = at risk (reason given), N = not addressed by this concept (belongs to another discipline or stage; stated why).

| REQ | Status | Note |
|---|---|---|
| SYS-001 | R | Sensor limit, not geometry: corners at 2.12 m exceed the 2 m radius (R-003); TP-SYS-001; radome per MDS §8 |
| SYS-002 | R | Radome εr unmeasured for PETG/resin/PA12 (R-001); radome uniform; the skirt groove is outside the cone (R-018 reduced); TP-SYS-002 A/B |
| SYS-003 | R | Spacing by test (R-007); concept adds nothing that helps or hinders |
| MECH-001 | M | Base plate with screws and drywall anchors (types and sizes TBD at G2 from anchor datasheets) |
| MECH-002 | M | Same base plate, screws and concrete plugs |
| MECH-003 | R | P3 in two variants; flange/tile geometry unsourced; slip along T-bar under load untested |
| MECH-004 | R | Depends on anchor choice and measured mass; placeholder load A-001 |
| MECH-005 | R | Flat notch seat with a hard stop (no back-drive, no cam-out); lug shear and creep at 40 °C unknown; hidden-land print quality; test |
| MECH-006 | M | Bayonet only; no screw through the shell |
| MECH-007 | M | Continuous face groove on P2 in all builds |
| MECH-008 | R | Squeeze set by notch depth and tolerance stack; bathroom only (R-016) |
| MECH-009 | M | Kit seat parallel to the bed face of P2; skirt fits in the collar bore; ceiling flatness outside the pod |
| MECH-010 | M | No metal forward of the antenna plane; no metallic pigment specified |
| MECH-011 | R | Serpentine friction hold unproven; cable-tie fallback; pull load set under MECH-015 |
| MECH-012 | M | Channel in the ceiling face exits at the ceiling plane into the raceway end |
| MECH-013 | R | Achievable by construction (one uniform floor thickness, no pocket); εr unknown, so T is unknown until TP-SYS-002 |
| MECH-014 | R | N × 2.5 mm by stack design; kit stack height unpublished (A-005), tolerance open |
| MECH-015 | N | Systems/qualified-human task before G2; concept supplies the parts to weigh |
| MECH-016 | M | Hand twist; kit and cable stay still (R-017 closed by architecture) |
| MECH-017 | R | Groove sized from ARSDG Table A at G2; cord splice rule absent (A-017) |
| MECH-018 | R | Bathroom only; cable hole needs a grommet not yet designed; test method via Q-17 |
| PWR-001 | M | Kit's own USB-C used as-is |
| PWR-002 | R | Kit property, not the enclosure (R-014); measure |
| PWR-003 | M | No battery in the BOM |
| PWR-004 | R | XIAO C-to-C sink behaviour unpublished (R-012) |
| PWR-005 | R | Kit property (A-007, A-008); measure |
| ELEC-001 | M | No mains conductor; USB only |
| ENV-001 | R | Kit ratings contain 0-40 °C; PETG softening and bayonet creep near 40 °C untested |
| ENV-002 | R | Kit in a closed cup with 2.5 mm walls and no vents; 32.1 K/W allowed (`thermal.max_thermal_resistance`) is unverified; TP-ENV-002 |
| SAFE-001 | R | Demo grades have UL 94 listings (Formlabs FR Resin V-0 at 3 mm; HP PA 12 FR V0 at 2.5 mm; §8). The class is set by a qualified human. FDM PETG is fit-check only. The production grade is not yet chosen |
| SAFE-002 | R | Limit from a qualified human (Q-17); test |
| SAFE-003 | N | Labelling and marketing text, not the enclosure |
| SAFE-004 | N | Wording and firmware entity names; no text is moulded on the shell in this concept |
| EMC-001 | R | Kit plus a plastic enclosure; test (Q-03) |
| EMC-002 | R | Grant coverage of the kit as built in is for a qualified human |
| EMC-003 | R | Test; standards to be confirmed by a qualified human |
| EMC-004 | R | Approval route for a qualified human |
| EMC-005 | M | No added transmitter |
| FW-001 | N | Firmware |
| FW-002 | N | Firmware |
| FW-003 | N | Firmware |
| FW-004 | N | Firmware (hardware supplies the skirt glow groove) |
| FW-005 | N | Firmware |
| FW-006 | N | Firmware |
| UX-001 | R | Colour matched at demo (Q-04). The FR demo resin is light grey (Formlabs TDS), so the demo parts need a non-metallic warm-white coating, and that coating's effect on UL 94 and on the radome is unassessed |
| UX-002 | M | Screw heads hidden under the shell |
| UX-003 | N | Instructions |
| UX-004 | R | Flush and same colour by construction; light through the skirt groove unproven until the LED is measured (A-005); light-guide or Grove-LED fallback |
| UX-005 | M | Outer face unbroken; BH1750 behind an unbroken wall; no pinhole |
| UX-006 | M | Kit fixed in P2; button exposed when P1 is off (button position A-005) |
| MNT-001 | N | Instructions |
| MNT-002 | N | Instructions |
| MNT-003 | R | Concept picks fixing types; sizes and part numbers TBD at G2 from datasheets |
| MNT-004 | N | Instructions; exit geometry supports it |
| MNT-005 | N | Instructions |
| MNT-006 | N | Instructions; spacing from TP-SYS-003 |
| MFG-001 | M | All three parts print without support on show faces (orientation above) |
| MFG-002 | M | Show faces are vertical or on the bed; 45° only on lead-ins and gussets; flat lands are hidden faces |
| MFG-003 | M | No show-face bridge; the only bridge is the hidden cable channel (at most 10 mm) |
| MFG-004 | M | Wall of at least 2.5 mm meets it; the radome floor and skirt groove are held at 1.2 mm or more |
| MFG-005 | M | Clearance is a per-process CAD parameter |
| MFG-006 | M | All parts are FDM PETG-printable |
| MFG-007 | M | P1 in SLA FR resin, P2 and P3 in MJF PA 12 FR; the 2.5 mm wall meets the MJF minimum |
| COST-001 | R | 50.00 - 28.99 = 21.01 left for two or three printed parts and fixings; no quote yet |
| COST-002 | R | Practically unreachable: 1.01 left after the kit (R-002); this concept minimises what that 1.01 must cover |
| COST-003 | N | BOM discipline (`bom/bom.csv`); every line below is priced or marked to be quoted |

Tally: 22 M, 28 R, 16 N.

## 4. Key dimensions (sourced or derived only)

| Item | Value | Source |
|---|---|---|
| Antenna-to-radome gap | N × 2.5 mm, N TBD at G2 | `radome.antenna_gap_step`, MDS p.12; REQ-MECH-014 |
| Radome thickness | N × 4.997/(2√εr) mm; εr from TP-SYS-002 | MDS p.12; `sensor.wavelength_free_space`; REQ-MECH-013 |
| Metal and coating keep-out | 60° half-angle cone about boresight | `radome.keepout_half_angle`; REQ-MECH-010 |
| Uniform radome extent (skirt inner radius) | ≥ r_ant + √3·d (r_ant measured, A-005) | `radome.keepout_half_angle`, `radome.antenna_gap_step`; MDS §8 item 2 |
| Antenna level | within 5° of the ceiling plane | `sensor.level_tolerance` (A-002); REQ-MECH-009 |
| Radar module / XIAO outline (cradle lower bound) | 25 × 31.5 mm / 21 × 17.8 mm; carrier board unpublished | MDS p.3; XIAO; A-005 |
| Nominal wall (P1 skirt, P2, P3) | ≥ 2.5 mm | max(`mfg.fdm.min_wall` 1.2, `mfg.mjf.wall_min_pn` 2.5) |
| Bayonet clearance | 0.5 FDM / 0.2 SLA / 0.6 MJF mm | `mfg.*.clearance_connecting`; REQ-MFG-005 |
| Overhangs / bridges | ≤ 45°; show-face bridge < 5 mm (none used); hidden bridge ≤ 10 mm | `mfg.fdm.max_overhang`, `max_bridge_show_face`, `max_bridge_hidden` |
| Minimum hole | 2.0 mm (FDM) | `mfg.fdm.min_hole` |
| Gasket squeeze / corner radius | per ARSDG Table A for the chosen cord; inside radius ≥ 3 × cross-section | `gasket.*`; ARSDG p.20, p.90 |
| T-bar jaw span | 15 mm and 24 mm variants | `tbar.grid_width_narrow`, `tbar.grid_width_wide` |
| Draft for production | ≥ 2° (added at G2) | `injection_molding.toml` `draft_min_general_deg` |
| Pod diameter, height, lug count, twist angle, window size | TBD at G2 | - |

## 5. Top 5 risks and mitigations

| # | Risk | Mitigation |
|---|---|---|
| 1 | Radome degrades sensing (R-001), or the skirt glow is too dim once the LED is measured (R-018) | Uniform-floor coupons at N and N+1 in TP-SYS-002 for FR resin, PA 12 FR and PETG before the G2 CAD; measure the LED position at G1; light-guide or Grove-LED fallback |
| 2 | The lugs shear or creep, or sagging hidden lands reduce the bearing area (R-005) | Flat notch seat with a hard stop; lug count and land width sized at G2 against the REQ-MECH-015 load; pull test at 40 °C; inspect the first FDM print; independent twist-lock review |
| 3 | The gap tolerance stack through the cradle and bayonet misses N × 2.5 mm (REQ-MECH-014) | Put the kit datum and the shell-seat datum on one part (P2). Measure the kit stack (A-005, and the free Seeed "mmWave 3D Case" STL listed on the Wiki as a cross-check). Test the gap sensitivity in TP-SYS-002 |
| 4 | The US$30 BOM is unreachable (R-002) | The concept holds printed parts to 2 (+1) and bought parts to fixings only, with no inserts or light pipe. Report the real total once quoted. The only real lever is a Seeed volume quote (`docs/seeed-questions-draft.md`) |
| 5 | Serpentine strain relief slips, or the cable does not fit the 10 mm hidden-bridge channel (REQ-MECH-011, Q-13) | Choose the cable before the G2 CAD; keep the cable-tie slots from the first print; pull test TP-MECH-011 |

Also noted: thermal in a closed cup (R-006) and the colour match across three processes (Q-04).

## 6. Rough cost view (US$ per unit)

| Line | Prototype (G3/demo) | Production (10+, pod only) | Source |
|---|---|---|---|
| K1 MR60FDA2 kit | 28.99 | 28.99 | `sensor.unit_price_web_qty10`, Seeed product page read 2026-09-25 |
| P1 shell-radome | to be quoted (FDM in-house / SLA service) | to be quoted (tool + part) | - |
| P2 base plate | to be quoted (FDM / MJF service) | to be quoted | - |
| P3 T-bar clip (optional; excluded from the pod-only scope unless shipped) | to be quoted | to be quoted | - |
| F1 screws + anchors or plugs | to be quoted | to be quoted | in the BOM scope per Owner round 2 (Q-10) |
| F2 cable tie (fallback) | to be quoted | to be quoted | - |
| Light pipe, inserts, gasket (v1) | 0 (none in the design) | 0 | this concept |
| **Known subtotal** | **28.99** | **28.99** | |
| Room left under the target | 50.00 - 28.99 = **21.01** | 30.00 - 28.99 = **1.01** | `cost.prototype_max`, `cost.production_bom_max` |

The honest view is that the production target holds only if P1, P2 and the fixings together cost at most US$1.01. No quote exists, so this concept cannot claim to meet it. Production moulding tooling is a one-off cost, to be quoted, and is outside the per-unit BOM. The cable, raceway and adapter are outside the pod-only scope and to be quoted (Q-13, A-009).

## 7. Why this differs from the obvious alternatives

- **Against "kit rides in the shell" (the obvious twist-off layout):** that layout twists the cable or needs a rotating connector or a slack loop (R-017), and it hides the reset button inside the removed part. Fixing the kit in the base plate removes the problem instead of engineering around it, and it puts both RF datums on one part.
- **Against a separate radome window or a separate light pipe:** each is another part, another joint across the radome (breaking MDS §8 item 2 uniformity) and another colour-match. Here the shell is the radome, with one uniform thickness, and the LED glows through a groove in the skirt outside the cone.
- **Against a snap-on or magnet shell:** magnets are metal, which the cone keep-out makes awkward, and they are an added bought part. Snaps put wear on the part at every reset. The printed bayonet adds no parts and meets the hand-twist requirement directly.
- **Against a bought strain-relief grommet or clamp:** the serpentine is free in every process; the cable-tie slots are the cheapest positive fallback.
- **Against "design for FDM now, redesign for moulding later":** the flat-seat bayonet with 45° lead-ins, the rim-open skirt groove, the shut-off-window-friendly base plate and the single 2.5 mm wall are chosen so the same geometry is FDM support-free, SLA/MJF-legal and straight-pull mouldable. Going to production is then "add draft", not a redesign.
- **What it gives up:** a closed cup with no vents (thermal margin unproven), a visible base-plate collar band at the ceiling (a two-part line, not a seamless dome), and a skirt glow spot whose brightness is uncertain until the LED is measured.

## 8. Safety gates (`concepts/gates.md`)

Material data below was fetched on 2026-09-25. The excerpts and sha256 hashes are in `concepts/sketches/D/material-sources-excerpt.txt`.
- **[FR-TDS]** Formlabs "Flame Retardant" TDS, Rev. 02, 26.07.2023 (formlabs-media.formlabs.com/datasheets/2301750-TDS-ENUS-0_1.pdf).
- **[HP-FR]** HP "3D HR PA 12 FR, enabled by Evonik" datasheet, February 2025 (distributor copy; HP's own URL returned 503).

### GATE-S1 no-fall retention: author claims meets (L0, for the judges to check)
1. **Interlock (Revision 1):** the shell is held by a bayonet whose lugs **seat in a notch on flat lands perpendicular to the axis, against a hard stop** (§2, "How it attaches"). That is positive mechanical engagement, not friction, adhesive or magnets.
   - At the seat, gravity and axial load act normal to the flat lands, so there is no helical back-drive component and no radial (cam-out) component. The notch walls run parallel to the axis.
   - 45° faces exist only on non-bearing lead-ins.
   - The click detent is feedback only.
2. **Load path:**
   - All mounts: shell floor → shell lugs → base-plate collar lugs → base plate → screws.
   - Drywall: screws → drywall anchors → board.
   - Concrete: screws → plugs → slab.
   - T-bar: screws → bosses on P3 → P3 jaws → T-bar flange edges → grid.
   - The kit load does not pass through the bayonet at all, because the kit is fixed in P2 (cradle snap arms → P2 → fixings).
3. **Accidental release:** release needs two deliberate actions: lift the shell toward the ceiling by the notch depth (against gravity, and against the gasket preload in the bathroom variant), then rotate it. Vibration and knocks load the shell downward or sideways into the notch walls, so they supply neither action. Notch depth is TBD at G2. A vibration and knock test is proposed for G2.
4. **Loads:** per REQ-MECH-015, test load = measured (shell + kit) weight × a safety factor recorded in `params/params.toml`. The factor is TBD at G2 (owner G2 entry criterion); the placeholder `mount.retention_load_factor` (A-001) applies until then.
- **Weak points, stated honestly:**
  - The failure mode is now lug shear or creep at 40 °C, and FDM sag on the hidden flat lands (risk 2, §5).
  - The T-bar jaw grip on unsourced flange geometry is at risk (REQ-MECH-003).

### GATE-S2 flammability: author claims a listed path exists (L0), two open points

| Part | FDM (G3) | Demo grade and process | UL 94 listing, cited | Intended wall vs listing |
|---|---|---|---|---|
| P1 shell-radome | PETG, **fit-check only, not a demo or production material** | Formlabs Flame Retardant Resin, SLA | [FR-TDS]: "UL 94 V-0 (3mm) V-1 (2.5mm) HB (1.5mm)", UL Blue Card referenced | Skirt ≥ 2.5 mm → V-1/HB listed; ≥ 3 mm if V-0 is required. The radome floor T(N) and the skirt groove wall are each at or above the listed thickness for the class |
| P2 base plate | PETG, fit-check only | HP 3D HR PA 12 FR, MJF | [HP-FR]: "1 mm XY and Z HB", "2.5 mm XY and Z V0"; "testing done by UL and reported on UL blue card on January, 2025" | Nominal wall ≥ 2.5 mm → V0 listed |
| P3 T-bar clip | PETG, fit-check only | HP 3D HR PA 12 FR, MJF | as P2 | ≥ 2.5 mm → V0 listed |
| Light pipe | none: glow groove in the P1 skirt (P1's grade applies). The fallback light-guide grade is not chosen, so the fallback has no listed path yet | - | - | - |

Open points:
- (a) Both demo materials are grey. [FR-TDS] gives "Color Light grey"; [HP-FR] does not state a colour. The warm-white finish therefore needs a coating, and its effect on the UL 94 listing has not been assessed. Options are to ask the qualified human, or to specify an unpainted demo.
- (b) The production grade (PC, ABS or PBT, chosen so εr is in the MDS table) is not yet named. It must carry a UL listing at the production wall, cited at G2.
- The class itself is for the qualified human (Q-17). No part depends on an unlisted material except the fit-check-only PETG.

### GATE-S3 radar window: author claims meets on method (L0); εr at 60 GHz not yet sourced, measurement plan given

1. **Material data:** the demo radome is Formlabs FR Resin, which is not in the MDS §8 table.
   - [FR-TDS] gives only low-frequency data: "Dielectric Constant 3.83 ASTM D150, 0.5 MHz", "3.82 … 1.0 MHz", "Dissipation Factor 0.024 … 0.5 MHz". **Those values are not used for design at 60 GHz.**
   - Measurement plan: flat coupons of each process material (FR resin; PA 12 FR as an alternate; PETG for fit checks) go into TP-SYS-002. εr and tan δ at 60 GHz are extracted from the A/B transmission against the bare kit, or from a 60 GHz open-resonator measurement by a lab (to be quoted).
   - The production radome is chosen from the MDS table, so its εr and tan δ are sourced there. For a ranged material (ABS 2.0–3.5, PBT 2.9–4.0) the grade's own datasheet value, or a coupon measurement, pins εr before tooling.
   - A shortfall against MDS §8 item 1: FR resin's 1 MHz dissipation factor (0.024) is higher than every MDS-table entry (the largest, ABS, is 0.019). If the 60 GHz value is similar, the demo radome is lossier than the table materials. PA 12 FR is the alternate demo radome if the coupons show it.
2. **Thickness:** T = N × 4.997 mm / (2√εr), with integer N, computed at G2 from the measured 60 GHz εr.
   - **Revision 1:** the floor is a single flat, smooth (bed face) plate of **one** thickness T(N), with no pocket, step or opening.
   - It extends at least to radius r_ant + √3·d, so it covers the whole 60° cone footprint.
   - N is the smallest integer giving T(N) ≥ 1.2 mm and at or above the UL 94 listed thickness for the class.
   - "T computed at G2 from the cited εr" applies.
3. **Gap:** d = N × 2.5 mm (`radome.antenna_gap_step`).
   - The datum runs kit board seat on P2 → P2 flat seat land → P1 lug underside → P1 floor inner face. Both base-side datums are on one part (P2).
   - The flat seat lands set P1 axially, and the skirt-in-collar-bore fit sets it radially.
   - N_gap is TBD at G2 from the measured kit stack (A-005).
4. **Keep-out:** there is nothing metallic in P1 or in the forward half-space. The only metal (ceiling screws and anchors) sits behind the antenna plane, outside the 60° cone about the downward boresight. There are no magnets and no springs. The light path (the skirt groove) lies outside the cone, and there is no light path through the radome. The finish coating must be non-metallic and non-conductive (REQ-MECH-010), and that coating's thickness must go into the TP-SYS-002 coupons.
