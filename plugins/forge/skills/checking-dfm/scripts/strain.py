"""Snap-fit root strain from the cantilever deflection formula (R5d, Covestro
snap-fit guide Table 1, p.9): ``y = k * eps * L^2 / h``, rearranged for strain::

    eps = h * y / (k * L^2)

``y``: tip deflection [mm]. ``L``: beam length [mm]. ``h``: beam thickness at
the root [mm]. ``k``: 0.67 for a constant rectangular section, 1.09 if the
thickness is tapered to h/2 at the tip, 0.86 if the width is tapered to b/4 --
tapering trades more allowed deflection for the same root strain (R5d:
"thickness tapered to half at the tip allows more than 60% extra deflection").

This is the standard first-order cantilever beam estimate; it does not include
BASF's short-arm correction factor Q (R5d: "plain beam formulas under-predict
root strain for short arms, where the wall also flexes... Q ~ 1 once
length/thickness is above about 10:1") -- callers should treat a strain result
for L/h < 10 as an underestimate and add margin, per that same source.
"""

from __future__ import annotations

__all__ = ["K_FACTORS", "root_strain", "short_arm_warning"]

K_FACTORS = {
    "constant": 0.67,
    "tapered_half_thickness": 1.09,
    "tapered_width_quarter": 0.86,
}


def root_strain(*, deflection_mm: float, length_mm: float, thickness_mm: float,
                 taper: str = "constant") -> float:
    """Root outer-fibre strain (fraction, e.g. 0.04 == 4%) for a cantilever
    snap-fit arm. Raises ``ValueError`` for a non-physical input (L<=0)."""
    if length_mm <= 0:
        raise ValueError("length_mm must be > 0")
    if thickness_mm <= 0:
        raise ValueError("thickness_mm must be > 0")
    if taper not in K_FACTORS:
        raise ValueError(f"taper must be one of {sorted(K_FACTORS)}, got {taper!r}")
    k = K_FACTORS[taper]
    return (thickness_mm * deflection_mm) / (k * length_mm ** 2)


def short_arm_warning(*, length_mm: float, thickness_mm: float, threshold: float = 10.0) -> str | None:
    """Non-``None`` when L/h is low enough that BASF's short-arm correction
    (R5d) means the plain-beam strain estimate likely under-predicts the true
    root strain."""
    ratio = length_mm / thickness_mm
    if ratio < threshold:
        return (f"length/thickness = {ratio:.2f} < {threshold}: BASF's short-arm correction (R5d) "
                "applies here -- the plain cantilever formula likely under-predicts root strain; "
                "treat this result as optimistic and add margin.")
    return None
