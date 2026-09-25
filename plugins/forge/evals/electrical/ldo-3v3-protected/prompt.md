---
max_turns: 60
timeout_seconds: 2400
allowed_tools: [Read, Glob, Grep, Edit, Write, Bash, Skill, TodoWrite]
---

Design the 3.3 V power stage in requirements/requirements.md: USB 5 V in, 300 mA load, reverse-polarity protection and a TVS on the input. Capture it as circuit code exported to ecad/ldo_3v3.kicad_sch, run ERC on it (ecad/waivers.toml holds the only waivers I've approved), and simulate the regulated output at minimum input and full load as analysis/spice/ldo_3v3.cir with its limits file. Show me the results.
