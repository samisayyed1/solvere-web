---
max_turns: 50
timeout_seconds: 2400
allowed_tools: [Read, Glob, Grep, Edit, Write, Bash, Skill, TodoWrite]
---

Model the spur gear pair in requirements/requirements.md: cad/pinion.py (centred on the origin, axis along Z) and cad/gear.py (placed on +X at the standard centre distance, rotated so the teeth mesh), both with true involute teeth and every gear parameter in params/params.toml. The geometry specs in requirements/geometry/ are the acceptance tests; don't edit them. Get them passing and export STEP files to out/step/.
