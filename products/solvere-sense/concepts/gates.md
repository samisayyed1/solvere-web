# G1 safety gates: pass/fail, applied BEFORE Pugh scoring

- **Recorded:** 2026-09-25, at the owner's instruction ("no-fall retention, enclosure flammability, radar-window material/thickness per MR60FDA2 … as pass/fail gates applied before Pugh scoring").
- **Machine-readable copy:** `concepts/gates.json`.

## How the gates are applied

- Every concept is judged against every gate **first**.
- A concept that FAILs any gate is **not scored** in the Pugh matrix. It is listed in the tournament report with the failing gate and the reason, and it may be revised and re-submitted.
- Gates are not weighted, traded off or averaged, and a high Pugh score never offsets a gate FAIL.
- Judges must quote the concept text that meets each gate criterion, or say that none does. At concept level "TBD at G2" is acceptable only where a gate says so below.

## GATE-S1: no-fall retention

**Sources:** REQ-MECH-004, REQ-MECH-005, REQ-MECH-015, REQ-MECH-016, and the owner's round-2 note on retention.

PASS only if **all** of these hold:

1. The pod is held to the base plate by a **positive mechanical interlock**, for example a bayonet or twist-lock with a detent or stop, which gravity, vibration or a light knock cannot release. Friction, adhesive or magnets alone FAIL.
2. The concept states a **load path** from the pod, through the base plate and the fixings, into the ceiling for each mount: drywall, concrete and the T-bar clip.
3. The hand twist-off (REQ-MECH-016) needs a deliberate rotation against the detent, and the concept says how accidental release is prevented.
4. The retention loads are stated as REQ-MECH-015: measured weight × a safety factor whose value and source live in `params/params.toml`. The numeric factor may be "TBD at G2" (the owner has set it as a G2 entry criterion); the mechanism may not.

## GATE-S2: enclosure flammability

**Sources:** REQ-SAFE-001 and R5a/R5b (UL 94 via IEC 62368-1). The required class is set by a qualified human (Q-17).

PASS only if **all** of these hold:

1. Every enclosure part (shell, base plate, radome, T-bar clip, light pipe) names a **specific material and grade** for each process it would be made in: FDM PETG for fit checks, and SLA resin or MJF nylon for demo units.
2. For each named grade the concept either cites a **published UL 94 listing** (the material maker's datasheet or UL Product iQ) at or below the part's intended wall thickness, or marks the part "fit-check only, not a demo or production material".
3. The concept does not depend on a material that has no UL 94 listing at any thickness.

The class itself (HB, V-2, V-1 or V-0) is **not** decided by Forge. The gate checks only that a listed material path exists, so the qualified human's class decision can be met.

## GATE-S3: radar window material and thickness

**Sources:** MR60FDA2 module datasheet §8, p.11–12, in `docs/sources/MR60FDA2-module-datasheet.pdf`; REQ-MECH-010, REQ-MECH-013, REQ-MECH-014; params `radome.antenna_gap_step` (2.5 mm) and `radome.keepout_half_angle` (60°).

PASS only if **all** of these hold:

1. **Material:** the radome material's dielectric constant εr and loss tangent tan δ come from the MDS §8 table or a cited material datasheet, never from memory.
   - The MDS table lists PC 2.9 / 0.012, ABS 2.0–3.5 / 0.0050–0.019, PEEK 3.2 / 0.0048, PTFE 2 / < 0.0002, PMMA 2.6 / 0.009, glass 5.75 / 0.003, ceramics 9.8 / 0.0005, PE 2.3 / 0.0003 and PBT 2.9–4.0 / 0.002.
   - PETG, SLA resins and PA12 are **not** in the table and need a cited source or a measurement plan.
   - MDS §8 item 1 asks for a small εr and tan δ.
2. **Thickness:** T = N·c / (2 f √εr), with N = 1, 2, 3… and f = 60 GHz (MDS §8 item 3), computed from that εr. The radome is smooth and of uniform thickness over the field of view (MDS §8 item 2). The concept states N and the resulting T, or "T computed at G2 from the cited εr" if εr is still being sourced.
3. **Antenna gap:** the antenna face to the radome inner surface is d = N × 2.5 mm (MDS §8 item 4; REQ-MECH-014), and the concept states how that gap is held (a datum from the sensor board to the radome).
4. **Keep-out:** no metal, metallic pigment or conductive coating inside the 60° half-angle cone about boresight (REQ-MECH-010). That includes fixings, magnets, springs and the light-pipe path.

A concept whose radome material has a range of εr (e.g. ABS 2.0–3.5) must state how the actual grade's εr is pinned down, because T depends on it.
