# Simulation -- standards and applicability

Simulation methodology (mesh convergence, hand-calc cross-checks, stated validity limits) is Forge's own discipline (`docs/brief/FORGE-BRIEF.md` §0 "physics in the loop"), not a single external standard. Where a sector-specific functional-safety standard governs the product, its analysis requirements apply on top of Forge's baseline method.

## When a sector standard adds simulation/analysis requirements

| Standard | Current edition (2026-09-25) | Applies when | Source |
|---|---|---|---|
| IEC 61508 | Ed. 2.0, 2010 (Ed.3 at CDV) | Functional-safety programmable-electronic systems needing quantified failure analysis. | R5b §1 |
| ISO 26262 | 2nd edition, 2018 (3rd-edition DIS 2026-08-04) | Automotive functional safety, including FTA/FMEDA-style analysis. | R5b §1 |
| IEC 60601-1 (+ -1-2) | Ed. 3.2 consolidated (2020); Ed.4 in draft, not before ~2029-2031 | Medical electrical equipment safety and EMC (only if the product is a medical device). | R5b §1 |

## What Forge automates

- FEA via gmsh + CalculiX (`running-fea`): boundary conditions stated explicitly, a hand-calc sanity check, a mesh/step convergence study, and safety factors computed and reported with units.
- Circuit simulation via ngspice for critical nets (`designing-circuits`), compared numerically against the spec.
- Recording every simulation result at evidence level L2 (simulated, with sanity check) until independently reviewed (L3) or physically tested (L4).

## What needs a qualified human

- Setting the boundary conditions and load cases themselves -- Forge checks that they are *stated*, not that they are the *right* ones for the product's actual use case.
- Any claim of "validated" from simulation alone -- L2 is the ceiling for simulation; L4 needs physical test data.
- Sector-specific analysis required by IEC 61508 / ISO 26262 / IEC 60601-1 (FMEDA, fault-tree quantification, etc.) is reviewed by an engineer qualified in that standard, not generated unsupervised.
