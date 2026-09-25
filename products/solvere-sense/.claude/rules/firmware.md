---
paths:
  - "firmware/**"
---

# Firmware

- Firmware is code with unit tests, static analysis, and simulation (Renode/QEMU/Wokwi-class, per the installed toolchain) before hardware. Simulate first; HIL is bounded and human-supervised.
- Every threshold, timing budget, buffer size and pin mapping comes from `params/params.toml`, not a magic number in source.
- A build alone proves nothing: `forge-python skills/building-firmware/scripts/verify.py --project . --changed firmware/ --fast` must run build + static analysis + unit tests (also runs via the PostToolUse `firmware/` hook: compile, fast mode).
- New tests are proven to fail on a mutated implementation before they're trusted -- a test that cannot fail proves nothing.
- State size and timing budgets explicitly (flash/RAM headroom, worst-case loop time), with units and margin.
- Boot/OTA paths get an explicit security review note (signature verification, rollback protection) before any release claim.
- HIL and flashing commands are `permissions.ask` (human sign-off) and run through bounded tools only -- never an unrestricted shell to the bench.
- Standards and applicability: `docs/standards/firmware.md`.
