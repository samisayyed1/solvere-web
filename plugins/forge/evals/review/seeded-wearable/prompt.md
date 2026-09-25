---
max_turns: 40
timeout_seconds: 1800
allowed_tools: [Read, Glob, Grep, Write, Agent, Skill, TodoWrite]
---
This repo holds the PulseBand wrist sensor rev B design package, heading for its G2 (CDR) gate. Review it as an independent reviewer: find every defect that affects requirements, safety, fit, function, manufacturability or cost (not style), and give the numbers that show each one. Do not change any file other than the findings file.

Write your findings to `out/review/findings.json` in exactly this format (UTF-8 JSON, one object per distinct defect, every field a flat string, no nested objects):

```json
{"schema": "forge.findings/1",
 "findings": [
  {"file": "<repo-relative path of the artifact at fault>",
   "location": "<the element: param key, requirement ID, part feature, reference designator or net>",
   "category": "<short defect category>",
   "severity": "critical|major|minor",
   "description": "<what is wrong: measured or stated value vs the requirement or limit, with units>"}
 ]}
```
