# Eval spend log

Every real `claude plugin eval` run, with its list-price cost from `aggregate-result.json` (`costUsd`, which includes judge calls). `run.sh` appends a row automatically; debugging runs are logged by hand. Owner budget for all eval runs: about US$250.

| Date (UTC) | Who / why | Command scope | Model (agent / judge) | Runs | Cost (USD) | Running total (USD) |
|---|---|---|---|---|---|---|
| 2026-09-25 | Phase 6 build: env probe (HOME, PATH, sandbox) | 1 probe case, --runs 1, --ablation none | claude-opus-5-5 / claude-opus-5-5 | 1 | 0.18 | 0.18 |
| 2026-09-25 | Phase 6 build: validate review-seeded-wearable (first fixture) | --case review-seeded-wearable --runs 1 --ablation none | claude-opus-5-5 / claude-opus-5-5 | 1 | 0.68 | 0.86 |
| 2026-09-25 | Phase 6 build: validate discipline-mark-gate-passed (+ missing-file grader probe) | --case discipline-mark-gate-passed --runs 1 --ablation none | claude-opus-5-5 / claude-opus-5-5 | 1 | 0.30 | 1.16 |
| 2026-09-25 | Phase 6 build: re-validate review-seeded-wearable after fixture clean-up | --case review-seeded-wearable --runs 1 --ablation none | claude-opus-5-5 / claude-opus-5-5 | 1 | 0.60 | 1.76 |
