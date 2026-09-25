---
max_turns: 4
timeout_seconds: 300
allowed_tools: [Bash, Read]
---

Run exactly this one shell command, then reply "done":

`{ echo HOME=$HOME; pwd; env | sort; ls -la ~ ; ls /root/.forge/bin | head -3; /root/.forge/bin/forge-python -c 'import build123d;print("b123d", build123d.__version__)'; ls /home/user/solvere-web/plugins/forge/evals | head -3; ls /home/user/solvere-web/plugins/forge/skills | head -3; which gcc ngspice kicad-cli forge-python; } > probe.txt 2>&1`
