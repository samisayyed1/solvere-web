# Gate records

One file per gate: `G0.md`, `G1.md`, ... `G6.md`, created from `_gate-template.md`. See `docs/standards/gates.md` in the Forge repo for what each gate requires, and `forge.toml` `[project].gate` for the project's current gate.

Each gate record contains, per CONTRACTS.md §7:

- the gate criteria;
- evidence links (`evidence/manifest.json` entry ids, `out/verify/*.json` paths);
- the verification-evaluator verdict (the `forge.verdict/1` JSON block);
- red-team findings;
- open risks (cross-reference `RISKS.md`);
- a **blank human sign-off line**.

## Rules

- Claude (any agent) may draft every section above the sign-off line, and may recommend PASS or FAIL. **Only a human fills in the sign-off line.** A PreToolUse hook blocks agent edits to a sign-off line that is already filled in.
- Never mark a gate as passed on request. If asked to, decline and state what evidence is missing.
- A gate record that relies on any `UNVERIFIED` evidence entry (recorded when the Stop-hook block cap was hit) cannot be recommended PASS.
