# Assumptions

Every assumption made in place of a measurement, datasheet value or confirmed requirement. Retire an assumption by replacing it with `datasheet`, `measured` or `verified` evidence (see `params/params.toml` `status`), and move the row to "Retired" with the evidence id.

An assumption is not a guess made silently -- when a requirement is ambiguous, conflicting, or missing a number, ask before assuming (see `AGENTS.md` rule 8). Each row names the open question (Q-xx in `reviews/G0.md`) that retires it, or the test that does. Source short names (DS, MDS, Wiki, XIAO, FDA1, Web) are defined in `docs/sources/README.md`.

## Open

| ID | Assumption | Status | Where used | Risk if wrong | Retired by | Owner |
|---|---|---|---|---|---|---|
| A-001 | Static pull test at 4 x installed weight held for 60 s is enough retention margin for the base plate and the shell. No source; placeholder until a qualified human sets the load. | assumed | `mount.retention_load_factor`, `mount.retention_hold_time`; REQ-MECH-004, -005, -011 | Pod or shell falls on a person (R-005). | Q-17 | systems-engineer |
| A-002 | The MR60FDA2 tolerates the same 5° tilt as the sibling MR60FDA1 (FDA1 wiki: horizontal deviation ≤5°). No MR60FDA2 source gives a limit. | assumed | `sensor.level_tolerance`; REQ-MECH-009 | Coverage or fall detection degrades at a tilt the pod allows. | Q-18 (ask Seeed); TP-SYS-001 | systems-engineer |
| A-003 | v1 ambient operating range is 0 °C to 35 °C (bedrooms and living rooms). | assumed | `env.ambient_min`, `env.ambient_max`; REQ-ENV-001, -002, REQ-SAFE-002 | Pod fails or overheats in a room outside the range. | Q-09 | systems-engineer |
| A-004 | The kit's maximum operating temperature is 85 °C, the lowest published component rating (radar module MDS p.4; XIAO). BH1750, WS2812 and carrier-board parts are unrated in the sources. | assumed | `sensor.kit_temp_max`, `thermal.*`; REQ-ENV-002 | Thermal budget too loose; a component drifts or fails. | Q-18 (ask Seeed) | systems-engineer |
| A-005 | The kit carrier board is used as-is; its outline, stack height (with the XIAO fitted) and hole pattern are unpublished and will be measured on a real kit before any CAD. Only the radar module (25 x 31.5 mm, MDS p.3) and XIAO (21 x 17.8 mm) are sourced. | assumed | IF-05 in `docs/interfaces.md` | CAD built on a wrong outline. | Caliper measurement at G1; Q-18 (drawing from Seeed) | mechanical-engineer |
| A-006 | The XIAO ESP32C6 in the kit is the pod's only compute and only radio host, and the pod takes power through the XIAO USB-C connector. | assumed | `model/system.sysml` `SensorKit`; REQ-EMC-002, -005; IF-06, IF-07 | Architecture, power, compliance and cost all change. | Q-01 | systems-engineer |
| A-007 | DS p.6 power figures (0.5 / 0.8 / 1.4 W) are whole-kit input power at the USB-C port, not radar-module-only. | assumed | `sensor.power_*`; `docs/budgets.md` | Power and thermal budgets are low (R-014). | TP-PWR-005 measurement; Q-18 | systems-engineer |
| A-008 | Pod input power stays at or below the DS 1.4 W "with Grove relay" figure with no Grove accessory. | assumed | `power.pod_power_max`; REQ-PWR-005 | Thermal budget exceeded (R-006, R-014). | TP-PWR-005 | systems-engineer |
| A-009 | The USB cable, wall adapter and adhesive raceway are standard retail parts outside the pod; whether they ship in the box and which raceway is used are open. | assumed | IF-06; REQ-MECH-012, REQ-MNT-004; `docs/budgets.md` cost | Cable exit does not fit the raceway; cost scope wrong. | Q-13 | systems-engineer |
| A-010 | One pod per room in v1; no minimum pod spacing is claimed. | assumed | REQ-MNT-002 | Two pods in one large room interfere (R-007). | Q-12 | systems-engineer |
| A-011 | Coverage stays specified as a 3.0 m x 3.0 m square despite the 2 m published sensing radius; the corner tests decide. | assumed | `mount.coverage_side`; REQ-SYS-001, REQ-MNT-001 | Corner falls missed (R-003). | Q-11; TP-SYS-001 | systems-engineer |
| A-012 | The pod makes no medical-device or emergency-alarm claim. | assumed | REQ-SAFE-003 | Regulatory route changes entirely (R-008). | Q-15 | systems-engineer |
| A-013 | Compliance is mapped for US, EU, UK and Canada until the owner names markets. | assumed | `compliance/compliance-map.md`; REQ-EMC-001..-004 | Wrong standards planned. | Q-03 | systems-engineer |
| A-014 | Data stays on the local network (ESPHome / Home Assistant, as the kit ships, DS p.2); no cloud service. | assumed | IF-07; REQ-FW-002, -003 | Cyber and privacy scope larger (CRA, GDPR). | Q-02 | systems-engineer |
| A-015 | Finish is a matte warm white with no colour reference yet. | assumed | `enclosure.colour`; REQ-UX-001 | Colour rework after G3. | Q-04 | industrial-designer |
| A-016 | The production BOM ceiling is compared at the Seeed 10+ price tier (the only tier published) and covers the pod only (no cable, adapter, raceway or packaging). | assumed | `cost.production_bom_max`; REQ-COST-002 | BOM target judged against the wrong volume and scope (R-002). | Q-10 | systems-engineer |

## Retired

| ID | Assumption | Retired by | Date |
|---|---|---|---|

## Replaced at G0 (2026-09-25, source re-verification)

These assumptions from the earlier G0 draft were replaced by sourced values when the sources were downloaded; they are listed so nothing is lost:

- Radar frequency "60 GHz nominal, band unpublished, FDA1 gives 58-63.5 GHz": now `sensor.freq_min` 58 GHz, `sensor.freq_max` 62 GHz, `sensor.freq_centre` 60 GHz (MDS p.4, p.12).
- Kit maximum operating temperature "60 °C from the FDA1 wiki": now radar module 85 °C (MDS p.4) and XIAO 85 °C (XIAO); the kit-level value is A-004.
- Board outline "47 x 29 mm estimated from a Seeed ruler photo": the photo is not on the published page and was never measured; dropped, see A-005.
- Radome "no Seeed guidance published": MDS §8 gives radome rules; now REQ-MECH-013 and REQ-MECH-014.
- Enclosure wall "2.0 mm chosen for stiffness" and natural-convection coefficient "5 W/(m²K)": unsourced design choices, removed from G0 params (wall is chosen at G1 within `mfg.fdm.min_wall`; the thermal budget now uses an allowed thermal resistance instead).
