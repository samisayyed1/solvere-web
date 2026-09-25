# Requirements: Solvere Sense ceiling pod (v1, G0 draft)

EARS sentences, one per requirement, with an ID (`REQ-<AREA>-<NNN>`), a `Rationale:` and a `Verify:` method (inspection|analysis|demo|test). See `.claude/rules/systems.md` and CONTRACTS.md §6. Requirement text and IDs belong to systems-engineer and humans; other agents may change only `status`, `evidence` and `tests` in `trace.json`. Lint: `forge ears`; trace: `forge trace`.

Sources, in the order used. Local copies, sha256 and fetch dates are listed in `docs/sources/README.md`.

- **Owner**: `docs/intake/G0-owner-answers.md` (2026-09-25, L0 claimed).
- **Owner round 2**: `docs/intake/G0-owner-answers-2.md` (2026-09-25, L0 owner decision), answering the questions in `reviews/G0.md`.
- **ARSDG**: Apple Rubber "Seal Design Guide" (122 pages), `docs/sources/apple-rubber-seal-design-guide.pdf`, fetched 2026-09-25.
- **Claims wording**: `compliance/claims-wording.md` (deny-list and neutral terms for all user-facing text).
- **DS**: Seeed Studio "Industrial Product Datasheet, XIAO 60GHz mmWave Human Fall Detection Sensor-MR60FDA2", SKU 114993388, 8 pages, "Updated 2026-07-30 08:17:32". `docs/sources/MR60FDA2-datasheet-114993388.pdf`, fetched 2026-09-25.
- **MDS**: Seeed "MR60FDA2 Fall detection module technical specifications (Beta Version)", V1.0, 2024-03-05, 12 pages, linked from the Wiki "Resources" list. `docs/sources/MR60FDA2-module-datasheet.pdf`, fetched 2026-09-25. It covers the radar module only, not the kit. Its introduction names the module "MR60FDC1", an apparent typo in the source.
- **Wiki**: Seeed wiki "Getting started with 60GHz mmWave Fall Detection Sensor Kit with XIAO ESP32C6 (MR60FDA2)", https://wiki.seeedstudio.com/getting_started_with_mr60fda2_mmwave_kit/ (page footer "Last updated on Aug 19, 2024"). `docs/sources/wiki-mr60fda2.html`, fetched 2026-09-25.
- **XIAO**: Seeed wiki "Getting Started with Seeed Studio XIAO ESP32C6", specification table (footer "Last updated on Aug 5, 2024"). `docs/sources/wiki-xiao-esp32c6.txt`, fetched 2026-09-25.
- **FDA1**: Seeed wiki for the sibling MR60FDA1 module (footer "Last updated on Mar 3, 2023"). Used only where MR60FDA2 sources are silent, always as an assumption. `docs/sources/wiki-mr60fda1.txt`.
- **Web**: Seeed product page p-5946, fetched 2026-09-25. `docs/sources/seeed-product-page-p5946-excerpt.txt`.
- **R5a/R5b/R5d/R5e**: Forge research files in `docs/research/` of the Forge repo.
- **A-xxx / Q-xx**: assumptions in `ASSUMPTIONS.md`; open questions for the owner in `reviews/G0.md`.

Wording: this file uses neutral terms for the sensor's outputs ("fall event", "fall-event output", "presence output"), per `compliance/claims-wording.md`. Vendor document titles are quoted as published.

Scope: v1 is the bedroom and living-room pod, powered over USB-C. The hardwired (mains) variant is out of scope for v1 (Owner). The bathroom variant is out of scope for v1, but its gasket-groove interface is designed now (REQ-MECH-007, REQ-MECH-008).

## REQ-SYS-001

While mounted at a height from 2.2 m to 3.0 m above the floor, the pod shall output a fall event for a staged fall at every corner and at the centre of a 3.0 m by 3.0 m floor area centred below the pod.

Rationale: Owner: about 3 x 3 m per pod; Owner round 2 (Q-11): keep 3 x 3 m, with a 2 m radius as the fallback if the corner tests fail. DS p.2, p.3 and p.6 give a fall range of "3x3x3 meter". The Wiki "Installation method and sensing range" and MDS p.3 and p.10 give a maximum sensing (fall) radius of 2 m, which is shorter than the 2.12 m half-diagonal of a 3 m square, so the corners are at risk (R-003). DS p.3: the parameters were tested in empty deployment environments.
Verify: test

## REQ-SYS-002

The pod shall report human static presence at every test point at which the bare MR60FDA2 kit reports presence under the same test protocol.

Rationale: The radome and shell must not degrade the sensor. MDS §8 (p.11-12) warns that a radome adds dielectric and reflection loss, distorts the beam and can saturate the receiver, and it gives design rules (REQ-MECH-013, REQ-MECH-014), but no acceptance level. The acceptance is therefore an A/B comparison against the bare kit (DS p.6: static presence up to 6 m).
Verify: test


## REQ-SYS-003

While a second pod operates in the same room at the minimum pod spacing stated in the installation instructions, the pod shall give the same fall-event and presence outputs at every test point as it gives with the second pod switched off.

Rationale: Owner round 2: support up to 2 pods per room and check radar-to-radar interference. The only source statements are the Wiki keep-out "Multiple radars installed too close together" (no distance given) and the DS p.8 FCC statement that the transmitter "must not be co-located or operating in conjunction with any other antenna or transmitter"; whether the latter applies to two separate pods in one room is for a qualified human (Q-17). No source gives a spacing, so the spacing is found by test (R-007) and asked of Seeed.
Verify: test

## REQ-MECH-001

The pod shall fix to a drywall ceiling through the base plate using screws and drywall anchors.

Rationale: Owner: drywall ceilings, one screw-on base plate using anchors or plugs. Owner round 2 (Q-05): Forge proposes the screws and anchors at G1; they are not in the box.
Verify: demo

## REQ-MECH-002

The pod shall fix to a concrete ceiling through the base plate using screws and wall plugs.

Rationale: Owner: concrete ceilings through the same base plate using plugs. Owner round 2 (Q-05): Forge proposes the fixings at G1; not in the box.
Verify: demo

## REQ-MECH-003

Where the T-bar clip adapter is fitted, the pod shall mount to 15 mm and 24 mm drop-ceiling T-bar grids without drilling or cutting the ceiling tile.

Rationale: Owner: drop ceilings use a T-bar clip as an optional adapter. Owner round 2 (Q-07): 15 mm and 24 mm grids.
Verify: demo

## REQ-MECH-004

The base plate installed with its specified fixings shall withstand a static downward pull of 4 times the installed pod weight for 60 s without detaching from the ceiling.

Rationale: A pod falling from a bedroom ceiling onto a person is the main mechanical hazard (R-005). No sourced retention load exists in the Forge R5 files, so the load factor and hold time are placeholder A-001, valid through G0 only (Owner round 2); REQ-MECH-015 replaces them before G2.
Verify: test

## REQ-MECH-005

The shell shall remain attached to the base plate under a static downward pull of 4 times the combined shell and sensor-kit weight for 60 s.

Rationale: Same falling-object hazard as REQ-MECH-004 for the removable shell. Load factor and hold time are placeholder A-001 through G0 only (Owner round 2); REQ-MECH-015 replaces them before G2.
Verify: test

## REQ-MECH-006

The shell shall attach to the base plate without any screw passing through the shell.

Rationale: Owner: no visible screws on the room-facing side. Owner round 2 (Q-06): the pod twists off by hand (REQ-MECH-016); the twist-lock concept is detailed at G1.
Verify: inspection

## REQ-MECH-007

The shell-to-base joint shall include a continuous gasket groove around its full perimeter in every variant, including v1 builds that carry no gasket.

Rationale: Owner: the bathroom variant uses the same shell plus a gasket; design the gasket-groove interface now. Owner round 2 (Q-08): IPX4 with an O-ring cord gasket; groove sizing in REQ-MECH-017.
Verify: inspection

## REQ-MECH-008

Where the bathroom gasket is fitted, the pod shall hold the gasket compressed in the groove around the full joint perimeter while the shell is attached.

Rationale: Owner bathroom-variant intent; Owner round 2: O-ring cord. The compression (squeeze) range comes from ARSDG Table A for the chosen cord cross-section (REQ-MECH-017).
Verify: inspection

## REQ-MECH-009

The pod shall hold the MR60FDA2 antenna face parallel to the ceiling plane within 5° and facing the floor.

Rationale: Wiki "Installation method and sensing range": top-mounted, with the sensor side aligned to the direction of detection. No MR60FDA2 source gives a tilt limit; the 5° value is the FDA1 wiki's "horizontal deviation angle of ≤5°" for the sibling module and is assumption A-002.
Verify: inspection

## REQ-MECH-010

The pod shall have no metal part, metallic pigment or conductive coating inside a cone of 60° half-angle about the MR60FDA2 antenna boresight.

Rationale: Wiki: keep large areas of metal and mirror reflections out of the detecting range. The sources disagree on the field of view (R-013): DS p.3 and p.6 give 120° horizontal by 100° vertical, the Wiki "Features" list gives 100° x 40°, and MDS p.4 gives a -3 dB beam of -60° to 60° in both planes. The widest (60° half-angle in every plane) is used as the keep-out.
Verify: inspection

## REQ-MECH-011

The pod shall provide a cable strain relief that clamps the USB cable jacket so that a pull on the cable is not transmitted to the USB-C connector.

Rationale: Owner: the cable runs down the wall in a raceway to a wall adapter, so the cable can be pulled during installation and cleaning. The pull load is set with the retention loads under REQ-MECH-015.
Verify: test

## REQ-MECH-012

The pod shall route the USB cable out of the enclosure at the ceiling plane into the end of the adhesive cable raceway.

Rationale: Owner: cable in an adhesive raceway to a standard USB wall adapter; hidden look. Whether cable and raceway ship in the box is an open product decision (Q-13, A-009).
Verify: demo

## REQ-MECH-013

The radome shall have a thickness across the sensor field of view equal to an integer multiple of half the 60 GHz wavelength in the radome material.

Rationale: MDS §8 item 3 (p.12): radome thickness T = N·c/(2·f·sqrt(εr)), N = 1, 2, 3, with f the centre frequency; item 2: smooth surface and uniform thickness. The permittivity εr of the chosen radome material at 60 GHz is not in the MDS table (which lists PC, ABS, PEEK, PTFE, acrylic, glass, ceramics, PE, PBT; no PETG, SLA resin or PA nylon), so the thickness is set from a coupon test (TP-SYS-002) and the tolerance is open (R-001).
Verify: analysis

## REQ-MECH-014

The pod shall hold the distance from the MR60FDA2 antenna face to the radome inner surface at an integer multiple of 2.5 mm.

Rationale: MDS §8 item 4 (p.12): antenna-to-housing distance d = N·c/(2·f), N = 1, 2, 3, with "f=60GHz c/2f=2.5mm". Tolerance is not given in the MDS and is open (R-001).
Verify: inspection


## REQ-MECH-015

The retention test loads of REQ-MECH-004, REQ-MECH-005 and REQ-MECH-011 shall each equal the measured weight of the retained parts multiplied by a safety factor whose value and source are recorded in `params/params.toml`.

Rationale: Owner round 2: the pull test stays a placeholder only through G0; before G2, derive a real retention requirement from pod mass x a stated safety factor, with its source. This is a G2 entry criterion (`reviews/G0.md`). The safety factor is chosen by the qualified human named under Q-17 or taken from a cited standard.
Verify: inspection

## REQ-MECH-016

The pod shall detach from the base plate by a hand twist with no tool.

Rationale: Owner round 2 (Q-05/Q-06): hand twist-off, no tools, no visible screws. It must still meet REQ-MECH-005 retention and REQ-MECH-006. If the sensor kit rides in the twisting part, the USB cable or connector must survive the twist (R-017).
Verify: demo

## REQ-MECH-017

The gasket groove shall have the static gland depth, groove width and squeeze range that ARSDG Table A gives for the chosen O-ring cord cross-section.

Rationale: Owner round 2 (Q-08): O-ring cord gasket. ARSDG Section 4 Table A (PDF p.20) gives static gland dimensions per cross-section, axial (face) and radial; ARSDG p.90: in a non-round face groove the inside corner radius is at least 3 times the cross-section and the O-ring centreline length equals the groove centreline length; ARSDG p.113: O-ring volume never exceeds the minimum gland volume. The cross-section is chosen at G1 (A-017); ARSDG gives no separate rule for spliced cord.
Verify: analysis

## REQ-MECH-018

Where the bathroom gasket is fitted, the pod shall meet the IPX4 degree of protection.

Rationale: Owner round 2 (Q-08): IPX4. The IP code test standard and edition are not in the Forge R5 files; a qualified human confirms the test method (Q-17). The cable exit is a leak path (IF-04).
Verify: test

## REQ-PWR-001

The pod shall operate from a USB-C supply of 5 V rated at 1 A.

Rationale: Owner: USB-C, 5 V / 1 A. DS p.6: power supply 5V/1A. XIAO: input voltage (Type-C) 5 V.
Verify: test

## REQ-PWR-002

While operating in any mode, the pod shall draw no more than 1 A from its USB-C input.

Rationale: Keeps the pod inside the Owner's 5 V / 1 A supply rating. DS gives no peak current. MDS p.4 gives a radar-module operating current of 600 mA at 3.1 V to 3.5 V and MDS p.7 and p.11 ask for a supply able to deliver at least 1 A, so peak draw at the USB input must be measured (R-014).
Verify: test

## REQ-PWR-003

The pod shall contain no battery.

Rationale: Owner: no battery. The XIAO has battery pads (XIAO wiki); none are fitted.
Verify: inspection

## REQ-PWR-004

When connected by a USB-C to USB-C cable to a USB Type-C wall adapter, the pod shall receive 5 V power and start operating.

Rationale: Owner: standard USB wall adapter. A USB-C sink that cannot request power from a C-to-C source would not start; DS, Wiki and XIAO do not state how the XIAO USB-C input behaves with a C-to-C source (R-012). Whether a cable ships in the box is open (Q-13).
Verify: test

## REQ-PWR-005

While operating with no Grove accessory fitted, the pod shall consume no more than 1.4 W of input power.

Rationale: Power and thermal budget cap (`docs/budgets.md`). DS p.6: 0.5 W standby mode, 0.8 W activation mode, 1.4 W working with a Grove relay. The pod fits no relay, so 1.4 W is the conservative ceiling (A-007, A-008). MDS p.4 (600 mA radar module current) may conflict (R-014).
Verify: test

## REQ-ELEC-001

The v1 pod shall contain no conductor connected to mains voltage.

Rationale: Owner: the hardwired version is a future variant needing an electrician and certification, out of scope for v1. v1 draws power only from an external USB adapter.
Verify: inspection

## REQ-ENV-001

The pod shall operate at ambient temperatures from 0 °C to 40 °C.

Rationale: Owner round 2 (Q-09): 0 °C to 40 °C ambient, because ceilings run hotter than rooms in summer. Checked against the published ratings: MDS p.4 radar module -20 °C to 85 °C and XIAO -40 °C to 85 °C both contain 0 °C to 40 °C. The kit as a whole has no published range (A-004).
Verify: test

## REQ-ENV-002

While operating at an ambient temperature of 40 °C, the pod shall keep the air temperature at the sensor kit at or below the kit's rated maximum operating temperature.

Rationale: The whole input power (at most 1.4 W, REQ-PWR-005) is dissipated inside the enclosure. The kit has no published operating range; its radar module is rated to 85 °C (MDS p.4) and the XIAO to 85 °C (XIAO). The BH1750, WS2812 and carrier-board parts are unrated in the sources, so the kit limit of 85 °C is assumption A-004 (ask Seeed, Q-18). Budget in `docs/budgets.md`.
Verify: test

## REQ-SAFE-001

The shell, base plate, radome and T-bar clip materials shall each carry a UL94 flammability rating, listed at or below the part's as-built wall thickness, of at least the class a qualified human assigns under IEC 62368-1.

Rationale: R5a: UL 94 ratings for enclosures and housings are called up by end-product standards such as IEC/UL 62368-1; R5b: 62368-1 covers AV/ICT equipment. The required class is a qualified human's decision, not Forge's (Q-17).
Verify: inspection

## REQ-SAFE-002

While operating at an ambient temperature of 40 °C, the pod shall keep its accessible outer surface temperature at or below the limit a qualified human sets for its thermal energy-source class under IEC 62368-1.

Rationale: R5b: 62368-1 classifies thermal energy sources and specifies safeguards. The numeric limit is not in the Forge R5 files and must come from a qualified human with the standard (Q-17).
Verify: test

## REQ-SAFE-003

The pod's labelling, packaging, instructions and marketing text shall make no medical-device or emergency-alarm claim unless a qualified human has approved the regulatory route.

Rationale: Project compliance rule and Owner round 2 (Q-15): home-automation use, with no medical or safety claims, kept strict. The sensor's fall-event output could be read as a medical or alarm function (R-008). DS p.3 describes the kit as an Early Build with evolving software; MDS p.1 is a Beta Version and MDS p.3 quotes a fall recognition accuracy of 90 %.
Verify: inspection


## REQ-SAFE-004

The pod's user-facing text, including labels, packaging, instructions, marketing, app screens and Home Assistant entity names, shall contain no term on the deny-list in `compliance/claims-wording.md`.

Rationale: Owner round 2: "even 'fall detection' wording must not imply a safety device". The deny-list turns this into a check that can fail; the kit ships ESPHome firmware (DS p.2) whose entity names must be reviewed too.
Verify: inspection

## REQ-EMC-001

Where the pod is placed on the US market, the pod shall meet the FCC Part-15 Subpart B Class B limits for unintentional radiators.

Rationale: R5e: FCC 47 CFR Part 15 Subpart B covers digital devices sold in the US. DS p.8 states the kit was tested and found to comply with the Class B digital-device limits. Markets are open (Q-03).
Verify: test

## REQ-EMC-002

Where the pod is placed on the US market, the pod shall hold an FCC equipment authorisation covering every intentional radiator it contains.

Rationale: R5e: Subpart C intentional radiators generally need Certification through a TCB. The kit contains a 60 GHz radar (MDS p.4: 58 GHz to 62 GHz, 12 dBm transmit power) and the XIAO ESP32C6 radio (Wiki "Features": Wi-Fi and Bluetooth; XIAO: 2.4 GHz Wi-Fi 6, Bluetooth LE and IEEE 802.15.4). DS p.8 carries an FCC Part 15 statement but no FCC ID; whether existing grants cover the kit as built into the pod is a question for a qualified human.
Verify: inspection

## REQ-EMC-003

Where the pod is placed on the EU market, the pod shall pass emission testing to EN55032 and immunity testing to EN55035.

Rationale: R5e: CISPR 32/35 (EN 55032/55035) are the usual harmonised EMC routes for multimedia equipment; radio products also use the ETSI EN 301 489 series [U in R5e], which a qualified human must confirm. Markets are open (Q-03).
Verify: test

## REQ-EMC-004

Where the pod is placed on the Canadian market, the pod shall hold an ISED radio equipment approval to RSS-Gen for every licence-exempt radio it contains.

Rationale: R5e: RSS-Gen Issue 6 (2026-07-30, Amendment 1 2026-09-15) applies to licence-exempt radios sold in Canada; RSS-247 Issue 4 covers 2.4 GHz radios. Markets are open (Q-03).
Verify: inspection

## REQ-EMC-005

The pod shall contain no radio transmitter other than those in the MR60FDA2 kit unless a qualified human has assessed the combined equipment authorisation.

Rationale: DS p.8 (FCC statement, "15.21"): the transmitter must not be co-located or operated in conjunction with any other antenna or transmitter. Owner round 2 (Q-01): kit as-is; the XIAO is the only compute and radio (R-010).
Verify: inspection

## REQ-FW-001

When the pod is commissioned, the pod firmware shall set the MR60FDA2 installation-height parameter to the installer-measured mounting height.

Rationale: Wiki "Fall Module API", `setInstallationHeight`: the installation height is "crucial for accurate fall detection" (vendor wording); the initial setting is 2.2 m and the valid range is typically 1 m to 5 m. MDS p.9: set Mounting Height according to the actual installation height. The pod is mounted between 2.2 m and 3.0 m (Owner).
Verify: demo

## REQ-FW-002

Where a network radio is enabled on the pod, the pod firmware shall provide no operating mode that allows use without a user-set or unique per-device credential.

Rationale: R5e: EN 18031-1/-2/-3 give no presumption of conformity when the user may skip setting a password (EU RED cyber delegated act); this is a mapping-compliance tripwire. Owner round 2 (Q-02): local Wi-Fi to Home Assistant only.
Verify: test

## REQ-FW-003

Where a network radio is enabled on the pod, the pod firmware shall ship with no universal default password.

Rationale: R5e: ETSI EN 303 645 V3.1.3 consumer-IoT baseline (no universal default passwords), which maps to EN 18031 and CRA Annex I.
Verify: inspection


## REQ-FW-004

While the pod is in normal operation with no active fault, the pod firmware shall keep the status LED off.

Rationale: Owner round 2 (Q-14): the light pipe is OFF in normal use. The LED is the kit's WS2812 RGB LED (DS p.6).
Verify: test

## REQ-FW-005

While the pod is in setup mode, pairing mode or a fault state, the pod firmware shall light the status LED unless the user has disabled the LED in settings.

Rationale: Owner round 2 (Q-14): it lights only during setup/pairing and on faults, and it can be disabled in settings.
Verify: test

## REQ-FW-006

Where the user has disabled the status LED in settings, the pod firmware shall keep the status LED off in every operating state.

Rationale: Owner round 2 (Q-14): the LED can be disabled in settings.
Verify: test

## REQ-UX-001

The shell and radome shall have a matte warm-white finish that matches the owner-approved colour sample.

Rationale: Owner: matte warm white; it should visually disappear into the ceiling. Owner round 2 (Q-04): the colour is matched at the demo stage. The finish must also meet REQ-MECH-010 (no metallic pigment) and MDS §8 item 2 (smooth radome surface).
Verify: inspection

## REQ-UX-002

When the pod is installed, the pod shall show no screw head on its room-facing side.

Rationale: Owner: no visible screws on the room-facing side.
Verify: inspection

## REQ-UX-003

The v1 instructions shall state that the pod is for bedrooms and living rooms and is not for bathrooms.

Rationale: Owner: v1 rooms are bedroom and living room; the bathroom variant comes later with a gasket. Note MDS p.3 and p.11 describe the radar module as suited to bathrooms and single-person scenes (R-004, Q-16).
Verify: inspection


## REQ-UX-004

The pod shall show the status LED only through a light pipe that sits flush with the shell surface and has the shell's matte warm-white finish.

Rationale: Owner round 2 (Q-14): a tiny flush light pipe in the same matte warm white. The light pipe must also meet REQ-UX-002 (no visible screws), REQ-MFG-001 (no supports on show faces) and REQ-MECH-010 (no metal in the keep-out cone), and must not degrade sensing (REQ-SYS-002, R-018).
Verify: inspection

## REQ-UX-005

The room-facing side of the pod shall have no light-sensor window and no reset pinhole.

Rationale: Owner round 2 (Q-14): no light-sensor window; no pinhole. The kit's BH1750 light sensor (DS p.6) is therefore unused.
Verify: inspection

## REQ-UX-006

While the pod is detached from the base plate, the kit reset button shall be reachable without tools.

Rationale: Owner round 2 (Q-14): reset by twisting the pod off; the button is reachable once removed. DS p.6 lists the button ("Rest").
Verify: demo

## REQ-MNT-001

The installation instructions shall state the mounting height range of 2.2 m to 3.0 m and the coverage of one pod as a 3.0 m by 3.0 m floor area.

Rationale: Owner mount height and coverage, citing the MR60FDA2 spec; Wiki and MDS p.10: top-mounted hanging height 2.2 m to 3.0 m. Owner round 2 (Q-11): 3 x 3 m, with a 2 m radius fallback if the corner tests fail.
Verify: inspection

## REQ-MNT-002

The installation instructions shall list each Wiki installation keep-out: radars mounted close together, curtains or plants moved by wind, water flow or water film, large metal or mirror surfaces, detection through glass or thin wooden boards, vibrating mounting locations and low-quality power supplies.

Rationale: The Wiki "Installation method and sensing range" note lists these seven scenarios to keep out of the detecting range. Owner round 2 (Q-12): up to 2 pods per room; spacing in REQ-MNT-006.
Verify: inspection

## REQ-MNT-003

The installation instructions shall specify the screw and anchor to use for drywall ceilings and for concrete ceilings.

Rationale: Owner: drywall and concrete through one base plate using anchors or plugs. Owner round 2 (Q-05): Forge proposes the fixings; they are not in the box, so the instructions name them.
Verify: inspection

## REQ-MNT-004

The installation instructions shall show the USB cable routed in the adhesive raceway from the pod to a standard USB wall adapter.

Rationale: Owner: the cable runs down the wall in an adhesive raceway to a standard USB wall adapter.
Verify: inspection

## REQ-MNT-005

The installation instructions shall state that the fall-event output is specified for one person in the covered area.

Rationale: MDS p.3 ("single person scenes in small areas") and MDS p.11 precaution 3 ("single-person situations") limit the radar module; bedrooms and living rooms often hold more than one person. Owner round 2 (Q-16): one person.
Verify: inspection


## REQ-MNT-006

The installation instructions shall state a limit of two pods per room and the minimum pod spacing verified under REQ-SYS-003.

Rationale: Owner round 2 (Q-12): up to 2 pods per room. The Wiki warns against radars installed too close together without a distance, so the spacing comes from test TP-SYS-003.
Verify: inspection

## REQ-MFG-001

The base plate, shell, radome and T-bar clip shall each print on a 0.4 mm nozzle FDM printer with no support structure touching any show face.

Rationale: Owner: must print on a standard 0.4 mm-nozzle FDM printer without supports on show faces.
Verify: inspection

## REQ-MFG-002

The printed parts shall have no unsupported show-face overhang steeper than 45° from vertical in their print orientation.

Rationale: R5d FDM: maximum overhang without support 45° (Protolabs Network design-rules PDF and FDM guide) [V].
Verify: analysis

## REQ-MFG-003

The printed parts shall have no horizontal bridge longer than 5 mm on a show face.

Rationale: R5d FDM: bridges under 5 mm print with no sag or support marks (Protolabs Network FDM guide) [V]; the 10 mm bridge limit (PN PDF) is kept for hidden faces only.
Verify: analysis

## REQ-MFG-004

The printed parts shall have a minimum wall thickness of 1.2 mm.

Rationale: R5d FDM: minimum wall 2 to 3 times the nozzle diameter, 0.8 mm to 1.2 mm (PN "What is FDM") [V]; unsupported walls at least 1.2 mm (Xometry) [R]. The upper value covers both. For MJF demo parts R5d also gives a 2.5 mm to 12.7 mm wall range (PN MJF guide), which the G1 design must reconcile (R-015).
Verify: analysis

## REQ-MFG-005

The pod design shall give each mating interface between printed parts the process clearance of 0.5 mm for FDM, 0.2 mm for SLA and 0.6 mm for MJF.

Rationale: R5d: FDM connecting parts 0.5 mm (PN PDF) [V]; SLA connections 0.2 mm (PN SLA guide) [V]; MJF parts assembled after printing 0.6 mm (PN MJF guide) [V]. Owner processes: FDM PETG for G3 fit, SLA resin or MJF nylon for demo units.
Verify: analysis

## REQ-MFG-006

The base plate, shell, radome and T-bar clip shall each print in PETG by FDM for G3 fit checks.

Rationale: Owner: fit checks (G3) in FDM PETG.
Verify: demo

## REQ-MFG-007

The base plate, shell, radome and T-bar clip shall each be producible in SLA resin or MJF nylon by a print service for demo units.

Rationale: Owner: demo units in SLA resin or MJF nylon from a service.
Verify: demo

## REQ-COST-001

The prototype build cost shall not exceed US$50 per unit.

Rationale: Owner: prototype at or below US$50 per unit. The sensor kit alone is US$26.90 excl. VAT on DS p.1 (updated 2026-07-30) and US$28.99 on the Seeed product page on 2026-09-25 (Web).
Verify: analysis

## REQ-COST-002

The production BOM cost shall not exceed US$30 per unit.

Rationale: Owner: production BOM at or below US$30. Owner round 2 (Q-10): pod only (shell, kit and fixings) at 10+ unit pricing, and Forge reports the real number. The sensor kit is US$28.99 at 10+ units on the Seeed product page on 2026-09-25 (Web), so the BOM is at least US$28.99 plus printed parts and fixings not yet quoted: the target is likely unreachable (R-002, `docs/budgets.md`).
Verify: analysis

## REQ-COST-003

The BOM shall record a unit price and the date that price was checked for every line.

Rationale: Owner: build the real BOM with prices and the dates they were checked. Enforced by costing-bom (`bom/bom.csv`).
Verify: inspection
