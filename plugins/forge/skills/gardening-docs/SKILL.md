---
name: gardening-docs
description: Find broken relative links and anchors, stale tool versions against the toolchain manifest, and rules with no stated enforcing mechanism across *.md, then propose small fixes. Use for the weekly routine, before a release, or when asked to "check the docs", "find broken links", or "garden the docs". Do NOT use this to write new documentation from scratch (that's a different task) -- this skill audits what already exists and proposes small, targeted fixes, it does not rewrite docs wholesale.
allowed-tools: Read, Grep, Glob, Edit, Bash(~/.forge/bin/forge-python *)
---

# Gardening docs

**Non-negotiable rules:**

1. **This skill proposes fixes; it doesn't rewrite docs wholesale.** Small, targeted edits only (fix a path, update a version marker, add a mechanism note) — never a full rewrite in this skill's name.
2. **Tool-version staleness only checks docs that opt in** with `<!-- forge-tool-version: <id> <version> -->`. Never guess a tool's pinned version from prose.
3. **Every finding cites the exact file and reason** — no vague "some links may be broken."

## Workflow

1. Run the check: `~/.forge/bin/forge-python scripts/verify.py --project <root>` (or `forge verify` for the `docs` domain). It reports:
   - **broken links/anchors**: every relative Markdown link that doesn't resolve, or whose `#anchor` doesn't match a heading in the target (or the same document);
   - **stale tool versions**: any `<!-- forge-tool-version: id version -->` marker that disagrees with `plugins/forge/toolchain/manifest.json`;
   - **unenforced rule bullets**: any bullet in `.claude/rules/*.md` that names no hook/lint/check/gate/enforcement mechanism, and also isn't marked `advisory` (ADR-001 §13 point 6).
2. **Fix what's cheap and obvious**: a typo'd path, a renamed heading, a version marker that just needs bumping, or — for a rule bullet — naming its real mechanism (`hook`, `lint`, `check`, `gate`, `enforced`) if it truly has one. Use `Edit`, one targeted change per finding.
3. **For anything structural** (a rule that genuinely has no mechanism yet, a doc that needs real rewriting), mark the bullet `(advisory)` if it truly has no automated enforcement — never invent a mechanism it doesn't have — or report it rather than papering over it if it should be enforced but isn't yet; that's a `capturing-failures` or a real engineering task, not a doc edit.
4. **Cite the check result** (`out/verify/gardening.docs.json`) as evidence for "docs are internally consistent" claims, at level **L1**.

## Opting a doc into version tracking

Add a marker right after the version is stated:
```markdown
KiCad 10.0.6 is the pinned version. <!-- forge-tool-version: kicad-cli 10.0.6 -->
```
The tool id must match an entry's `id` in `plugins/forge/toolchain/manifest.json`.

## References

- `plugins/forge/toolchain/manifest.json` — the pinned-version source of truth this check compares against.
