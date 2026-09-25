# SPEC.md template

Copy this structure into the project's `SPEC.md`. Every section should
trace to something a stakeholder actually said; mark anything you filled
in without asking as `[ASSUMED -- confirm]` and mirror it into
`ASSUMPTIONS.md`.

```markdown
# <Product name> -- SPEC

## Problem & users
Who has this problem, in their own words if possible. What they do today
without this product.

## Jobs-to-be-done
- JTBD-1: When <situation>, the user wants to <motivation>, so they can <outcome>.
- JTBD-2: ...

## Success metrics
- Metric, target, and how it will be measured. Prefer numbers.
  e.g. "80% of test users complete first measurement within 60 s of unboxing,
  measured via the onboarding-flow analytics event."

## Constraints
- Budget: ...
- Timeline: ...
- Regulatory / claims: any medical, safety or radio claim, even implied
  (flag for mapping-compliance).
- Must-use / must-avoid: vendors, components, platforms.
- Physical: size, weight, power source, environment.

## Scope
### In (v1)
- ...
### Out (explicit non-goals)
- ... (write these down even if "obviously" out -- that's exactly what
  quietly creeps back in)

## Known risks
- Risk the stakeholder already flagged, in their words.

## Open assumptions
- Anything unresolved. Mirror each one into ASSUMPTIONS.md with an owner
  and a "resolve by" gate/date.

## Stakeholder quotes
- "..." -- attributed, area (e.g. success metrics), date.
```

## Example (fictional, for a handheld soil-moisture sensor)

```markdown
## Problem & users
Small-scale market-garden operators currently probe soil by hand or guess
from surface appearance, leading to over- or under-watering. Users are
non-technical growers who want a fast go/no-water decision at each bed.

## Jobs-to-be-done
- JTBD-1: When walking the beds each morning, the grower wants a
  30-second moisture read per bed, so they can decide whether to irrigate
  today.

## Success metrics
- "A grower should be able to check 10 beds in under 5 minutes." --
  stakeholder interview, 2026-09-20.
- Unit cost target: under $25 at 1,000-unit volume [ASSUMED -- confirm
  with stakeholder; only "affordable" was stated].

## Constraints
- Must run outdoors, -10 degC to +45 degC ambient [ASSUMED from "works in
  a New England spring/fall" -- confirm exact range].
- No subscription/cloud dependency -- explicit non-goal per stakeholder
  ("I don't want to build a SaaS").

## Scope
### In (v1)
- Single-probe moisture reading, local display, no connectivity.
### Out (v1)
- Bluetooth/app connectivity (stakeholder: "maybe v2, not now").
- Multi-probe networked monitoring.
```
