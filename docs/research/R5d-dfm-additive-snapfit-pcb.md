# R5d — DFM rule tables: additive (FDM/SLA/SLS/MJF), snap-fit strain, PCB fab
- Date accessed: 2026-09-25 · Author: R5 sub-research agent (Phase 1) · Status: salvaged — parent R5 agent was stopped to save usage; this is the sub-agent's complete returned report, unedited.
- Tags: [V] verified on issuing body / manufacturer page · [R] reported (secondary) · [U] unverified

I found numbers for all seven areas: FDM 16 rows, SLA 20, SLS 16, MJF 13, snap-fit strain 25, JLCPCB 20 and PCBWay 16, for about 125 in total. That is over your 90-row target because the sources often disagree and I kept both values.

**Tags.** [V] means I read the number myself on the manufacturer's own page or PDF. [R] means it came from a search snippet or from a manufacturer PDF on someone else's site; for the BASF and DuPont rows I still read the tables in the PDF myself. The fetch tool summarises HTML pages, so HTML-page numbers passed through it; I read the PDFs directly. JLCPCB, Formlabs Form 4 and Xometry's MJF rows were fetched two or three times to check them. "PN" is Protolabs Network (formerly Hubs).

**Main URLs** (tables below use short names):
- PN design-rules PDF (Protolabs-branded poster): https://4075618.fs1.hubspotusercontent-na1.net/hubfs/4075618/Gated%20content%20-%20PL%20Network%20-%202024/PL_3DP_Design_Rules_EN.pdf. The file path says 2024; the PDF itself shows no date.
- Covestro snap-fit guide: https://solutions.covestro.com/-/media/covestro/solution-center/brands/downloads/imported/1557218421.pdf (created 3 May 2019, from the file's metadata)
- JLCPCB: https://jlcpcb.com/capabilities/pcb-capabilities
- PCBWay: https://www.pcbway.com/capabilities.html

## FDM
| Rule | Value | Source | URL | Tag |
|---|---|---|---|---|
| Supported / unsupported wall | 0.8 mm / 0.8 mm | PN PDF | PN PDF | V |
| Minimum wall | 0.8–1 mm desktop, 1 mm industrial; 2–3× nozzle diameter (0.8–1.2 mm) | PN "What is FDM" | hubs.com/knowledge-base/what-is-fdm-3d-printing/ | V |
| Supporting walls | 0.047"–0.06" (1.2–1.5 mm) | Xometry FDM mini-guide (updated 4 Sep 2025) | xometry.com/resources/3d-printing/mini-guide-fdm-3d-printing/ | V |
| Unsupported (cantilever) walls | ≥1.2 mm; 2.5 mm for large-format FDM | Xometry FDM design guide (download is behind a form) | xometry.com/resources/design-guides/design-guide-fused-deposition-modeling-fdm-3d-printing/ | R |
| Max overhang without support | 45° | PN PDF; PN FDM guide | PN PDF; hubs.com/knowledge-base/how-design-parts-fdm-3d-printing/ | V |
| Horizontal bridge | 10 mm | PN PDF | PN PDF | V |
| Bridge with no sag or support marks | < 5 mm | PN FDM guide | hubs.com/…/how-design-parts-fdm-3d-printing/ | V |
| Embossed / engraved detail | 0.6 mm wide & 2 mm high | PN PDF | PN PDF | V |
| Raised text | ≥ 0.04" (1 mm); 1.2–1.5 mm recommended; cut-out text the same | Xometry mini-guide | as above | V |
| Minimum hole | Ø2 mm | PN PDF | PN PDF | V |
| Minimum hole | > 0.04" (1 mm); holes < .040" print slightly oval | Xometry mini-guide; Xometry manufacturing standards (updated 28 Jan 2025) | mini-guide; xometry.com/manufacturing-standards/ | V |
| Clearance, moving/connecting parts | 0.5 mm | PN PDF; PN snap-fit article | PN PDF; hubs.com/knowledge-base/how-design-snap-fit-joints-3d-printing/ | V |
| Clearance / gaps | about 0.5–1 mm | Xometry (search snippet) | xometry.com design guide (above) | R |
| Min feature / pin | 2 mm / 3 mm; pins < 5 mm print as perimeter only | PN PDF; PN FDM guide | PN PDF; FDM guide | V |
| Tolerance | ±0.3% (lower limit ±0.3 mm) | PN PDF | PN PDF | V |
| Tolerance | Desktop ±0.5% (lower ±1.0 mm); industrial ±0.3% (lower ±0.2 mm) | PN "What is FDM" | as above | V |
| Tolerance | ±1 layer thickness for the first inch + ±.002"/in after; mini-guide gives ±0.005" | Xometry standards; mini-guide | as above | V |
| Minimum rib | 0.06" (1.5 mm) | Xometry mini-guide | as above | V |

## SLA
| Rule | Value | Source | URL | Tag |
|---|---|---|---|---|
| Supported / unsupported wall | 0.5 mm / 1 mm | PN PDF | PN PDF | V |
| Supported / unsupported wall | ≥ 0.4 mm / ≥ 0.6 mm | PN SLA guide | hubs.com/knowledge-base/how-design-parts-sla-3d-printing/ | V |
| Supported / unsupported wall | 0.2 mm / 0.2 mm (Grey V5 resin, 50 µm, Form 4) | Formlabs | formlabs.com/support/Design-specifications-for-3D-models-Form-4-generation/ | V |
| Minimum wall | Normal 0.010 in (0.254 mm); High 0.004 in; Micro 0.0025 in | Protolabs SLA service page | protolabs.com/services/3d-printing/stereolithography/ | V |
| Minimum wall | Normal 0.012 in (0.305 mm); High 0.006 in (0.152 mm); MicroFine 0.003 in | Protolabs 3DP toolkit | protolabs.com/resources/design-for-3d-printing-toolkit/ | V |
| Overhang | "support always required" | PN PDF | PN PDF | V |
| Overhang | < 1.0 mm long and ≥ 19° from level | PN SLA guide | as above | V |
| Overhang | Max unsupported 5.0 mm; min angle 10° from level | Formlabs Form 4 (Form 3 is the same) | Form 4 support page; formlabs.com/support/Design-specifications-for-3D-models-form-3 | V |
| Horizontal bridge / span | < 21 mm (PN) vs 29 mm (Formlabs) | PN SLA guide; Formlabs | as above | V |
| Embossed / engraved | 0.4 mm wide & high | PN PDF | PN PDF | V |
| Embossed / engraved | Embossed ≥ 0.1 mm high; engraved ≥ 0.4 mm wide × 0.4 mm | PN SLA guide | as above | V |
| Embossed / engraved | 0.1 mm / 0.15 mm | Formlabs Form 4 | Form 4 support page | V |
| Minimum hole | Ø0.5 mm (PN PDF); 0.5–0.8 mm (PN guide); 0.5 mm (Formlabs Form 3/4, Form 2 was 0.8 mm) | PN; Formlabs | PN PDF; formlabs.com/blog/design-guide-form3/ | V |
| Minimum hole | Normal 0.025 in (0.635 mm); High 0.020 in; Micro 0.015 in | Protolabs SLA service page | as above | V |
| Clearance | Moving 0.5 mm; connections 0.2 mm; push fit 0.1 mm (PN PDF gives 0.5 mm) | PN SLA guide; PN PDF | as above | V |
| Clearance | Minimum 0.4 mm (Form 4), 0.5 mm (Form 3); interlocking parts 0.2 mm small, up to 0.4 mm large | Formlabs | Form 4 support page; formlabs.com/blog/how-to-3d-print-interlocking-joints/ | V |
| Escape / drain hole | 4 mm (PN PDF); ≥ 3.5 mm (PN guide); 2.5 mm (Formlabs Form 3); 0.75 mm (Formlabs Form 4) | PN; Formlabs | as above | V |
| Hollow-part wall | ≥ 2 mm | PN SLA guide | as above | V |
| Min feature / pin | 0.2 mm / 0.5 mm (PN PDF); vertical wire 0.3 mm at 7 mm tall and 0.6 mm at 30 mm tall (Form 4) | PN; Formlabs | as above | V |
| Tolerance | ±0.2% (lower ±0.13 mm) | PN PDF | PN PDF | V |
| Tolerance | 1–30 mm: ±0.15% (lower ±0.02 mm); 31–80 mm: ±0.2% (±0.06 mm); 81–150 mm: ±0.3% (±0.15 mm) | Formlabs Form 4 white paper | formlabs.com/white-papers/form-4-design-guide/ | V |
| Tolerance | X/Y ±0.002 in (0.05 mm) for the first inch + 0.1%; Z ±0.005 in + 0.1% | Protolabs | protolabs.com/resources/design-tips/3d-printing-tolerances/ | V |
| Tolerance | XY ±0.005" first inch + ±0.002"/in; Z ±0.010" + ±0.002"/in; features < .020" at risk, < .010" won't build | Xometry standards | as above | V |

## SLS
| Rule | Value | Source | URL | Tag |
|---|---|---|---|---|
| Supported wall | 0.7 mm | PN PDF | PN PDF | V |
| Minimum wall | 0.8 mm (PA12); 2.0 mm (carbon-filled PA) | PN SLS guide | hubs.com/knowledge-base/how-design-parts-sls-3d-printing/ | V |
| Minimum wall | 0.6 mm vertical / 0.3 mm horizontal (Nylon 12) | Formlabs Fuse guide | formlabs.com/white-papers/fuse-series-sls-design-guide/ | V |
| Minimum wall / feature | Nylons 0.030 in (0.762 mm); PP and TPU 0.04 in (1.01 mm) | Protolabs SLS service page | protolabs.com/services/3d-printing/selective-laser-sintering/ | V |
| Min feature / pin | 0.8 mm (PN PDF, PN guide, Formlabs); Xometry: < .030" may not resolve | several | as above | V |
| Minimum hole | Ø1.5 mm (PN); 1.0 mm (Formlabs); holes < .040" may sinter shut (Xometry) | several | as above | V |
| Clearance | Moving 0.3 mm, connections 0.1 mm (PN PDF); axles 0.3 mm, hinge ball-in-socket 0.2 mm (PN guide) | PN | as above | V |
| Clearance | Separate assemblies: < 20 mm² 0.2 mm, > 20 mm² 0.4 mm. Printed in place: 0.3–0.6 mm | Formlabs | Fuse guide; interlocking-joints blog | V |
| Escape hole | 5 mm (PN PDF); ≥ 3.5 mm (PN guide); 3.5 mm (Formlabs) | PN; Formlabs | as above | V |
| Embossed / engraved | 1 mm wide & high (PN PDF); 1 mm height/depth, font ≥ 2 mm (PN guide) | PN | as above | V |
| Text | Embossed 4.5 mm high × 0.3 mm deep; engraved 3.0 mm high × 0.3 mm deep | Formlabs | Fuse guide | V |
| Living hinge | 0.3–0.8 mm thick, ≥ 5 mm long | PN SLS guide | as above | V |
| Minimum gap between features | 0.030 in (0.762 mm) | Protolabs nylon guide | protolabs.com/resources/design-tips/how-to-design-for-nylon-3d-printing/ | V |
| Tolerance | ±0.3% (lower ±0.3 mm); ±0.05 mm per extra 25 mm | PN PDF / PN guide | as above | V |
| Tolerance | ±0.010 in (0.25 mm) + 0.1% | Protolabs | SLS service page | V |
| Tolerance | Nylon 12: ±.015" or ±.002"/in, whichever is greater; Nylon 11/TPU: ±.020" or ±.003"/in | Xometry standards | as above | V |

## MJF
| Rule | Value | Source | URL | Tag |
|---|---|---|---|---|
| Minimum wall | 0.020 in (0.5 mm); toolkit says 0.508 mm | Protolabs MJF service page; toolkit | protolabs.com/services/3d-printing/multi-jet-fusion/ | V |
| Wall range | 2.5–12.7 mm (PN calls it minimum/maximum) | PN MJF guide | hubs.com/knowledge-base/how-to-design-parts-for-mjf/ | V |
| Ideal wall | 2.5–3.8 mm | Protolabs UK | protolabs.com/en-gb/resources/insight/designing-parts-for-3d-printing-using-multi-jet-fusion/ | V |
| Wall (combined SLS & MJF row) | 0.7 mm | PN PDF | PN PDF | V |
| Minimum feature | 0.5 mm (Protolabs, PN); 0.8 mm (PN PDF); < .030" may not resolve (Xometry) | several | as above | V |
| Raised text / cosmetic detail | Features < 0.5 mm may not survive post-processing | PN; Protolabs UK | hubs.com/knowledge-base/what-is-multi-jet-fusion/ | V |
| Minimum hole | Ø1.5 mm (PN PDF); holes < .040" may sinter shut (Xometry) | PN; Xometry | as above | V |
| Clearance | 0.6 mm if assembled after printing; 0.9 mm if printed assembled | PN MJF guide | as above | V |
| Escape hole | 5 mm (only in the combined SLS & MJF row) | PN PDF | PN PDF | V |
| Watertightness | 1 mm wall for water resistance; ≥ 4 mm for watertight | PN MJF guide | as above | V |
| Tolerance | ±0.012 in (0.30 mm) + 0.1% | Protolabs | MJF service page | V |
| Tolerance | ±0.3% (lower ±0.3 mm) | PN | what-is-multi-jet-fusion | V |
| Tolerance | Prototype (under 30 mm): rigid ±0.70 mm, TPU ±1.05 mm. Production (under 30 mm): XY ±0.25 mm, Z ±0.42 mm, only after engineering review | Xometry standards | as above | V |

## Snap-fit permissible strain

**Per-material strain values**

| Material | Value | Source | URL | Tag |
|---|---|---|---|---|
| PC (Makrolon) | 4% | Covestro snap-fit guide, Table 2, 23 °C, single assembly | 1557218421.pdf, p.12 | V |
| High-heat PC (Apec) | 4% | same | same | V |
| PC/ABS (Bayblend) | 2.5% | same | same | V |
| PC blend (Makroblend) | 3.5% | same | same | V |
| PC with 10% / 20% glass fibre | 2.2% / 2.0% | same | same | V |
| PC with 10% / 20% / 30% glass fibre | 2.0% / 1.5% / 1.0% | Covestro Part & Mold Design guide, Table 4-1 (PDF metadata 2015/16) | solutions.covestro.com/-/media/covestro/solution-center/brands/downloads/imported/1557222937.pdf, p.86 | V |
| PC/ABS with 10% / 20% glass fibre; PC/SAN with 10% / 20% / 30% | 1.5% / 1.0%; 2.0% / 1.5% / 1.0% | same | same | V |
| PC blend with 10% / 20% glass fibre | 2.5% / 2.5% | same | same | V |
| POM, Delrin 100 | 8% once; 2–4% frequent | DuPont General Design Principles, Table 10.06 (PDF dated 2000, on a distributor's site) | distrupol.com/General_Design_Principles_for_Engineering_Polymers.pdf, p.75 | R |
| POM, Delrin 500 | 6% once; 2–3% frequent | same | same | R |
| PA66 (Zytel 101) dry / 50% RH | 4% / 6% once; 2% / 3% frequent | same | same | R |
| PA66 glass-reinforced (Zytel GR) dry / 50% RH | 0.8–1.2% / 1.5–2.0% once; 0.5–0.7% / 1.0% frequent | same | same | R |
| PET GR (Rynite) / PBT GR (Crastin) | 1% / 1.2% once; 0.5% / 0.6% frequent | same | same | R |
| TPC elastomer (Hytrel) | 20% once; 10% frequent | same | same | R |
| POM (acetal) unfilled / 30% glass | 7% / 2.0% | BASF Snap-Fit Design Manual, Table IV-I (third-party copy) | productdesignonline.com/wp-content/uploads/2019/08/Snap-Fit-Design-Manual.pdf, p.IV-4 | R |
| PA6 dry-as-moulded unfilled / 30% glass | 8% (BASF says use 4% in the mating-force formula) / 2.1% | same | same | R |
| PBT unfilled / 30% glass | 8.8% / 2.0% | same | same | R |
| ABS | 6–7% | same | same | R |
| PC | 4–9.2% | same | same | R |
| PC/PET; PEI; PET 30% glass | 5.8%; 9.8%; 1.5% | same | same | R |

**Rules of thumb and the deflection formula**

| Rule | Value | Source | URL | Tag |
|---|---|---|---|---|
| Frequent separation and rejoining | Use about 60% of the single-assembly values | Covestro | 1557218421.pdf, p.12 | V |
| How the limit is set | Semi-crystalline plastics: almost up to yield strain. Amorphous: about 70% of yield strain. Glass-filled: about half the elongation at break | Covestro | 1557218421.pdf, p.11 | V |
| Taper and root radius | Thickness tapered to half at the tip allows more than 60% extra deflection. Root radius ≥ 0.015 in; R/h 0.6 is where benefit levels off | Covestro | 1557218421.pdf, pp.8, 12 | V |
| Deflection formula (my wording) | The root's outer-fibre strain is proportional to thickness × tip deflection ÷ length², so allowed deflection y = k·ε·L²/h. Covestro k: 0.67 constant rectangle; 1.09 thickness tapered to h/2; 0.86 width tapered to b/4. Deflection force P = (b·h²/6)·Es·ε/L, with Es the secant modulus at that strain | Covestro Table 1 | 1557218421.pdf, p.9 | V |
| Mating force (my wording) | Add friction μ and lead angle α: W = P·(μ + tan α)/(1 − μ·tan α) | BASF | BASF PDF, p.IV-4 | R |
| Short-arm correction (my wording) | Plain beam formulas under-predict root strain for short arms, where the wall also flexes. BASF divides by a factor Q from charts: ε = 1.5·t·Y/(L²·Q). Q ≈ 1 once length/thickness is above about 10:1 | BASF | BASF PDF, p.IV-1 | R |

## PCB – JLCPCB
The page has no separate "advanced" table. Some options are flagged as costing more: the 0.15 mm drill, 0.15 mm via holes, and the ±0.1 mm high-precision outline. The only date shown is a note that its LDI equipment was upgraded in June 2025.

| Rule | Value | Source | URL | Tag |
|---|---|---|---|---|
| Trace/space, 1 oz, 1–2 layer | 0.10/0.10 mm (4/4 mil) | JLCPCB | JLCPCB | V |
| Trace/space, 1 oz, multilayer | 0.09/0.09 mm (3.5/3.5 mil); 3 mil allowed in BGA fan-out | JLCPCB | JLCPCB | V |
| Trace/space, 2 oz | 2-layer 0.16/0.16 mm (6.5 mil); multilayer 0.15/0.15 mm (6 mil) | JLCPCB | JLCPCB | V |
| Trace/space, heavier copper (2-layer only) | 2.5 oz 0.2/0.2 mm; 3.5 oz 0.25/0.25 mm; 4.5 oz 0.3/0.3 mm | JLCPCB | JLCPCB | V |
| Trace width tolerance | ±20% | JLCPCB | JLCPCB | V |
| Drill range | 1-layer 0.3–6.3 mm; 2-layer and multilayer 0.15–6.3 mm (0.15 mm "more costly") | JLCPCB | JLCPCB | V |
| Min via hole / via diameter | 0.15 / 0.25 mm on 2-layer and multilayer (costs more); 1-layer 0.3 / 0.5 mm | JLCPCB | JLCPCB | V |
| PTH annular ring | Headline ≥ 0.20 mm. 2-layer 1 oz: 0.25 mm recommended, 0.18 mm absolute minimum. Multilayer 1 oz: 0.20 recommended, 0.15 absolute minimum | JLCPCB | JLCPCB | V |
| NPTH pad annular ring | ≥ 0.45 mm | JLCPCB | JLCPCB | V |
| Min NPTH | 0.50 mm | JLCPCB | JLCPCB | V |
| Hole-to-hole spacing | Via 0.2 mm; pad (different nets) 0.45 mm | JLCPCB | JLCPCB | V |
| Via-to-track / PTH-to-track / pad-to-track | 0.2 / 0.28 / 0.1 mm | JLCPCB | JLCPCB | V |
| SMD pad-to-pad, different nets | 0.15 mm | JLCPCB | JLCPCB | V |
| Copper to routed edge / V-cut | ≥ 0.2 mm / ≥ 0.4 mm | JLCPCB | JLCPCB | V |
| Hole tolerance | Plated +0.13 / −0.08 mm; press-fit ±0.05 mm; non-plated ±0.2 mm | JLCPCB | JLCPCB | V |
| Outline tolerance | Routed ±0.2 mm regular, ±0.1 mm high-precision; V-cut ±0.4 mm | JLCPCB | JLCPCB | V |
| Solder mask | 1:1 expansion, keep ≥ 0.09 mm to nearby traces. Dam, 1 oz: 0.10 mm (green/red/yellow/blue/purple), 0.13 mm (black/white). Dam, 2 oz: 0.20 mm | JLCPCB | JLCPCB | V |
| Silkscreen | Line ≥ 0.15 mm; text height ≥ 1.0 mm (40 mil); width:height 1:6; pad-to-silk 0.15 mm | JLCPCB | JLCPCB | V |
| Board thickness | 0.4–4.5 mm range. FR-4 2-layer options 0.4/0.6/0.8/1.0/1.2/1.6/2.0 mm; ≥ 2.5 mm only for 12+ layers. Tolerance ±10% (≥ 1.0 mm), ±0.1 mm (< 1.0 mm) | JLCPCB | JLCPCB | V |
| Min slot / castellated | Plated slot 0.5 mm (2-layer), 0.35 mm (multilayer); non-plated slot 1.0 mm. Castellated hole ≥ 0.5 mm, ≥ 1 mm from edge. Min board 3 × 3 mm | JLCPCB | JLCPCB | V |

## PCB – PCBWay
PCBWay has a Standard table and an Advanced table. The Advanced table grades each item as normal, medium or high difficulty. The page shows no date.

| Rule | Value | Source | URL | Tag |
|---|---|---|---|---|
| Trace/space (standard) | 0.1 mm / 4 mil | PCBWay standard | PCBWay | V |
| Outer-layer trace/space (advanced, normal tier) | 18 µm copper ≥ 4/5 mil; 35 µm ≥ 5/6 mil; 70 µm ≥ 7/8 mil; 105 µm ≥ 10/12 mil | PCBWay advanced | PCBWay | V |
| Inner-layer trace/space (advanced, normal tier) | 18 µm ≥ 4/4 mil; 35 µm ≥ 4/5 mil; 70 µm ≥ 6/8 mil | PCBWay advanced | PCBWay | V |
| Drill / finished hole | 0.15–6.0 mm | PCBWay standard | PCBWay | V |
| Min annular ring | 0.15 mm (6 mil) standard. Advanced, outer layer, 18 µm: via ≥ 5 mil, component hole ≥ 8 mil | PCBWay | PCBWay | V |
| Hole tolerance | Standard: PTH ±0.08 mm, NPTH ±0.05 mm. Advanced normal: PTH ±0.075 mm, NPTH ≥ ±0.075 mm | PCBWay | PCBWay | V |
| Hole position tolerance | ±0.075 mm (normal) | PCBWay advanced | PCBWay | V |
| Hole-to-hole | Component holes ≥ 16 mil (normal); vias ≤ 0.45 mm need ≥ 11 mil | PCBWay advanced | PCBWay | V |
| Trace to board edge (CNC routing) | 0.25 mm normal; 0.20 mm medium | PCBWay advanced | PCBWay | V |
| Solder mask (green, 18 µm) | Opening ≥ 2 mil; bridge 4 mil (under 2 oz), 5 mil (2 oz and up) | PCBWay advanced | PCBWay | V |
| Silkscreen (standard) | Width 0.15 mm; height 0.8 mm; ratio 1:5 | PCBWay standard | PCBWay | V |
| Silkscreen (advanced, normal tier) | 18 µm: 8 mil wide / 40 mil high; 35 µm: 9 / 40 mil | PCBWay advanced | PCBWay | V |
| Board thickness | 0.2–3.2 mm (0.2 … 3.2 options). Tolerance ±10% (≥ 1.0 mm), ±0.1 mm (< 1.0 mm) | PCBWay standard | PCBWay | V |
| Outline tolerance | ±0.2 mm CNC routing; ±0.5 mm V-score. Advanced shape tolerance ≥ ±0.15 mm (normal) | PCBWay | PCBWay | V |
| Plated half-hole / castellated | Standard min 0.4 mm; advanced normal ≥ 0.5 mm with ≥ 0.3 mm spacing | PCBWay | PCBWay | V |
| Slots / aspect ratio | Plated ≥ 0.5 mm; non-plated ≥ 0.8 mm; thickness:hole diameter ≤ 8 (normal) | PCBWay advanced | PCBWay | V |

## Disagreements
1. **SLA escape hole:** 4 mm (PN PDF), 3.5 mm (PN guide), 2.5 mm (Formlabs Form 3), 0.75 mm (Formlabs Form 4).
2. **SLA walls:** supported 0.5 / 0.4 / 0.2 mm (PN PDF / PN guide / Formlabs); unsupported 1 / 0.6 / 0.2 mm.
3. **Protolabs SLA minimum wall at normal resolution:** 0.010 in on the service page vs 0.012 in in the toolkit.
4. **SLA overhang:** PN PDF says always support; the PN guide says ≥ 19° and < 1 mm; Formlabs says ≥ 10° and ≤ 5 mm.
5. **SLS minimum wall:** 0.7 mm (PN PDF), 0.8 mm (PN guide), 0.6 mm (Formlabs), 0.762 mm (Protolabs).
6. **SLS escape hole:** 5 mm (PN PDF) vs 3.5 mm (PN guide and Formlabs).
7. **SLS minimum hole:** 1.5 mm (PN) vs 1.0 mm (Formlabs) vs about 1 mm (Xometry's .040").
8. **SLS/MJF clearance:** PN PDF 0.3 mm moving / 0.1 mm connections; PN MJF guide 0.6 mm / 0.9 mm; Formlabs 0.2–0.4 mm.
9. **MJF wall:** 0.5 mm (Protolabs) vs 2.5–12.7 mm (PN, really a recommended range) vs 0.7 mm (PN PDF). Minimum feature: 0.5 mm vs 0.8 mm.
10. **MJF tolerance:** about ±0.3 mm (Protolabs and PN) vs Xometry's prototype ±0.70 mm under 30 mm.
11. **FDM tolerance:** PN PDF ±0.3% (lower ±0.3 mm) vs PN article ±0.5% (lower ±1.0 mm) desktop. Xometry gives two different figures: ±0.005" and ±1 layer + .002"/in.
12. **FDM minimum hole and bridges:** hole 2 mm (PN) vs 1 mm (Xometry); bridge 10 mm (PN PDF) vs < 5 mm to avoid sag (PN FDM guide).
13. **Covestro glass-filled PC:** 2.2% / 2.0% in the 2019 snap-fit guide vs 2.0% / 1.5% in the 2015/16 part design guide.
14. **Strain across resin makers:**
    - PC: 4% (Covestro) vs 4–9.2% (BASF).
    - POM: 6–8% (DuPont) vs 7% (BASF).
    - Nylon dry: 4% for PA66 (DuPont) vs 8% for PA6 (BASF, which still uses 4% for force).
    - PBT with glass: 1.2% (DuPont) vs 2.0% (BASF).
    - Repeated assembly: Covestro uses about 60%; DuPont's frequent-use column is about 25–50% of its single-use values.
15. **JLCPCB vs PCBWay:**
    - Annular ring: ≥ 0.20 mm (minimum 0.18 / 0.15) vs 0.15 mm.
    - Silkscreen height: 1.0 mm vs 0.8 mm.
    - V-score tolerance: ±0.4 vs ±0.5 mm.
    - PTH tolerance: +0.13/−0.08 vs ±0.08 mm.
    - NPTH tolerance: ±0.2 vs ±0.05 mm.
    - Copper to edge: 0.2 vs 0.25 mm.
16. **JLCPCB inconsistency:** one read gave ±0.2 mm for all non-plated holes; another tied it only to non-plated slots.
17. **PN MJF page unit error:** it gives 80 µm as "0.0003 in"; by my conversion that should be about 0.003 in.

## Could not find / blocked
- **Xometry:** the FDM, SLA and SLS design guides are downloads behind a form. The community knowledge-base pages (articles 734, 751, 752) returned no content. The Xometry cantilever-wall and 0.5–1 mm clearance figures come only from search snippets.
- **Pages that returned 404:**
  - protolabs.com/services/3d-printing/{multi-jet-fusion, selective-laser-sintering, stereolithography}/design-guidelines/
  - formlabs.com/blog/design-guide-3d-printing-sla/
  - delrin.com general design principles page
- **Could not fetch:**
  - hubs.com key-design-considerations page: its table is only in the PN PDF above.
  - Lanxess snap-fit guides for PA6 and PBT: connection refused on both techcenter.lanxess.com and sunny-plastic.com.
- **Snap-fit gaps:**
  - No resin maker's source found for PP, PE, SAN, or PA6 conditioned.
  - The older Bayer version, which may have these, only turned up on Scribd, which I didn't fetch.
  - No BASF-hosted or DuPont-hosted copy of their manuals found, so those rows are [R].
  - Celanese and SABIC strain tables not located.
- **Missing values:**
  - Formlabs gives no SLS tolerance.
  - FDM has no escape-hole rule.
  - MJF escape holes appear only in the PN PDF's combined SLS & MJF row.
  - Neither PCB maker states a minimum solder-mask sliver separately from the dam/bridge value.
  - PCBWay's standard table has no hole-to-hole or edge-clearance figures; those are only in the advanced table.
- **Search budget:** web searches ran out partway through (200 of 200 used), which limited finding other versions of the snap-fit guides.