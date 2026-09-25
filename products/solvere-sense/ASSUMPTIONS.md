# Assumptions

Every assumption made in place of a measurement, datasheet value or confirmed requirement. Retire an assumption by replacing it with `datasheet`, `measured` or `verified` evidence (see `params/params.toml` `status`), and move the row to "Retired" with the evidence id.

An assumption is not a guess made silently -- when a requirement is ambiguous, conflicting, or missing a number, ask before assuming (see `AGENTS.md` rule 8). Each row names the open question (Q-xx in `reviews/G0.md`) that retires it, or the test that does. Source short names (DS, MDS, Wiki, XIAO, FDA1, Web) are defined in `docs/sources/README.md`.

## Open

| ID | Assumption | Status | Where used | Risk if wrong | Retired by | Owner |
|---|---|---|---|---|---|---|
| A-001 | PLACEHOLDER through G0 only (Owner round 2): static pull test at 4 x installed weight held for 60 s. No source. | assumed | `mount.retention_load_factor`, `mount.retention_hold_time`; REQ-MECH-004, -005, -011 | Pod or shell falls on a person (R-005). | REQ-MECH-015 before G2: measured weight x a sourced safety factor (Q-17) | systems-engineer |
| A-002 | The MR60FDA2 tolerates the same 5° tilt as the sibling MR60FDA1 (FDA1 wiki: horizontal deviation ≤5°). No MR60FDA2 source gives a limit. | assumed | `sensor.level_tolerance`; REQ-MECH-009 | Coverage or fall-event output degrades at a tilt the pod allows. | Seeed answer (`docs/seeed-questions-draft.md`); TP-SYS-001 | systems-engineer |
| A-004 | The kit's maximum operating temperature is 85 °C, the lowest published component rating (radar module MDS p.4; XIAO). BH1750, WS2812 and carrier-board parts are unrated in the sources. | assumed | `sensor.kit_temp_max`, `thermal.*`; REQ-ENV-002 | Thermal budget too loose; a component drifts or fails. | Seeed answer; TP-ENV-002 | systems-engineer |
| A-005 | The kit carrier board is used as-is; its outline, stack height, hole pattern and LED position are unpublished and are measured on a real kit before any CAD. Only the radar module (25 x 31.5 mm, MDS p.3) and XIAO (21 x 17.8 mm) are sourced. | assumed | IF-05, IF-09 | CAD built on a wrong outline; light pipe misplaced. | Caliper measurement at G1; Seeed drawing | mechanical-engineer |
| A-007 | DS p.6 power figures (0.5 / 0.8 / 1.4 W) are whole-kit input power at the USB-C port, not radar-module-only. | assumed | `sensor.power_*`; `docs/budgets.md` | Power and thermal budgets are low (R-014). | TP-PWR-005; Seeed answer | systems-engineer |
| A-008 | Pod input power stays at or below the DS 1.4 W "with Grove relay" figure with no Grove accessory. | assumed | `power.pod_power_max`; REQ-PWR-005 | Thermal budget exceeded (R-006, R-014). | TP-PWR-005 | systems-engineer |
| A-009 | USB-C cable, wall adapter and adhesive raceway are standard retail parts outside the pod; whether they ship in the box is an open product decision; their prices are to be quoted (none sourced). | assumed | IF-06; REQ-MECH-012, REQ-MNT-004; `docs/budgets.md` cost note | Unit cost and packaging wrong; cable exit does not fit the raceway. | Q-13; dated quotes in `bom/` | systems-engineer |
| A-017 | The O-ring cord gland can be sized with ARSDG Table A (written for moulded O-rings); ARSDG gives no separate rule for spliced cord, and the cross-section is chosen at G1. | assumed | `gasket.*`; REQ-MECH-017 | Splice leaks; IPX4 fails. | Cord supplier's datasheet at G1; TP-MECH-018 | mechanical-engineer |

## Retired

| ID | Assumption | Retired by | Date |
|---|---|---|---|
| A-003 | Ambient 0 °C to 35 °C | Owner round 2 (Q-09): 0 °C to 40 °C, now `env.*` as an owner requirement | 2026-09-25 |
| A-006 | XIAO ESP32C6 is the only compute and radio | Owner round 2 (Q-01): kit as-is | 2026-09-25 |
| A-010 | One pod per room | Owner round 2 (Q-12): up to 2 pods per room (REQ-SYS-003, REQ-MNT-006) | 2026-09-25 |
| A-011 | Coverage stays 3 m x 3 m | Owner round 2 (Q-11): keep 3 x 3 m, 2 m radius fallback | 2026-09-25 |
| A-012 | No medical-device or emergency-alarm claim | Owner round 2 (Q-15): home-automation use, strict (REQ-SAFE-003, -004) | 2026-09-25 |
| A-013 | Compliance mapped for US, EU, UK, Canada | Owner round 2 (Q-03): map all four, sell nowhere until a qualified human confirms | 2026-09-25 |
| A-014 | Data stays on the local network | Owner round 2 (Q-02): local Wi-Fi to Home Assistant | 2026-09-25 |
| A-015 | Matte warm white with no colour reference | Owner round 2 (Q-04): colour matched at the demo stage | 2026-09-25 |
| A-016 | Production BOM at the 10+ tier, pod only | Owner round 2 (Q-10): pod only (shell, kit, fixings) at 10+ unit pricing | 2026-09-25 |

Owner decisions retire an assumption as a requirement, not as evidence: they are L0 (claimed) until tested.

## Replaced at G0 (2026-09-25, source re-verification)

These assumptions from the earlier G0 draft were replaced by sourced values when the sources were downloaded; they are listed so nothing is lost:

- Radar frequency "60 GHz nominal, band unpublished, FDA1 gives 58-63.5 GHz": now `sensor.freq_min` 58 GHz, `sensor.freq_max` 62 GHz, `sensor.freq_centre` 60 GHz (MDS p.4, p.12).
- Kit maximum operating temperature "60 °C from the FDA1 wiki": now radar module 85 °C (MDS p.4) and XIAO 85 °C (XIAO); the kit-level value is A-004.
- Board outline "47 x 29 mm estimated from a Seeed ruler photo": the photo is not on the published page and was never measured; dropped, see A-005.
- Radome "no Seeed guidance published": MDS §8 gives radome rules; now REQ-MECH-013 and REQ-MECH-014.
- Enclosure wall "2.0 mm chosen for stiffness" and natural-convection coefficient "5 W/(m²K)": unsourced design choices, removed from G0 params (wall is chosen at G1 within `mfg.fdm.min_wall`; the thermal budget now uses an allowed thermal resistance instead).
