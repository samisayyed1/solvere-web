# `requirements/dfm/<part>.toml` schema

One file per part. `scripts/verify.py` applies a process's rule table
(`references/rules/<process>.toml`) to `forge_cad` measurements, plus any
`[[snap_fit]]` entries against `references/rules/snap_fit.toml`.

```toml
[part]
name = "lid"
module = "cad/lid.py"
process = "fdm"                              # selects references/rules/fdm.toml
nominal_wall_param = "enclosure.wall_thickness"  # required only if a ratio-based rule is used
pull_direction = [0, 0, 1]                    # optional, default [0,0,1]

[[check]]
rule = "wall_min_unsupported_mm"              # id from references/rules/fdm.toml
requirement = "REQ-MFG-001"
# optional per-family overrides, same meaning as verifying-geometry's schema:
#   sample_count, faces, other_module, boundary_face

[[check]]
rule = "hole_min_diameter_mm"
requirement = "REQ-MFG-002"

[[snap_fit]]
name = "lid_latch"
requirement = "REQ-MECH-010"
material = "pc_makrolon"        # id from references/rules/snap_fit.toml
deflection_mm = 2.0
length_mm = 15.0
thickness_mm = 1.5
taper = "constant"              # constant | tapered_half_thickness | tapered_width_quarter
frequent = false                # true applies the repeated-use allowable (material value or the 60% default factor)
```

**Rule `check_family`.** Every rule in a `references/rules/*.toml` table
names the `forge_cad` measurement it maps to (`geometry.min_wall`,
`geometry.hole_diameter`, `geometry.clearance`, `geometry.draft`,
`geometry.min_radius`, `geometry.hole_edge`, `geometry.boss_rib`) or
`"unsupported"` for a real DFM number that has no matching measurement yet
(e.g. bend relief, K-factor, thread depth ratios -- see each rule table's
`conflict` field). Referencing an `unsupported` rule in a spec is a hard
error, not a skip -- fix the spec to reference a checkable rule, or check
that limit by hand and record it as a manual finding instead.

**Ratio rules.** A rule with `comparison = "min_ratio_of_wall"` or
`"max_ratio_of_wall"` (e.g. rib/boss thickness ratios, sheet-metal
bend-radius-to-thickness) is resolved to an absolute mm/deg limit by
multiplying `value_ratio` by `[part].nominal_wall_param`'s value in
`params/params.toml` -- the spec must set `nominal_wall_param` if it uses
any such rule.

**Conservative-value policy.** Every rule table's numbers trace to
`docs/research/R5c-dfm-molding-cnc-sheetmetal.md` /
`R5d-dfm-additive-snapfit-pcb.md`. Where sources disagreed, the table keeps
the conservative (stricter/safer) value and records the discarded
alternative in `conflict` -- read that field before trusting a near-limit
result, since a project with unusual tooling or material may legitimately
want the less conservative figure.
