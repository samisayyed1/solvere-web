# Forge build: progress checkpoint

- **Updated:** 2026-09-25, stopped at 93% of the window after review #1 · branch `claude/epic-greider-a8740c` · worktree `.claude/worktrees/forge-product-engineering-55a284`
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
   - (c) DONE: independent Opus review #1 gave **FAIL** (`docs/reviews/phase3-review-1.md`). 3 critical, 9 major and 5 minor findings; the FEA formulas were verified correct.
   - (d) **NEXT: fix review #1, in two parallel agents, then re-review with a fresh Opus reviewer:**
     - **Enforcement fixer (Opus)** owns `plugins/forge/hooks/**`, `lib/forge/{evidence,state,params,checkresult}.py`, `lib/forge/commands/{evidence,params,verify}.py`, `schemas/*`, `agents/{verification-evaluator,red-team}.md` and `workflows/gate-review.js`. It fixes:
       - C1: add a `docs` domain everywhere;
       - C2: bind evidence to real, passing `forge.check/1` files with a matching `inputs_sha256`; reject future timestamps; diff against the last-green SHA; protect `evidence/`;
       - C3: fail closed without `tomllib`, or pin the interpreter;
       - M1: case-folded path guards;
       - M2: judge Bash allowlist;
       - M3: Bash parsing (newlines, `-C`, `+refspec`, path normalisation), plus a Stop-time diff check on verified params, with the residual Bash risk written into ADR §16;
       - M4: `params set` drops the status to `measured` and needs a citation;
       - M5: enforce `overall == PASS ⇒ every criterion PASS`; the gate review returns BLOCKED on a missing judge;
       - M6: newest entry per entrypoint;
       - M9: `set_last_green` in `forge verify`;
       - m5: NotebookEdit paths, the SessionStart hook self-check, the no-op test assertion, and gating bom/mfg/compliance.
       
       It also adds an **integration test** that scaffolds `templates/project` and runs the real Stop, PostToolUse and SubagentStop hooks.
     - **Skills fixer (Sonnet):**
       - M7: trace graph files go outside `out/verify`; ignore `.gitkeep`; the template passes gardening-docs; bind fix messages by check_id;
       - M8: DFM rib/boss ratio vs ratio; overhang on down-facing faces; seeded tests;
       - M9: release refuses UNVERIFIED or failing evidence; regression-sweep uses a script diff against last-green;
       - m1: checking-ecad annular-ring and edge rules; fix the no-op test;
       - m2: add the kicad-mcp-pro srt profile in the template; parameterise `~/.forge`;
       - m3: DFM citations and strain unit; surface the short-arm warning;
       - m4: Roark 3.140/3.667/1.527, a tighter plate-hole tolerance, tests anchored to published values.
     - **Then:** full suite, lint, validate, a fresh Opus re-review (must PASS), commit. **Independent Opus review** of the whole plugin (read-only, fresh context). Covers the brief §3 checklist, ADR deviations, security (hooks fail closed, reviewer read-only), and re-verifying the FEA textbook citations (Peterson/Heywood/Roark, written from memory). Fix its findings, then commit.
2. **Verify ladder (Phase 5):** `forge verify --all` on a fixture project; `make verify` in the template; a ladder doc.
3. **Solvere Sense ceiling pod through G2** (Phase 4 smoke project):
   - G0: EARS requirements from the owner answers; SysML model; params; ASSUMPTIONS; RISKS.
   - G1: concept tournament, then an ASK to the owner to pick one of the top 2.
   - G2: CAD, geometry, DFM, tolerances, FEA, drawings, renders, BOM; `reviewing-designs`; a gate record with a blank sign-off.
4. **Evals (Phase 6):** smoke tier, then the full suite (25+ cases × 3 runs × 2 arms, agent and judge pinned to `claude-opus-5-5`, with a cost ceiling), then `evals/BASELINE.md`.
5. **Phases 7–8:** capturing-failures and weekly routine (ASK before enabling), acceptance, README, final ASK.

## Solvere Sense G0: work in progress (agent stopped mid-run to move to cloud)

- **Last status:** requirements, params and the SysML model were drafted, the model passes spec42, and the checker catches seeded faults.
- **Not done:** `docs/interfaces.md`, `docs/budgets.md`, the ASSUMPTIONS/RISKS updates, the compliance map, `forge verify --all` evidence, and `reviews/G0.md`.
- **To resume:** re-run the G0 brief (systems-engineer role, product folder only, never invent numbers, cite the MR60FDA2 datasheet), then review the WIP files and complete them.

## Known failing or open items

- The FEA formula citations are unverified (item 1c).
- No ARM cross-compiler is installed, so firmware target builds SKIP. The firmware eval needs `arm-none-eabi-gcc` or the Zephyr SDK: **ASK the owner** before installing.
- Desktop-bundled Claude Code is 2.1.280, which gives a doctor warning only.
- Peer sessions "Fix conftest.py module-name collisions" and "Fix forge-python symlink" duplicate fixes that are already in this worktree. **Don't merge them.**

## Evals: run on the owner's Mac (not in the cloud)

The cloud host can't run Claude Code's sandboxed Bash as root, and `claude plugin eval` refuses `enableWeakerNestedSandbox` by design (details in ADR §10). So the evals run on the Mac, under the owner's plan limits or API key. Run each block in order and check the noted output before the next.

**1. Update the worktree**
```bash
cd /Users/samisayyed/solvere/.claude/worktrees/forge-product-engineering-55a284
git status --short                       # if anything prints, run the next line
git stash push -u -m "pre-sync $(date +%F)"
git fetch origin claude/epic-greider-a8740c-i7dhii
git checkout -B claude/epic-greider-a8740c-i7dhii origin/claude/epic-greider-a8740c-i7dhii
```

**2. Toolchain check.** Expect 0 fail; the files_lock warning is a separate human step. `check` is free and must show $0.00.
```bash
claude update
export PATH="$HOME/.forge/bin:$PATH"
plugins/forge/bin/forge doctor | tail -5
plugins/forge/evals/run.sh check
```

**3. Smoke tier.** 48 runs, about 2–3 h at concurrency 3, ceiling $70.
```bash
caffeinate -i plugins/forge/evals/run.sh smoke --max-cost-usd 70 --concurrency 3 2>&1 | tee /tmp/forge-smoke.log
```

**4. Full suite, after the smoke tier is analysed.** 26 cases × 3 runs × 2 arms, estimated $95–185, ceiling $190.
```bash
caffeinate -i plugins/forge/evals/run.sh full --max-cost-usd 190 --concurrency 3 2>&1 | tee /tmp/forge-full.log
```

**5. Push the results back for analysis** (`forge passk`, seeded recall and precision, `evals/BASELINE.md`)
```bash
git add -f plugins/forge/evals/results plugins/forge/evals/SPEND.md
git commit -m "Eval results (Mac run)"
git pull --rebase origin claude/epic-greider-a8740c-i7dhii
git push origin claude/epic-greider-a8740c-i7dhii
```

**Billing:** the runs use whatever login the Mac's `claude` has. A subscription login uses plan limits (the `$` figures are estimates). An API key uses credits, capped by `--max-cost-usd`. Check with `/status` inside `claude`.

## Resume command

In this worktree, tell Claude: "Resume from PROGRESS.md". Or run these checks first:

```bash
cd /Users/samisayyed/solvere/.claude/worktrees/forge-product-engineering-55a284 && ~/.forge/bin/forge-python -m pytest plugins/forge/tests -q -p no:cacheprovider > /tmp/forge-tests.txt 2>&1; tail -3 /tmp/forge-tests.txt && plugins/forge/bin/forge lint all | tail -1 && plugins/forge/bin/forge doctor --quick | tail -1
```
