"""Closed-form hand calculations used as the mandatory FEA cross-check.

Each formula takes the case's ``inputs`` table plus the material (E in MPa, nu) and returns a
:class:`HandCalc` with the value, unit, the formula as text and its reference. Derivations,
validity ranges and citations are in references/hand-calcs.md. Units: N, mm, MPa, rad.

Standard library only.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


class HandCalcError(ValueError):
    """Unknown formula or missing / invalid inputs."""


@dataclass
class HandCalc:
    value: float
    unit: str
    formula: str
    reference: str
    notes: str = ""


def _need(inputs: dict, *keys: str) -> list[float]:
    missing = [k for k in keys if k not in inputs]
    if missing:
        raise HandCalcError(f"missing hand-calc input(s): {', '.join(missing)}")
    vals = [float(inputs[k]) for k in keys]
    return vals


def _shear_modulus(e: float, nu: float) -> float:
    return e / (2.0 * (1.0 + nu))


def cowper_kappa_rectangle(nu: float) -> float:
    """Timoshenko shear coefficient for a rectangular section (Cowper 1966)."""
    return 10.0 * (1.0 + nu) / (12.0 + 11.0 * nu)


def cantilever_end_load_deflection(inputs: dict, e: float, nu: float) -> HandCalc:
    f, length, b, h = _need(inputs, "force_n", "length_mm", "width_mm", "height_mm")
    inertia = b * h ** 3 / 12.0
    d_eb = f * length ** 3 / (3.0 * e * inertia)
    kappa = cowper_kappa_rectangle(nu)
    d_s = f * length / (kappa * _shear_modulus(e, nu) * b * h)
    include_shear = bool(inputs.get("include_shear", False))
    value = d_eb + d_s if include_shear else d_eb
    return HandCalc(
        value, "mm",
        "Euler-Bernoulli F L^3/(3 E I), I = b h^3/12" + (" + Timoshenko shear F L/(kappa G A)" if include_shear else ""),
        "Gere & Goodno, Mechanics of Materials, cantilever with end load; shear term: Timoshenko beam, "
        "kappa = 10(1+nu)/(12+11nu) (Cowper, J. Appl. Mech. 33 (1966) 335)",
        f"EB = {d_eb:.6g} mm; Timoshenko shear correction = {d_s:.6g} mm ({100 * d_s / d_eb:.2f} % of EB, "
        f"kappa = {kappa:.4f}); {'included' if include_shear else 'NOT included -- expect FEA slightly above EB'}",
    )


def cantilever_bending_stress(inputs: dict, e: float, nu: float) -> HandCalc:
    f, arm, b, h = _need(inputs, "force_n", "lever_arm_mm", "width_mm", "height_mm")
    inertia = b * h ** 3 / 12.0
    return HandCalc(f * arm * (h / 2.0) / inertia, "MPa",
                    "sigma = F a (h/2) / I, I = b h^3/12 (outer-fibre bending stress at lever arm a from the load)",
                    "Euler-Bernoulli flexure formula (any mechanics-of-materials text)")


def simply_supported_center_load_deflection(inputs: dict, e: float, nu: float) -> HandCalc:
    f, span, b, h = _need(inputs, "force_n", "span_mm", "width_mm", "height_mm")
    inertia = b * h ** 3 / 12.0
    return HandCalc(f * span ** 3 / (48.0 * e * inertia), "mm", "F L^3 / (48 E I), I = b h^3/12",
                    "Euler-Bernoulli, simply supported beam with central point load")


def plate_hole_kt_net(d_over_w: float, method: str = "peterson") -> float:
    """Net-section Kt for a central circular hole in a finite-width plate in uniaxial tension."""
    if not 0.0 <= d_over_w < 1.0:
        raise HandCalcError(f"d/W = {d_over_w} outside [0, 1)")
    s = 1.0 - d_over_w
    if method == "peterson":   # Pilkey & Pilkey, Peterson's SCF 3rd ed., Chart 4.1 curve fit
        return 2.0 + 0.284 * s - 0.600 * s ** 2 + 1.32 * s ** 3
    if method == "heywood":    # Heywood (1952)
        return 2.0 + s ** 3
    if method == "roark":      # Young & Budynas, Roark's Formulas for Stress and Strain, 7th ed.,
                                # Table 17.1 case 4a curve fit (m4, review #1: the coefficients were
                                # 3.13/3.66/1.53, rounded from the 7th edition's own 3.140/3.667/1.527)
        return 3.00 - 3.140 * d_over_w + 3.667 * d_over_w ** 2 - 1.527 * d_over_w ** 3
    raise HandCalcError(f"unknown plate-hole Kt method {method!r} (peterson | heywood | roark)")


def plate_hole_tension_peak_stress(inputs: dict, e: float, nu: float) -> HandCalc:
    w, d = _need(inputs, "width_mm", "hole_diameter_mm")
    if "gross_stress_mpa" in inputs:
        s_gross = float(inputs["gross_stress_mpa"])
    else:
        f, t = _need(inputs, "force_n", "thickness_mm")
        s_gross = f / (w * t)
    method = str(inputs.get("method", "peterson"))
    ratio = d / w
    if ratio > 0.6:
        raise HandCalcError(f"d/W = {ratio:.3f} > 0.6: outside the range this skill trusts the curve fits")
    kt = plate_hole_kt_net(ratio, method)
    s_nom = s_gross / (1.0 - ratio)
    spread = [plate_hole_kt_net(ratio, m) for m in ("peterson", "heywood", "roark")]
    return HandCalc(
        kt * s_nom, "MPa",
        f"sigma_max = Kt_n * sigma_nom, sigma_nom = sigma_gross W/(W-d); d/W = {ratio:.3f}, Kt_n({method}) = {kt:.4f}",
        "Pilkey & Pilkey, Peterson's Stress Concentration Factors 3rd ed. (2008) Chart 4.1; Heywood (1952); "
        "Roark's Formulas for Stress and Strain -- see references/hand-calcs.md (plane stress, thin plate)",
        f"sigma_gross = {s_gross:.4g} MPa, sigma_nom(net) = {s_nom:.4g} MPa; Kt_n spread across the three fits "
        f"{min(spread):.4f}..{max(spread):.4f}",
    )


def _tube_j(od: float, id_: float) -> float:
    if not 0.0 <= id_ < od:
        raise HandCalcError(f"need 0 <= inner_diameter_mm < outer_diameter_mm, got {id_}, {od}")
    return math.pi * (od ** 4 - id_ ** 4) / 32.0


def tube_torsion_twist(inputs: dict, e: float, nu: float) -> HandCalc:
    t, length, od = _need(inputs, "torque_nmm", "length_mm", "outer_diameter_mm")
    id_ = float(inputs.get("inner_diameter_mm", 0.0))
    j = _tube_j(od, id_)
    g = _shear_modulus(e, nu)
    return HandCalc(t * length / (g * j), "rad",
                    f"phi = T L / (G J), J = pi (D^4 - d^4)/32 = {j:.6g} mm^4, G = E/(2(1+nu)) = {g:.6g} MPa",
                    "Saint-Venant torsion of a circular shaft/tube (exact in linear elasticity)")


def tube_torsion_peak_von_mises(inputs: dict, e: float, nu: float) -> HandCalc:
    t, od = _need(inputs, "torque_nmm", "outer_diameter_mm")
    id_ = float(inputs.get("inner_diameter_mm", 0.0))
    j = _tube_j(od, id_)
    tau = t * (od / 2.0) / j
    return HandCalc(math.sqrt(3.0) * tau, "MPa",
                    f"sigma_vM = sqrt(3) tau_max, tau_max = T (D/2)/J = {tau:.6g} MPa (pure shear)",
                    "Saint-Venant torsion of a circular shaft/tube; von Mises of pure shear")


def thick_cylinder_internal_pressure_hoop_stress(inputs: dict, e: float, nu: float) -> HandCalc:
    p, ri, ro = _need(inputs, "pressure_mpa", "inner_radius_mm", "outer_radius_mm")
    if not 0.0 < ri < ro:
        raise HandCalcError(f"need 0 < inner_radius_mm < outer_radius_mm, got {ri}, {ro}")
    return HandCalc(p * (ro ** 2 + ri ** 2) / (ro ** 2 - ri ** 2), "MPa",
                    "Lame: sigma_theta(r_i) = p (r_o^2 + r_i^2)/(r_o^2 - r_i^2) (the max principal stress)",
                    "Lame thick-walled cylinder, internal pressure, open ends (Timoshenko & Goodier, "
                    "Theory of Elasticity; Roark thick-walled cylinder table)")


FORMULAS = {
    "cantilever_end_load_deflection": cantilever_end_load_deflection,
    "cantilever_bending_stress": cantilever_bending_stress,
    "simply_supported_center_load_deflection": simply_supported_center_load_deflection,
    "plate_hole_tension_peak_stress": plate_hole_tension_peak_stress,
    "tube_torsion_twist": tube_torsion_twist,
    "tube_torsion_peak_von_mises": tube_torsion_peak_von_mises,
    "thick_cylinder_internal_pressure_hoop_stress": thick_cylinder_internal_pressure_hoop_stress,
}


def evaluate(formula: str, inputs: dict, e: float, nu: float) -> HandCalc:
    """Evaluate a named formula, or ``custom`` (value, unit, expression, reference all required)."""
    if formula == "custom":
        for k in ("value", "unit", "expression", "reference"):
            if k not in inputs:
                raise HandCalcError(f"custom hand calc needs inputs.{k} (value, unit, expression, reference)")
        return HandCalc(float(inputs["value"]), str(inputs["unit"]), str(inputs["expression"]),
                        str(inputs["reference"]), "author-supplied value: re-derive before trusting")
    fn = FORMULAS.get(formula)
    if fn is None:
        raise HandCalcError(f"unknown hand-calc formula {formula!r}; known: {sorted(FORMULAS)} or 'custom'")
    return fn(inputs, e, nu)
