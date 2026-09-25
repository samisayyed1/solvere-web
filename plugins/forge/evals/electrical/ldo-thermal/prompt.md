---
max_turns: 30
timeout_seconds: 1200
allowed_tools: [Read, Glob, Grep, Edit, Write, Bash, Skill, TodoWrite]
---

Check the supply design in ecad/power.md against REQ-ELEC-011 with a simulation at worst-case input and full load: put it in analysis/spice/ldo_thermal.cir with a limits file, and don't change the design. Is the requirement met? If not, what would you change?
