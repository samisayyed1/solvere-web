# DFMEA Action Priority: what's sourced and what isn't

Source: `docs/research/R5b-standards-safety-risk-se.md` §"AIAG & VDA FMEA
Handbook", 1st edition, June 2019, AIAG/VDA QMC (erratum June 2020, no 2nd
edition found).

## What R5b actually verified

- The handbook uses a 7-step method: planning, structure analysis, function
  analysis, failure analysis, risk analysis, optimisation, documentation
  [U — R5b's own summary, handbook is paywalled].
- Three rating scales, 1–10 each:
  - **Severity (S)**: how bad the worst effect of a failure mode is. 1 = no
    noticeable effect. The top ratings (9–10) are reserved for effects on
    safe operation, health or regulatory compliance.
  - **Occurrence (O)**: how likely the failure *cause* is to happen, judged
    mainly by how effective the prevention controls are and how proven the
    design/process is. 1 = the cause has effectively been designed out.
  - **Detection (D)**: how well current detection controls would catch the
    cause or failure mode before the design is released or the part ships.
    10 = no detection method; 1 = always caught.
  - (FMEA-MSR swaps Occurrence/Detection for Frequency/Monitoring — Forge
    does not implement FMEA-MSR yet.)
- **Action Priority (AP)** replaces the old RPN (S x O x D). It is a
  **lookup over S/O/D combinations** that returns High, Medium or Low,
  weighting **Severity first, then Occurrence, then Detection** — so a
  high-severity risk can't hide behind a merely-moderate product score the
  way RPN allowed.
- High = the team must act, or document why current controls are enough.
  Medium = the team should act. Low = the team could act.

## What R5b explicitly did NOT verify

> "AIAG & VDA FMEA content: the S/O/D and AP descriptions come from
> background knowledge, not the paywalled handbook [U]. I did not
> reproduce the AP table."

The actual per-triple lookup table (e.g. exactly which of the ~1000
S/O/D combinations map to High vs. Medium at the boundaries) is
**copyrighted content in a handbook Forge does not have a license to
reproduce**, and R5b did not attempt to reconstruct it from memory as fact.

## What `scripts/ap.py` implements instead

A **banded, monotonic approximation** using only the sourced rule
(severity dominates, then occurrence, then detection):

1. Band each of S, O, D into qualitative levels (critical/high/moderate/low/none
   for S; high/moderate/low/none for O; poor/moderate/good for D).
2. Apply the documented hierarchy: S band selects a base rule; O band
   refines it; D band only matters as a tiebreaker within a band, never to
   escalate priority above what S/O already indicate.
3. **Never** classify a critical-severity (S 9–10) row as Low — R5b's own
   text on what the top severities mean forbids it.
4. Tag every result `approximate: True` with a pointer back to the
   handbook (`ap.HANDBOOK_NOTE`).

This is intentionally **conservative at the edges**: where the exact table
might legitimately call something Medium and this approximation calls it
High, that costs a team a few minutes double-checking a row; the reverse
error (calling a real High a Low) is the one this design avoids. It is
still an approximation, not the standard.

## Using it correctly

- Treat `scripts/verify.py`'s failing rows (High AP with no tracked action)
  as real gate blockers — those need an action regardless of whether the
  exact AP tier is precisely right.
- Treat passing rows (Medium/Low) as "no automatic action required by this
  script", **not** as "the handbook agrees this is Medium/Low". If the
  team has the licensed handbook, re-check boundary cases (severity 5–8
  with high occurrence) against the real table before closing them out.
- If your organisation licenses the AIAG & VDA Handbook, replace
  `_band_severity`/`_band_occurrence`/`_band_detection`/`action_priority`
  in `scripts/ap.py` with the exact table, keep the same function
  signature, and drop the `approximate` flag once it matches. `capturing-failures`
  should log this as a permanent-check upgrade with an eval case, per the
  brief's self-improvement loop.
