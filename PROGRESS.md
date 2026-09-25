# Forge build: progress checkpoint

- **Updated:** 2026-09-25, stopped at 86% of the window · branch `claude/epic-greider-a8740c` · worktree `.claude/worktrees/forge-product-engineering-55a284`
- **Owner rules:** speed mode, no scope cuts. Opus for design, reviews, judging and eval subject runs; Sonnet for scaffolding and fixes. Stop at 85% of the 5-hour window.

## Done

- **Phase 1:** research (`docs/research/`, cross-check 26/3/0) and ADR-001, accepted.
- **Phase 2:** toolchain, with 28 pinned tools in `~/.forge` (`plugins/forge/toolchain/`); `forge doctor`; MCP lock, owner-approved; srt profiles.
- **Phase 3, built:**
  - 16 agents, 28 skills, 8 hooks and 4 workflows;
  - the output style, the marketplace and the project template;
  - `forge` commands: doctor, lock, lint, evidence, params, state, ears, trace, verify and passk;
  - the product-agnostic denylist test.
- **Phase 3 integration:**

  | Check | Result |
  |---|---|
  | Tests (`forge-python -m pytest plugins/forge/tests`) | 641 pass, 0 fail |
  | `forge lint all` | 0 fail |
  | `forge doctor` | 0 fail |
  | `claude plugin validate` (plugin and repo root) | PASS |
  | FEA extended to general geometry (tet10) | 44 tests; known answers within 1% |
- **Product project:** `products/solvere-sense/`, scaffolded by Forge, with the G0 owner answers in `docs/intake/G0-owner-answers.md`.

## In flight when this was written

- Nothing. I3 (drawings for general geometry) is done: 3 test parts drawn headlessly, 0.000 mm drawn-vs-model difference, and 41 new tests, 33 of them seeded-wrong.

## Next, in order

1. **Close Phase 3:**
   - (a) DONE: I3 finished. forge-python: 718 passed; stdlib: 589 passed, 15 skipped; lint 0 fail; validate PASS (commit f1bb09f).
   - (b) DONE: CAD-only tests are guarded with `importorskip`.
   - (c) **NEXT:** **Independent Opus review** of the whole plugin (read-only, fresh context). Covers the brief §3 checklist, ADR deviations, security (hooks fail closed, reviewer read-only), and re-verifying the FEA textbook citations (Peterson/Heywood/Roark, written from memory). Fix its findings, then commit.
2. **Verify ladder (Phase 5):** `forge verify --all` on a fixture project; `make verify` in the template; a ladder doc.
3. **Solvere Sense ceiling pod through G2** (Phase 4 smoke project):
   - G0: EARS requirements from the owner answers; SysML model; params; ASSUMPTIONS; RISKS.
   - G1: concept tournament, then an ASK to the owner to pick one of the top 2.
   - G2: CAD, geometry, DFM, tolerances, FEA, drawings, renders, BOM; `reviewing-designs`; a gate record with a blank sign-off.
4. **Evals (Phase 6):** smoke tier, then the full suite (25+ cases × 3 runs × 2 arms, agent and judge pinned to `claude-opus-5-5`, with a cost ceiling), then `evals/BASELINE.md`.
5. **Phases 7–8:** capturing-failures and weekly routine (ASK before enabling), acceptance, README, final ASK.

## Known failing or open items

- The FEA formula citations are unverified (item 1c).
- No ARM cross-compiler is installed, so firmware target builds SKIP. The firmware eval needs `arm-none-eabi-gcc` or the Zephyr SDK: **ASK the owner** before installing.
- Desktop-bundled Claude Code is 2.1.280, which gives a doctor warning only.
- Peer sessions "Fix conftest.py module-name collisions" and "Fix forge-python symlink" duplicate fixes that are already in this worktree. **Don't merge them.**

## Resume command

In this worktree, tell Claude: "Resume from PROGRESS.md". Or run these checks first:

```bash
cd /Users/samisayyed/solvere/.claude/worktrees/forge-product-engineering-55a284 && ~/.forge/bin/forge-python -m pytest plugins/forge/tests -q -p no:cacheprovider > /tmp/forge-tests.txt 2>&1; tail -3 /tmp/forge-tests.txt && plugins/forge/bin/forge lint all | tail -1 && plugins/forge/bin/forge doctor --quick | tail -1
```
