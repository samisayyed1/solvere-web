---
name: designing-circuits
description: Capture a circuit as code with tscircuit and export it to KiCad, then verify critical nets with ngspice run inside a sandbox. Use when creating or editing a schematic or PCB circuit (power trees, regulators, protection, analog/digital interfaces) under ecad/ or circuits/, or when asked to "design a circuit", "add a regulator", "simulate this net", or "export to KiCad". Do NOT use for ERC/DRC or fab DFM checks (see checking-ecad), firmware (see building-firmware), or mechanical CAD (see modeling-cad-parts).
allowed-tools: Read, Grep, Glob, Write, Edit, Bash(tsci *), Bash(kicad-cli *), Bash(~/.forge/bin/forge-python *), Bash(git diff *), Bash(git status *)
---

# Designing circuits

**Non-negotiable rules:**

1. **tscircuit is the capture tool.** Always run it with `TSCI_TELEMETRY_DISABLED=1`. **Never** run `tsci login`, `tsci push`, `tsci clone`, `tsci registry` or `tsci import` without explicit owner approval in the chat — these are network operations against the tscircuit registry (ADR-001 D11).
2. **Every dimension and value comes from `params/params.toml`.** Never hard-code a resistor value, a voltage rail, a tolerance — read it from params, and if it's missing, ask (don't assume) or add it as `status = "assumed"` with a source.
3. **A netlist whose `.control` block contains `shell` is never executed**, by this skill's `scripts/verify.py` or by hand. ngspice's `shell` command runs `/bin/sh -c` unconditionally; `-n` does not disable it.
4. **ngspice always runs inside `srt`** (network denied, writes confined to `out/verify/`) — never bare on the host, even for a "quick check."
5. This skill **exports to KiCad**; it does not run ERC/DRC or fab DFM (that's `checking-ecad`) and it does not fabricate anything.

## Workflow

1. **Read `params/params.toml`** for every value the circuit needs (supply voltage, target output, load current, tolerances). If a value is missing, either ask the user or add it with `status = "assumed"` and a source string — never invent a number silently.
2. **Write the circuit as tscircuit code** under `ecad/` (`.tsx`/`.ts` per tscircuit's convention). Keep it in small, buildable steps: one net or sub-circuit at a time, not a whole board blind (brief §0 "build in small, measured steps").
3. **Export to KiCad** for anything that will go to `checking-ecad` or to fab:
   ```
   TSCI_TELEMETRY_DISABLED=1 tsci build --kicad-project --ci
   ```
   or `tsci export <file> -f kicad_pcb` / `-f kicad_sch` (docs.tscircuit.com/command-line/tsci-export). Never `tsci push` unless the owner approved it in chat.
4. **For any critical net** (anything with a numeric requirement: regulator output, ripple, protection threshold, dissipation, timing), write an ngspice netlist to `analysis/spice/<name>.cir` plus a sidecar `analysis/spice/<name>.limits.toml` — see `references/spice-limits-format.md` for the exact TOML shape and worked examples (regulator output at 3.3 V ± 2%, ripple, dissipation).
   - The netlist's `.control` block should end with `.meas` lines that name each result exactly as it appears in the limits file, e.g. `meas tran vout_dc avg v(out) from=2m to=5m`.
   - `.meas` is only valid inside `tran`, `dc`, `sp` or `ac` analyses — not `.op`. For a DC operating point with ripple, use a `.tran` with a small AC component superimposed and measure `avg` / `pp` over one settled period.
5. **Run the check**: `~/.forge/bin/forge-python scripts/verify.py --project <root>` (or let `forge verify` call it). It refuses shell-bearing netlists, runs ngspice sandboxed, parses `.meas` results, and checks them against the limits file. A failing measurement's `remediation` says the rule, the measured value, the limit, and the fix — read it and fix the circuit, not the limit (unless the limit itself was wrong, in which case fix it with a sourced justification).
6. **Cite the check result** (`out/verify/spice.<name>.json`) as evidence for the claim, at level **L2** (simulated) — never call a simulated result "validated" (that needs L4 physical test evidence, CONTRACTS.md §4).

## What this skill refuses

- Running `tsci login`/`push`/`clone`/`registry`/`import` without an explicit chat approval.
- Running ngspice outside `srt`, or with a netlist whose `.control` block contains `shell`.
- Hard-coding a value that belongs in `params/params.toml`.
- Calling a simulated result "validated" — it is L2 at best until a physical test exists.

## References

- `references/spice-limits-format.md` — the sidecar TOML schema, worked examples, and why the sandbox confines writes to `out/verify/` rather than a bare `/tmp`.
- `docs/research/R4b-tools-electronics-embedded-software.md` §3–4 — tscircuit and ngspice version pins, telemetry and security notes.
- `docs/decisions/ADR-001-forge-architecture.md` D11 — why tscircuit is primary and atopile is deferred, and the ngspice sandbox rationale.
