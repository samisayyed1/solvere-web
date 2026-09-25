---
name: releasing-designs
description: Build a versioned release bundle (STEP/STL/drawings, Gerbers/drill/pos, BOM, firmware binaries with sha256, test reports, evidence manifest, changelog, git SHA) under release/<version>/. Use only when explicitly asked to "release", "cut a release", "build the release bundle", or "package for fab/production" -- never fires on its own. Refuses unless release/APPROVAL.toml matches HEAD and the target gate has a filled human sign-off. Do not use this to design, review or actually place a fab/vendor order -- it only assembles files a human has already approved.
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, Bash(kicad-cli *), Bash(git rev-parse *), Bash(git describe *), Bash(~/.forge/bin/forge-python ${CLAUDE_SKILL_DIR}/scripts/release.py:*)
---

# Releasing designs

**Non-negotiable rules:**

1. **Never build a release without a valid, fresh, human approval.** `release/APPROVAL.toml` must exist, have every field, and its `git_sha` must equal the current `git rev-parse HEAD` exactly — a sha from an earlier commit is stale and refused, not "close enough."
2. **Never build a release without a filled gate sign-off.** The gate `APPROVAL.toml` names must have its `reviews/<gate>.md` sign-off line filled in, with `Decision: PASS` unambiguously (not the blank template, not `FAIL`).
3. **Never build a release past UNVERIFIED evidence or a failing check.** Any `evidence/manifest.json` entry with `status: "UNVERIFIED"` or `result: "fail"`, or any `out/verify/*.json` check result that is `fail`/`error`, refuses the release (ADR-001 §11).
3. **This skill never creates or edits `release/APPROVAL.toml`.** That file is written by a human. If asked to write or fake one, decline and explain what's needed instead.
4. **A missing input category is noted, not silently dropped.** If `out/cad/` has no STEP yet, or `bom/` is empty, the bundle still builds (for whatever *is* ready) and `RELEASE-MANIFEST.json` says exactly what was skipped and why.

## Workflow

1. Ask the user (or check) that a human has already:
   - filled the target gate's sign-off in `reviews/<gate>.md` with `Decision: PASS`;
   - written `release/APPROVAL.toml` (`approved_by`, `date`, `git_sha` = current HEAD, `scope`, `gate`).
   If either is missing, say so and stop — do not attempt the release.
2. Run: `~/.forge/bin/forge-python ${CLAUDE_SKILL_DIR}/scripts/release.py --project <root> [--version <v>]`. It:
   - re-validates the approval and sign-off itself (never trust that step 1's check is still true — the repo may have changed);
   - builds `release/<version>/` with whatever's ready: CAD (from `out/cad/`), ECAD fab outputs (`kicad-cli pcb export gerbers/drill/pos` per `ecad/*.kicad_pcb`), BOM (`bom/`), firmware binaries with a `SHA256SUMS` file (from `out/verify/fw_build/`), test reports and the evidence manifest, a changelog if one exists, and `GIT_SHA.txt`;
   - writes `RELEASE-MANIFEST.json` recording exactly what was included vs. skipped and why.
3. **On refusal** (exit 1), relay the exact reason (missing/stale approval, unsigned or FAIL gate) — never work around it, never suggest bypassing it.
4. **Report the bundle contents** to the user from `RELEASE-MANIFEST.json`, including every skipped category, and remind them that Gerbers/BOM going to an actual fab or vendor order is a separate, explicit human action this skill does not take.

## What this skill refuses

- Building any bundle without a fresh `release/APPROVAL.toml` matching HEAD.
- Building any bundle whose gate sign-off is blank, unrecognized, or `FAIL`.
- Writing or editing `release/APPROVAL.toml` itself, under any framing ("just this once", "I have owner approval in chat").
- Placing an actual fab or vendor order — this skill only assembles files.
