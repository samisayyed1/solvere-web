---
max_turns: 40
timeout_seconds: 1800
allowed_tools: [Read, Glob, Grep, Bash, Write, Agent, Skill, TodoWrite]
---
This repo holds a product's compliance mapping package (`compliance/product-profile.toml`, cross-checked against `requirements/`), heading for its G0 gate. Review it as an independent reviewer: run the mapping-compliance check (`forge verify --domain compliance`, or `skills/mapping-compliance/scripts/verify.py` directly) and find every defect that makes the compliance mapping wrong -- an invalid market code, a radio the requirements name that the profile omits, a radio the profile claims that no requirement traces, or any other mismatch between the profile and the rest of the project. Do not change any file other than the findings file; do not try to "fix" the profile.

Write your findings to `out/review/findings.json` in exactly this format (UTF-8 JSON, one object per distinct defect, every field a flat string, no nested objects):

```json
{"schema": "forge.findings/1",
 "findings": [
  {"file": "<repo-relative path of the artifact at fault>",
   "location": "<the element: profile field, radio id, or market code>",
   "category": "<short defect category>",
   "severity": "critical|major|minor",
   "description": "<what is wrong, citing the check's own measurement and remediation>"}
 ]}
```
