# Requirements: Solvere Sense ceiling pod (v1, G0 draft)

EARS sentences, one per requirement, with an ID (`REQ-<AREA>-<NNN>`), a `Rationale:` and a `Verify:` method (inspection|analysis|demo|test). See `.claude/rules/systems.md` and CONTRACTS.md §6. Requirement text and IDs belong to systems-engineer and humans; other agents may change only `status`, `evidence` and `tests` in `trace.json`. Lint: `forge lint ears`; trace: `forge trace`.

Sources, in the order used:

- **Owner**: `docs/intake/G0-owner-answers.md` (2026-09-25, L0 claimed).
- **DS**: Seeed Studio "Industrial Product Datasheet, XIAO 60GHz mmWave Human Fall Detection Sensor-MR60FDA2", SKU 114993388, 8 pages, price-updated 2026-07-30. https://files.seeedstudio.com/Bazaar/product_pdf/114993388.pdf, read 2026-09-25 [V].
- **Wiki**: Seeed Studio wiki "Getting started with MR60FDA2", https://wiki.seeedstudio.com/getting_started_with_mr60fda2_mmwave_kit/ (source commit 880cf8b, 2026-05-15), read 2026-09-25 [V].
- **R5a/R5b/R5d/R5e**: Forge research files in `docs/research/` of the Forge repo.
- **A-xxx / Q-xx**: assumptions in `ASSUMPTIONS.md`; open questions for the owner in `reviews/G0.md`.

Scope: v1 is the bedroom and living-room pod, powered over USB-C. The hardwired (mains) variant is out of scope for v1 (Owner). The bathroom variant is out of scope for v1, but its gasket-groove interface is designed now (REQ-MECH-007, REQ-MECH-008).

## REQ-SYS-001

While mounted at a height from 2.2 m to 3.0 m above the floor, the pod shall report a staged fall at every corner and at the centre of a 3.0 m by 3.0 m floor area centred below the pod.

Rationale: Owner coverage of about 3 x 3 m per pod; DS p.6 gives fall detection in a 3x3x3 m range. The Wiki also gives a maximum sensing radius of 2 m, which is shorter than the 2.12 m half-diagonal of a 3 m square, so the corners are at risk (RISKS R-003, question Q-03). The DS p.3 notes the ranges were tested in empty rooms.
Verify: test

## REQ-SYS-002

The pod shall report human static presence at every test point at which the bare MR60FDA2 kit reports presence under the same test protocol.

Rationale: The radome and shell must not degrade the sensor. Seeed publishes no radome material or thickness guidance (searched 2026-09-25), so the acceptance is an A/B comparison against the bare kit (DS p.6: static presence up to 6 m). Retires A-015.
Verify: test

## REQ-MECH-001

The pod shall fix to a drywall ceiling through the base plate using screws and drywall anchors.

Rationale: Owner: drywall ceilings, one screw-on base plate using anchors or plugs. Fixing type and count are open (Q-10).
Verify: demo

## REQ-MECH-002

The pod shall fix to a concrete ceiling through the base plate using screws and wall plugs.

Rationale: Owner: concrete ceilings through the same base plate using plugs.
Verify: demo

## REQ-MECH-003

Where the T-bar clip adapter is fitted, the pod shall mount to a drop-ceiling T-bar grid without drilling or cutting the ceiling tile.

Rationale: Owner: drop ceilings use a T-bar clip as an optional adapter. Grid widths to fit are open (Q-11).
Verify: demo

## REQ-MECH-004

The base plate installed with its specified fixings shall withstand a static downward pull of 4 times the installed pod weight for 60 s without detaching from the ceiling.

Rationale: A pod falling from a bedroom ceiling onto a person is the main mechanical hazard (RISKS R-005). No sourced retention load exists in the Forge R5 files, so the load factor is assumption A-003, to be replaced by a qualified human's choice.
Verify: test

## REQ-MECH-005

The shell shall remain attached to the base plate under a static downward pull of 4 times the combined shell and sensor-kit weight for 60 s.

Rationale: Same falling-object hazard as REQ-MECH-004 for the removable shell. Load factor is assumption A-003.
Verify: test

## REQ-MECH-006

The shell shall attach to the base plate without any screw passing through the shell.

Rationale: Owner: no visible screws on the room-facing side. The fastening concept (twist-lock, snap-fit or other) is chosen at G1; tool-free removal is open (Q-08).
Verify: inspection

## REQ-MECH-007

The shell-to-base joint shall include a continuous gasket groove around its full perimeter in every variant, including v1 builds that carry no gasket.

Rationale: Owner: the bathroom variant uses the same shell plus a gasket; design the gasket-groove interface now. Groove size depends on the gasket choice and ingress target (Q-12).
Verify: inspection

## REQ-MECH-008

Where the bathroom gasket is fitted, the pod shall hold the gasket compressed in the groove around the full joint perimeter while the shell is attached.

Rationale: Owner bathroom-variant intent. The compression range comes from the chosen gasket's datasheet once Q-12 is answered.
Verify: inspection

## REQ-MECH-009

The pod shall hold the MR60FDA2 antenna face parallel to the ceiling plane within 5° and facing the floor.

Rationale: Wiki "Installation method and sensing range": top-mounted, with the sensor side aligned to the detection direction. The 5° limit comes from the sibling MR60FDA1 wiki (horizontal deviation of 5° or less) [R] and is assumption A-004.
Verify: inspection

## REQ-MECH-010

The pod shall have no metal part, metallic pigment or conductive coating inside the MR60FDA2 field of view of 120° horizontal by 100° vertical.

Rationale: Wiki: keep large areas of metal and mirror reflections out of the detecting range. FoV from DS p.6. The Wiki introduction gives a different angle (100° x 40°); the larger DS value is used as the keep-out (RISKS R-013).
Verify: inspection

## REQ-MECH-011

The pod shall provide a cable strain relief that clamps the USB cable jacket so that a pull on the cable is not transmitted to the USB-C connector.

Rationale: Owner: the cable runs down the wall in a raceway to a wall adapter, so the cable can be pulled during installation and cleaning. The pull load is set with A-003's owner at G1.
Verify: test

## REQ-MECH-012

The pod shall route the USB cable out of the enclosure at the ceiling plane into the end of the adhesive cable raceway.

Rationale: Owner: cable in an adhesive raceway to a standard USB wall adapter; hidden, minimal look. Raceway product, size and route are open (Q-09, A-018).
Verify: demo

## REQ-PWR-001

The pod shall operate from a USB-C supply of 5 V rated at 1 A.

Rationale: Owner: USB-C, 5 V / 1 A. DS p.6: power supply 5V/1A.
Verify: test

## REQ-PWR-002

While operating in any mode, the pod shall draw no more than 1 A from its USB-C input.

Rationale: Keeps the pod inside the Owner's 5 V / 1 A supply rating. Peak current is not published in DS; it is measured.
Verify: test

## REQ-PWR-003

The pod shall contain no battery.

Rationale: Owner: no battery.
Verify: inspection

## REQ-PWR-004

When connected by a USB-C to USB-C cable to a USB Type-C wall adapter, the pod shall receive 5 V power and start operating.

Rationale: Owner: standard USB wall adapter. A USB-C sink that cannot request power from a C-to-C source would not start; DS and Wiki do not state how the kit's USB-C input behaves (RISKS R-012).
Verify: test

## REQ-PWR-005

While operating with no Grove accessory fitted, the pod shall consume no more than 1.4 W of input power.

Rationale: Power and thermal budget cap (`docs/budgets.md`). DS p.6: 0.5 W standby, 0.8 W active, 1.4 W with a Grove relay. The pod fits no relay, so 1.4 W is the conservative ceiling.
Verify: test

## REQ-ELEC-001

The v1 pod shall contain no conductor connected to mains voltage.

Rationale: Owner: the hardwired version is a future variant needing an electrician and approval, out of scope for v1. v1 draws power only from an external USB adapter.
Verify: inspection

## REQ-ENV-001

The pod shall operate at ambient temperatures from 0 °C to 35 °C.

Rationale: The v1 rooms are bedrooms and living rooms (Owner). The owner gave no temperature range, so this range is assumption A-005 (Q-13).
Verify: test

## REQ-ENV-002

While operating at an ambient temperature of 35 °C, the pod shall keep the air temperature at the sensor kit at or below the kit's rated maximum operating temperature.

Rationale: The whole input power (at most 1.4 W, REQ-PWR-005) is dissipated inside the enclosure. The MR60FDA2 operating temperature is not published; 60 °C from the sibling MR60FDA1 is assumption A-006. Draft estimate in `docs/budgets.md`.
Verify: test

## REQ-SAFE-001

The shell, base plate, radome and T-bar clip materials shall each carry a UL94 flammability rating, listed at or below the part's as-built wall thickness, of at least the class a qualified human assigns under IEC 62368-1.

Rationale: R5a: UL 94 ratings for enclosures and housings are called up by end-product standards such as IEC/UL 62368-1; R5b: 62368-1 covers AV/ICT products including sensors with a mains adapter. The required class is a human decision, not Forge's.
Verify: inspection

## REQ-SAFE-002

While operating at an ambient temperature of 35 °C, the pod shall keep its accessible outer surface temperature at or below the limit a qualified human sets for its thermal energy-source class under IEC 62368-1.

Rationale: R5b: 62368-1 classifies thermal energy sources and specifies safeguards. The numeric limit is not in the Forge R5 files and must come from a qualified human with the standard.
Verify: test

## REQ-SAFE-003

The pod's labelling, packaging, instructions and marketing text shall make no medical-device or emergency-alarm claim unless a qualified human has approved the regulatory route.

Rationale: Project compliance rule: no accidental medical, safety or regulatory claims. Fall detection could be read as a medical or alarm function (Q-04, RISKS R-008). DS p.3 describes the kit as an Early Build with evolving software.
Verify: inspection

## REQ-EMC-001

Where the pod is placed on the US market, the pod shall meet the FCC Part-15 Subpart B Class B limits for unintentional radiators.

Rationale: R5e: FCC 47 CFR Part 15 Subpart B covers digital devices sold in the US. DS p.8 states the kit was tested to the Class B digital-device limits. Markets are open (Q-02).
Verify: test

## REQ-EMC-002

Where the pod is placed on the US market, the pod shall hold an FCC equipment authorisation covering every intentional radiator it contains.

Rationale: R5e: Subpart C intentional radiators generally need Certification through a TCB. The pod contains a 60 GHz radar and, if the kit is used as bought, the XIAO ESP32C6 Wi-Fi and Bluetooth radio (DS p.2, p.6).
Verify: inspection

## REQ-EMC-003

Where the pod is placed on the EU market, the pod shall pass emission testing to EN55032 and immunity testing to EN55035.

Rationale: R5e: CISPR 32/35 (EN 55032/55035) are the usual harmonised EMC routes for multimedia equipment; radio products also use the ETSI EN 301 489 series [U in R5e], which a qualified human must confirm.
Verify: test

## REQ-EMC-004

Where the pod is placed on the Canadian market, the pod shall hold an ISED radio equipment approval to RSS-Gen for every licence-exempt radio it contains.

Rationale: R5e: RSS-Gen Issue 6 (2026-07-30, Amendment 1 2026-09-15) applies to licence-exempt radios sold in Canada. Markets are open (Q-02).
Verify: inspection

## REQ-EMC-005

The pod shall contain no radio transmitter other than those in the MR60FDA2 kit unless a qualified human has assessed the combined equipment authorisation.

Rationale: DS p.8 (FCC statement): the transmitter must not be co-located or operated with any other antenna or transmitter. Adding other compute or radio (for example the Voice PE mentioned elsewhere) changes the authorisation (Q-01, RISKS R-010).
Verify: inspection

## REQ-FW-001

When the pod is commissioned, the pod firmware shall set the MR60FDA2 installation-height parameter to the installer-measured mounting height.

Rationale: Wiki `setInstallationHeight`: the installation height is crucial for fall detection; the default is 2.2 m and the valid range is typically 1 m to 5 m. The pod is mounted between 2.2 m and 3.0 m (Owner).
Verify: demo

## REQ-FW-002

Where a network radio is enabled on the pod, the pod firmware shall provide no operating mode that allows use without a user-set or unique per-device credential.

Rationale: R5e: EN 18031-1/-2/-3 give no presumption of conformity when the user may skip setting a password (EU RED cyber delegated act); this is a mapping-compliance tripwire.
Verify: test

## REQ-FW-003

Where a network radio is enabled on the pod, the pod firmware shall ship with no universal default password.

Rationale: R5e: ETSI EN 303 645 V3.1.3 consumer-IoT baseline (no universal default passwords), which maps to EN 18031 and CRA Annex I.
Verify: inspection

## REQ-UX-001

The shell and radome shall have a matte warm-white finish that matches the owner-approved colour sample.

Rationale: Owner: matte warm white, it should disappear into the ceiling. The colour reference is open (Q-06). The finish must also meet REQ-MECH-010 (no metallic pigment).
Verify: inspection

## REQ-UX-002

When the pod is installed, the pod shall show no screw head on its room-facing side.

Rationale: Owner: no visible screws on the room-facing side.
Verify: inspection

## REQ-UX-003

The v1 instructions shall state that the pod is for bedrooms and living rooms and is not for bathrooms.

Rationale: Owner: v1 rooms are bedroom and living room; the bathroom variant comes later with a gasket.
Verify: inspection

## REQ-MNT-001

The installation instructions shall state the mounting height range of 2.2 m to 3.0 m and the coverage of one pod as a 3.0 m by 3.0 m floor area.

Rationale: Owner mount height and coverage, citing the MR60FDA2 spec; Wiki: top-mounted hanging height 2.2 m to 3.0 m. Coverage wording may change with Q-03.
Verify: inspection

## REQ-MNT-002

The installation instructions shall list the MR60FDA2 installation keep-outs for metal or mirror surfaces, vibrating mounting locations, low-quality power supplies and radars mounted close together.

Rationale: Wiki lists these scenarios to keep out of the detecting range. Owner notes larger rooms may need 2 pods, which conflicts with the close-radar keep-out (Q-16, RISKS R-007).
Verify: inspection

## REQ-MNT-003

The installation instructions shall specify the screw and anchor to use for drywall ceilings and for concrete ceilings.

Rationale: Owner: drywall and concrete through one base plate using anchors or plugs. Fixing sizes are open (Q-10).
Verify: inspection

## REQ-MNT-004

The installation instructions shall show the USB cable routed in the adhesive raceway from the pod to a standard USB wall adapter.

Rationale: Owner: the cable runs down the wall in an adhesive raceway to a standard USB wall adapter.
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

Rationale: R5d FDM: minimum wall 2 to 3 times the nozzle diameter, 0.8 mm to 1.2 mm [V]; unsupported walls at least 1.2 mm (Xometry) [R]. The upper value covers both.
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

Rationale: Owner: prototype at or below US$50 per unit. The sensor kit alone is US$26.90 at 1 unit (DS p.1, price updated 2026-07-30).
Verify: analysis

## REQ-COST-002

The production BOM cost shall not exceed US$30 per unit.

Rationale: Owner: production BOM at or below US$30. The sensor kit is US$26.50 at 10+ units (Seeed product page, read 2026-09-25), leaving about US$3.50 for everything else (RISKS R-002). Volume tier and scope are open (Q-15).
Verify: analysis

## REQ-COST-003

The BOM shall record a unit price and the date that price was checked for every line.

Rationale: Owner: build the real BOM with prices and the dates they were checked. Enforced by costing-bom (`bom/bom.csv`).
Verify: inspection
