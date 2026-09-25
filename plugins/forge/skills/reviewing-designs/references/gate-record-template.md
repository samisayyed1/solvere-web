# `reviews/Gx.md` — gate record template

Fallback copy for the `gate-review` workflow when `templates/project/reviews/_gate-template.md`
doesn't exist in the target project yet (that scaffold file is owned by `new-project`/`init`,
not by this skill). If it exists, use it instead — it is the canonical template.

```markdown
# Gate {{GATE}} — {{SUBJECT}}

Date: {{DATE}}
Git SHA: {{GIT_SHA}}

## Criteria

| ID | Verdict | Reviewer | Evidence | Finding |
|---|---|---|---|---|
| ... | PASS/FAIL/BLOCKED | ... | out/verify/... | ... |

## Evidence links

- ...

## Evaluator verdict (forge:verification-evaluator)

​```json
{...verbatim verdict block...}
​```

## Red-team findings (forge:red-team)

​```json
{...verbatim verdict block...}
​```

## Specialist reviews

- ...

## Open risks

- ...

## Recommendation

{{ONE-PARAGRAPH SUMMARY: PASS / FAIL / BLOCKED, and why. Recommends only -- does not decide.}}

## Human sign-off

Human sign-off: ____________  Name: ____  Date: ____  Decision: PASS / FAIL
```

The sign-off line is **always** left blank by this skill's workflow. A PreToolUse hook
blocks any agent edit to a filled sign-off line (CONTRACTS.md §7); this skill relies on
that hook as the enforcing mechanism, not on remembering not to fill it in.
