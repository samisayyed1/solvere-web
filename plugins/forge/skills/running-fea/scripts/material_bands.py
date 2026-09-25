"""S8: a plausibility band for Young's modulus (E), keyed by material name.

This is a sanity check, not a materials database -- it exists to catch a
mistyped value (most commonly a GPa/MPa unit slip: entering ``210`` for a
steel that means 210 GPa = 210 000 MPa, three orders of magnitude off) before
it silently drives a safety factor or a hand-calc comparison. It never
supplies a value: CONTRACTS.md and SKILL.md both require every material
property to carry its own ``source``; this module only checks that the
*given* E is in the neighbourhood of what real materials of that family are
published to have.

Bands are deliberately wide (generous enough to cover ordinary alloy/temper
variation) and keyed by matching a keyword against the case's free-text
material ``name`` (case-insensitive substring). A name that matches no
keyword here is not checked -- "never invent material data" means this module
refuses to guess at a family it doesn't recognise, rather than silently
approving or silently rejecting it.

Sources (typical published ranges for the material family, not a specific
alloy or temper):
  - Steels (carbon, alloy, stainless), aluminum, titanium, copper, brass,
    bronze, magnesium: Shigley's Mechanical Engineering Design, 10th ed.,
    Table A-5 (nominal E per material) widened to the family's normal alloy
    range per standard engineering handbooks (e.g. ASM Handbook Vol. 2).
  - Cast iron: wide range from Table A-24 owing to graphite flake structure.
  - Engineering thermoplastics (ABS, polycarbonate, nylon/PA, acetal/POM,
    PEEK): typical unfilled-resin datasheet ranges (e.g. MatWeb-style
    material property summaries); glass/carbon-filled grades run higher and
    are intentionally outside these bands (they need their own source, not
    this generic check).
"""
from __future__ import annotations

# keyword (lowercase, matched as a substring of the material name) -> (min, max) E in MPa.
# Order matters only in that the first matching keyword wins, so more specific
# names should be listed before generic ones that could also match them.
MATERIAL_E_BANDS_MPA: tuple[tuple[str, tuple[float, float]], ...] = (
    ("stainless", (180_000.0, 205_000.0)),
    ("steel", (150_000.0, 230_000.0)),
    ("cast iron", (60_000.0, 170_000.0)),
    ("aluminium", (60_000.0, 85_000.0)),
    ("aluminum", (60_000.0, 85_000.0)),
    ("titanium", (95_000.0, 125_000.0)),
    ("brass", (90_000.0, 115_000.0)),
    ("bronze", (95_000.0, 120_000.0)),
    ("copper", (100_000.0, 135_000.0)),
    ("magnesium", (40_000.0, 48_000.0)),
    ("peek", (3_000.0, 4_500.0)),
    ("acetal", (2_500.0, 3_500.0)),
    ("delrin", (2_500.0, 3_500.0)),
    ("polycarbonate", (1_800.0, 2_600.0)),
    ("nylon", (500.0, 4_500.0)),
    ("abs", (1_000.0, 3_000.0)),
)


def find_band(material_name: str) -> tuple[str, float, float] | None:
    """The first (keyword, min_MPa, max_MPa) whose keyword is a substring of
    ``material_name`` (case-insensitive), or ``None`` if nothing matches."""
    name = (material_name or "").strip().lower()
    if not name:
        return None
    for keyword, (lo, hi) in MATERIAL_E_BANDS_MPA:
        if keyword in name:
            return keyword, lo, hi
    return None


def implausible_e(material_name: str, e_mpa: float) -> tuple[str, float, float] | None:
    """Returns (keyword, min_MPa, max_MPa) if ``material_name`` matches a known
    family and ``e_mpa`` falls outside its plausibility band; ``None`` if it
    matches no known family (nothing to check against) or is within band."""
    band = find_band(material_name)
    if band is None:
        return None
    keyword, lo, hi = band
    if lo <= e_mpa <= hi:
        return None
    return band
