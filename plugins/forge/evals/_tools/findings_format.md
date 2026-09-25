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
