# Requirements

EARS sentences, one per requirement, with an ID (`REQ-<AREA>-<NNN>`), a `Rationale:` and a `Verify:` method (inspection|analysis|demo|test). See `.claude/rules/systems.md` and CONTRACTS.md §6. Requirement text and IDs belong to systems-engineer and humans; other agents may change only `status`, `evidence` and `tests` in `trace.json`. Lint: `forge lint ears`; trace: `forge trace`.

These two are placeholders from the scaffold -- replace them with the project's real requirements and delete this note.

## REQ-MECH-001

When the enclosure lid is closed, the enclosure shall retain the lid with a snap-fit engagement force of at least 15 N and at most 40 N.

Rationale: the lid must stay closed under normal handling (drop, shake) without tools, but must be openable by hand without a tool for battery access.
Verify: test

## REQ-SYS-001

While the device is powered, the system shall report battery state of charge with an accuracy of ±5 percentage points.

Rationale: the product spec requires the user-facing battery indicator to be trustworthy enough to avoid unplanned shutdowns.
Verify: analysis
