---
max_turns: 50
timeout_seconds: 2400
allowed_tools: [Read, Glob, Grep, Edit, Write, Bash, Skill, TodoWrite]
---

Design the shelf bracket in docs/bracket-brief.md as cad/bracket.py (build123d, build(), dimensions in params/params.toml) and prove it meets REQ-MECH-020 and REQ-MECH-021 with an FEA case at analysis/fea/bracket.toml (case name "bracket"), including a hand-calc cross-check. Export a STEP to out/step/bracket.step.
