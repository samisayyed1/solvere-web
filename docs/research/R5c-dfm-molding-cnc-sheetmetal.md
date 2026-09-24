# R5c — DFM rule tables: injection molding, CNC, sheet metal
- Date accessed: 2026-09-25 · Author: R5 sub-research agent (Phase 1) · Status: salvaged — parent R5 agent was stopped to save usage; this is the sub-agent's complete returned report, unedited.
- Tags: [V] verified on issuing body / manufacturer page · [R] reported (secondary) · [U] unverified

I pulled about 80 numeric rules from 48 manufacturer pages. Every [V] number was read on the fetched page itself, but WebFetch reads pages through a summarizing model. I re-checked the values that looked odd with targeted re-fetches, and they are recorded as the page shows them. **[R]** means I only saw the value in a search snippet. **[U]** means I couldn't confirm it. Dates are given only where the page shows one. `t` means sheet thickness, `T` means nominal wall and `R` means bend radius.

## 1. Injection molding

| Rule | Value | Source | URL | Tag |
|---|---|---|---|---|
| Wall, ABS / POM / PA / PC / PE | ABS 0.045–0.140 in; acetal 0.030–0.120 in; nylon 0.030–0.115 in; PC 0.040–0.150 in; PE 0.030–0.200 in (identical on both sites) | Protolabs + Fictiv | https://www.protolabs.com/services/injection-molding/plastic-injection-molding/design-guidelines/ ; https://www.fictiv.com/articles/injection-molding-design-guide (dated 08.15.2025) | V |
| Wall, PP | 0.035–0.150 in (0.889–3.81 mm) on the design-guidelines page; **0.025–0.150 in** on two Protolabs tip pages | Protolabs | design-guidelines URL above; https://www.protolabs.com/resources/design-tips/improving-part-design-with-uniform-wall-thickness/ ; https://www.protolabs.com/resources/design-tips/injection-molding-basics/ | V |
| Wall, PP | 0.040–0.150 in (1.02–3.81 mm) in the 2025 guide; 0.025–0.150 in (0.64–3.81 mm) in the 2023 article | Fictiv | IM guide URL above; https://www.fictiv.com/articles/wall-thickness-recommendations-for-injection-molding (Jan 13 2023) | V |
| Wall, PS | 0.035–0.150 in (Protolabs, Fictiv 2023); 0.025–0.125 in / 0.64–3.18 mm (Fictiv 2025 guide) | Protolabs / Fictiv | same URLs as above | V |
| Wall, acrylic/PMMA | 0.025–0.500 in (0.635–12.7 mm) | Protolabs | design-guidelines URL | V |
| Wall, acrylic/PMMA | 0.025–0.150 in. The 2025 guide's mm column repeats "0.025–0.150" (a typo); the 2023 article gives 0.64–3.81 mm | Fictiv | IM guide + 2023 article URLs | V |
| Wall, PBT and others | PBT 0.080–0.250 in; PEEK 0.020–0.200 in; PEI 0.080–0.120 in; PPSU 0.030–0.250 in; TPE/TPU 0.025–0.125 in | Fictiv | IM guide URL | V |
| Wall, others | Polyester 0.025–0.125 in; LCP 0.030–0.120 in; PPS 0.020–0.180 in; PU 0.080–0.750 in; long-fiber reinforced 0.075–1.000 in | Protolabs | design-guidelines URL | V |
| General nominal wall | Small parts 0.040 in (1 mm); hand-sized parts 0.080 in (2 mm); most stable 0.060–0.100 in; sink risk at ≥0.150 in (3.8 mm) | Protolabs | https://www.protolabs.com/resources/design-tips/design-stronger-molded-parts/ | V |
| General nominal wall | Usually 1–5 mm; about 1 mm is the thinnest; limit the maximum to 5 mm | Fictiv | https://www.fictiv.com/articles/wall-thickness-in-injection-molding (01.26.2023) | V |
| Draft, general | 0.5° on all vertical faces; 1–2° works in most cases; 1° per inch of cavity depth; 0.25–0.5° only after consulting them | Protolabs | https://www.protolabs.com/resources/design-tips/improving-part-moldability-with-draft/ | V |
| Draft, general / shut-off | 2° for most situations; at least 3° at shut-offs | Protolabs | design-guidelines URL | V |
| Draft, general | At least 2°; add 1° per 25 mm of feature height (example: 3° at 75 mm) | Hubs | https://www.hubs.com/guides/injection-molding/ | V |
| Draft by material | Min/recommended: nylon 0°/1°, PE 0.5°/1.5°, PVC 0.5°/1.5°, PP 1°/2°, PC 1.5°/2° | Hubs | https://www.hubs.com/knowledge-base/draft-angle/ | V |
| Draft by depth | Under 25 mm: 0.5–1°; 25–75 mm: 1–2°; 75–150 mm: 2–3°; over 150 mm: 3–5° | Xometry | https://www.xometry.com/resources/machining/draft-angle/ (published Sep 10 2026) | V |
| Texture draft | 1° per 0.0005–0.0006 in (0.0127–0.01524 mm) of texture depth; about 6–7° for wood grain or leather | Protolabs | https://www.protolabs.com/resources/design-tips/mold-texture-standards-and-finishes/ (cites a 2022 guide) | V |
| Texture draft | PM-T1 light texture at least 3°; PM-T2 heavy texture 5° or more | Protolabs | draft tip + design-guidelines URLs | V |
| Texture draft | 1.5° per 0.001 in (Mold-Tech). MT-11010 (0.001 in) needs 1.5°, MT-11020 (0.0015 in) 2.25°, MT-11030 (0.002 in) 3° | Xometry | https://www.xometry.com/resources/injection-molding/choosing-the-right-finish-for-your-injection-molded/ (updated May 14 2025) | V |
| Texture draft | MT-11020 needs about 2.5° (conflicts with 2.25° above) | Xometry | snippet only, source page not identified | R |
| Texture draft | Add 1–1.5° per 0.025 mm of texture depth | Xometry | draft-angle URL | V |
| Texture draft | 1.5° per 0.001 in (0.025 mm); light 3°, heavy 5° or more, leather/snakeskin 10° or more; stepped shut-offs 5–7° | Fictiv | https://www.fictiv.com/articles/draft-and-texture-in-plastic-injection-molded-parts (Jan 13 2022) | V |
| Texture draft | Add 1–2° for textured surfaces (guide); PM-T1 1–5°, PM-T2 5–12°+ (knowledge base) | Hubs | guide URL + draft-angle KB URL | V |
| Rib thickness | At most 60% of nominal wall (design-stronger tip); 40–60% of adjacent wall (basics tip) | Protolabs | design-stronger URL; injection-molding-basics URL | V |
| Rib thickness | At most 60% of nominal wall; 40% for glossy materials | Xometry | https://www.xometry.com/resources/injection-molding/plastic-ribs-for-injection-molding-design/ (updated Sep 11 2025) | V |
| Rib thickness | 0.5 × wall (Hubs); 0.5–0.6T (Fictiv) | Hubs / Fictiv | Hubs guide URL; Fictiv IM guide URL | V |
| Rib height | Less than 3 × rib thickness | Hubs, Xometry | Hubs guide URL; Xometry ribs URL | V |
| Rib height | At most 2.5T | Fictiv | IM guide URL | V |
| Rib spacing / draft | Xometry: spacing at least 2.5–3 × nominal wall, draft 0.5–1.5°. Hubs: at least 4 × rib thickness from walls, draft at least 0.25–0.5°. Fictiv: draft at least 0.5° per side | Xometry / Hubs / Fictiv | ribs, guide and IM guide URLs | V |
| Rib base fillet | Hubs: more than ¼ × rib thickness. Fictiv: 0.25–0.5T (a "max 0.010 in" cap is unconfirmed). Xometry: 0.5–1 × wall | Hubs / Fictiv / Xometry | same URLs | V (cap U) |
| Boss wall | 40–60% of the wall it rises from; aluminum molds may need thicker walls | Protolabs | https://www.protolabs.com/resources/design-tips/plastic-boss-design-on-molded-parts/ | V |
| Boss wall | At most 60–70% of adjacent wall | Protolabs | https://www.protolabs.com/resources/blog/design-better-screw-bosses-on-molded-parts/ (Apr 26 2018) | V |
| Boss wall | 40–60% of outer wall; blind-hole ratio also 40–60% (Xometry). At most 60% of wall (Fictiv) | Xometry / Fictiv | https://www.xometry.com/resources/injection-molding/managing-sink-in-injection-molding-designs/ (updated Aug 21 2026); Fictiv IM guide URL | V |
| Boss OD/ID | OD = 2 × nominal screw or insert diameter; ID = screw core diameter | Hubs | guide URL | V |
| Boss draft | 0.5–3°, depending on boss height | Protolabs | boss tip URL; https://www.protolabs.com/en-gb/resources/design-tips/choosing-the-right-boss-for-your-part-design/ | V |
| Core-out / sink | Groove 30% of wall deep, blending back at 30°. Wall transitions taper over 3 × the thickness change (Hubs, Xometry). Secondary walls at least 40–60% of adjacent walls (Protolabs, Fictiv) | Xometry / Hubs / Protolabs / Fictiv | sink URL; Hubs guide URL; uniform-wall URL | V |
| Radii | Inside at least 0.5 × wall; outside 1.5 × wall | Protolabs | https://www.protolabs.com/resources/design-tips/cutting-corners-on-injection-molded-parts/ | V |
| Radii | Inside at least 0.5 × wall; outside = inside radius + wall | Hubs, Fictiv | Hubs guide URL; Fictiv IM guide URL | V |
| Undercuts / side actions | Largest side core: width under 8.419 in (213.84 mm), height under 2.377 in, pull under 2.875 in. Hand-loaded inserts must be larger than a 0.5 in cube | Protolabs | design-guidelines URL; basics URL | V |
| Undercuts, stripped | Up to 5% of diameter in flexible plastics; lead angle 30–45° | Hubs | guide URL | V |
| Tolerance | Machining ±0.003 in (0.08 mm), plus resin tolerance of at least ±0.002 in/in | Protolabs | design-guidelines URL | V |
| Tolerance | Mold ±0.005 in plus ±0.002 in/in for shrink; part-to-part repeatability under ±0.004 in | Xometry | https://www.xometry.com/manufacturing-standards/ (Jan 28 2025) | V |
| Tolerance | Standard ±0.250 mm (0.010 in); tight ±0.125 mm, down to ±0.025 mm. Manufacturing standards: mold ±0.125 mm, repeatability under 0.100 mm | Hubs | guide URL; https://www.hubs.com/manufacturing-standards/ (v2.1, Jan 12 2024) | V |

## 2. CNC machining

| Rule | Value | Source | URL | Tag |
|---|---|---|---|---|
| Default tolerance | ±0.005 in (0.13 mm); ±0.002 in (0.05 mm) through network partners; ISO 2768-1 medium or fine at partners | Protolabs | https://www.protolabs.com/services/cnc-machining/cnc-milling/design-guidelines/ ; https://www.protolabs.com/resources/design-for-machining-toolkit/ | V |
| Default tolerance | ±0.005 in for metals, ±0.010 in for plastics and composites (ISO 2768) | Xometry | manufacturing-standards URL | V |
| Default tolerance | Guide: ±0.125 mm (0.005 in) standard, ±0.025 mm feasible. KB: ±0.1 mm typical, ±0.02 mm feasible. Standards: ISO 2768-f for metals and 2768-m for plastics (e.g. >6–30 mm is ±0.1 / ±0.2 mm) | Hubs | https://www.hubs.com/guides/cnc-machining/ ; https://www.hubs.com/knowledge-base/how-design-parts-cnc-machining/ ; manufacturing-standards URL | V |
| Tolerance | Tolerances tighter than 0.05 mm (0.002 in) may be loosened; below 0.1 mm is hard in plastics | Fictiv | https://www.fictiv.com/articles/fictiv-cnc-machining-design-guide (06.29.2021) | V |
| Internal corner radius | At least ⅓ × cavity depth; adding about 1 mm over that helps. Floor edges sharp, 0.5 mm or 1 mm (KB) vs sharp, 0.1 mm or 1 mm (guide) | Hubs | guide + KB URLs | V |
| Internal corner radius | About 30% above tool radius, radius:depth 1:4 (video); 130% of milling radius (10 tips); add 0.02–0.05 in, e.g. 0.25 in → 0.27–0.30 in (corner-radii article) | Xometry | https://www.xometry.com/resources/machining/video-5-cost-saving-cnc-design-tips/ (updated Sep 10 2024); https://www.xometry.com/resources/machining/10-tips-improve-cad-cnc-design/ (updated Feb 27 2026); https://www.xometry.com/resources/machining/cnc-machining-optimizing-internal-corner-radii/ (updated Aug 13 2024) | V |
| Internal corner radius | At least half the tool diameter and more than the tool radius; avoid radii under 0.8 mm | Fictiv | CNC guide URL | V |
| Internal corner radius | Example: 0.130 in instead of 0.125 in | Fictiv | snippet only | R |
| Smallest tool / radius | Smallest cutter 0.040 in (1 mm), limited to pockets 0.375 in (9.52 mm) deep. In stainless, a 0.031 in (0.8 mm) end mill leaves a 0.016 in (0.4 mm) radius, and steel end mills reach at most 5 × diameter | Protolabs | https://www.protolabs.com/resources/design-tips/mastering-complex-features-on-machined-parts/ ; https://www.protolabs.com/resources/design-tips/how-to-reduce-cnc-machining-costs/ | V |
| Corner relief | A 0.25 in (6.35 mm) relief gives functionally sharp corners to about 1.25 in (32 mm) deep in steel and about 2.5 in (64 mm) in aluminum or plastic | Protolabs | how-to-reduce URL | V |
| Internal corner radius | "A little more than half the tool diameter" | Protolabs | snippet only | R |
| Pocket depth | 4 × width recommended; 10 × tool diameter feasible (guide); up to 30:1 with special tooling (KB); 2–3 × tool diameter is optimal (cost tips) | Hubs | guide URL; KB URL; https://www.hubs.com/knowledge-base/reducing-cnc-machining-costs-design-tips/ | V |
| Pocket depth | At most 3–5 × width (10 tips); width:depth 1:6 or shallower (video) | Xometry | 10-tips and video URLs | V |
| Pocket depth | At most 15 × tool diameter in plastics, 10 × in aluminum, 5 × in steel | Fictiv | CNC guide URL | V |
| Max depth | 2 in (50.8 mm) from each side; slots under 6 × width | Protolabs | milling guidelines + complex-features URLs | V |
| Min wall | Metal 0.8 mm recommended, 0.5 mm feasible; plastic 1.5 mm recommended, 1.0 mm feasible | Hubs | guide + KB URLs | V |
| Min wall | Metal 0.794 mm (about 0.030 in); plastic 1.5 mm (about 0.060 in) | Xometry | 10-tips + video URLs | V |
| Min wall | Over 0.25 mm in metal, over 0.50 mm in plastic; turned parts 0.02 in (0.508 mm). A snippet also said 0.5 mm / 1.0 mm | Fictiv | CNC guide URL | V (0.5/1.0: R) |
| Min wall / feature | Walls at least 0.020 in (0.51 mm); nominal thickness 0.040 in (1.02 mm); smallest feature 0.035 in (0.90 mm) in metal, 0.020 in in plastic; smallest part 0.25 × 0.25 in | Protolabs | milling guidelines + how-to-reduce URLs | V |
| Hole depth | KB: 4 × diameter recommended, 10 × typical, 40 × feasible. Guide: 4 × recommended, 6 × maximum | Hubs | KB + guide URLs | V |
| Hole depth | 4 × diameter, up to 10 × at extra cost; drilled holes up to 1:10 | Xometry | 10-tips + video URLs | V |
| Hole depth | Drill to at most 12 × bit diameter; make blind holes 25% deeper than needed | Fictiv | CNC guide URL | V |
| Hole depth | More than 6 diameters deep becomes a challenge | Protolabs | toolkit URL; https://www.protolabs.com/resources/design-tips/6-ways-to-optimize-part-design-for-cnc-machining/ | V |
| Thread depth | Length 3 × D recommended (minimum 1.5 ×); M6 or larger recommended, M2 feasible; add 1.5 × D unthreaded at the bottom of tapped blind holes | Hubs | KB URL | V |
| Thread depth | 2 × hole diameter; at least 0.5 × D unthreaded at the bottom | Xometry | video + 10-tips URLs | V |
| Thread depth | 1–1.5 × D engagement; avoid taps deeper than 3 × diameter | Fictiv | CNC guide URL | V |
| Thread depth | At most 3 × diameter; sizes M2–M12 and #2 to 0.5 in | Protolabs | toolkit + milling URLs | V |
| Min hole / tool | Smallest hole 2.5 mm (0.1 in) recommended; feasible given as "0.05 mm (0.005 in)" (units don't match); tall features height/width under 4 | Hubs | KB + guide URLs | V |
| Text / engraving | Stroke width at least 0.018 in (0.457 mm) in plastic or soft metal, 0.033 in (0.838 mm) in hard metal; depth 0.0118 in (0.3 mm); 20 pt or larger, recessed | Protolabs | milling guidelines + 6-ways URLs | V |
| Text / engraving | 20 pt or larger. Hubs prints "5 mm engraved" (looks wrong); Xometry says 20 pt sans-serif | Hubs / Xometry | KB URL; 10-tips URL | V |

## 3. Sheet metal

| Rule | Value | Source | URL | Tag |
|---|---|---|---|---|
| Min bend radius | At least equal to thickness | Hubs, Xometry | https://www.hubs.com/guides/sheet-metal-fabrication/ ; https://www.xometry.com/resources/machining/sheet-metal-mini-guide/ (updated Sep 10 2024) | V |
| Bend radius | Standard radii 0.030, 0.060, 0.090 and 0.120 in; tooling covers 0.010–0.250 in; 0.030 in (0.762 mm) suits about 95% of parts; 6061-T6 may need a larger radius | Protolabs | https://www.protolabs.com/services/sheet-metal-fabrication/design-guidelines/ ; https://www.protolabs.com/resources/design-tips/the-basics-of-bend-radii-in-sheet-metal/ | V |
| Min flange | At least 4t | Protolabs | design-guidelines URL | V |
| Min flange | At least 2t + R | Hubs | guide URL | V |
| Min flange | 2.5t + R (this is Xometry's stamping guide) | Xometry | https://www.xometry.com/resources/industry-design-tips/stamping-design-tips/ (updated Mar 12 2026) | V |
| Hole-to-bend | At least 4t from edges and inside corners (bend-radii tip); 2–3t from the bend region (bend-relief blog) | Protolabs | bend-radii URL; https://www.protolabs.com/resources/blog/bend-relief/ (Aug 15 2022) | V |
| Hole-to-bend | At least 2t from the start of the bend radius | Hubs | guide URL | V |
| Hole-to-bend | Holes under 0.100 in: 2t + R. Holes 0.100 in or larger: 2.5t + R (stamping) | Xometry | stamping URL | V |
| Hole-to-edge | 0.062 in (1.574 mm) if t ≤ 0.036 in; 0.125 in (3.175 mm) if thicker | Protolabs | design-guidelines URL | V |
| Hole-to-edge / hole-to-hole | At least 1t from the edge; at least 2t between holes | Hubs | guide URL | V |
| Hole-to-edge / hole-to-hole | Laser/waterjet: edge 2t or 0.125 in, whichever is smaller; hole-to-hole 6t or 0.125 in, whichever is smaller. Stamping: edge at least 2t | Xometry | https://www.xometry.com/resources/sheet/sheet-cutting-tips/ (Mar 12 2025); stamping URL | V |
| Min hole diameter | Equal to t (Protolabs); at least t (Hubs); stamping: 1.2t in ductile Al, 2t in stainless, slots 1.5t (Xometry) | Protolabs / Hubs / Xometry | design-guidelines, guide and stamping URLs | V |
| Bend relief | At least 0.030 in (0.762 mm) wide, extending at least 0.015 in (0.381 mm) past the bend radius; for 90° bends, relief = t + R | Protolabs | bend-relief blog URL | V |
| Bend relief | Width at least t | Hubs | guide URL | V |
| Bend relief | Stamping: at least 2t wide × (R + t) long. Laser relief cuts: 0.010 in or 1t, whichever is greater | Xometry | stamping + cutting URLs | V |
| K-factor | 0.33 for air bending, 0.42 for bottoming, rising toward 0.5 at large radii | Protolabs | bend-radii URL | V |
| K-factor | 0.3–0.5, average 0.4468 (the page wrongly adds "mm") | Hubs | guide URL | V |
| Tolerances | For stock under / over 0.13 in: edge-to-edge and hole-to-hole 0.005 / 0.015 in; bend-to-edge 0.010 / 0.020 in; bend-to-hole and bend-to-bend 0.015 / 0.025 in; across 3+ bends 0.030 / 0.040 in; bend angle ±1° | Protolabs | design-guidelines URL | V |
| Tolerances | Edge-to-bend ±0.015 in; across bend ±0.030 in; bend-to-hole ±0.015 in; bend angle ±1° | Xometry | manufacturing-standards URL (Jan 28 2025) | V |
| Tolerances | Cutouts ±0.020 in; bend ±2° | Xometry | mini-guide URL | V |
| Tolerances | Cut features ±0.2 mm; bend angle ±1.0°; bend-to-edge ±0.254 mm | Hubs | manufacturing-standards URL (v2.1) | V |
| Hems | Inside diameter at least t, return 6t (Protolabs). Open hem ID 1t, return 4t; teardrop opening ¼t (Xometry) | Protolabs / Xometry | design-guidelines URL; https://www.xometry.com/resources/sheet/understanding-sheet-metal-tolerances/ (updated Aug 21 2026) | V |
| Curls / countersinks | Curl outside radius at least 2t; holes at least R + t from a curl; bends at least 6t + R from a curl. Countersink depth at most 0.6t, spacing 8t, 4t from edge, 3t from bend | Xometry | tolerances URL | V |
| Tabs / notches / fillets | Protolabs: notch at least t or 0.04 in, tab at least 2t or 0.126 in, both no longer than 5 × width. Xometry laser: tab at least 0.063 in or t, slot at least 0.040 in or t, corner fillet 0.5t or 0.125 in (smaller) | Protolabs / Xometry | design-guidelines + cutting URLs | V |

## Where the sources disagree
- **PP and PS wall thickness are inconsistent even within one company.** Protolabs gives PP a 0.035 in minimum on one page and 0.025 in on two others. Fictiv gives PP 0.025 in (2023) and 0.040 in (2025), and PS 0.035–0.150 in vs 0.025–0.125 in.
- **Acrylic maximum wall:** Protolabs says 0.500 in, Fictiv 0.150 in.
- **General draft:** Protolabs uses 0.5° minimum with 1–2° typical. Hubs says 2° minimum. Xometry sets draft by depth band.
- **Texture draft:** Protolabs' 1° per 0.0005–0.0006 in works out to about 1.7–2° per 0.001 in (my conversion). Xometry and Fictiv say 1.5° per 0.001 in. Xometry's own draft article says 1–1.5° per 0.025 mm, and its MT-11020 value is 2.25° on the page vs 2.5° in a snippet.
- **Ribs:** height is 3 × rib thickness (Hubs, Xometry) vs 2.5 × nominal wall (Fictiv). Thickness ranges from 40–60% to 50–60% to 0.5 × wall. Base fillet ranges from 0.25 × rib thickness up to 1 × wall.
- **Boss wall:** 40–60% (Protolabs tip, Xometry) vs 60–70% (Protolabs 2018 blog).
- **Outside radius:** Protolabs says 1.5 × wall; Hubs and Fictiv say inside radius + wall. These agree only when the inside radius is 0.5 × wall.
- **Molding tolerance:** Protolabs ±0.003 in vs Xometry ±0.005 in (both plus 0.002 in/in) vs Hubs ±0.25 mm part tolerance.
- **CNC corner radius:** ⅓ of depth (Hubs), 1:4 radius-to-depth (Xometry), or simply larger than the tool radius (Fictiv, Xometry +30%).
- **CNC pocket depth:** 4 × width (Hubs), 3–5 × or 6 × width (two Xometry pages), or 5 / 10 / 15 × tool diameter by material (Fictiv).
- **CNC minimum wall:** Fictiv's 0.25 / 0.5 mm is far below Hubs' and Xometry's 0.8 / 1.5 mm. Protolabs says 0.51 mm.
- **Hole depth:** Hubs' guide says 6 × maximum while its KB says 40 × feasible. Fictiv says 12 ×; Protolabs calls more than 6 × a challenge.
- **Thread depth:** 3 × D (Hubs, Protolabs), 2 × D (Xometry), 1–1.5 × D engagement (Fictiv).
- **Sheet metal flange:** 4t (Protolabs) vs 2t + R (Hubs) vs 2.5t + R (Xometry stamping).
- **Hole-to-bend:** Protolabs contradicts itself (4t vs 2–3t); Hubs says 2t; Xometry stamping says 2–2.5t + R.
- **Hole-to-edge:** 1t (Hubs), 2t (Xometry), or fixed 0.062 / 0.125 in (Protolabs).
- **Bend angle tolerance:** ±1° (Protolabs, Hubs, Xometry standards) vs ±2° (Xometry mini-guide).
- **Hem return:** 6t (Protolabs) vs 4t (Xometry).
- **K-factor:** Protolabs gives fixed 0.33 / 0.42; Hubs gives a 0.3–0.5 range averaging 0.4468.

## Errors printed on the source pages
- Hubs draft knowledge base: "1 inch (2.2 cm)"; it should be 2.54 cm.
- Hubs CNC KB: "0.05 mm (0.005 inches)" is not a matching pair, and "5 mm engraved" looks wrong.
- Hubs sheet metal guide: K-factor given in mm, but it has no units.
- Fictiv 2025 IM guide: the PMMA mm column repeats the inch values.
- Fictiv CNC guide: "0.5 in end mill in steel reaches 2.75 in", which is more than its own 5 × rule allows.
- Xometry sheet-metal-bending page (https://www.xometry.com/resources/sheet/sheet-metal-bending/): minimum bendable thickness printed as "127 mm".
- PPS is labelled "Polypropylene Sulfide" on the Protolabs basics page and "Polyethylene Sulfide" in Fictiv's 2023 article.

## Could not find / blocked pages
- **Fictiv sheet metal:** I found no Fictiv sheet metal design page. My guessed URLs returned the articles index, and the WebSearch budget (200 per session) ran out before I could search further.
- **Xometry's full design guides are download-only.** The injection molding, sheet metal and CNC guide pages (under xometry.com/resources/design-guides/) are landing pages with no numbers.
- **Missing wall-thickness tables:** Xometry has no molding wall-thickness-by-material table on any page I fetched, and neither Hubs molding page has one.
- **Broken or oversized pages:**
  - 404: hubs.com/knowledge-base/injection-molding-design-guidelines/, hubs.com/knowledge-base/cnc-machining-design-guide/ and xometry.com/resources/injection-molding/injection-molding-design-guide/.
  - Fictiv's molding ebook PDF is over the 10 MB fetch limit.
- **Only one source:** boss OD/ID ratio (Hubs), numeric curl and countersink rules (Xometry), and K-factor (Protolabs and Hubs only).
- **Protolabs sheet metal design-guidelines page** has no K-factor or relief dimensions; those numbers come from its separate tip and blog pages.