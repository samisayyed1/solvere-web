---
paths:
  - "analysis/**"
---

# Simulation

- Geometry is not function. Every physical requirement claimed as met needs analysis, FEA, circuit simulation, firmware simulation or HIL -- not just a model that looks right.
- Every simulation states: boundary conditions, a hand-calc sanity check, a mesh/step convergence check, safety factors, and validity limits (what the model does *not* cover). Missing any of these means the result is not yet trustworthy.
- Run `forge-python skills/running-fea/scripts/verify.py --project . --changed analysis/ --fast` (gmsh + CalculiX) and cite `out/verify/*.json`, not just a picture.
- A converged mesh/step is required before a result is quoted; state the convergence metric and the step at which it stabilized.
- Evidence level is L2 (simulated, with a hand-calc and convergence check) until independently reviewed (L3) or physically tested (L4) -- never claim higher.
- Standards and method references: `docs/standards/simulation.md`.
