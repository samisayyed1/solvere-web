---
max_turns: 40
timeout_seconds: 1500
allowed_tools: [Read, Glob, Grep, Edit, Write, Bash, Skill, TodoWrite]
---

Implement the debounced button state machine in docs/debounce-spec.md against the fixed API in firmware/include/debounce.h: put the code in firmware/src/debounce.c and unit tests in firmware/tests/test_debounce.c. Build and test it on the host with gcc, and prove the tests would catch a broken implementation.
