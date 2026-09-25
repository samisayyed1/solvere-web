---
paths:
  - "firmware/**"
---

# Firmware

- Firmware is code with unit tests, static analysis, and simulation (Renode/QEMU/Wokwi-class, per the installed toolchain) before hardware. Simulate first; HIL is bounded and human-supervised (see the HIL/flashing bullet below for the actual gate).
- Every threshold, timing budget, buffer size and pin mapping comes from `params/params.toml`, not a magic number in source (`building-firmware`'s verify entrypoint checks size/timing budgets, check_id `firmware.<module>`, `target_size_bytes`; a magic-number literal not sourced from params is caught in review, not by a check).
- A build alone proves nothing: `forge-python skills/building-firmware/scripts/verify.py --project . --changed firmware/ --fast` must run build + static analysis + unit tests (also runs via the PostToolUse `firmware/` hook: compile, fast mode).
- New tests are proven to fail on a mutated implementation before they're trusted -- a test that cannot fail proves nothing (`building-firmware`'s verify entrypoint requires a `FORGE_MUTANT` guard per module and checks the mutant build's tests actually fail, measurement `mutation_kills`).
- State size and timing budgets explicitly (flash/RAM headroom, worst-case loop time), with units and margin (checked against `params.toml`'s `size_budget_bytes` by `building-firmware`'s verify entrypoint, measurement `target_size_bytes`).
- Boot/OTA paths get an explicit security review note (signature verification, rollback protection) before any release claim (advisory -- no automated check parses boot/OTA code for this; caught in review, and `releasing-designs` still refuses a release bundle without VERIFIED, passing evidence regardless).
- HIL and flashing commands are `permissions.ask` (human sign-off) and run through bounded tools only -- never an unrestricted shell to the bench (enforced by `permissions.ask`, CONTRACTS §8, plus the Bash guardrails in the PreToolUse hook).
- Standards and applicability: `docs/standards/firmware.md` (advisory -- a citation pointer, not an enforced rule).
