# Assumptions

Every assumption made in place of a measurement, datasheet value or confirmed requirement. Retire an assumption by replacing it with `datasheet`, `measured` or `verified` evidence (see `params/params.toml` `status`), and move the row to "Retired" with the evidence id.

An assumption is not a guess made silently -- when a requirement is ambiguous, conflicting, or missing a number, ask before assuming (see `AGENTS.md` rule 8).

## Open

| ID | Assumption | Where used | Risk if wrong | Owner |
|---|---|---|---|---|
| A-001 | Enclosure wall thickness of 2.0 mm is stiff enough without a stiffener rib. | `params/params.toml` `enclosure.wall_thickness` | Lid flexes under snap-fit load; reprint with ribs or thicker wall. | mechanical-engineer |

## Retired

| ID | Assumption | Retired by | Date |
|---|---|---|---|
