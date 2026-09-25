# `analysis/spice/<name>.limits.toml` — sidecar format

Every `analysis/spice/<name>.cir` that `scripts/verify.py` checks needs a sidecar
`analysis/spice/<name>.limits.toml` declaring what a passing simulation looks like.
Values are not invented by the check script — they come from the requirement or the
component datasheet, and belong in `params/params.toml` first; the limits file just
restates them for the simulation.

```toml
# analysis/spice/regulator.limits.toml
[[measurement]]
name = "vout_dc"                 # must match a .meas result name in the .cir
unit = "V"
equals = 3.3
tol = 0.066                       # 3.3 V +/- 2%
requirement = "REQ-ELEC-010"
remediation = "vout_dc must be 3.3 V +/- 2% (params.regulator.vout); check the feedback divider."

[[measurement]]
name = "ripple_pp"
unit = "V"
max = 0.05
requirement = "REQ-ELEC-011"

[[measurement]]
name = "dissipation_w"
unit = "W"
max = 0.35
requirement = "REQ-ELEC-012"
remediation = "Regulator dissipation exceeds the package's thermal budget; add a heatsink pad or pick a switcher."
```

- `name` must exactly match a `.meas` result name emitted by the `.cir`'s `.control`
  block (`meas tran vout_dc avg v(out) from=2m to=5m`, for example).
- Give either `min`/`max`, or `equals`+`tol` (both use `forge.checkresult.Check.measure`'s
  own limit semantics — see `plugins/forge/lib/forge/checkresult.py`).
- **`unit` may be a base SPICE unit (`V`, `A`, `W`, `s`, `Hz`, `F`, `H`, `Ohm`) or that
  unit with exactly one SI prefix (`p`/`n`/`u`/`µ`/`m`/`k`/`M`/`G`/`T`), or `"1"` for
  unitless.** ngspice's own `.meas` results are always printed in the *base* unit — SPICE
  itself has no notion of "mV". `min`/`max`/`equals`/`tol` are read in whatever unit you
  declared, and the script converts the raw ngspice value into that unit before comparing
  (`unit = "mV", max = 40` against a 0.05 V ripple compares the converted 49.99 mV to 40,
  not the raw 0.0499923). Any other unit string (`"Vrms"`, `"dB"`, a typo) is a hard ERROR,
  never silently treated as the base unit.
- `requirement` should cite a `REQ-<AREA>-<NNN>` id from `requirements/requirements.md`.
- `remediation` is optional; if omitted, the script writes a generic one. Prefer a
  specific one that names the fix.

## Why the sandbox confines writes to `out/verify/` only, not `/tmp`

ngspice's own C-library scratch calls (`tmpfile()`) resolve to `$TMPDIR`, which on
macOS is a per-user directory under `/private/var/folders/...`. Granting `srt`
`allowWrite: ["/tmp"]` looks narrow but is **not**, because a project checked out
under `/tmp/...` (common in CI and in this repo's own tests) would then have its
*entire tree* writable, not just `out/`. `scripts/verify.py` instead points
`TMPDIR` at a scratch directory *inside* `out/verify/` for the duration of the run,
so `allowWrite` can name exactly one directory — `out/verify/` — and nothing else,
matching CONTRACTS.md §9's "write only to `out/`."

## Why the netlist scan happens before any subprocess runs

ngspice registers a `shell` front-end command unconditionally; `-n` only skips
`.spiceinit`, not `shell` (ADR-001 D11, `docs/research/CROSSCHECK.md` C17). Text-scanning
every `.control ... .endc` block for a `shell` command is a second, cheap layer on top
of the OS sandbox — never the only one, and never skipped because "the sandbox should
catch it anyway."
