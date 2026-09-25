# G0 owner answers, round 2: Solvere Sense ceiling pod

- **Source:** the product owner, in chat, 2026-09-25, answering the open questions in `reviews/G0.md`. The options were offered by Forge; the owner's picks and notes are recorded exactly as given.
- **Status:** L0 (claimed, owner decision).

| Q | Owner answer |
|---|---|
| Q-01 Compute and radio | **Kit as-is.** The XIAO ESP32C6 in the MR60FDA2 kit is the pod's only compute and radio. |
| Q-10 BOM scope | **Pod only, 10+ tier.** Shell, kit and fixings at 10+ unit pricing. Forge flags the $30 target as likely unreachable and reports the real number. |
| Q-05/Q-06 Fixing and removal | **Forge proposes; hand twist-off.** Forge picks screws and anchors for drywall and concrete (not in the box). The pod twists off the base plate by hand, with no tools and no visible screws. |
| Q-07 T-bar widths | **15 mm and 24 mm grids.** |
| Q-08 Bathroom ingress | **IPX4, O-ring cord gasket.** |
| Q-14 LED, light sensor, reset | **LED light pipe only.** Owner's note: "A tiny flush light pipe in the same matte warm white, OFF in normal use. It lights only during setup/pairing and on faults, and it can be disabled in settings. No light-sensor window. Reset by twisting the pod off (the button is reachable once removed), so no pinhole." |
| Other defaults | Accepted as offered (local Wi-Fi to Home Assistant; map US/EU/UK/Canada but sell nowhere until a qualified human confirms; colour matched at the demo stage; keep 3×3 m coverage with a 2 m radius fallback; home-automation use; one person; Forge drafts the Seeed questions and the owner sends them), **except:** |

The owner's exceptions, verbatim:

1. "Temperature: use 0–40 °C ambient (ceilings run hotter than rooms in summer), and check it against the MR60FDA2 and XIAO datasheet limits."
2. "Pods per room: my G0 answer said larger rooms may need 2 pods. Support up to 2 per room, and add a check for radar-to-radar interference between two pods."
3. "In the box: don't decide 'nothing extra' yet. Flag the cable question (a 2.2–3.0 m ceiling needs a long USB-C cable plus raceway) as an open product decision with a cost note."

Further instructions, verbatim:

- "The pull test stays a placeholder only through G0. Before G2, derive a real retention requirement from pod mass × a stated safety factor, with its source."
- "Keep 'no medical or safety claims' strict: even 'fall detection' wording must not imply a safety device."
