---
name: building-firmware
description: Build firmware on the host with cc, run its unit tests through a tiny stdlib-only C test harness, static-analyze it with clang --analyze, check size/timing budgets from params, and cross-compile for the real target when the toolchain exists. Use when writing or editing firmware under firmware/, or when asked to "build the firmware", "add a driver/state machine", "write firmware tests", or "check the mutation coverage". Do NOT use for flashing or hardware-in-the-loop testing (see testing-on-hardware) or for the electrical design itself (see designing-circuits).
allowed-tools: Read, Grep, Glob, Write, Edit, Bash(cc *), Bash(clang *), Bash(arm-none-eabi-gcc *), Bash(~/.forge/bin/forge-python ${CLAUDE_SKILL_DIR}/scripts/verify.py:*)
---

# Building firmware

**Non-negotiable rules:**

1. **A test suite that cannot fail proves nothing.** Every module with a test file must guard at least one real comparison with `#ifdef FORGE_MUTANT` (`references/mutation-testing.md`). `scripts/verify.py` rebuilds with `-DFORGE_MUTANT` and FAILS the check if the tests still all pass.
2. **No ARM cross-compiler is installed yet.** If `arm-none-eabi-gcc` (or `$FORGE_CROSS_CC`) is absent, the target build and the real target size budget **SKIP with the install fix** — never a faked pass, and never silently substituted with a host number without saying so.
3. **The test harness is `references/forge_test.h`** — no download, no third-party framework. Don't vendor a different one into a product repo without a reason.
4. **Every size/timing budget number comes from `params/params.toml`** (`[firmware.<module>]`), never hard-coded in the check or the source.

## Workflow

1. Put implementation in `firmware/src/<name>.c` (+ `firmware/include/<name>.h`), and its tests in `firmware/tests/test_<name>.c`, `#include "forge_test.h"` (resolved from this skill's `references/`, no copying needed):
   ```c
   #include "debounce.h"
   #include "forge_test.h"
   static void test_debounces_after_threshold(void) {
       FORGE_CHECK(debounce_is_stable(1, 1, DEBOUNCE_THRESHOLD) == 1);
   }
   int main(void) { test_debounces_after_threshold(); return FORGE_REPORT(); }
   ```
2. **Guard a real comparison with `FORGE_MUTANT`** in the implementation (references/mutation-testing.md) — pick a boundary or sign that a real bug would actually hit, not a cosmetic one.
3. **Declare any size/timing budget** in `params/params.toml`:
   ```toml
   [firmware.debounce]
   size_budget_bytes = 512
   ```
4. **Run the check**: `~/.forge/bin/forge-python ${CLAUDE_SKILL_DIR}/scripts/verify.py --project <root>` (or `forge verify` for the `fw` domain). Per module it: builds + runs tests on the host, static-analyzes with `clang --analyze`, checks the size budget (target build if the cross-compiler exists, else a clearly-labelled host proxy, or a clean SKIP), and runs the mutation check.
5. **A build or test failure's `remediation`** names the file and the failing assertion or compiler error — fix the code, not the check.
6. **Cite the result** (`out/verify/firmware.<module>.json`) as evidence at level **L1** (host build) — target-build evidence is still L1 until it runs on real hardware (L4, via `testing-on-hardware`).

## What this skill refuses

- Marking a module's checks PASS when its tests can't be proven to fail (no `FORGE_MUTANT` guard is an **error**, not a skip).
- Faking a target size/timing number when the cross-compiler is missing — it SKIPs with the exact install command.
- Flashing hardware or driving a debugger — that's `testing-on-hardware`, through agentic-hil's bounded tools only.

## References

- `references/forge_test.h` — the whole test harness; `#include` it, don't reinvent it.
- `references/mutation-testing.md` — the `FORGE_MUTANT` convention, worked example, and why an absent mutant is an error rather than a skip.
