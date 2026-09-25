# Concept C: "Drop-and-turn" bayonet pod with a live service loop

- **Lens:** best install and removal experience (one person on a ladder; drywall, concrete, T-bar; twist-off feel and retention; cable handling; installed appearance).
- **Gate:** G1 concept, evidence level L0 (claimed). Nothing here is measured, analysed or verified. Every number is cited to `params/params.toml` or a source; everything else is "TBD at G2".
- **Author:** concept generator C (independent; other concepts not read).

## 1. Summary

A round, flat pod in two main printed parts. A **base plate** screws to the ceiling (or to a T-bar adapter) and carries everything that must not move: the ceiling fixings, a tool-free cable clamp, the gasket groove and a detent. The **pod** (shell and radome printed as one part) carries the MR60FDA2 kit, located from the radome, so the MDS §8 antenna gap is set inside one part and does not depend on the twist-lock tolerance. The pod attaches with a **three-lug bayonet with unequal lug spacing**: a conical lead-in centres the pod by feel, it goes in one way only, and a short turn up a ramp draws the rim flush to the ceiling and ends in a detent click. The USB cable is clamped at the base plate and runs to the XIAO through a short **service loop** held in a gutter in the base plate. The loop takes up the small twist angle, and because the pod stays plugged in when twisted off, it stays **powered in the hand**, so the reset button (REQ-UX-006) can be used right away without holding the cable up to the ceiling. The installed pod shows one flat matte face, a fluted side grip, a flush light pipe and a cable exiting at the ceiling plane into the raceway. The rim sitting flush on the ceiling is the "locked" cue, and a gap means not locked. For the bathroom variant, a **radial** O-ring gland on the base-plate boss seals against the pod's inner rim bore, so the O-ring squeeze does not load the bayonet ramp or add to the twist torque the way a face seal would.

## 2. Architecture and part list

| # | Part | Function | Process (G3 fit / demo) | Print orientation, support note |
|---|---|---|---|---|
| P1 | Pod (shell + radome, one part) | Radome window, side grip, bayonet lugs (inner wall), kit standoffs referenced to the radome inner face, pod-side cable jacket clip, light-pipe bore, cable notch in rim | FDM PETG / SLA resin or MJF PA | Radome face down on the bed: the show face is the first layer and needs no support. Side wall vertical. Lug undersides chamfered ≥45° (hidden). |
| P2 | Base plate | Ceiling fixing holes (slotted for rotation), bayonet L-slots with ramp and end stop, detent flexure, radial gland on boss, service-loop gutter, cable channel with clamp seat, ceiling datum face | FDM PETG / SLA or MJF | Ceiling face down (hidden, flat datum). Slot roofs are hidden bridges ≤10 mm or 45° roofs. Detent flexure lies in the XY plane. |
| P3 | Cable clamp lid | Snaps over the cable in the P2 zig-zag channel and clamps the jacket (REQ-MECH-011); no tool | FDM PETG / SLA or MJF | Flat on bed; hidden part. |
| P4 | Light pipe | Carries WS2812 light to a flush room-side face | Translucent white SLA resin or natural PETG (TBD by coupon) | Axis vertical; room end on the bed so it prints flat and flush. |
| P5 | T-bar adapter (optional) | Clips onto a 15 mm **or** 24 mm T-bar flange through a stepped jaw; P2 screws to it | FDM PETG / SLA or MJF | Printed on its side so the hook fingers flex in-plane; no show face. |
| P6 | O-ring cord (bathroom variant only) | Radial static seal, P2 boss to P1 rim bore | Bought cord, spliced; to be quoted | n/a |
| P7 | Kit, SKU 114993388 | Radar module + XIAO ESP32C6, used as-is; the vendor's 3D-printed case (DS p.7) is not used | Bought | n/a |
| P8 | Ceiling fixings (not in the box) | Drywall: screws + drywall anchors; concrete: screws + wall plugs; types and sizes chosen at G1 from the anchor makers' datasheets | Bought | n/a |
| P9 | Detent fallback (only if P2 flexure fails TP) | Off-the-shelf spring plunger at the base-plate periphery, behind the antenna plane and so outside the 60° cone (REQ-MECH-010) | Bought; to be quoted | n/a |

## 3. How it installs and detaches (the lens)

**Install, one person on a ladder (drywall/concrete):**
1. Hold P2 to the ceiling as its own drill template and mark the holes. Drill, then set the anchors or plugs (REQ-MNT-003 names them).
2. Put the screws in loosely. The fixing holes are **slotted arcs**, so P2 can be turned to point its cable notch at the raceway line, then tightened. Screw heads sit inside the P2 boss, under the pod (REQ-UX-002, REQ-MECH-006).
3. Press the cable into the P2 channel and snap P3 on by thumb. Leave the service loop in the gutter.
4. At chest height, plug the USB-C into the XIAO and press the jacket into the P1 jacket clip, so the connector never carries the cable load.
5. Lift the pod. The conical lead-in centres it without looking. The unequal lugs let it enter at one rotation only, with the cable notch toward the cable. Push up, turn by the fluted side wall until it clicks. The rim goes flush with the ceiling when locked; a visible gap means not locked.

**T-bar:** lift the adjacent tile, press P5 onto the flange (the stepped jaw takes 15 mm in the inner step and 24 mm in the outer step, `tbar.grid_width_narrow`/`_wide`), lower the tile, screw P2 to P5, then continue from step 3. No drilling or cutting (REQ-MECH-003).

**Removal (cleaning, reset):** turn back past the detent and lower the pod. The service loop pays out, so the pod stays plugged in and **powered** in the installer's hand. Reset is pressed on the kit from the open ceiling side of the pod. To take the pod away, unclip the jacket and unplug.

**Twist feel and retention:** the vertical load goes through the bayonet lugs in bearing. The detent resists rotation only, so detent wear does not reduce pull retention (REQ-MECH-005). The ramp's end stop pulls the P1 rim against the P2 datum, so axial play from the process clearance (REQ-MFG-005) is taken out when locked. That keeps the level chain short (REQ-MECH-009). The turn angle, detent torque and lug count and size are TBD at G2, with retention loads from REQ-MECH-015.

## 4. Key dimensions (derived only; everything else TBD at G2)

| Item | Value | Derivation / citation |
|---|---|---|
| Antenna face to radome inner surface | N × 2.5 mm (N = 1 preferred) | `radome.antenna_gap_step` (MDS p.12 item 4); REQ-MECH-014 |
| Radome thickness | N × 4.997 mm / (2·√εr); εr of the chosen material TBD by TP-SYS-002 coupon | `sensor.wavelength_free_space`; MDS p.12 item 3; REQ-MECH-013 |
| Radome thickness, illustration only (MDS-table materials, not the owner's) | PC εr 2.9: N=1 1.47 mm, N=2 2.93 mm. ABS εr 2.0–3.5: N=1 1.34–1.77 mm | Computed from MDS p.11-12 table. Shows N=1 is near `mfg.fdm.min_wall` 1.2 mm and below `mfg.mjf.wall_min_pn` 2.5 mm, so an MJF radome probably needs N=2 (R-015) |
| Light-pipe clear of the cone at gap d | LED at least d·tan 60° outboard of the antenna aperture edge: 4.33 mm at N=1, 8.66 mm at N=2 | `radome.keepout_half_angle`, `radome.antenna_gap_step`; favours N=1 for R-018. Apex taken at the aperture edge (conservative; confirm at G1) |
| T-bar jaw openings | 15 mm and 24 mm (plus process clearance) | `tbar.grid_width_*`; `mfg.*.clearance_connecting` |
| Bayonet and clamp mating clearance | 0.5 mm FDM / 0.2 mm SLA / 0.6 mm MJF (one CAD param per process) | REQ-MFG-005; `mfg.fdm/sla/mjf.clearance_connecting` |
| Minimum wall, hole, overhang, show-face bridge | 1.2 mm; Ø2.0 mm; 45°; <5 mm | `mfg.fdm.min_wall`, `min_hole`, `max_overhang`, `max_bridge_show_face` |
| Radial gland (bathroom) | depth, width and squeeze from ARSDG Table A **radial** column for the chosen cross-section; static squeeze 10–40 % bounds | REQ-MECH-017; `gasket.static_squeeze_min/max` (ARSDG p.113). The round pod makes the ARSDG p.90 corner-radius rule moot |
| Pod diameter, height, turn angle, lug size, loop length, grip flute depth, fixing sizes and pattern | TBD at G2 | needs the measured kit (A-005) and the mass (REQ-MECH-015) |

## 5. Radome, light pipe, cable, T-bar, gasket and printability notes

- **Radome (MDS §8):** a flat, uniform-thickness window across the whole ±60° field. It is the pod's first printed layer, which is the smoothest face (MDS item 2). No text, logo or texture on it. Pigment must be non-metallic (REQ-MECH-010, REQ-UX-001). The kit sits on standoffs referenced to the radome inner face, with antenna-face locating pads. A thickness/εr coupon set per material (PETG, SLA resin, PA) comes before any CAD freeze (TP-SYS-002). The side-wall grip flutes lie outside the cone footprint.
- **Light pipe:** a separate insert in a bore at the radome edge, outside the cone footprint when the LED position (A-005) allows (§4). Its room end prints on the bed, so it is flush, in the same matte warm white, and glows only when lit. If the measured LED position puts the pipe inside the cone, the pipe goes into the TP-SYS-002 A/B coupons (R-018).
- **Cable:** it enters at the ceiling plane through the P1 rim notch into the P2 channel (REQ-MECH-012). The jacket is clamped at P2 (P3) and again at P1 (jacket clip), so neither a raceway pull nor the pod's hanging weight reaches the USB-C receptacle (REQ-MECH-011, R-017). The loop only has to take a short turn angle, not a full rotation.
- **T-bar:** one stepped-jaw part covers both grid widths, so there is no loose insert to drop off a ladder. Flange thickness and the tile-edge clearance are measured on real 15 mm and 24 mm grids at G1.
- **Gasket groove (REQ-MECH-007):** the radial groove is in every P2 and stays empty in v1. The FDM layer lines on the boss and bore run around the circumference and so do not cross the seal. The rotation happens under constant radial squeeze, which reduces the O-ring drag and roll risk compared with a squeeze-on-twist face seal (R-016). The bathroom cable crossing needs a grommet in the rim notch (TBD at G1).
- **Printability:** there are no supports on show faces (REQ-MFG-001). The only show faces are the P1 radome face (on the bed), the P1 side wall (vertical) and the P4 end (on the bed). The P1 rim-to-side chamfer is at ≥45°.

## 6. Requirement-by-requirement assessment (all 66)

| REQ | Status | Reason |
|---|---|---|
| SYS-001 | at risk | Corner coverage is a sensor limit (R-003). The concept does not add to the risk beyond the radome |
| SYS-002 | at risk | Radome εr is unknown for PETG, resin and PA (R-001); the A/B test decides |
| SYS-003 | at risk | Spacing unknown (R-007); the concept adds nothing either way |
| MECH-001 | meets (concept) | Screws + drywall anchors through P2, types chosen at G1 |
| MECH-002 | meets (concept) | Screws + plugs through the same P2 |
| MECH-003 | at risk | Stepped jaw fits 15 and 24 mm by concept. Flange thickness and tile clearance are not measured |
| MECH-004 | at risk | Anchor pull-out is set by the makers' datasheets; the load is a placeholder until REQ-MECH-015 |
| MECH-005 | at risk | Bayonet lugs in bearing; lug sizing waits for mass and safety factor (R-005). Independent twist-lock review at G1 |
| MECH-006 | meets | No screw passes through P1 |
| MECH-007 | meets (concept) | Continuous radial groove on every P2 |
| MECH-008 | at risk | Needs a Table A radial gland and a splice (A-017) |
| MECH-009 | at risk | Ramp preload removes play; tilt stack TBD once the diameter is known; 5° is A-002 |
| MECH-010 | meets (concept) | No metal in P1. The fallback P9 plunger sits behind the antenna plane. Screws are behind the kit, outside the downward cone. Inspect at G2 |
| MECH-011 | at risk | Two jacket clamps; clamp force untested; load from REQ-MECH-015 |
| MECH-012 | meets (concept) | Exit at the ceiling plane through the rim notch, aimed by the slotted P2 rotation |
| MECH-013 | at risk | Needs εr from the coupon; MJF wall conflict (R-015) |
| MECH-014 | meets (concept) | Gap set within P1 from the radome face (N × 2.5 mm); tolerance open (R-001) |
| MECH-015 | not addressed | G2 entry item (mass × sourced factor). The concept only lets the lug size scale with it |
| MECH-016 | meets (concept) | Hand turn by the side flutes. Torque TBD; demo at G3 |
| MECH-017 | at risk | Cross-section and radial dims chosen at G1 from ARSDG |
| MECH-018 | at risk | Cable-crossing grommet not designed; IPX4 method via Q-17 |
| PWR-001 | meets (by kit) | Kit USB-C 5 V used as-is |
| PWR-002 | at risk | Peak current unmeasured (R-014) |
| PWR-003 | meets | No battery |
| PWR-004 | at risk | C-to-C start-up unknown (R-012) |
| PWR-005 | at risk | A-007/A-008 unmeasured |
| ELEC-001 | meets | No mains |
| ENV-001 | at risk | Needs test; the ratings contain the range |
| ENV-002 | at risk | Kit enclosed by P1+P2; 32.1 K/W budget not yet analysed (R-006) |
| SAFE-001 | at risk | UL94 grades of PETG/resin/PA not chosen; class from Q-17 |
| SAFE-002 | at risk | Limit from Q-17; not measured |
| SAFE-003 | not addressed | Text item; the concept adds no text |
| SAFE-004 | not addressed | Text and firmware item |
| EMC-001 | at risk | Kit claim DS p.8; the pod as built is untested |
| EMC-002 | at risk | Grant coverage is for a qualified human |
| EMC-003 | at risk | Untested |
| EMC-004 | at risk | Qualified human |
| EMC-005 | meets | No added radio |
| FW-001 | not addressed | Firmware. The instructions must add the pod depth to the measured ceiling height (TBD) |
| FW-002 | not addressed | Firmware |
| FW-003 | not addressed | Firmware |
| FW-004 | not addressed | Firmware |
| FW-005 | not addressed | Firmware; the light pipe makes it visible |
| FW-006 | not addressed | Firmware |
| UX-001 | at risk | Colour matched at the demo stage; bed-face texture vs "matte" TBD |
| UX-002 | meets (concept) | Screw heads are under the pod |
| UX-003 | not addressed | Instructions |
| UX-004 | at risk | Flush pipe by concept; position depends on A-005 and R-018 |
| UX-005 | meets | No window, no pinhole |
| UX-006 | meets (concept) | Kit back is open when removed and stays powered on the loop; button face side TBD (A-005) |
| MNT-001 | not addressed | Instructions |
| MNT-002 | not addressed | Instructions |
| MNT-003 | at risk | Fixing types named at G1; not yet chosen |
| MNT-004 | not addressed | Instructions; P2 notch aim supports it |
| MNT-005 | not addressed | Instructions |
| MNT-006 | not addressed | Instructions + TP-SYS-003 |
| MFG-001 | meets (concept) | Show faces on the bed or vertical |
| MFG-002 | meets (concept) | All overhangs ≥45° or hidden |
| MFG-003 | meets (concept) | No show-face bridges |
| MFG-004 | at risk | Radome at N=1 may fall near 1.2 mm; MJF 2.5 mm conflict (R-015) |
| MFG-005 | meets (concept) | Clearance is a per-process param |
| MFG-006 | meets (concept) | All parts are PETG-printable; the detent flexure strain is unverified (PETG not in R5d) |
| MFG-007 | at risk | SLA resin detent brittleness and MJF wall |
| COST-001 | at risk | $28.99 kit leaves $21.01 for P1–P5 and fixings, none quoted |
| COST-002 | at risk (likely fails) | $1.01 left after the kit (R-002); this concept has more small parts than the minimum |
| COST-003 | not addressed | BOM not built |

Tally: meets / meets (concept) 22, at risk 30, not addressed 14 (66).

## 7. Top 5 risks and mitigations

| # | Risk | Mitigation |
|---|---|---|
| 1 | Installer lets go before the turn completes, or the detent backs off, and the pod falls (R-005) | Rim-flush "locked" cue; the ramp only seats at the end stop; the detent gets a turn-back torque spec; independent twist-lock review at G1; pull test by REQ-MECH-015 loads; P9 metal plunger fallback |
| 2 | The pod hangs on the service loop during removal and overloads a clamp or the USB-C receptacle (R-017) | Two jacket clamps put the hanging load on the jacket; include pod weight on the loop in TP-MECH-011; the loop length limits the drop; instructions say "support the pod" |
| 3 | Detent flexure fatigues or cracks in PETG or SLA resin (no PETG row in R5d; resin brittle) | Frequent-use strain at 60 % of the single-assembly value (Covestro, `snap_fit.toml`); cycle test at G3; replaceable P9 plunger path |
| 4 | Light pipe or kit standoffs break the radome uniformity (R-018, R-001) | Measure the LED position first (A-005); prefer N=1 gap so the pipe can clear the cone (§4); pipe included in TP-SYS-002 A/B |
| 5 | Cost over target: extra parts (P3, P4, P5, P9) on top of a kit that already takes 96.6 % of the $30 (R-002) | Merge P3 into P2 as a living-hinge lid if strain allows; P5 optional SKU; P9 only if needed; report the real BOM |

## 8. Rough cost view (sourced prices only)

| Line | US$ | Source |
|---|---|---|
| Kit, 10+ tier | 28.99 | Web 2026-09-25 (`sensor.unit_price_web_qty10`) |
| P1–P5 printed parts (FDM PETG / SLA / MJF) | to be quoted | print-service quotes with dates (REQ-COST-003) |
| O-ring cord P6 (bathroom only), plunger P9 (if needed) | to be quoted | supplier quotes |
| Fixings P8 (in BOM scope, not in box) | to be quoted | anchor makers' price lists |
| **Pod BOM** | **≥ 28.99 + unquoted lines** | against $50 prototype (room 21.01) and $30 production (room 1.01) |

## 9. Why it differs from the obvious alternatives

- **Kit in the base plate, dumb twist-off cover:** the cable never moves, but reset means reaching up to a live board on the ceiling, and the radome gap then depends on the twist-lock axial stack. C keeps the gap inside one part and puts reset in the installer's hand, still powered.
- **Screw-thread cover:** several turns twist the cable, can cross-thread overhead and give no clear "done" signal. C uses one short turn, one entry position, a click and a flush rim.
- **Magnetic attach:** puts magnets or steel near the antenna and depends on magnet pull for fall retention. C has no metal in the pod and carries the load through lugs in bearing.
- **Face-seal bathroom gasket on the twist ramp:** the squeeze grows while turning, so torque rises and the O-ring drags (R-016). C's radial gland seals independently of the twist, so v1 and bathroom feel alike and the bayonet does not carry the squeeze load.
- **Two T-bar clips or an adjustable jaw:** C uses one stepped jaw that fits both widths with no setting to get wrong on a ladder.
