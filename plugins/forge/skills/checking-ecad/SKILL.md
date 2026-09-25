---
name: checking-ecad
description: Run KiCad's ERC and DRC (JSON output) and check the board's measured minima against a fab house's DFM rules. Use after a schematic or PCB layout changes under ecad/, before any fab-related step, or when asked to "check the board", "run ERC/DRC", "is this ready to fab", or "check DFM". Do NOT use this to design a circuit (see designing-circuits) or to actually order/export fab files (see releasing-designs) — this skill never fabricates anything and never sets a gate to PASS.
allowed-tools: Read, Grep, Glob, Bash(kicad-cli *), Bash(~/.forge/bin/forge-python *)
---

# Checking ECAD

**Non-negotiable rules:**

1. **Never fabricate anything, and never mark a fab-readiness gate PASS from this skill.** Checking-ecad only runs machine checks and reports; a human sign-off is required before any fab order, enforced by the release hook (CONTRACTS.md §13 approval file) — this skill only states that requirement, it does not (and cannot) satisfy it.
2. **`kicad-cli` only, never `--save-board`.** Review-mode DRC must never mutate the board file. The annular-ring/copper-to-edge check (below) also never mutates the real board or writes into `ecad/`: it runs against a scratch copy under `out/verify/`.
3. **Every ERC/DRC violation is fixed or explicitly waived.** A waiver needs a `reason` and an `approver` in `ecad/waivers.toml` (`references/waivers-format.md`); a waiver missing either is rejected outright — the whole check errors, it does not silently skip the waiver.
4. **Fab DFM numbers come only from `references/fab_rules.toml`**, sourced line-by-line to `docs/research/R5d-dfm-additive-snapfit-pcb.md`. Never invent a fab minimum.
5. **Every fab-rule key `references/fab_rules.toml` promises is actually checked, and a missing key is an ERROR, not a silent skip.** `min_track_width_mm`/`min_track_clearance_mm`/`min_drill_diameter_mm` (from `kicad-cli pcb export stats`) and `min_annular_ring_mm`/`copper_to_edge_mm` (extracted via a scratch DRC pass, since `pcb export stats` doesn't report either) all run every time; a rule table entry with no matching check, or a check with no matching rule-table key, fails closed (m1, review #1).

## Workflow

1. Make sure the board's `ecad/<name>.kicad_sch` and `ecad/<name>.kicad_pcb` exist (from `designing-circuits`'s KiCad export).
2. Run the check: `~/.forge/bin/forge-python scripts/verify.py --project <root>` (or let `forge verify` call it for the `elec` domain). It:
   - runs `kicad-cli sch erc --format json --exit-code-violations` and `kicad-cli pcb drc --format json --exit-code-violations`, writing `out/verify/erc.<name>.json` / `drc.<name>.json`;
   - counts violations by KiCad's `type` field, subtracts anything covered by a valid `ecad/waivers.toml` entry, and fails on the remainder;
   - runs `kicad-cli pcb export stats --format json` and compares the board's *measured* `min_track_width`, `min_track_clearance` and `min_drill_diameter` against the chosen fab's floor (`params/params.toml`'s `[manufacturing] pcb_fab`, default `jlcpcb`) from `references/fab_rules.toml`;
   - measures the board's real minimum annular ring and copper-to-board-edge distance (`dfm_min_annular_ring`, `dfm_copper_to_edge`) against the same fab's floor — `pcb export stats` doesn't report either number, so this runs a second, scratch-only `kicad-cli pcb drc` pass with a custom `.kicad_dru` rule (an unreachable 100 mm minimum) that forces KiCad to report every via/pad's and every copper feature's real measured value, which this parses out of the violation text;
   - writes one `out/verify/ecad.<name>.json` check result per board.
3. **Read every failing `remediation` string** — it names the rule, the measured value against the fab floor, and the fix. Fix the design; only add a waiver when the violation is genuinely non-functional and someone with authority to say so has reviewed it.
4. **Cite the check result** as evidence at level **L1** (measured, in KiCad) — ERC/DRC passing is not "validated" (L4) and never "production-ready" (L5) on its own.
5. **State the human sign-off requirement explicitly** in any summary you give the user: fabrication needs a human to fill `release/APPROVAL.toml` and the target gate's sign-off line (CONTRACTS.md §13); this skill cannot and does not do that for them.

## Adding a waiver

Run the check once, read the violation's exact `type` string from `out/verify/erc.<name>.json` or `drc.<name>.json`, then add a `[[waiver]]` block to `ecad/waivers.toml` per `references/waivers-format.md` — with a real `reason` and `approver`, never placeholders.

## References

- `references/fab_rules.toml` — JLCPCB/PCBWay DFM minima, one source citation per number (R5d).
- `references/waivers-format.md` — the `ecad/waivers.toml` schema and why an unapproved waiver is rejected rather than ignored.
- `docs/research/R4b-tools-electronics-embedded-software.md` §1 — the exact `kicad-cli` subcommand syntax this script relies on.
