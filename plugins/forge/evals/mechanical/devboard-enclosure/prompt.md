---
max_turns: 60
timeout_seconds: 2400
allowed_tools: [Read, Glob, Grep, Edit, Write, Bash, Skill, TodoWrite]
---

Design a parametric FDM (ABS) enclosure for the dev board in docs/board.md: a base in cad/enclosure_base.py and a snap-fit lid in cad/lid.py, each exposing build(), with the lid modelled in its closed position and every dimension in params/params.toml. A USB-C plug must fit into the board's port. The specs in requirements/geometry/ and requirements/dfm/ are the acceptance tests: don't weaken them; only add the lid_latch snap-fit entry where marked. Get every check passing, export STEP files of both parts to out/step/, and save an isometric render of the closed assembly to out/renders/assembly_iso.png.
