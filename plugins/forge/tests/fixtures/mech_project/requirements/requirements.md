# Requirements -- fixture project (dev-board-style enclosure)

Fixture only, for `plugins/forge/tests/mech`'s end-to-end PASS/seeded-FAIL
demonstration of `verifying-geometry` and `checking-dfm`. Not a real product.

**REQ-MECH-001** The enclosure base shall be a valid, watertight solid.
Rationale: unprintable/unmanufacturable geometry fails downstream regardless of dimensions.
Verify: analysis

**REQ-MECH-002** The enclosure base shall fit within a 60.0 x 40.0 x 20.0 mm +-0.1 mm envelope.
Rationale: must fit the target product footprint (params/params.toml enclosure.*).
Verify: analysis

**REQ-MECH-003** The enclosure base shall have a volume and mass consistent with the modeled geometry within +-5%.
Rationale: catches a missing/oversized feature or a boolean that silently failed to apply.
Verify: analysis

**REQ-MECH-004** The enclosure base wall shall be at least 1.9 mm thick everywhere sampled.
Rationale: params/params.toml enclosure.wall_thickness = 2.0 mm +-0.1 mm; 1.9 mm is the tolerance floor.
Verify: analysis

**REQ-MECH-005** The lid shall clear the enclosure base by at least 0.2 mm with zero interference.
Rationale: params/params.toml enclosure.lid_clearance = 0.3 mm; prevents the lid binding on assembly.
Verify: analysis

**REQ-MECH-006** Every measured fillet/hole-wall radius on the enclosure base shall be at least 1.0 mm.
Rationale: fixture-level check of geometry.min_radius; see verifying-geometry/references/algorithms.md
for the known limitation that this also measures hole-wall radii, not fillets only.
Verify: analysis

**REQ-MECH-007** Every mounting hole shall be at least 3.0 mm from the base's outer edge (wall-to-edge).
Rationale: params/params.toml mounting.hole_inset = 6.0 mm, hole radius 1.5 mm -> 4.5 mm nominal margin.
Verify: analysis

**REQ-MFG-001** The enclosure base wall shall meet the FDM unsupported-wall DFM minimum.
Rationale: checking-dfm/references/rules/fdm.toml wall_min_unsupported_mm (1.2 mm, R5d-sourced).
Verify: analysis

**REQ-MFG-002** Every mounting hole shall meet the FDM minimum hole-diameter DFM rule.
Rationale: checking-dfm/references/rules/fdm.toml hole_min_diameter_mm (2.0 mm, R5d-sourced).
Verify: analysis

**REQ-MFG-003** The lid-to-base clearance shall meet the FDM minimum moving-clearance DFM rule.
Rationale: checking-dfm/references/rules/fdm.toml clearance_moving_mm (1.0 mm, R5d-sourced). The fixture's
0.3 mm lid clearance is deliberately below this to demonstrate a real DFM (not geometry-spec) failure.
Verify: analysis

**REQ-MECH-010** A PC (Makrolon) snap-fit latch arm's root strain shall stay within the material's allowable strain.
Rationale: checking-dfm/references/rules/snap_fit.toml pc_makrolon (4.0%, R5d-sourced).
Verify: analysis
