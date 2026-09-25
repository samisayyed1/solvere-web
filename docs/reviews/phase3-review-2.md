# Phase 3 independent review #2

- **Date:** 2026-09-25. **Commit:** 7a7bfa5. `plugins/forge/evals/` and `passk.py` were not reviewed.
- **Reviewer:** read-only; built none of the plugin. Every probe ran on projects freshly scaffolded with `skills/new-project/scripts/scaffold.py` into `/tmp/claude-0/review2/p1…p9`. Each probe piped realistic hook JSON into `python3 hooks/_failclosed.py <hook>`, which is exactly what `hooks.json` runs.
- **Verdict: FAIL.** Two critical and five major findings are open. Most of review #1's fixes are real, but the evidence gate and the guards can still be switched off with one ordinary command.

## Commands requested
| Command | Result |
|---|---|
| `forge-python -m pytest plugins/forge/tests … --ignore=…/evals` | `1043 passed, 1 skipped in 468.22s`, exit 0 (`/tmp/claude-0/review2/pytest.txt`) |
| `plugins/forge/bin/forge lint all` | `324 pass, 0 fail, 0 warn, 1 skip` |
| `claude plugin validate plugins/forge` | `√ Validation passed` |
| `forge doctor --quick` | `31 pass, 0 fail, 1 warn`. The warning is `files_lock`: `<no files tracked>`, so the hook and settings integrity lock guards nothing yet. |

## Review #1 findings: status
| ID | Status | Evidence (probe → output) |
|---|---|---|
| C1 | FIXED | Appending to `docs/README.md` makes Stop exit 2 with "docs/gardening-docs … no `forge verify` run". After `forge verify --all`, Stop exits 0. With no verify, 9 Stops in a row gave 2,2,2,2,2,2, then 0 with the handoff `systemMessage`, then 2,2. An UNVERIFIED `docs` entry EV-0001 was written, the counter reset, and no exception was raised. |
| C2 | PARTIAL | These now block (exit 2): `forge evidence add --domain docs --result pass --claim "trust me…"`, committing the cad change, and a copied verify entry dated 2099 ("EV-9999 is dated in the future"). But N1, N2, N3 and N11 below still get past the gate. |
| C3 | FIXED | Under `/usr/bin/python3.10`, all 8 hook modules exit 2 with "Python 3.10.20 … too old". Bad JSON on stdin and an unknown module name also exit 2. (3.9 is not installed here; the wrapper avoids post-3.7 syntax.) |
| M1 | FIXED | `PARAMS/params.toml` Edit, `Release/x.txt` Write, and `CAD/x.py` Write by the electrical engineer are all denied. |
| M2 | PARTIAL | `echo pwned > f.txt` and `python3 -c open(...)` are denied for judges. But `git grep -O<cmd>` still runs arbitrary commands (N4). |
| M3 | FIXED | All 12 of review #1's probes are denied, including the newline, `bash -c`, `out/../cad`, `find -delete`, `git -C . push --force`, `+main` and urllib cases. ADR §16's residual list is incomplete, though (N1–N3, N8). |
| M4 | PARTIAL | `set --value 0.5` without `--source` is refused. With a source, the param drops to `measured`, `verified_by` and `evidence` are cleared, the CHANGELOG is logged and file comments are kept. But the param can then be re-promoted to verified by the agent itself (N6). |
| M5 | FIXED | A verdict with overall PASS and a critical FAIL gets SubagentStop exit 2 ("overall is PASS but … C1=FAIL"). An empty `criteria` list fails the schema. `gate-review.js:157-161` returns BLOCKED when a required reviewer is missing. |
| M6 | FIXED | `evidence.newest_verify_entry` takes the newest entry per (domain, entrypoint), pass or fail. `test_failing_sibling_check_blocks` covers it. |
| M7 | PARTIAL | On a fresh scaffold SessionStart prints only the gate and open items, and editing `.claude/rules` no longer blocks `.md` edits. But the fresh template fails its own tracing check (N10). |
| M8 | FIXED | `verify.py:129-133` compares ratio to ratio, and overhang is checked only on downward faces. `mech/test_dfm_ratio_and_overhang.py` has 4 seeded tests that assert the check id, value and limit. |
| M9 | PARTIAL | Release refuses UNVERIFIED and fail entries, `set_last_green` is now called (`verify.py:231`), and `regression_diff.py` does the diff. But the release refusal is too broad (N7). |
| m1 | FIXED | Annular ring and copper-to-edge are measured. There is a seeded annular-ring failure test, and a missing rule key gives exit 2. There is still no seeded failure test for copper-to-edge. |
| m2 | FIXED | `security/srt/kicad-mcp-pro.json` exists, and the template uses `${FORGE_ROOT}`. |
| m3 | FIXED | The CNC hole-to-edge rule is `unsupported` with a corrected citation. Strain unit is `%`. The short-arm warning reaches `notes`. |
| m4 | FIXED | Coefficients are 3.140/3.667/1.527, the plate-hole case tolerance is 3 %, and the unit test uses independently typed coefficients. |
| m5 | FIXED | NotebookEdit into `security/` is denied. SessionStart checks X_OK (`session_start.py:196`). The `in (0, 2)` assertion is gone. `bom/`, `mfg/` and `compliance/` are gated. |

## New findings
| ID | Sev | file:line | Defect | Evidence | Fix |
|---|---|---|---|---|---|
| N1 | critical | `hooks/pre_tool_use.py` `_path_policy` (forge.toml is only guarded as a write target); `hooks/_common.py:66` `find_project_root` | Deleting `forge.toml` turns off every hook. Deletion is allowed for any agent, subagents included. ADR §16 says "`forge.toml` changes are hook-denied or `ask`", which is false for deletion. | These got no decision (rc=0, empty output): `rm forge.toml`, `rm -f forge.toml`, `python3 -c "import os; os.remove('forge.toml')"`, `git checkout HEAD~1 -- forge.toml`, and `rm forge.toml` as `forge:mechanical-engineer`. Then, with a verified param changed 2.0→0.5 and `cad/bracket.py` changed, Stop exits 0. Red-team `echo pwn > f` and an electrical-engineer Write to `release/x` are both allowed. | Treat rm/mv/checkout/unlink of `forge.toml` as a write: deny for subagents, ask on the main thread. Fail closed when `.forge/`, `evidence/` or git history shows a Forge project but `forge.toml` is missing. |
| N2 | critical | `lib/forge/state.py` `changed_since` (relies on `git diff`) | `git update-index --assume-unchanged` or `--skip-worktree` hides a tracked change from the gate. PreToolUse allows both. ADR §16 does not list it. | After a green run: `git update-index --assume-unchanged cad/dims.py`, then change `W=2.0` to `W=0.1`, and Stop exits 0. The params check still catches this for `params.toml` (it reads the file directly), but no other domain has that protection. | Compare each domain's working-tree `inputs_sha256` with the digest recorded at last green, not `git diff`. Deny `git update-index` in PreToolUse. |
| N3 | major | `lib/forge/evidence.py` `project_files`; `state.changed_since` (`--exclude-standard`) | Adding a path to `.gitignore` hides new design files from both the change list and the inputs digest. `.gitignore` itself is in no domain. A gitignored helper imported by a tracked part is never hashed. | `echo cad/new_part.py >> .gitignore; echo x=1 > cad/new_part.py` → Stop exits 0. | Hash every file under the domain globs, ignored or not, and add `.gitignore` to every domain's inputs. List it in ADR §16. |
| N4 | major | `hooks/pre_tool_use.py` judge Bash allowlist | `git grep -O<pager>` (open-files-in-pager) runs any command, so judges can still write. | `pt.sh forge:verification-evaluator "git grep -O'sh -c \"echo x > evidence/manifest.json\"' value"` got no decision (allowed). In a scratch copy, `git grep -O'touch pwned' value` created `pwned`. | Allowlist git options per subcommand; deny `-O`/`--open-files-in-pager` and any `-c`. |
| N5 | major | all hooks; `_common.find_project_root(data["cwd"])` | Each hook finds the project only from the payload's `cwd`. When that is outside the project, every guard is off, including the judge write ban. | With `cwd=/tmp`: `rm -rf <proj>/cad` is allowed, red-team `echo x > <proj>/evidence/manifest.json` is allowed, a red-team Write to `<proj>/release/x` is allowed, and Stop exits 0. (Whether Claude Code ever sends an outside `cwd`, for example after a `cd`, is platform behaviour I could not test here.) | Find the root from `CLAUDE_PROJECT_DIR` and from the target paths. Deny judge writes whether or not a project is found. |
| N6 | major | `pre_tool_use.py` `_verified_param_violation`; `stop.py` `verified_param_violations` | An agent can mark a param `verified` itself, with a made-up human name and unrelated evidence. Only leaves that were already verified are guarded, so `assumed` → `verified` by Edit is never checked. The ADR's "a human signs verified values" is not enforced anywhere. | `forge params set … --value 0.5 --source …` demotes the param. Then a mechanical-engineer Edit setting `status="verified"`, `verified_by="QA Person"`, `evidence=["EV-0002"]` (EV-0002 is a sysml check) is allowed. After `forge verify --all`, Stop exits 0. | Deny any Write/Edit that sets `status="verified"` or changes `verified_by`/`evidence`; only `forge params set --status verified` (an `ask` rule) should do it. Require evidence tied to the param key. |
| N7 | major | `skills/releasing-designs/scripts/release.py:99-115` | Release is refused if *any* manifest entry, ever, was `fail` or UNVERIFIED. The manifest is append-only, so any project that has ever failed a check (normal in development), or hit the Stop handoff, can never be released. | p9: after the tracing failure was fixed, `forge verify --all` was all PASS, but `check_evidence_clean` still returned "REFUSED: … 'EV-0005' … records a failing result". | Judge only the newest entry per (domain, entrypoint) or artifact, and any UNVERIFIED entry not yet superseded. |
| N8 | minor | `pre_tool_use.py` (the cp/ln handling) | `ln` into a protected path is denied, but `cp -l` (a hard link) is not. Writing to the link then rewrites `evidence/manifest.json`. ADR §16 does not list this. | `cp -l evidence/manifest.json app/m.json` is allowed, as is `echo '{}' > app/m.json`. Both names are inode 2917168 with link count 2. | Treat the sources of `cp -l`/`--link` as write targets. Deny Write targets whose link count is above 1. |
| N9 | minor | `pre_tool_use.py` `PROTECTED` | `.mcp.json`, `Makefile` and `.github/workflows/forge-ci.yml` are writable by any agent. An edit to `.mcp.json` can drop `forge-mcp-guard` and `srt`, and nothing checks the product's `.mcp.json` (files-lock is empty). ADR §16 relies on CI, which an agent can edit. | A mechanical-engineer Write to each of these files was allowed. | Ask or deny for these files. Pin them in files-lock. Have doctor compare `.mcp.json` with the template. |
| N10 | minor | `templates/project/requirements/trace.json` | A fresh scaffold fails its own checks (a remnant of M7). Every edit to `requirements/` blocks Stop until tests exist, and with N7 it makes the project unreleasable. | Fresh p1: `forge verify --all` gives `[FAIL] sys/tracing-requirements`, "REQ-MECH-001 has no tests[]". | Ship placeholder requirements as `waived` with a reason, or make the check aware of the current gate. |
| N11 | minor | `lib/forge/state.py` `scaffold_base` | Rewriting the root commit empties the gate's diff. ADR §16 does mention "a new root commit made some other way", but `commit --amend` is an everyday command, not a deliberate trick. | Fresh p5: change cad, then `git add -A && git commit --amend --no-edit` (allowed) → Stop exits 0. After a green run, `git reset --soft $(git commit-tree $(git write-tree) -m root)` is allowed and Stop exits 0. | Pin the scaffold SHA in `.forge/` at scaffold time. Deny `--amend` of the base commit and `reset` to a commit that does not descend from it. |
| N12 | minor | `tests/integration/test_scaffold_real_hooks.py:330` | The M1 `PARAMS/` test skips on case-sensitive filesystems, so the Linux run never exercises the case-folded verified-param path. | The code does `pytest.skip("case-sensitive filesystem…")`. | Simulate case-insensitivity (monkeypatch `resolve`), or also assert the deny reason. |
| N13 | minor | `plugins/forge/toolchain/INSTALL-LOG.md:22-27` | A machine-specific path remains in the plugin. | It contains `/Users/samisayyed/...`. No other plugin or template files have one. | Redact to `~`. |
| N14 | minor | `templates/project/.github/workflows/forge-ci.yml` | CI uses `runs-on: ubuntu-latest` but needs a pre-installed `~/.forge`. The "CI reruns make verify" layer in ADR §16 will not run as shipped. | The workflow's own header comment says the toolchain must already be set up on the runner. | Use a self-hosted runner label, or add an install step. |
| N15 | minor | `hooks/hooks.json` (`"command": "python3"`) | If there is no `python3` on PATH at all, the platform gets exit 127, which fails open. This is not listed in ADR §16. | Code. | Document it, or have doctor or SessionStart assert `python3` ≥ 3.11 on PATH. |

## Novel attacks that were correctly stopped
- **Denied or asked:** Write through a symlink into `evidence/`; `ln evidence/…`; `evidence//manifest.json`, `./evidence`, and `/proc/self/cwd/evidence`; `rsync` or `dd` into `evidence/`; `mv evidence`; `git switch --orphan`; `git restore --source=HEAD~1 .`; `sed -i`, `echo >>` and `truncate` on `forge.toml` (ask); `python -c` with `'evi'+'dence'` and `getattr(open)`.
- **Denied for judges:** `git -c core.fsmonitor=…`, `diff.external`, `core.pager`, `--output=`, `--ext-diff`, `find -fprint`/`-exec`, `sort -o`, `tee`, `sed w`, `awk system`, `rg --pre`, `less`, and `forge verify`/`params set`/`evidence add`.
- **Gate and hooks:** a verify entry dated 2099; `git stash` (the change returns and is gated at the next Stop); a verdict with overall PASS and a FAIL criterion; `/Forge:Releasing-Designs` without approval (UserPromptExpansion exit 2).
- **Speed:** a 6000-command Bash line is analysed in 0.29 s, inside the 1 s PreToolUse timeout.

## Brief §3 and ADR checklist
- **Agents:** all 16 exist. The makers are `sonnet` with `memory: project`. The judges are `opus` with `effort: xhigh`, no memory, tools Read/Grep/Glob/Bash, and Write/Edit/NotebookEdit/Agent disallowed. They are read-only in configuration apart from N4 and N5.
- **Skills:** all 26 in §3.3 exist, plus `init` and `new-project`.
  - `disable-model-invocation: true` is set on releasing-designs, testing-on-hardware, init and new-project.
  - reviewing-designs uses `context: fork`, and its `allowed-tools` no longer includes `forge-python *`.
- **Hooks and workflows:** all 8 hooks are wired through `_failclosed.py`, and all 4 workflows exist. The `engineering-report` output style exists, and all 8 `.claude/rules` exist.
- **ADR §5 mismatch:** the ADR says Stop honours `stop_hook_active`; the code uses only its own block counter. This is harmless but undocumented.

## FEA textbook values (recomputed independently at E = 200 GPa, ν = 0.3)
- **Kt fits:** the Peterson fit `2+0.284s−0.6s²+1.32s³`, the Heywood fit `2+s³` and the Roark fit `3−3.140x+3.667x²−1.527x³` match my own computation at d/W = 0 to 0.6 (for example 2.5190, 2.5120 and 2.5065 at 0.2).
- **The three fits agree:** within 0.5 % for d/W ≤ 0.2 (the unit test's bound), and within 1.9 % across 0 to 0.6. All three reach Kirsch's 3.0 at d/W = 0.
- **Old vs new Roark coefficients:** the old 3.13/3.66/1.53 fit differs from the new one by at most 0.134 %.
- **Attribution:** I could not check offline whether 3.140/3.667/1.527 belongs to Roark 7th ed. or to Pilkey's Peterson eq. 4.1. Numerically, expanding the Peterson fit in x gives 3.004−3.044x+3.36x²−1.32x³, which is consistent with it.
- **Other formulas all match hand calculation:**
  - Euler-Bernoulli cantilever FL³/3EI = 0.2 mm.
  - Simply supported beam FL³/48EI = 0.1 mm.
  - Lamé hoop stress p(ro²+ri²)/(ro²−ri²) = 16.667 MPa (p = 10, ri = 10, ro = 20).
  - Plate with hole: 314.88 MPa.
  - Tube twist TL/GJ = 0.0088278 rad.
  - Cowper κ = 0.84967.

## Tests and product separation
- **Seeded-wrong tests:** I spot-checked 12 files. Each asserts the specific failing check id, its measurement and a remediation, not just a non-zero exit:
  - `test_dfm_ratio_and_overhang`, `test_running_fea`, `test_verifying_geometry_entrypoint`, `test_checking_dfm_entrypoint`, `test_writing_requirements`, `test_building_firmware`, `test_exploring_concepts`, `test_checking_ecad`, `test_measure_hole_edge`, `test_running_fea_general_units`, `test_scaffold_real_hooks`, `test_product_agnostic`.
  - I found no assertion that cannot fail and no `except` that swallows errors. The only weak spot is the N12 skip.
- **Product content:** the 4 denylist patterns match nothing in `plugins/forge`, `templates`, `docs/standards` or `.claude-plugin`. `test_check_catches_a_seeded_leak` proves the check can fail.
- **Absolute paths:** the only machine-specific paths are N13 and test fixtures that deliberately contain a bad path.

## To pass
- Fix N1–N7.
- Add scaffold integration tests for each of them.
- Add N2, N3, N8 and N15 to ADR §16.
- Then run a fresh review.

Verdict: FAIL
