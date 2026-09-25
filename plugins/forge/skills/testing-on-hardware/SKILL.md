---
name: testing-on-hardware
description: Hardware-in-the-loop test procedure and checklist for flashing, probing and stimulating real hardware through agentic-hil's bounded tools. Use only when the user explicitly asks to run a test on real hardware, flash a board, or perform HIL verification, and only after building-firmware's checks are green. Never fires automatically. Do not use this for host-only firmware testing (see building-firmware) or as a substitute for agentic-hil, which is not installed yet on this machine (ADR-001 Phase 2 defers it to the HIL phase) -- this skill is procedure-only until it is.
disable-model-invocation: true
allowed-tools: Read, Grep, Glob
---

# Testing on hardware

**Non-negotiable rules:**

1. **agentic-hil is not installed on this machine yet.** Nothing in this skill runs a real flash, probe or stimulus today. Treat every step below as the procedure to follow once it is installed (ADR-001 §8 T3, D12), and say so plainly if a user asks to run it now.
2. **HIL access is through agentic-hil's bounded MCP tools only** — never a raw `openocd`/`pyocd`/`st-flash` shell command, and never a debugger attached by hand from this skill.
3. **Bench config lives outside the workspace**, registered and owned by a human operator (`agentic-hil grant|revoke` from the operator shell) — this skill never creates, edits or adopts bench config. The Forge permission profile denies `project_config_create`, `project_config_set`, `project_config_adopt_hardware` and `server_upgrade` (ADR-001 §9).
4. **`allow_raw_debugger_commands` and `allow_mass_erase` stay `false`.** Flashing is refused while either is true; this skill never asks for them to be turned on.
5. **Every test is also run once against a wrong expectation, to prove it can fail** (brief §3.3) — the same discipline as the mutation check in `building-firmware`, applied to the physical test itself.
6. **A HIL result is L4 evidence** (physically tested, with data) — the first level at which "validated" wording is allowed (CONTRACTS.md §4). Record it in `evidence/manifest.json` with `signed_by` naming whoever ran the bench.

## Preconditions (check all before proposing a HIL run)

- [ ] `building-firmware`'s checks are green for the module under test (host build, static analysis, size/timing budget, mutation check).
- [ ] A target binary exists (cross-compiled, not the host test binary).
- [ ] The operator has registered bench config for this project outside the workspace, and `agentic-hil` is installed and reachable (`docs/research/R4b-tools-electronics-embedded-software.md` §8 has the pinned version and install command).
- [ ] The specific test's pass criteria are written down *before* the run (brief §0 "done is agreed before building").

## Procedure

1. **Probe**: confirm the target is connected and identifies correctly, through agentic-hil's probe tool. Do not proceed if it doesn't match the expected part.
2. **Flash**: flash the target binary through agentic-hil's flash tool. Never pass `allow_mass_erase` or raw debugger commands.
3. **Stimulate and read**: drive UART/CAN or other bounded stimulus tools per the test plan, and capture the response.
4. **Assert**: compare the captured response against the written pass criteria.
5. **Negative control**: re-run the same test once against a **wrong** expectation (e.g. assert the opposite of the correct value). It must fail. If it doesn't, the test itself is broken — fix the test before trusting a pass from step 4.
6. **Record evidence**: write the raw log and the pass/fail to `evidence/manifest.json` at level **L4**, with `signed_by` set to whoever ran the bench (a human — this skill does not sign for itself) and `evidence_files` pointing at the captured log.
7. **Never mark a gate PASS from here.** HIL evidence feeds `reviewing-designs`; only a human fills a gate's sign-off line.

## What this skill refuses

- Running any HIL action before agentic-hil is installed and bench config exists outside the workspace.
- Raw debugger commands, mass erase, or any bench-config-mutating call.
- Treating a HIL pass as sufficient on its own for "certified" or "production-ready" wording (needs L5, a human or accredited-body sign-off).

## References

- `docs/research/R4b-tools-electronics-embedded-software.md` §8 — agentic-hil's exact tool list, the denied tools, and the version pin.
- `docs/decisions/ADR-001-forge-architecture.md` §9 — the MCP guard profile this skill will run under once adopted.
