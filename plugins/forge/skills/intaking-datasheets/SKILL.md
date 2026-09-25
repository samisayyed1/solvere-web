---
name: intaking-datasheets
description: Turn a datasheet (PDF or pasted/extracted text) into params/params.toml entries with status="datasheet" and a page-referenced source, and write a caliper-measurement procedure for anything the datasheet doesn't state. Use when the user provides a datasheet, MPN spec sheet, or component PDF and asks to pull values into params, or when docs/datasheets/*-intake.toml changes. Also fires from the mechanical.md path rule on params/**. Do NOT use to invent a value the datasheet doesn't state -- that always becomes a measurement procedure, never a guess.
paths:
  - "docs/datasheets/**"
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(${CLAUDE_SKILL_DIR}/scripts/intake.py:*), Bash(${CLAUDE_SKILL_DIR}/scripts/verify.py:*), Bash(forge-python ${CLAUDE_SKILL_DIR}/scripts/intake.py:*), Bash(forge-python ${CLAUDE_SKILL_DIR}/scripts/verify.py:*), Bash(pdftotext:*)
---

# Intaking datasheets

**Non-negotiable rules, read first:**
1. A value goes into `params/params.toml` only if a pattern actually matched text in the datasheet, with `status = "datasheet"` and `source = "<doc>, p.<N>"` -- **a real page number, not invented**. CONTRACTS.md §2 requires a page reference for every datasheet-sourced param, and `verify.py` fails a param whose source has no real page number (`p.unknown`, produced when the source text had no page markers at all) rather than accepting it.
2. A param the datasheet is silent on **never gets a guessed value**. It gets a caliper-measurement procedure written to `docs/measurements/<param>.md` instead (docs/brief/FORGE-BRIEF.md §0: never guess silently).
3. Extraction is by explicit, reviewable regex pattern per param (`[[param]]` in the intake spec), not free-form NLP parsing of the datasheet -- every match is exactly reproducible and the pattern is visible in the spec for a human to sanity-check.
4. `intake.py`/`verify.py` never overwrite an existing `params/params.toml` entry -- they only add params that aren't already present. Changing a value someone already recorded (especially a `verified` one) goes through the sourced-justification path (`forge params set`), not this skill.
5. Page numbers come from splitting the source text on form-feed (`\f`, what `pdftotext` inserts between pages) or `[PAGE n]` markers. A datasheet pasted as one undifferentiated blob of text cannot be cited by page -- fix the source text, don't fix the check.
6. A pattern's captured number is only trusted if the unit that follows it **in the datasheet text** agrees with the `[[param]]`'s declared `unit` -- a pattern that captures only digits (`([\d.]+)`, no unit literal) against text in a different unit (`"Length: 2.56 in"` with `unit = "mm"`) is rejected, never silently accepted with the spec's unit pasted onto the text's number.

## File format

`docs/datasheets/<name>-intake.toml`:

```toml
[datasheet]
doc = "ACME-1234 Rev C"       # exact string used in every source citation
text_file = "docs/datasheets/acme-1234.txt"   # OR: pdf = "docs/datasheets/acme-1234.pdf"

[[param]]
id = "battery.capacity_mah"          # -> params.toml key path (dotted -> nested tables)
pattern = 'Capacity:\s*([\d.]+)\s*mAh'   # first capture group is the numeric value
unit = "mAh"

[[param]]
id = "enclosure.wall_thickness"
pattern = 'Wall thickness:\s*([\d.]+)\s*mm'
unit = "mm"
tol_plus = 0.1                        # optional; omit for no tolerance
tol_minus = 0.1
```

If `text_file` doesn't exist yet, extract it first: `pdftotext -layout <the.pdf> docs/datasheets/<name>.txt` (this is exactly what `intake.py --pdf` does internally when given a PDF path directly -- either form works, and both preserve `\f` page breaks). If the datasheet was pasted rather than extracted from a PDF, insert `[PAGE n]` markers (or literal form-feed characters) between pages yourself when creating `text_file`.

## Running

```
forge-python ${CLAUDE_SKILL_DIR}/scripts/intake.py --project <root> --spec docs/datasheets/<name>-intake.toml   # low-level, one-off
forge-python ${CLAUDE_SKILL_DIR}/scripts/verify.py --project <root> [--changed docs/datasheets/<name>-intake.toml]
```

`verify.py` re-runs the intake (idempotently -- see rule 4) and then checks it. Writes `out/intake/<doc>.json` (what matched, what was silent, what got added, and what had a unit mismatch) and `out/verify/mech.datasheet_<doc>.json` with measurements `matched_params_in_params_toml`, `datasheet_params_have_page_ref`, `silent_params_have_measurement_procedure`, `matched_params_unit_agrees_with_text`. No `docs/datasheets/*-intake.toml` files means `[SKIP]` and exit 0.

**The unit is captured from the datasheet text itself, not just trusted from the spec.** Whatever unit token actually follows the matched number in the text (independent of whether the pattern's own non-captured text happened to include it) is compared against the `[[param]]`'s declared `unit`. A mismatch ("Length: 2.56 in" matched with `unit = "mm"`) is never written to `params/params.toml` and fails `matched_params_unit_agrees_with_text` -- fix the pattern or the unit, never guess which one is right.

## What this skill refuses

- Inventing a value for a param the datasheet doesn't state -- it writes a measurement procedure, never a number.
- Accepting a datasheet-sourced param whose source has no real page number.
- Writing a value to `params/params.toml` when the unit in the datasheet text disagrees with the spec's declared `unit`.
- Overwriting an existing `params/params.toml` entry (datasheet or otherwise) -- add-only.
- An intake spec with an empty `[[param]]` list -- exit 2, nothing to check.

See `references/pattern-writing.md` for tips on writing robust extraction patterns and common datasheet formatting traps.
