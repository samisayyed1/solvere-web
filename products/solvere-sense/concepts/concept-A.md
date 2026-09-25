# Concept A: two-part bayonet puck (minimum part count)

- **Lens:** minimum part count and assembly simplicity. The fewest printed parts and fasteners that still meet every owner decision.
- **Gate:** G1 concept tournament (PDR level). Evidence level L0: nothing here is measured.
- **Author:** generator A, 2026-09-25. Independent of the other concept files, which I have not read.
- **Rule used for numbers:** every dimension below comes from `params/params.toml`, a source in `docs/sources/`, a requirement, or arithmetic on those, with the citation given. Everything else is "TBD at G2".

## 1. Summary

The v1 pod has **two printed parts**: a **base plate** that screws to the ceiling and holds the sensor kit, and a **shell** printed as one piece with the radome. The shell twists onto the base plate with a bayonet. Nothing else is in the box. The kit clips straight into cradle features printed into the base plate. So the kit, the USB-C plug and the cable all stay on the part that does not move, and the shell twists freely over them (this removes R-017). With the shell off, the reset button is left exposed (REQ-UX-006). The radome is the flat floor-facing face of the shell. Its thickness is uniform, sized by MDS §8 item 3, and set by one CAD parameter for each material. The kit's cradle and the shell's radome are located from one axial datum, the bayonet lug seat, so the antenna-to-radome gap (MDS §8 item 4) depends on only two part dimensions. There is no separate light pipe: the WS2812 LED shows through the uniform radome as a soft glow, so no extra part and no dielectric post sits in the beam. A separate clear pipe is kept as a +1-part fallback. Strain relief is a serpentine channel printed into the base plate, with no clamp part and no screw. The cable leaves through a channel in the base plate's ceiling face, at the ceiling plane. The O-ring groove is a continuous circular face groove in the base plate, present in every build. The T-bar option does not use an adapter part fitted to the base plate. Instead, a printed **alternative base plate** with the same bayonet and cradle hooks onto the grid flange. It has break-off inner hooks, so one part fits both 15 mm and 24 mm grids. Fixings are two screws with two anchors or plugs (not in the box). The installed pod is therefore 2 printed parts + kit + 4 fixings. The bathroom variant adds only an O-ring cord and a cable seal.

## 2. Part list

| # | Part | Qty | Process (G3 fit / demo) | Ships in box | Notes |
|---|---|---|---|---|---|
| P1 | Base plate: ceiling datum face, 2 screw holes, kit cradle with integral snap clips, bayonet ledge with seat notches and an integral detent flexure, O-ring face groove, serpentine strain relief, cable channel in the ceiling face | 1 | FDM PETG (fit only) / SLA Formlabs Flame Retardant Resin or MJF HP 3D HR PA 12 (see §9) | yes | Printed ceiling face down, so the channel and screw holes open onto the bed; the groove opens upward |
| P2 | Shell + radome (one piece): flat uniform radome face, skirt, bayonet lugs, rim that closes the gasket gland | 1 | as P1 (§9) | yes | Printed radome face down on the bed: the show face is the bed face, with no supports |
| P3 | T-bar base plate (optional, replaces P1): same bayonet, cradle, groove and strain relief as P1; flange hooks at 24 mm spacing plus break-off hooks at 15 mm spacing | 1 | as P1 (§9) | optional SKU | Hidden behind P2 once installed |
| F1 | Screw, countersunk, for P1 | 2 | purchased | no (Owner round 2, Q-05) | Type and size TBD at G2 from the anchor maker's datasheet against the REQ-MECH-015 load |
| F2 | Drywall anchor (plastic expansion type) **or** concrete wall plug (nylon) | 2 | purchased | no | Chosen per ceiling (REQ-MECH-001, -002, REQ-MNT-003); size TBD at G2 |
| K1 | Seeed MR60FDA2 kit, SKU 114993388, used as-is | 1 | purchased | yes | DS p.1, p.7. The kit's own 3D-printed case is **not** used (see §7) |
| B1 | O-ring cord, bathroom variant only | 1 | purchased | bathroom only | Cross-section per ARSDG Table A, chosen at G1 or G2 (A-017) |
| B2 | Cable-exit seal, bathroom variant only | 1 | purchased | bathroom only | Type TBD (IF-04 open parameter) |
| FB1 | Clear press-fit light pipe, **fallback only** | 0 (1 if needed) | FDM or SLA clear | fallback | Used only if the glow-through test fails (Risk 2) |

Why there are two screws: one screw would let a bayonet base plate spin on the ceiling when the shell is twisted, so two is the minimum that reacts the twist torque. Whether two also carries the pull load is checked at G2 (REQ-MECH-004, -015).

**Assembly (installer, no tools after drilling):** (1) Drill and fit F2, then screw P1 to the ceiling with F1. (2) Plug the USB-C cable into the XIAO, press the cable into the serpentine channel, and lead it out through the ceiling-face channel to the raceway. (3) Press the kit into the P1 cradle clips. (4) Offer up P2 and twist it until the detent clicks. Removal is step 4 in reverse. Steps 2 and 3 can swap if the cradle blocks access to the plug (TBD once the kit is measured, A-005).

## 3. Architecture details

**Attach and detach (IF-03).** A gravity-seated bayonet. Lugs on the inside of the P2 skirt enter entry gaps in a ledge on a P1 boss. The installer pushes P2 up and twists it. At the end of travel each lug drops into a **seat notch** on the underside of the ledge, against a rotation end stop. From then on, gravity and any downward pull hold the lug in the notch: the notch walls block rotation, so the shell cannot turn out until it is first pushed up by the notch depth. On top of that, an integral detent flexure on P1 must be overridden by the rotation. The lug-in-notch contact is the **axial datum**, and it is the same whether or not a gasket is fitted. The notch depth and the detent release torque are TBD at G2. The number of lugs, the twist angle and the hand torque are TBD at G2. Because the kit sits in P1, P2 has no orientation that matters (the radome is uniform and rotationally symmetric), so the lugs can be symmetric. The lugs print as horizontal cantilevers in the layer plane, so a downward pull bends them within the layers, not across the layer bonds. Their undersides get 45° chamfers (`mfg.fdm.max_overhang`), so they need no support.

**Radome (IF-05, following MDS §8).**
- The flat bottom face of P2 is the radome: smooth and uniform (MDS §8 item 2). It is printed fully solid, with no infill.
- Thickness is T = N·c/(2·f·sqrt(εr)), with f = 60 GHz (`sensor.freq_centre`) and λ0 = 4.997 mm (`sensor.wavelength_free_space`), so T = N × 2.4985 mm / sqrt(εr).
  - εr for PETG, the SLA resin and MJF PA is not in the MDS table. It comes from the TP-SYS-002 coupons (R-001), so T is **one CAD parameter per material**.
  - N is the smallest integer that makes T at least the process minimum wall: 1.2 mm for FDM (`mfg.fdm.min_wall`, REQ-MFG-004), 2.5 mm for MJF (`mfg.mjf.wall_min_pn`), and 1.0 mm unsupported for SLA (sla.toml `wall_min_unsupported_mm`). N can therefore differ between processes.
  - For FDM, T should also be a whole number of layers (layer height TBD at G2) so the sliced part keeps the design thickness.
- The antenna-to-radome gap is d = N'·2.5 mm (`radome.antenna_gap_step`, REQ-MECH-014). N' is TBD at G2, once the kit's stack height and any parts standing proud of the antenna face have been measured (A-005).
- The gap stack has two dimensions only: from the P1 ledge notch to the cradle seat (part P1), and from the P2 lug top face to the radome inner surface (part P2). They meet at the datum contact.
- Flat-radome extent (derived): the uniform region must cover the 60° keep-out cone (`radome.keepout_half_angle`) where it crosses the radome inner surface.
  - Using the radar module outline as a conservative bound on the antenna (25 × 31.5 mm, MDS p.3, half-diagonal 20.1 mm), the minimum flat radius is 20.1 + d·tan 60°.
  - That gives **24.4 mm for d = 2.5 mm** and **28.8 mm for d = 5.0 mm**: a minimum flat diameter of 48.9 mm or 57.6 mm.
  - The skirt then lies on or outside the cone boundary above the radome plane, so it needs no RF control.
  - The shell's outer diameter is set by the larger of this and the kit carrier-board outline (TBD, A-005).
- Show-face edge: a 45° chamfer (`mfg.fdm.max_overhang`) where the radome meets the skirt on the bed, not a fillet, so the first layers have no overhang steeper than 45°.

**Light pipe (IF-09).** Baseline: no pipe. The WS2812 sits behind the uniform radome and shows through it as a glow when lit. It is invisible when off (REQ-FW-004), which suits "visually disappear". This adds no part and puts no post or thinned spot inside the cone, so REQ-MECH-013 and R-018 are not broken. Open questions: does the warm-white radome at thickness T pass enough light, and does a diffuse glow satisfy the owner's "tiny flush light pipe" (REQ-UX-004)? Both are checked on the TP-SYS-002 coupons and put to the owner at G2. Fallback in order:
1. A light-guide boss printed as part of P2, if the measured LED position (A-005) turns out to be outside the 60° cone.
2. The clear press-fit pipe FB1 (+1 part), included in the TP-SYS-002 A/B test.

**Cable entry and strain relief (IF-06).** The XIAO USB-C plug stays on P1. The cable jacket runs round a serpentine of printed posts in P1, which grips it by wrap friction (REQ-MECH-011, no clamp part). It then leaves radially through an open channel in P1's ceiling face, at the ceiling plane, into the raceway end (REQ-MECH-012). Because P1 never rotates, the twist never reaches the cable (R-017). The channel width, post spacing and grip depend on the cable jacket diameter, which is unknown until the cable is chosen (Q-13, A-009), so they are TBD at G2. The cable passes the P2 skirt through the gap between the skirt and the ceiling-face channel, so P2 needs no notch that has to line up.

**Gasket-groove provision (IF-04).** A continuous circular face groove on P1, on the base-plate side of the joint as IF-04 requires, faces the P2 rim.
- It is round, so the ARSDG p.90 non-round inside-corner rule does not apply.
- The gland depth is set by the lug seat (the rim position at the datum), so the squeeze is fixed by geometry, not by bayonet torque. The candidate cord sizes and glands are the three ARSDG Table A sets quoted in `docs/interfaces.md` IF-04; the cross-section is chosen at G2 (A-017).
- v1 ships with the groove empty. The bathroom variant uses the same P1 and P2, plus B1 and B2.
- The cable passes through P1 inside the seal line, so B2 is the only other leak path.

**T-bar option (IF-02).** P3 replaces P1 and keeps its bayonet, cradle, groove and strain relief, so the pod stays at 2 printed parts. P3 hooks over the exposed flange edges of the grid. For a 24 mm grid (`tbar.grid_width_wide`) the outer hook pair is used and the inner pair, at 15 mm (`tbar.grid_width_narrow`), is snapped off. On a 15 mm grid the inner pair stays and grips. Hook depth, flange-thickness allowance and slide resistance along the bar are TBD at G2. No drilling or cutting is needed (REQ-MECH-003). The steel grid sits behind the antenna plane, outside the forward 60° cone (REQ-MECH-010).

**Print orientation (REQ-MFG-001..003).**
- P2 prints radome face down. The skirt is vertical or flares out at no more than 45°, and the lug undersides are chamfered. Its only show face is on the bed, so it has no supports and no show-face bridges.
- P1 and P3 print ceiling face down. Their show faces are only the rim ring visible past P2, if any (TBD), and it prints vertically.
- Hidden bridges stay within 10 mm (`mfg.fdm.max_bridge_hidden`).

**Mating clearance.** The bayonet is a moving joint. The params give 0.5 / 0.2 / 0.6 mm for FDM / SLA / MJF (REQ-MFG-005), but the rules files give more conservative moving clearances: 1.0 mm FDM (fdm.toml), 0.5 mm SLA (sla.toml) and 0.9 mm MJF (mjf.toml). The G2 design must settle this conflict. The lug seat, not the clearance, sets the radome gap. The push-up release travel must exceed the notch depth; with a gasket fitted it also compresses the cord slightly further (to be kept within the ARSDG squeeze range).

## 4. Requirement compliance (all 66)

| REQ | Status | How / why |
|---|---|---|
| SYS-001 | at risk | Sensor-limited: 2.12 m corner half-diagonal against the 2 m radius (R-003). Concept adds only a uniform radome |
| SYS-002 | at risk | Radome εr unknown and the gap crosses a joint (R-001, Risk 1). There is no pipe or post in the beam |
| SYS-003 | at risk | Spacing found by TP-SYS-003 (R-007). Concept-neutral |
| MECH-001 | meets | P1 + F1 screws + F2 drywall anchors. Sizes TBD at G2 |
| MECH-002 | meets | Same P1, F2 = concrete plugs |
| MECH-003 | at risk | P3 break-off hooks: grip, tile lift and slide on the flange are untested (Risk 5) |
| MECH-004 | at risk | Two-anchor pull-out is unquantified. Load is the A-001 placeholder |
| MECH-005 | at risk | Gravity-seated notch + detent (GATE-S1). Lug shear and ledge creep unquantified; PETG strain not in snap_fit.toml (Risk 4) |
| MECH-006 | meets | No screw passes through P2 |
| MECH-007 | meets | Continuous circular groove in P1 (and P3) in every build |
| MECH-008 | at risk | Squeeze is fixed by the lug-seat datum, but gasket reaction against the bayonet and O-ring drag in the twist are unproven (R-016) |
| MECH-009 | meets (architecture) | Cradle and ceiling datum face are on the same part (P1). Tolerance TBD once the kit is measured (A-005) |
| MECH-010 | meets | No metal in the printed parts. Screws and the T-bar are behind the antenna plane. No metallic pigment specified |
| MECH-011 | at risk | Serpentine wrap-grip unproven; cable diameter unknown (Risk 3) |
| MECH-012 | meets | Ceiling-face channel exits at the ceiling plane. Size to the raceway end TBD (A-009) |
| MECH-013 | at risk | Single part, uniform by design; εr from the coupon; FDM layer quantization |
| MECH-014 | at risk | d = N'·2.5 mm across the lug-seat datum (two-dimension stack). Tolerance open (R-001) |
| MECH-015 | not addressed | G2 entry criterion (GATE-S1 item 4). The kit hangs from P1, not from the bayonet, but the REQ-MECH-005 test still uses shell + kit weight as written |
| MECH-016 | meets | Bayonet by hand. Torque TBD |
| MECH-017 | at risk | Cross-section not chosen (A-017). Round groove avoids the corner rule |
| MECH-018 | at risk | Cable-exit seal B2 undefined; FDM porosity; MJF watertight wall 4.0 mm (mjf.toml) |
| PWR-001 | meets | Kit as-is on its XIAO USB-C |
| PWR-002 | at risk | Peak current unmeasured (R-014) |
| PWR-003 | meets | No battery |
| PWR-004 | at risk | C-to-C start-up unpublished (R-012) |
| PWR-005 | at risk | R-014 conflict (MDS 600 mA against DS 0.8 W) |
| ELEC-001 | meets | USB only |
| ENV-001 | at risk | Kit-level rating is assumed (A-004) |
| ENV-002 | at risk | Closed puck with no vents (vents would conflict with the groove and the look). The 32.1 K/W budget is unchecked (R-006) |
| SAFE-001 | at risk | Listed path: FR Resin V-0 3 mm / V-1 2.5 mm / HB 1.5 mm; HP PA 12 HB 0.75 mm; PETG fit-check only (§9). Class set by a qualified human (Q-17); a colour coating is not covered by either listing |
| SAFE-002 | at risk | Surface limit from a qualified human (Q-17); measure at 40 °C |
| SAFE-003 | not addressed | Text, not geometry. No marking is printed on the parts |
| SAFE-004 | not addressed | Text and firmware entity names |
| EMC-001 | not addressed | Kit compliance; the concept adds no electronics |
| EMC-002 | not addressed | Qualified-human question |
| EMC-003 | not addressed | Test route set by a qualified human |
| EMC-004 | not addressed | ISED question |
| EMC-005 | meets | Zero added electronics or radios |
| FW-001 | not addressed | Firmware |
| FW-002 | not addressed | Firmware |
| FW-003 | not addressed | Firmware |
| FW-004 | not addressed | Firmware. The glow-through LED is invisible when off |
| FW-005 | not addressed | Firmware. Glow brightness to be confirmed (Risk 2) |
| FW-006 | not addressed | Firmware |
| UX-001 | at risk | Colour matched at the demo stage; the white must be translucent enough for the glow (Risk 2) |
| UX-002 | meets | Screw heads sit inside, under P2 |
| UX-003 | not addressed | Instructions |
| UX-004 | at risk | A glow through the radome may not count as a "tiny flush light pipe" (Risk 2). Fallback FB1 |
| UX-005 | meets | No window and no pinhole; the BH1750 sits unused behind the radome |
| UX-006 | at risk | Kit stays in P1 and is exposed when P2 is off; the button position on the board is unmeasured (A-005) |
| MNT-001 | not addressed | Instructions |
| MNT-002 | not addressed | Instructions |
| MNT-003 | at risk | Types proposed (countersunk screw + plastic expansion anchor or nylon plug); sizes TBD at G2 |
| MNT-004 | not addressed | Instructions |
| MNT-005 | not addressed | Instructions |
| MNT-006 | not addressed | Instructions, after TP-SYS-003 |
| MFG-001 | meets | Orientations in §3: P2 show face on the bed; no show-face supports |
| MFG-002 | meets | 45° chamfers on the lugs and the radome edge; vertical or ≤45° skirt |
| MFG-003 | meets | No show-face bridges; hidden bridges ≤10 mm |
| MFG-004 | meets | Walls ≥1.2 mm; N chosen so T ≥ the process minimum |
| MFG-005 | at risk | Conflict between the params and the rules files over moving-joint clearance (§3) |
| MFG-006 | meets | All parts in PETG |
| MFG-007 | at risk | MJF 2.5 mm walls (R-015); N and T set per process; clearance per process |
| COST-001 | at risk | US$21.01 left for 2 printed parts + 4 fixings; not yet quoted |
| COST-002 | at risk | US$1.01 left after the kit (R-002). Almost certainly fails at any part count |
| COST-003 | not addressed | BOM lines listed in §6; dated quotes at G2 |

Totals: 20 meets (including MECH-009 by architecture), 26 at risk, 20 not addressed. All 20 "not addressed" rows are firmware, instructions, compliance or the G2 BOM, none of which a mechanical concept can meet.

## 5. Key dimensions (derived only)

| Item | Value | Source |
|---|---|---|
| Antenna-to-radome gap d | N'·2.5 mm (N' TBD at G2) | `radome.antenna_gap_step`, MDS p.12 item 4 |
| Radome thickness T | N·4.997/(2·sqrt(εr)) mm; εr from TP-SYS-002 | MDS p.12 item 3; `sensor.wavelength_free_space` |
| Minimum T by process | ≥1.2 mm FDM, ≥2.5 mm MJF (PN), ≥1.0 mm SLA | `mfg.fdm.min_wall`; `mfg.mjf.wall_min_pn`; sla.toml |
| Minimum flat-radome radius | 20.1 + d·tan 60° = 24.4 mm (d = 2.5) or 28.8 mm (d = 5.0) | MDS p.3 25 × 31.5 mm module; `radome.keepout_half_angle` |
| Level tolerance to hold | ≤5° | `sensor.level_tolerance` (A-002) |
| T-bar hook spacings | 15 mm and 24 mm grid widths | `tbar.grid_width_narrow`, `tbar.grid_width_wide` |
| Gland candidates | per ARSDG Table A (3 sets in IF-04) | ARSDG p.20 |
| Show-face overhang / bridge | ≤45° / <5 mm | `mfg.fdm.max_overhang`, `mfg.fdm.max_bridge_show_face` |
| Everything else (shell OD and height, lug count, twist angle, torque, fixing sizes, channel width) | TBD at G2 | kit measurement (A-005), cable (Q-13), REQ-MECH-015 |

## 6. Cost view (US$ per unit)

| Line | Price | Source / status |
|---|---|---|
| K1 MR60FDA2 kit | 28.99 (qty 1 and 10+) | Web, product page p-5946, 2026-09-25 |
| P1 base plate, P2 shell (P3 T-bar base when ordered) | to be quoted | FDM PETG in-house; SLA or MJF from a service |
| F1 ×2, F2 ×2 | to be quoted | In the BOM scope (Owner round 2, Q-10) though not in the box |
| B1, B2 (bathroom only) | to be quoted | outside the v1 BOM |
| FB1 (fallback only) | to be quoted | added only if Risk 2 fires |
| **Prototype room** | 50.00 − 28.99 = **21.01** for P1 + P2 + fixings | `cost.prototype_max` |
| **Production room** | 30.00 − 28.99 = **1.01** | `cost.production_bom_max`; R-002 |

This concept gives the smallest BOM a printed enclosure can have: 2 printed lines and 2 fixing lines, with no inserts, no magnets, no separate pipe and no clamp. That also means fewer BOM lines needing a dated quote (REQ-COST-003). It does not fix R-002: the kit alone uses 97% of the US$30 target.

## 7. Top 5 risks and mitigations

| # | Risk | Mitigation |
|---|---|---|
| 1 | Because the kit is in P1 and the radome in P2, the gap d spans the bayonet joint. Wear at the notch, lug slop or creep of the ledge under gravity load could move d off N'·2.5 mm (REQ-MECH-014, R-001) | A single lug-seat datum; the gasket gland is depth-limited, so the gasket cannot change the datum. Run TP-SYS-002 A/B at nominal d and at the tolerance extremes. Fallback: move the kit into P2 (same part count, but R-017 returns) |
| 2 | Glow-through LED: too dim through white at thickness T, or too diffuse, or not accepted as a "light pipe" (REQ-UX-004, UX-001) | Print radome coupons in the demo grade and colour at each T (FR Resin is light grey [FL-FR], so the colour route is open, §9); show them lit to the owner at G2; confirm in firmware (REQ-FW-005). Fallback order: integral boss outside the cone, then FB1 (+1 part) inside the A/B test |
| 3 | The serpentine wrap-grip slips under the REQ-MECH-011 pull; the cable diameter is unknown (Q-13) | Size the posts once the cable is chosen; pull-test on FDM and demo materials. Fallback: a cable tie through a printed slot (+1 purchased part, still no screw) |
| 4 | Bayonet retention: lug shear, and the integral detent creeping or relaxing in PETG (no PETG row in snap_fit.toml). Gasket squeeze load and O-ring drag during the twist in the bathroom variant (R-005, R-016) | Detent strain from the PETG supplier datasheet at G2; pull and cyclic twist tests (TP-MECH-005, -016); ramp profile TBD so the rim reaches the gland late in the travel; independent twist-lock review (R-005) |
| 5 | P3 break-off hooks: poor grip on the flange, the tile lifted by the hook tips, slide along the bar, or a 15 mm snapped by mistake (REQ-MECH-003) | Test on real 15 mm and 24 mm grids; pull test as for REQ-MECH-004. Fallback: two P3 SKUs (still 1 part per install) |

Also tracked: the thermal budget with no vents (R-006, ENV-002) and cable-exit sealing in the bathroom variant (MECH-018).

## 8. How it differs from the obvious alternatives

- **Separate radome window plus shell:** gives a better εr choice (for example a PC window), but adds a part and a sealed joint in the beam. Here the radome is the shell, so there is no joint in the cone. The cost is that one material has to serve colour, strength and RF.
- **Kit in the twisting shell:** keeps the RF stack inside one part, but twists the cable and needs a slip loop or rotating strain relief (R-017), with more features and possibly more parts. This concept accepts a two-dimension gap stack to keep the cable static.
- **Screw-clamp strain relief, heat-set inserts or magnets for retention:** each adds purchased parts and assembly steps. This concept uses printed geometry only.
- **Separate T-bar clip bolted to a standard base plate:** adds a part and fasteners. Here the T-bar part replaces the base plate outright.
- **Reusing the kit's own 3D-printed case (DS p.1 "Early Build"):** would save the cradle, but its geometry is unpublished and it would put a second, uncontrolled dielectric layer in the beam, which goes against MDS §8. Rejected.
- **Cost of this lens:** a single material across the shell and radome; strain relief and T-bar fit that are harder to verify; and an LED approach the owner may reject. Each has a named +1-part fallback, so the worst case is 3 printed parts + 1 purchased tie.

## 9. Safety gates (GATE-S1..S3, `concepts/gates.md`)

Sources fetched 2026-09-25, not taken from memory. They are not yet in `docs/sources/`; the coordinator should add them with these hashes:
- **[HP-UL]** HP, "HP 3D High Reusability PA 12 ... UL 94 and UL 746A Certification Technical Note", 4AA7-2792ENW, May 2018, https://forerunner3d.com/wp-content/uploads/2024/09/HP-PA12-UL-94-and-746A-Certification.pdf, sha256 96d85f61630749c2e3f38225d20e12962e2ef7ad9efdcd194d12009c1537e3c3. It says "HB at a 0.75mm thickness", with the Blue Card at UL iQ ULID 103600424 (QMTC2, published 2018-03-13). The listing covers HP 3D600/700/710 agents on Jet Fusion 4200/4210 printers. I have not opened the UL iQ card itself.
- **[FL-FR]** Formlabs, "Flame Retardant Resin" TDS, prepared 13.04.2023, Rev. 02 26.07.2023, https://formlabs-media.formlabs.com/datasheets/2301750-TDS-ENUS-0_1.pdf, sha256 1d189b9c62303704479cb48b14592c272914befae0a21fe0906ccfc26885774c. It gives UL 94 "V-0 (3mm) V-1 (2.5mm) HB (1.5mm)", colour "Light grey", and dielectric constant 3.83 at 0.5 MHz and 3.82 at 1.0 MHz, dissipation factor 0.024 at 0.5 MHz and 0.025 at 1 MHz (ASTM D150).
- **[FL-EL]** Formlabs support, "Electrical properties of selected Formlabs SLA resins" (undated), https://formlabs.com/support/Electrical-properties-of-selected-Formlabs-SLA-resins/. It gives ASTM D150 values at 60 Hz to 27.12 MHz only; for example White Resin V4 is 3.07 / 0.004 at 27.12 MHz. It has no FR Resin row and no mm-wave data.
- A web search for 60 GHz permittivity of MJF PA12 on 2026-09-25 found no published value.

### GATE-S1 no-fall retention: PASS at concept level (numbers TBD at G2, as the gate allows)

| Criterion | How concept A meets it |
|---|---|
| 1 Positive interlock | A gravity-seated bayonet (§3). Each P2 lug sits in a seat notch under the P1 ledge, against a rotation end stop. The notch walls block rotation while the lug is loaded downward, and an integral detent flexure resists rotation as well. There is no friction-only, adhesive or magnet retention |
| 2 Load path, drywall / concrete | Shell P2 → lugs → P1 ledge notches → P1 body → countersunk heads of the 2 F1 screws → F2 drywall anchors or concrete plugs → ceiling. The kit: kit → P1 cradle clips → P1 → same path. If a clip lets go, the kit drops onto the P2 radome inner face and then follows the shell path, which is why REQ-MECH-005 stays at shell + kit weight |
| 2 Load path, T-bar | P2 → lugs → P3 ledge notches → P3 body → P3 flange hooks (24 mm pair, or 15 mm break-off pair) → T-bar flange → the building's grid hangers (outside the pod) |
| 3 Deliberate release | Release takes two actions in sequence: push the shell **up** by at least the notch depth, against gravity (and against the cord in the bathroom build), **and** rotate it past the detent. Gravity, vibration or a sideways knock gives neither action on its own, and an upward knock alone does not turn the shell. The notch depth and detent torque are TBD at G2 |
| 4 Loads per REQ-MECH-015 | TP-MECH-004 / -005 / -011 loads = measured weight × a safety factor recorded in `params/params.toml` (value and source due before G2). The concept's mechanism is fixed now; only the factor is TBD |

Residual risk (Risk 4): lug shear, ledge creep in the notch under sustained load, and the unsourced PETG strain limit. The FDM PETG parts are fit-check only (S2), so the retention proof is run on the demo grades.

### GATE-S2 flammability: PASS as a listed-material path (the class is set by a qualified human, Q-17)

| Part | FDM (G3 fit) | SLA demo | MJF demo |
|---|---|---|---|
| P1 base plate, P2 shell + radome, P3 T-bar base | PETG, **fit-check only, not a demo or production material** | Formlabs Flame Retardant Resin: V-0 at 3 mm, V-1 at 2.5 mm, HB at 1.5 mm [FL-FR] | HP 3D HR PA 12 (HP 3D600/700/710 agents): HB at 0.75 mm [HP-UL] |
| Light pipe | none in the baseline (glow-through). FB1, if ever needed, has **no listed grade identified**: using it means a re-gate | as FDM column | as FDM column |

- **Wall rule:** every wall, including the radome at T, must be at least the listed thickness for the class the qualified human picks.
  - FR Resin: ≥1.5 mm for HB, ≥2.5 mm for V-1, ≥3 mm for V-0.
  - PA 12: ≥0.75 mm for HB, and the MJF 2.5 mm wall rule governs anyway.
- **Class limit:** if Q-17 demands V-2 or better, the MJF path has no listing at any grade named here, so only the SLA FR Resin path remains.
- **Colour shortfall:** FR Resin is "Light grey" [FL-FR], and HP-UL states no colour. Matte warm white (REQ-UX-001) would need a coating, and neither UL listing covers a coated part. A coating inside the cone also adds a second dielectric layer (S3).
  - The fix is a UL 94-listed white grade, or a coating assessed by the qualified human and included in the TP-SYS-002 coupons. Neither is identified yet.
  - This is a UX shortfall, not a gate fail, because the listed path exists.

### GATE-S3 radar window: PASS as a measurement plan (T computed at G2 from a measured εr)

| Criterion | How concept A meets it |
|---|---|
| 1 Material εr, tan δ | None of the three grades is in the MDS §8 table. Formlabs publishes εr for FR Resin only at 0.5 and 1 MHz (3.83 / 0.024 [FL-FR]); HP publishes no εr for PA 12 [HP-UL]; nothing is published for PETG. The 60 GHz values are **pinned by measurement**, per grade and process, in TP-SYS-002 (plan below). The 1 MHz value is used only to size the coupons, never as the design εr |
| 2 Thickness | T = N·c/(2·f·sqrt(εr)), f = 60 GHz, i.e. T = N × 2.4985 mm / sqrt(εr). The radome is uniform, fully solid, smooth (bed face) and flat over the whole cone footprint (§3). Coupon sizing with the 1 MHz FR value: N = 1 → 1.28 mm, **N = 2 → 2.55 mm**, N = 3 → 3.83 mm. The concept's pick is **N = 2 for SLA FR Resin**: it clears HB 1.5 mm and V-1 2.5 mm; N = 3 is needed if V-0 at 3 mm is required. **MJF PA 12: N is the smallest integer with T ≥ 2.5 mm** (MJF wall), computed at G2 from its measured εr. The final T for every grade is computed at G2 |
| 3 Antenna gap | d = N'·2.5 mm (`radome.antenna_gap_step`); N' is fixed at G2 from the measured kit stack (A-005). It is held by one datum, the bayonet lug seat, with two dimensions: P1 notch → cradle seat, and P2 lug top → radome inner face (§3). It does not depend on the gasket or the clearance. It is checked at the tolerance extremes in TP-SYS-002 (Risk 1) |
| 4 Keep-out cone | No metal in any printed part. The F1 screws sit in P1 above the antenna plane, and the T-bar grid is above it too, so both are outside the forward 60° cone (`radome.keepout_half_angle`). No magnets or springs: the detent is a printed flexure. No light-pipe path in the cone (glow-through). No metallic pigment or conductive coating is specified, and any colour coating must be shown non-conductive and pass TP-SYS-002 |

**εr measurement plan (retires the S3 open item):**
1. Print flat coupons of each grade and process (PETG, FR Resin, HP PA 12) at the final process settings: solid fill, the chosen layer height, and the FR Resin post-cure per [FL-FR].
2. Print each as a thickness sweep around the N = 1, 2 and 3 values sized from the nearest published εr.
3. Measure εr and tan δ at 58–62 GHz (`sensor.freq_min`..`freq_max`) by a free-space or resonator method from a lab (to be quoted).
4. Also run the kit A/B presence test through each coupon (REQ-SYS-002). The transmission peak in the sweep confirms the half-wave T directly, which pins the actual grade even where only a range or a low-frequency value is published.
5. Record εr and T in `params/params.toml` (as `measured`) before the G2 CAD freeze.
