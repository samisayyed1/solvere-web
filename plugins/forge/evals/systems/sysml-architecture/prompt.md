---
max_turns: 25
timeout_seconds: 1200
allowed_tools: [Read, Glob, Grep, Edit, Write, Bash, Skill]
---

Turn docs/architecture.md into a SysML v2 textual model in model/system.sysml: every block as a part, the power, UART and I2C interfaces as ports and connections, and both requirements linked. Make sure the model validates cleanly.
