"""Action Priority (AP) approximation for AIAG & VDA-style DFMEA (S/O/D).

**Sourcing note (read this before trusting the output):** ``docs/research/R5b-standards-safety-risk-se.md``
confirms the *existence and shape* of the AIAG & VDA FMEA Handbook (June
2019) Action Priority method -- it replaces the old RPN (Severity x
Occurrence x Detection) with a lookup over S/O/D that returns High/Medium/Low,
weighting Severity first, then Occurrence, then Detection -- but the research
session could not read the handbook itself (it is paywalled) and explicitly
did **not** reproduce its S x O x D -> AP lookup table [R5b §(3), item 12:
"AIAG & VDA FMEA content: the S/O/D and AP descriptions come from background
knowledge, not the paywalled handbook [U]. I did not reproduce the AP
table."].

So this module implements only what R5b actually sources: the three rating
scales' *meaning* (Severity = how bad the worst effect is; Occurrence = how
likely the failure cause is; Detection = how well current controls would
catch it before release/ship) and the qualitative rule that Severity
dominates the classification, then Occurrence, then Detection. It does
**not** claim to reproduce the handbook's exact per-triple table. Every
result is tagged ``approximate: True`` with a pointer back to the handbook,
and the classifier is deliberately conservative: it never rounds a
high-severity, non-trivial-occurrence combination down to Low.

A team with the real handbook should treat this as a first pass, not a
substitute -- CONTRACTS' credibility ladder would call this L0 (claimed)
information until the team itself checks it against the source table.
"""
from __future__ import annotations

from typing import NamedTuple

HANDBOOK_NOTE = (
    "AIAG & VDA FMEA Handbook (1st ed., Jun 2019) Action Priority table is "
    "paywalled and was not reproduced in docs/research/R5b -- this is a "
    "sourced approximation using only the documented S-then-O-then-D rule. "
    "Verify against the licensed handbook before treating a Low/Medium as final."
)


class APResult(NamedTuple):
    ap: str  # "High" | "Medium" | "Low"
    approximate: bool
    note: str


def _band_severity(s: int) -> str:
    if s >= 9:
        return "critical"   # safety / health / regulatory-compliance effects (R5b)
    if s >= 7:
        return "high"
    if s >= 5:
        return "moderate"
    if s >= 2:
        return "low"
    return "none"


def _band_occurrence(o: int) -> str:
    if o >= 7:
        return "high"
    if o >= 4:
        return "moderate"
    if o >= 2:
        return "low"
    return "none"


def _band_detection(d: int) -> str:
    """Detection: 10 = no detection method, 1 = always caught (R5b)."""
    if d >= 7:
        return "poor"
    if d >= 4:
        return "moderate"
    return "good"


def action_priority(severity: int, occurrence: int, detection: int) -> APResult:
    """Classify one Design/Process FMEA row into High/Medium/Low.

    Raises ValueError if severity/occurrence/detection are not integers in
    1..10 (the AIAG & VDA scale, R5b).
    """
    for name, val in (("severity", severity), ("occurrence", occurrence), ("detection", detection)):
        if not isinstance(val, int) or isinstance(val, bool) or not (1 <= val <= 10):
            raise ValueError(f"{name}={val!r} must be an integer in 1..10")

    s_band = _band_severity(severity)
    o_band = _band_occurrence(occurrence)
    d_band = _band_detection(detection)

    if s_band == "critical":
        # R5b: "top ratings are reserved for effects on safe operation,
        # health or regulatory compliance" -- never let these read Low.
        if o_band == "none" and d_band == "good":
            ap = "Medium"
        else:
            ap = "High"
    elif s_band == "high":
        if o_band in ("high", "moderate"):
            ap = "High"
        elif o_band == "low":
            ap = "Medium"
        else:  # occurrence "none"
            ap = "Medium" if d_band != "good" else "Low"
    elif s_band == "moderate":
        if o_band == "high":
            ap = "Medium"
        elif o_band == "moderate":
            ap = "Medium" if d_band == "poor" else "Low"
        else:
            ap = "Low"
    else:  # s_band in ("low", "none")
        # Severity dominates the classification (R5b): a low-severity cause
        # stays Low even with poor detection, in this approximation.
        ap = "Low"

    return APResult(ap=ap, approximate=True, note=HANDBOOK_NOTE)
