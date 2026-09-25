# Mesh convergence and stress singularities

## The convergence study (mandatory, ≥ 3 levels)

`[mesh].sizes_mm` lists global maximum element sizes h₁ > h₂ > h₃ (…).

- **Refinement ratio.** Each step must shrink h by a ratio of at least 1.2. Smaller steps make anything look converged, so they are refused. Roache's grid-convergence-index guidance asks for ≥ 1.3.
- **Refine zones.** A `[[refine]]` zone sets the local size to `size_factor × h` within `dist_min_mm` of the selected faces, growing linearly to h at `dist_max_mm` (gmsh `Distance` + `Threshold` fields). Because it scales with h, every level refines everywhere by the same ratio.

For every quantity of interest (each hand-calc quantity, plus the assessed peak von Mises that sets the safety factor), the report gives:

- **% change**: |f₃ − f₂| / |f₂| × 100 between the two finest levels. The case fails if it is above `convergence_tol_pct`, or above `stress_convergence_tol_pct` for stress quantities.
- **Observed order**: p = ln(|f₂ − f₁| / |f₃ − f₂|) / ln r, with r the geometric-mean refinement ratio. It is only defined when the two differences have the same sign.
- **Richardson estimate**: f₃ + (f₃ − f₂)/(r^p − 1), plus GCI_fine = 1.25 |ε| / (r^p − 1), when p > 0. These are reported for context only and never used to pass a case.

## Singularity detection

A re-entrant corner, a point load, a knife-edge support or the edge of a fully clamped face has infinite elastic stress. Its FE "peak" grows without bound as the mesh is refined. Such a number is a property of the mesh, not of the part, and must not become a safety factor.

**Hot-spot test.** For each tracked point P, take the maximum von Mises inside a **fixed** ball of radius ρ = ½ h₁ around P, at every level.
- If the field is bounded near P, this converges to the true maximum in the ball.
- If there is a singularity at P, it grows as nodes approach P.

A series is **diverging**, and a singularity is suspected, when all of these hold:
- it is not converged within tolerance;
- it rises monotonically (f₁ < f₂ < f₃);
- the observed order p < 0.25, i.e. the differences are not shrinking.

A singularity of strength λ gives p ≈ −λ: about −0.5 at a crack tip, −2 or so under a point load. A smooth under-resolved peak gives p > 0.

**What is tracked:**
- the assessed peak location at the finest level;
- the global peak (including exclusion zones), for the record;
- every `point_force` node.

If any tracked point *inside the assessed region* diverges, `stress_singularity_suspected = true` and the check fails at L1.

**Measured on the known-answer cases:**

| case | series (MPa) | p | verdict |
|---|---|---|---|
| point load, 100 N on the cantilever top | 2.59 → 13.98 → 29.92 | −0.97 | diverging (flagged) |
| plate hole, refined | peak converged 0.02 % | | converged |
| tube torsion | 188.05 → 187.25 → 187.06 | 3.7 | converged |
| Lamé cylinder | 161.67 → 161.51 → 161.29 | | converged |

## What to do with a flagged singularity

1. **Model the real thing**: a fillet radius instead of a sharp corner, a load patch instead of a point, a compliant support instead of a perfect clamp. Then the stress is real and converges.
2. **Or exclude it, if it cannot cause failure.**
   - Declare `[stress].exclude = [{ faces = …, distance_mm = …, reason = "…" }]`. The reason is mandatory, at least 10 characters.
   - Nodes within the distance of those faces do not count toward the safety factor.
   - The unexcluded peak and its trend are still printed in the report, marked "NOT used for the safety factor".
   - The Saint-Venant distance is typically one section depth.
   - Excluding a zone is an engineering claim ("this stress is not physical, or not failure-relevant") and a reviewer must be able to see it. For fatigue or brittle materials, excluding a real notch is wrong.

## The seeded-wrong cases that prove these checks can fail

| case | expected result |
|---|---|
| coarse plate with a hole, no refinement, sizes 8/5/3 mm | peak σ₁ 145.4 → 136.3 → 148.9 MPa, change 9.2 % > 2 %: FAIL, L1 |
| 100 N point load on the cantilever | singularity flagged: FAIL, L1, located "0.00 mm from 'load:poke'" |
| wrong hand calc (h = 11 mm instead of 10) | +33 % vs a ±3 % tolerance: FAIL, L1 |
| under-constrained (one symmetry plane only) | ERROR, exit 2, before solving (see SKILL.md) |
