# Concept B: "Radome-datum pod" (RF-first)

- **Lens:** best radar/RF performance. The radome geometry, antenna gap, keep-out cone and sensor orientation follow MDS §8 exactly, even where that costs appearance, cable handling or cost.
- **Revision 1 (2026-09-25):** the only change is to clear GATE-S2 for the light pipe P4.
  - P4's demo material is now **Covestro Makrolon 2407, transparent**: UL 94 V-2 at 0.75 mm and HB at 2.7 mm [MK2407].
  - P4's smallest section is set at ≥ 0.75 mm, so the V-2 listing sits at or below the pipe wall.
  - The unlisted VCC reference is removed.
  - The GATE-S2 table, the P4 part row, the cost line and R-B3 are updated to match. The requirement statuses are unchanged.
- **Status:** G1 concept, evidence L0/L1. The only analysis is `concepts/sketches/B/rf_geometry.py` (output in `rf_geometry.out.txt`), which is arithmetic on params and cited values. Nothing here is measured.
- **Sources fetched 2026-09-25 for this concept (not from memory):**
  - [GREG22] N. Gregory, "Measuring the Electrical Properties of 3D Printed Plastics in the W-Band", Univ. of Arkansas, 2022, https://scholarworks.uark.edu/eleguht/85/. Abstract: PETG "lowest permittivity at 2.675"; imaginary part "below 0.045 for all samples" over 75-110 GHz.
  - [FLFR] Formlabs "Flame Retardant" resin TDS, Rev. 01, 13.04.2023, https://formlabs-media.formlabs.com/datasheets/2301761-TDS-ENUS-0.pdf. "UL 94 V-0 (3mm) V-1 (2.5mm) HB (1.5mm)"; dielectric constant 3.82 at 1.0 MHz and dissipation factor 0.025 at 1 MHz (ASTM D150).
  - [HPPA12] HP technical note 4AA7-2792ENW, May 2018, "HP 3D High Reusability PA 12 … UL 94 and UL 746A Certification" (copy hosted by forerunner3d.com). Certified "HB at a 0.75mm thickness", with a UL Blue Card on UL iQ.
  - [HPFR] HP 3D HR PA 12 FR (enabled by Evonik) datasheet, Feb 2025 (copy hosted by druckerfachmann.de). UL 94: "1 mm XY and Z HB Pass" and "2.5 mm XY and Z V0 Pass"; per a UL Blue Card of Jan 2025.
  - [MK2407] Covestro Makrolon 2407 product page, https://solutions.covestro.com/en/products/makrolon/makrolon-2407_000000000086286874, fetched 2026-09-25. UL 94 "V-2" at 0.75 mm and "HB" at 2.7 mm; "available in transparent, translucent and opaque colors".
    - Cross-checked against the PolyOne Distribution datasheet of 2020-01-29 (https://www.teameliteonline.com/wp-content/uploads/2020/01/document-10.pdf). It lists the same UL 94 rows and transmittance of 89.0 % at 2.00 mm (ISO 13468-2).
  - [ARX26] Işık et al., "Permittivity Characterization of 3D-Printed Materials at Millimeter Waves", arXiv 2607.16937, 2026. PLA and resins measured at 70-110 GHz, εr 2.45 to 2.75. It is used only as support for the coupon plan and gives no PETG or PA12 value.

## 1. Summary

The radar kit rides in a one-piece **pod**: a cup whose closed bottom is a **flat, uniform, featureless radome window**, printed face-down on the build plate. The kit's radar board registers **directly on a datum ledge inside the same part**, so the antenna-to-radome gap d = N × 2.5 mm (MDS §8 item 4) is set by a single printed dimension, with no joint or twist-lock in the tolerance chain.

Everything that is not radome sits behind the antenna plane, which puts it outside the 60° keep-out cone (REQ-MECH-010). That includes the bayonet, the detent, the fixings, the gasket groove, the cable clamp and the light pipe. The light pipe turns 90° and exits flush on the pod's **side skirt**, never through the radome. The pod twists onto a screw-fixed **base plate** through a 3-lug bayonet with a printed detent and end stops. The base plate carries the cable clamp and the O-ring face groove.

Because the radome is flat and parallel to the antenna, the half-wave thickness rule (MDS §8 item 3) holds exactly at boresight and degrades smoothly off-axis. A domed shell would vary the incidence angle and the thickness over the field of view. The cost of this approach is a visibly flat-bottomed "drum" look, a pod diameter set by the cone footprint, and a USB cable that must follow the pod through the twist (R-017).

## 2. Architecture and parts

| # | Part | Function | Fit-check process (G3) | Demo process (REQ-MFG-007) |
|---|---|---|---|---|
| P1 | Pod (side skirt + integral flat radome + kit datum ledge + bayonet lugs + light-pipe bore) | holds the kit; RF window; the twisting part | FDM PETG, radome face on the bed | MJF, HP 3D HR PA 12 FR [HPFR] (primary); SLA, Formlabs FR resin [FLFR] (backup) |
| P2 | Kit retainer ring | clamps the radar board onto the P1 datum ledge; printed flexure fingers, no metal | FDM PETG | as P1 |
| P3 | Base plate (bayonet ramps + detent + O-ring face groove + cable clamp + ceiling screw holes) | fixed to the ceiling; carries the pod | FDM PETG, ceiling face on the bed | MJF HP 3D HR PA 12 FR [HPFR] |
| P4 | Light pipe (90° TIR prism rod) | carries WS2812 light to a flush side-skirt exit | FDM PETG stand-in (optical check only) | Covestro Makrolon 2407, transparent [MK2407]. Moulded, or machined from stock certified as 2407; the source is to be quoted. Smallest section ≥ 0.75 mm |
| P5 | T-bar clip adapter (optional) | screws to P3's hole pattern; jaws for 15 and 24 mm grids | FDM PETG | MJF HP 3D HR PA 12 FR [HPFR] |
| P6 | Fixings: screws + drywall anchors, screws + concrete plugs | P3 to the ceiling | bought-in (proposed at G2 from the anchor makers' datasheets, REQ-MNT-003) | same |
| P7 | O-ring cord (bathroom variant only) | IPX4 seal in the P3 groove | not fitted in v1 | cord supplier TBD |
| — | Seeed MR60FDA2 kit, SKU 114993388 | sensor, compute, radio | as-is | as-is |

**Kit handling assumption (new, for the owner):** the kit electronics are used as-is, and the kit's own 3D-printed case (DS p.7) is **left out**. That case is a second dielectric layer of unknown εr and thickness in front of the antenna, and it would make REQ-MECH-013/-014 impossible to control. This needs owner confirmation, because Q-01 "kit as-is" was about compute and radio.

## 3. Key features

**Radome geometry (MDS §8 items 1-4; REQ-MECH-013/-014).**
- **Flat disc** perpendicular to the pod axis. It has no ribs, text, seams, gate marks, fillets or light-pipe holes inside the keep-out footprint.
- Printed **show face down on the bed**, so the thickness is a whole number of layers. The layer height is chosen at G2 to land on T.
- **Thickness** T = N·c/(2f√εr), f = 60 GHz (`sensor.freq_centre`):
  - Fit check (PETG, εr 2.675 [GREG22]): **N = 1, T = 1.527 mm**. This is above `mfg.fdm.min_wall` 1.2 mm; the thinnest legal choice gives the lowest dielectric loss.
  - Demo (HP 3D HR PA 12 FR): **N = 2, T computed at G2 from the coupon εr**. N = 1 is ruled out by the MJF 2.5 mm wall rule (`mfg.mjf.wall_min_pn`) and by the V-0 listing at 2.5 mm. N = 2 keeps T ≥ 2.5 mm only if εr ≤ 3.99; otherwise use N = 3, which works for εr ≤ 8.99 (sketch output).
  - Backup (Formlabs FR): **N = 2, T = 2.556 mm** at the TDS εr of 3.82. That εr is at 1 MHz only, so it is re-measured at 60 GHz.
- **Gap** d: **N = 1, d = 2.5 mm** (`radome.antenna_gap_step`). This gives the smallest keep-out footprint (Ø48.9 mm at the radome inner face, using the conservative module half-diagonal a = 20.11 mm) and the smallest band-edge phase error (12° round trip at 58/62 GHz, against 24° for N = 2).
  - Fallback: **N = 2, d = 5.0 mm** (footprint Ø57.5 mm), if the kit measurement at G1 (A-005) shows parts on the antenna face taller than 2.5 mm less the clearance.
- **How the gap is held:** the radar board's antenna-side face seats on a **datum ledge moulded in P1**, in the same print as the radome. d is then one Z-dimension of one part. P2 clamps the board from behind, so the gap does not depend on the bayonet, the base plate or the ceiling.
- **Uniform incidence:** at the 3 × 3 m corners the ray is 44.0° off boresight at 2.2 m height and 35.3° at 3.0 m. Refraction inside PETG gives a path factor of 1.105 and 1.068 respectively (sketch). Both are smooth and symmetric, which a dome would not be. This is checked by TP-SYS-001/-002, not claimed.

**Sensor orientation (REQ-MECH-009).**
- The board plane is set by the P1 ledge, which is parallel to the P1 rim. The rim seats on the flat P3 bayonet land, and P3's ceiling face is flat.
- The stack is ledge ∥ rim ∥ land ∥ ceiling face, and every one of these is a planar print face. The ≤5° tilt (`sensor.level_tolerance`, A-002) is then limited by ceiling flatness plus the bayonet clearance of 0.5 mm FDM / 0.6 mm MJF (REQ-MFG-005).
- Rotation about boresight is keyed by a flat on the ledge, so the 2T2R antenna axes line up with the room as the instructions describe (G2).

**Keep-out (REQ-MECH-010).**
- Every metal item sits at or above the antenna plane, which is ≥90° from boresight and so outside the 60° cone: the screws and anchors, the XIAO, the USB-C plug and cable, and any T-bar clip hardware.
- The pod contains no magnets, springs or metallic pigment.
- The side-skirt inner radius is set at G2 to be ≥ the cone radius at the radome plane (24.4 mm for d = 2.5 mm) plus `mfg.fdm.min_wall`.

**Attach and detach (REQ-MECH-005/-006/-016; IF-03).**
- The pod has 3 lugs, which enter 3 slots in P3 and rotate onto flat bayonet lands. The rotation angle is TBD at G2.
- At the end of travel a **printed cantilever detent** in P3 drops behind a lug, and a hard stop blocks over-travel. Removal needs a deliberate hand twist against the detent. The detent torque is TBD at G2, and snap-fit strain comes from R5d for PA12/resin (PETG has no R5d row).
- No screw passes through the shell. The pod skirt carries a shallow grip texture outside the cone.

**Cable entry and strain relief (REQ-MECH-011/-012; R-017).**
- The cable enters at the **ceiling plane** through an edge notch in P3 that lines up with the raceway end.
- A **printed clamp in P3** (a serrated saddle plus a hook-over tab, no metal) grips the jacket, so a pull stops at the fixed base.
- Between the clamp and the XIAO USB-C socket there is a **service loop** in the P3 cavity, sized to take the bayonet rotation. Length TBD at G2.
- On removal the pod comes away on the loop, and the user unplugs the USB-C before setting the pod down. This is the price of keeping the kit in the RF-datum part.

**Light pipe (REQ-UX-004, R-018).**
- The WS2812 is on the radar board (Wiki). P4 picks up light just beside the LED, turns it 90° by TIR, and runs radially **behind the antenna plane** to exit **flush on the side skirt**, with the end faced flush.
- The pipe never enters the cone and never breaks the radome's uniformity. The trade-off is that the LED is seen from the side, not from directly below.

**T-bar adapter (REQ-MECH-003).** P5 is a plate that screws to P3's own hole pattern. It has one fixed hook jaw and one jaw with two indexed positions: `tbar.grid_width_narrow` 15 mm and `tbar.grid_width_wide` 24 mm. The flange thickness and hook depth are TBD at G2 from a measured grid sample.

**O-ring groove (REQ-MECH-007/-008/-017).**
- A continuous **round axial face groove** in the P3 land, facing the P1 rim. Being round, it has no corners, so the ARSDG p.90 corner rule does not arise.
- Candidate cord 2.62 mm (0.103 in), per ARSDG Table A p.20: depth 1.91-2.06 mm, width 3.71 mm, squeeze 19-29 %. It is confirmed at G2.
- The bayonet land ramps set the squeeze. The O-ring drag during the twist is R-016.

**Printability (REQ-MFG-001..005).**
- P1 prints radome-down: the skirt is vertical and the lugs are chamfered at ≤45° (`mfg.fdm.max_overhang`). The datum ledge is a 45° chamfer upward. There are no show-face bridges.
- P3 prints ceiling-face down, and the groove and ramps open upward.
- The show faces are the bed face (radome) and the vertical skirt, and neither needs supports.
- For thermal (REQ-ENV-002) there is no vent in the radome. If G2 thermal analysis needs vents, they go in the skirt, outside the cone.

## 4. Key dimensions (derived only)

| Item | Value | Source |
|---|---|---|
| Radome T, PETG fit check | 1.527 mm (N = 1) | εr 2.675 [GREG22]; MDS §8 item 3; sketch |
| Radome T, MJF PA 12 FR demo | N = 2, T computed at G2 from the coupon εr; ≥ 2.5 mm needs εr ≤ 3.99, else N = 3 | `mfg.mjf.wall_min_pn`; [HPFR] V-0 at 2.5 mm; sketch |
| Radome T, Formlabs FR backup | 2.556 mm (N = 2) at εr 3.82 (1 MHz); re-derived from the 60 GHz coupon | [FLFR]; sketch |
| Antenna gap d | 2.5 mm (N = 1); fallback 5.0 mm (N = 2) | `radome.antenna_gap_step` |
| Keep-out Ø at the radome inner face | 48.9 mm (d = 2.5), 57.5 mm (d = 5.0) | `radome.keepout_half_angle`; module 25 × 31.5 mm (MDS p.3); sketch |
| Radar board envelope | ≥ 25 × 31.5 mm; carrier outline TBD (A-005) | `sensor.radar_module_*` |
| Wall minimum | 1.2 mm FDM; 2.5 mm MJF (PN) | `mfg.fdm.min_wall`, `mfg.mjf.wall_min_pn` |
| Mating clearances | 0.5 / 0.2 / 0.6 mm FDM / SLA / MJF | `mfg.*.clearance_connecting` |
| O-ring groove (candidate 2.62 mm cord) | depth 1.91-2.06 mm, width 3.71 mm | ARSDG Table A p.20 |
| Pod diameter, height, bayonet angle, detent torque, loop length, fixings | TBD at G2 | — |

## 5. Safety gates (concepts/gates.md)

**GATE-S1, no-fall retention: claimed PASS at concept level.**
1. *Positive interlock:* "3 lugs … rotate onto flat bayonet lands … a printed cantilever detent in P3 drops behind a lug, and a hard stop blocks over-travel." Gravity loads the lugs normal to the flat lands, with no rotational component, so neither weight nor a knock can unwind the pod without first lifting the detent. The design uses no friction, adhesive or magnets.
2. *Load path:*
   - Drywall: pod → lugs → P3 lands → P3 → screws → drywall anchors → drywall.
   - Concrete: pod → lugs → P3 → screws → plugs → slab.
   - T-bar: pod → lugs → P3 → machine screws → P5 → hook jaws → T-bar flanges → grid.
   - The kit itself is carried board → P2 retainer → P1, so the kit load never passes through the USB cable.
3. *Deliberate release:* removal takes a hand twist that first lifts the detent and then rotates the lugs to the slots. The hard stop prevents over-travel. Clearance and detent geometry are sized at G2 so the lug cannot ratchet under vibration. A knock produces a translational load, and the flat lands turn that into zero torque.
4. *Loads:* per REQ-MECH-015, test load = measured weight × safety factor. The value and source of the factor go in `params/params.toml` and are TBD at G2, as the owner set. The G0 placeholder `mount.retention_load_factor` 4.0 is not used as a design value.
   - Weak point: the P5 printed hook jaws on the T-bar flange (see Risks).

**GATE-S2, flammability: PASS for P1-P5 (Revision 1).**

| Part | Fit-check grade | Demo grade and published UL 94 listing | Demo wall vs listing |
|---|---|---|---|
| P1 pod + radome | PETG: **fit-check only, not a demo or production material** | HP 3D HR PA 12 FR: V-0 at 2.5 mm, HB at 1 mm [HPFR]. Backup Formlabs FR: V-1 at 2.5 mm, V-0 at 3 mm, HB at 1.5 mm [FLFR] | walls ≥ 2.5 mm (MJF rule); radome N chosen so T ≥ 2.5 mm, so a V-0 [HPFR] or V-1 [FLFR] listing sits at or below the wall |
| P2 retainer | PETG fit-check only | as P1 | ≥ 2.5 mm |
| P3 base plate | PETG fit-check only | HP 3D HR PA 12 FR [HPFR] (plain HP HR PA 12 is HB at 0.75 mm [HPPA12]) | ≥ 2.5 mm |
| P5 T-bar clip | PETG fit-check only | HP 3D HR PA 12 FR [HPFR] | ≥ 2.5 mm |
| P4 light pipe | PETG stand-in, fit-check only | Covestro Makrolon 2407 transparent: V-2 at 0.75 mm, HB at 2.7 mm [MK2407] | smallest pipe section ≥ 0.75 mm, so V-2 is listed at or below the wall. If the qualified human requires HB-or-better at the pipe wall, the pipe section goes to ≥ 2.7 mm; this is geometry only, and the pipe stays outside the cone |

- No part depends on an unlisted material for demo units.
- The class itself is set by the qualified human (Q-17).
- REQ-SAFE-001 does not name the light pipe, but the gate does. P4 now cites a maker's listing that states a thickness [MK2407].
- The HP FR datasheet does not state colour; the warm-white finish is at risk (R-B4).

**GATE-S3, radar window: PASS at concept level (the concept is built around it).**
1. *Material:*
   - PETG εr 2.675 with imaginary part < 0.045 [GREG22]. This is W-band data (75-110 GHz), not 60 GHz.
   - Formlabs FR εr 3.82 and tan δ 0.025 [FLFR]. This is 1 MHz data only.
   - PA 12 FR has no cited εr, so it has a **measurement plan**: TP-SYS-002 flat coupons in each demo material at N = 1, 2 and 3 candidate thicknesses, with εr extracted at 58-62 GHz. PETG and FR resin are re-measured the same way.
   - The εr in the MDS table is not used, because no MDS material is proposed.
2. *Thickness:* T = N·c/(2f√εr) at f = 60 GHz:
   - PETG: N = 1, T = 1.527 mm.
   - Formlabs FR: N = 2, T = 2.556 mm (at the 1 MHz εr).
   - PA 12 FR: N = 2, "T computed at G2 from the cited εr".
   - In all cases the window is flat, smooth and uniform across the keep-out footprint (MDS §8 item 2).
3. *Gap:* d = 1 × 2.5 mm (fallback 2 × 2.5 mm), held by the radar board seating on a datum ledge in the same part as the radome.
4. *Keep-out:* all metal (fixings, XIAO, USB plug, clip hardware) sits at or behind the antenna plane. The pod has no magnets, springs or pigment, and the light pipe exits through the side skirt outside the cone.

## 6. Requirement coverage

M = meets (by concept), R = at risk, N = not addressed by the enclosure concept (firmware, instructions or compliance).

| REQ | Status | Note |
|---|---|---|
| SYS-001 | R | RF-optimal radome helps; corner radius 2.12 m > 2 m source radius (R-003) |
| SYS-002 | R | Best-case design for A/B, but loss is unmeasured until coupons (R-001) |
| SYS-003 | R | Spacing from TP-SYS-003; enclosure-neutral |
| MECH-001 | M | Screws + drywall anchors through P3 |
| MECH-002 | M | Screws + plugs through P3 |
| MECH-003 | R | P5 two-position jaw for 15/24 mm; printed hook strength unproven |
| MECH-004 | R | Load path stated; loads TBD (REQ-MECH-015) |
| MECH-005 | R | Bayonet with detent; strength TBD at G2 |
| MECH-006 | M | No screw through P1 |
| MECH-007 | M | Continuous round face groove in P3 |
| MECH-008 | R | Squeeze from bayonet ramps; drag during twist (R-016) |
| MECH-009 | M | Planar datum stack ledge ∥ rim ∥ land ∥ ceiling face |
| MECH-010 | M | All metal behind the antenna plane; light pipe via the skirt |
| MECH-011 | M | Printed clamp on fixed P3; R for slip under load |
| MECH-012 | M | Edge notch at the ceiling plane into the raceway |
| MECH-013 | R | N and T set; εr at 60 GHz still to be measured |
| MECH-014 | M | d = 2.5 mm set by a single-part datum |
| MECH-015 | R | Factor TBD at G2 (owner entry criterion) |
| MECH-016 | M | Hand twist against the detent |
| MECH-017 | M | ARSDG Table A candidate stated |
| MECH-018 | R | Cable-notch leak path and splice not solved (bathroom) |
| PWR-001 | M | Kit's USB-C used as-is |
| PWR-002 | R | Peak current unmeasured (R-014) |
| PWR-003 | M | No battery |
| PWR-004 | R | C-to-C start-up unknown (R-012) |
| PWR-005 | R | Kit draw per A-008, unmeasured |
| ELEC-001 | M | No mains conductor |
| ENV-001 | R | Kit rated range covers 0-40 °C; enclosure effect untested |
| ENV-002 | R | Sealed flat-window pod; 32.1 K/W unverified; skirt vents are the fallback |
| SAFE-001 | R | Listed grades cited for P1/P2/P3/P5; class from Q-17 |
| SAFE-002 | R | Surface temperature untested |
| SAFE-003 | N | Text/claims, not enclosure |
| SAFE-004 | N | Text/claims, not enclosure |
| EMC-001 | N | Compliance route (Q-17); enclosure adds no radiator |
| EMC-002 | N | Compliance route (Q-17); enclosure adds no radiator |
| EMC-003 | N | Compliance route (Q-17); enclosure adds no radiator |
| EMC-004 | N | Compliance route (Q-17); enclosure adds no radiator |
| EMC-005 | M | No added transmitter |
| FW-001 | N | Firmware |
| FW-002 | N | Firmware |
| FW-003 | N | Firmware |
| FW-004 | N | Firmware; pipe shows LED states |
| FW-005 | N | Firmware; pipe shows LED states |
| FW-006 | N | Firmware; pipe shows LED states |
| UX-001 | R | MJF FR colour not stated; painting the radome changes RF (R-B4) |
| UX-002 | M | Hidden bayonet; no screw visible |
| UX-003 | N | Instructions |
| UX-004 | R | Flush pipe on the side skirt; finish-matching a clear PC end face is at risk |
| UX-005 | M | No light-sensor window or pinhole |
| UX-006 | M | Kit rides in the pod; reset reachable once twisted off (button position A-005) |
| MNT-001 | N | Instructions |
| MNT-002 | N | Instructions |
| MNT-003 | N | Instructions; fixings proposed at G2 from maker datasheets |
| MNT-004 | N | Instructions |
| MNT-005 | N | Instructions |
| MNT-006 | N | Instructions |
| MFG-001 | M | Radome and base printed show face on the bed |
| MFG-002 | M | Lugs and ledge ≤45° |
| MFG-003 | M | No show-face bridge |
| MFG-004 | M | ≥1.2 mm everywhere (radome 1.527 mm in PETG) |
| MFG-005 | M | Clearances from params |
| MFG-006 | M | All parts PETG FDM for the fit check |
| MFG-007 | R | MJF PA 12 FR / SLA FR; the per-process radome T makes P1 differ between processes |
| COST-001 | R | Kit 28.99 leaves 21.01; MJF parts to be quoted |
| COST-002 | R | 1.01 left after the kit (R-002); this concept does not improve it |
| COST-003 | R | Quotes to be dated in `bom/` |

## 7. Top 5 risks

| ID | Risk | Mitigation |
|---|---|---|
| R-B1 | εr of PA 12 FR at 60 GHz is unknown; if > 3.99, N = 2 gives T < 2.5 mm, below the MJF wall rule and the V-0 listing | Coupons first at G1-G2 (TP-SYS-002); N = 3 path valid to εr 8.99; Formlabs FR backup |
| R-B2 | USB cable/connector strained by the pod twist and by the pod hanging on the loop at removal (R-017) | Small bayonet angle; loop sized to the angle; clamp on the fixed P3; instructions: unplug first; TP-MECH-011/-016 |
| R-B3 | Kit carrier geometry (A-005) puts parts on the antenna face or the LED where the pipe cannot reach behind the antenna plane | Measure a kit at G1; d fallback N = 2; if the pipe must enter the cone, include it in the coupons (R-018); quote a source of Makrolon 2407 pipes at prototype volume early |
| R-B4 | Warm-white finish vs RF: MJF FR colour not stated; paint on the radome adds an unmodelled layer | Leave the radome face unpainted and colour-match by material, or include the paint layer in the coupon stack; owner colour sample at demo |
| R-B5 | Printed T-bar hook jaws or the bayonet detent creep or crack under the REQ-MECH-015 load at 40 °C | Size at G2 once the safety factor is set; hot pull test (TP-MECH-004/-005 at 40 °C) |

## 8. Cost (sourced prices only)

| Line | Price | Source |
|---|---|---|
| MR60FDA2 kit, 1 and 10+ | US$28.99 | Web, 2026-09-25 (`sensor.unit_price_web_qty*`) |
| P1-P3, P5 in MJF HP 3D HR PA 12 FR or SLA Formlabs FR | to be quoted | — |
| P4 light pipe in Makrolon 2407, P6 fixings, P7 cord | to be quoted | — |
| **Prototype** | ≥ 28.99 + quotes; 21.01 left under US$50 | `cost.prototype_max` |
| **Production (pod only)** | ≥ 28.99 + quotes; 1.01 left under US$30, which is likely unreachable (R-002) | `cost.production_bom_max` |

The RF-first choices (FR-grade MJF material, coupon testing, a separate Makrolon 2407 pipe) all push cost up, not down.

## 9. Why it differs from the obvious alternatives

- **Compared with a domed or rounded "puck":** a dome cannot keep a uniform thickness at a constant incidence angle across ±60°. The flat window is the only shape where MDS §8 items 2-3 hold across the field of view, and it prints on the bed with a thickness set in whole layers.
- **Compared with putting the kit in the base plate** (which suits cable handling): that puts the bayonet clearance and the ceiling tolerance into the antenna gap. Concept B puts the gap in one printed dimension instead.
- **Compared with a light pipe through the radome** (the shortest route): that breaks uniformity where the beam is strongest. Concept B routes the light behind the antenna plane to the side skirt.
- **The cost of the approach:** a flat-bottomed drum shape, a diameter set by the cone, a cable that follows the twist, and an FR-grade demo material. Concept B knowingly trades appearance, cable robustness and cost for RF margin.
