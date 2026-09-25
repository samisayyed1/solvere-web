# Forge eval suite (`claude plugin eval`)

Brief §6 and ADR-001 §10. There are 25 Forge-built cases (plus any added later), grouped by domain. Each one grades the **outcome** (Forge's own `out/verify/*.json` check results, and the files produced) and the **path** (`tool_used` / `tool_order`: the checker ran, the skill fired, nothing was fabricated).

```
evals/
  run.sh                   smoke | full | check  (pinned models, cost ceiling, passk, seeded scoring, SPEND.md)
  SPEND.md                 every paid run, with a running total (owner budget ~US$250)
  _lib/scaffold.sh         shared scaffold: links ~/.forge, seeds templates/project + fixture/, git-commits
  _lib/neutral/            empty stand-ins for the template's worked examples (A-001, R-001, the sysml requirement...)
  _tools/grader_sim.py     offline dry-run of regex / tool_used / tool_order / file_exists graders
  _tools/seeded_score.py   seeded-defect recall + precision against key/answer_key.json
  _tools/gen_seeded.py     generates the review/seeded-* case files from their answer keys
  <domain>/<case>/         prompt.md, case.yaml, scaffold.sh, fixture/, selftest.json [, key/, reference/]
```

## Running

```
plugins/forge/evals/run.sh check                          # free: loads every case, spends $0
plugins/forge/evals/run.sh smoke --max-cost-usd 70        # 8 cases x 3 runs x 2 arms
plugins/forge/evals/run.sh full  --max-cost-usd 190       # all cases x 3 runs x 2 arms
```

`run.sh` pins `--model claude-opus-5-5 --judge-model claude-opus-5-5` (an owner decision that overrides ADR §10), and always passes `--trust-plugin --scaffold --no-publish --json --allow-tools Bash Write Edit --keep-temp`. It refuses to run without `--max-cost-usd`, or with `--runs` below 3. It writes to `results/<UTC timestamp>/`:

- `aggregate-result.json`, `results.json` and `report.html`;
- `passk.json` and `passk.txt` (`forge passk --k 1,<runs>`, per case and per arm);
- `seeded-report.json` with `findings/<case>/<arm>-<n>.json` (the archived findings files);
- `stderr.log`.

It then deletes the kept temp dirs and appends a row to `SPEND.md`.

**Host requirement:** the cases grant sandboxed Bash, so the host needs a working Claude Code sandbox. On the Linux cloud build machine (root in a container), every sandboxed Bash call fails with `apply-seccomp: write /proc/self/uid_map: Operation not permitted`. Only hook-driven checks run there, so the Bash-dependent graders fail. Run the suite on the owner's Mac, or on a Linux host where `claude` Bash sandboxing works.

## HOME and FORGE_HOME

Each run gets a throwaway `$HOME` and a filtered environment:
- The run inherits only `PATH`, provider and proxy variables, and `EVAL_*`.
- The scaffold script inherits only `PATH` and `HOME`, and **no `EVAL_*`**.
- Sandboxed Bash cannot read the real home, except for directories that are on `PATH`.

Forge's tools live in the real `~/.forge`, and skills and hooks find them as `Path.home()/.forge` or `~/.forge/bin/forge-python`. So:

1. **`run.sh` changes the environment.** It prepends `$FORGE_HOME/bin` and `$FORGE_HOME` to `PATH`.
   - The harness turns PATH entries into sandbox `allowRead` rules. With `$FORGE_HOME` on PATH, `//root/.forge` is readable. This was confirmed in a real run's generated `config/settings.json`.
   - `bwrap` and `socat` are found through `$FORGE_HOME/bin`.
   - It also exports `EVAL_FORGE_HOME`.
2. **`_lib/scaffold.sh` links the toolchain.** It finds the real toolchain from `FORGE_HOME`, then `forge-python` on PATH, then `~<user>/.forge` (tilde-user expansion reads the passwd db, not `$HOME`). It links `$HOME/.forge` to that directory. Hooks run on the host with the throwaway HOME and resolve through the link. This was confirmed in real runs.

## Grader discipline

- Every case sets explicit `max_turns` and `timeout_seconds`.
- Every case has at least one outcome grader and one path grader.
- `llm` graders are used only for short rubrics:
  - the enclosure render PNG;
  - four refusal replies.
- `tests/evals/test_graders.py` runs each case's real scaffold, then applies the `selftest.json` variants:
  - `good` must pass every free grader;
  - each `bad-*` variant must fail the graders it names;
  - every free grader must fail in at least one variant.

  Where cheap, the `good` and `bad` checker outputs are **real** outputs of Forge's checkers on a hidden `reference/` solution and on a seeded-wrong version of it. The enclosure, firmware, requirements, stack, DFM, BOM, DFMEA and SysML cases work this way. The other cases use hand-made files in the same `forge.check/1` shape.

## Seeded-defect precision

1. Reviewers write `out/review/findings.json` as flat JSON objects. The format is stated in the prompt.
2. `seeded_score.py` reads each run's workspace, found through `tracePath` in the kept temp dir. If the file is missing, it falls back to the last Write of that file in `trace.jsonl`. It archives the findings.
3. It matches findings to `key/answer_key.json` deterministically:
   - `file` regex AND `locator` regex AND `keywords` regex;
   - maximum bipartite matching.

The score is computed as:

- **recall** = planted defects found / planted defects;
- **precision** = (matched + acceptable) / (matched + acceptable + false positives), with duplicates excluded.

`acceptable` entries are true defects that were not planted. They include two generic classes: process-artefact findings, and requirement-quality findings. A false positive is a finding that is wrong, or one that flags a decoy (a deliberately correct item).

The keys live under `evals/`, which the agent under test cannot read (sandbox `denyRead`). The scaffold never copies `key/`, `reference/` or `selftest.json`, and a test asserts this.

Always read the transcripts before trusting a number. In the first real review run, 7 of the 9 "false positives" were real defects that the first fixture had by accident.
