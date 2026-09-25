# `ecad/waivers.toml` — waiver format

Every ERC/DRC violation must either be fixed, or explicitly waived with a reason and an
approver — never silently ignored. `scripts/verify.py` rejects (errors, exit 2) any
waiver missing either field: an unapproved waiver is worse than no waiver, because it
looks like the violation was reviewed when it wasn't.

```toml
[[waiver]]
rule_id = "footprint_link_issues"   # matches the KiCad "type" field in the ERC/DRC JSON
reason = "Library metadata missing on this vendored demo board; confirmed non-functional."
approver = "jane.doe"               # a human name or id -- required
date = "2026-09-25"                 # required
max_count = 31                      # optional: waive at most N occurrences of this rule_id;
                                     # omit to waive every occurrence
```

- `rule_id` must match the `type` field KiCad's ERC/DRC JSON reports for that violation
  (run the check once without a waiver and read `out/verify/erc.json` / `drc.json` to find
  the exact string).
- `reason` and `approver` are both required and must be non-empty, or the whole check
  errors out rather than silently applying a half-written waiver.
- `max_count` caps how many occurrences the waiver covers; violations beyond the cap still
  fail the check. Omit it to waive every occurrence of that `rule_id`.
- A waiver never suppresses the sign-off requirement before fabrication (see SKILL.md) --
  it only tells the automated check to stop flagging a specific, reviewed violation.
