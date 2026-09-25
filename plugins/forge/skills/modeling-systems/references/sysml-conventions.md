# SysML v2 textual conventions and a worked example

Tooling: `spec42` (v0.53.1, MIT, pinned per ADR-001 §8/D12/T6) — the SysML v2
Pilot-compatible checker Forge uses in CI. It bundles the standard library,
so `model/**/*.sysml` never needs to vendor kernel types.

## Minimal worked example: `model/system.sysml`

```sysml
package HydroSenseModel {
    import ScalarValues::*;

    part def Sensor {
        attribute mass : Real;
        attribute powerBudget : Real;

        port def MeasurePort;
        port measure : MeasurePort;
    }

    part def Battery {
        attribute capacityWh : Real;
    }

    part hydroSense : Sensor {
        attribute :>> mass = 80.0;         // grams -- mirrors params.toml sensor.mass
        attribute :>> powerBudget = 0.15;  // watts, average
    }

    part battery : Battery {
        attribute :>> capacityWh = 3.7;
    }

    connection powerLink connect hydroSense to battery;
}
```

Run:
```
spec42 check model/system.sysml --warnings-as-errors
```
Zero errors, zero warnings is the bar. `forge-python skills/modeling-systems/scripts/verify.py --project .` wraps this, writes `out/verify/systems.sysml_check.json`, and turns every diagnostic into a check-result measurement with a remediation string.

## Diagnostic severities (from `spec42 check --format json`)

| Severity | Meaning | Treated as |
|---|---|---|
| 1 | error (parse or hard semantic failure, e.g. `missing_closing_brace`) | fail |
| 2 | warning (e.g. `unresolved_type_reference`) | fail (because `--warnings-as-errors` is always on) |
| 3 | information | ignored (not surfaced as a measurement) |
| 4 | hint | ignored |

## Common fixes

- **`unresolved_type_reference`**: the referenced type isn't imported or isn't spelled exactly as declared. Add an `import` or fix the spelling; don't redefine a type with a new name just to make the reference resolve.
- **`missing_closing_brace`**: count braces top to bottom; a `part def { ... ` block left open cascades into confusing downstream errors — fix the first reported error first and re-run.
- **Budget mismatch with `params.toml`**: if a value here disagrees with `params/params.toml`, `params.toml` is the source of truth (CONTRACTS §2) — update the model to match, or raise the mismatch to whichever agent owns the params entry, never silently pick one.

## Keeping the model and `params.toml` honest

The model's `attribute` values are a second surface for the same numbers `params.toml` already owns. Prefer expressing them as literal values that a human/script can diff against `params.toml` in review (spec42 doesn't read TOML), and note the mirrored source, e.g. `// mirrors params.toml enclosure.wall_thickness` as a comment next to the value.
