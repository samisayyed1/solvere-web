# Hand-calc library (`scripts/handcalc.py`)

Every general case declares at least one `[[hand_calc]]`. Units are N, mm, MPa and rad, and G = E / (2(1 + ν)).

- **Named formulas** take their `inputs` table plus E and ν from the case material.
- **`formula = "custom"`** requires `value`, `unit`, `expression` and `reference`. The report marks it "author-supplied value: re-derive before trusting". Use it only when none of the named formulas fits, and derive it where a reviewer can check it.

**Citation honesty.**
- The formulas below are standard.
- For the plate-with-hole fits, the page, chart and equation numbers come from memory and were **not** re-read for this build. They are marked *[ref not re-verified]*.
- The evidence that the Kt value is right is independent:
  - the three published fits agree to 0.43 % at d/W = 0.2;
  - all three reach the Kirsch infinite-plate limit Kt = 3 as d/W → 0;
  - FEA with the hole refined lands within 1 % of them (see below).
- Before an L3 review, have someone check the chart numbers against the physical book.

## cantilever_end_load_deflection

Inputs: `force_n`, `length_mm`, `width_mm` (b), `height_mm` (h); optional `include_shear` (default false).

- δ_EB = F L³ / (3 E I), with I = b h³ / 12 (Euler–Bernoulli).
- Shear correction (Timoshenko): δ_s = F L / (κ G b h), with κ = 10(1 + ν)/(12 + 11ν) for a rectangle (Cowper 1966, *J. Appl. Mech.* 33, 335).
- The report always states δ_s and its percentage of δ_EB. For L/h = 10 and ν = 0.3 it is **0.77 %**.
- Expect the 3-D FEA of a fully clamped root to land between EB and EB + shear. The clamp suppresses Poisson contraction and warping at the root, which slightly stiffens the model.
- Reference case: 100 × 10 × 10 mm steel, F = 100 N.
  - δ_EB = 0.190476 mm; tet10 FEA = 0.190442 mm (**−0.018 %**); converged 0.065 %.

## cantilever_bending_stress

Inputs: `force_n`, `lever_arm_mm` (a, distance from the load to the section), `width_mm`, `height_mm`.

- σ = F a (h/2) / I, the outer-fibre flexure stress.
- Use it at the edge of a declared root-exclusion zone: 10 mm from the root gives a = 90 mm and σ = 54.0 MPa. FEA gave 54.10 MPa (**+0.19 %**) at x = 10.007 mm.

## simply_supported_center_load_deflection

Inputs: `force_n`, `span_mm`, `width_mm`, `height_mm`. δ = F L³ / (48 E I). No known-answer test covers it; it is formula-level only.

## plate_hole_tension_peak_stress: finite-width plate, central circular hole, uniaxial tension

Inputs:
- `width_mm` (W, the FULL plate width);
- `hole_diameter_mm` (d);
- either `gross_stress_mpa`, or `force_n` with `thickness_mm`;
- optional `method` = `peterson` (default) | `heywood` | `roark`.

**Derivation.**
- The load P acts over the gross section W t, so σ_gross = P / (W t).
- The net (ligament) section through the hole centre is (W − d) t, so the nominal net stress is σ_nom = P / ((W − d) t) = σ_gross · W / (W − d).
- The peak stress is at the hole edge, on the net section (θ = ±90° from the load axis): σ_max = K_tn · σ_nom.
- K_tn is a function of d/W only, for a thin plate in plane stress:

| method | K_tn(d/W), s = 1 − d/W | source |
|---|---|---|
| peterson | 2 + 0.284 s − 0.600 s² + 1.32 s³ | Pilkey & Pilkey, *Peterson's Stress Concentration Factors*, 3rd ed. (Wiley 2008), Chart 4.1 curve fit (after Howland 1930) *[ref not re-verified]* |
| heywood | 2 + s³ | Heywood, *Designing by Photoelasticity* (Chapman & Hall 1952) *[ref not re-verified]* |
| roark | 3.00 − 3.13(d/W) + 3.66(d/W)² − 1.53(d/W)³ | Young & Budynas, *Roark's Formulas for Stress and Strain*, stress-concentration table, "central circular hole in a finite-width plate, uniaxial tension" *[ref not re-verified]* |

**Limits.**
- All three give K_tn → 3 as d/W → 0. That is Kirsch's (1898) infinite-plate value, σ_max = 3σ.
- The skill refuses d/W > 0.6, where the fits diverge.
- They are 2-D (plane-stress) results. In a plate of finite thickness the mid-plane peak rises slightly above plane stress as t/d grows. The effect is small at t/d = 0.2 and is **not** quantified here.

**Known-answer case (the test).**
- Plate: W = 50 mm, d = 10 mm, so **d/W = 0.20**, and t = 2 mm (t/d = 0.2).
- Model: a 1/8 model (100 × 25 × 1 mm) with symmetry on x = 0, y = 0 and z = 0.
- Load: σ_gross = 50 MPa (1250 N on the 25 mm² end face), so σ_nom = 62.5 MPa.
- Hand calc: K_tn(peterson) = 2.5190, so **σ_max = 157.44 MPa**. The spread across the three fits is 2.5082–2.5190 (0.43 %).
- FEA peak max-principal = **158.89 MPa (+0.92 %)** at x = 0.05, y = 5.000, z = 0.12 mm. That is the hole edge on the net section, as theory says.
- Mesh: 26 947 nodes; peak converged to 0.03 %.
- The test tolerance is 10 % and the result must also be < 3 %.

## tube_torsion_twist / tube_torsion_peak_von_mises: Saint-Venant torsion of a circular tube

Inputs: `torque_nmm`, `length_mm` (twist only), `outer_diameter_mm` (D), optional `inner_diameter_mm` (d, default 0 = solid shaft).

- J = π (D⁴ − d⁴)/32.
- Twist: φ = T L / (G J).
- Shear: τ_max = T (D/2) / J.
- Von Mises of pure shear: σ_vM = √3 τ_max.
- The solution is exact in linear elasticity for circular sections: no warping, so a fully clamped end is exact. The `torque` load applies the matching traction, τ ∝ r. FEA therefore has no end-effect excuse.
- Known-answer case: Ø20/Ø16 × 100 mm steel tube, T = 100 N·m.
  - φ = 0.013350 rad; FEA face rotation −0.0001 %.
  - σ_vM = 186.76 MPa; FEA 187.06 MPa (**+0.16 %**).

## thick_cylinder_internal_pressure_hoop_stress: Lamé, open ends

Inputs: `pressure_mpa` (p), `inner_radius_mm` (a), `outer_radius_mm` (b).

- σθ(a) = p (b² + a²)/(b² − a²). This is the largest principal stress; σr(a) = −p and σz = 0 (open ends).
- Source: Lamé; Timoshenko & Goodier, *Theory of Elasticity*.
- Known-answer case: a = 10, b = 15, L = 20 mm quarter model, p = 50 MPa.
  - σθ = 130.0 MPa; FEA 131.14 MPa (**+0.87 %**).
  - The pressure resultant on the quarter bore (p a L = 10 000 N per axis) matches the reactions to 0.001 %.
  - This case also proves that the pressure acts along the *outward* normal. An inward normal would make the hoop stress compressive.
