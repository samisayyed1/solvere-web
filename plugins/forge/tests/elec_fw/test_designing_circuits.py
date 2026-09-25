"""designing-circuits verify.py: spice PASS / seeded out-of-spec FAIL / shell-bearing netlist refused."""
from __future__ import annotations

import json

import pytest

from .conftest import load_skill_module, require_tool

DIVIDER_CIR = """\
regulator-like output with ripple
V1 in 0 DC 5 AC 0 SIN(5 0.05 1k)
R1 in out 1k
R2 out 0 1k
.tran 10u 5m
.control
run
meas tran vout_dc avg v(out) from=2m to=5m
meas tran ripple_pp pp v(out) from=2m to=5m
quit
.endc
.end
"""

SHELL_CIR = """\
malicious netlist
V1 in 0 DC 5
R1 in 0 1k
.control
shell touch shell_marker.txt
run
.endc
.end
"""


@pytest.fixture(autouse=True)
def _tools():
    require_tool("ngspice")
    require_tool("srt")


@pytest.fixture
def verify_mod():
    return load_skill_module("designing-circuits")


@pytest.fixture
def project(tmp_path):
    spice_dir = tmp_path / "analysis" / "spice"
    spice_dir.mkdir(parents=True)
    return tmp_path


def _write_divider(project, name, limits_toml):
    spice_dir = project / "analysis" / "spice"
    (spice_dir / f"{name}.cir").write_text(DIVIDER_CIR)
    (spice_dir / f"{name}.limits.toml").write_text(limits_toml)


def test_spice_pass_within_spec(verify_mod, project):
    _write_divider(project, "regulator", """\
[[measurement]]
name = "vout_dc"
unit = "V"
equals = 2.5
tol = 0.05
requirement = "REQ-ELEC-010"

[[measurement]]
name = "ripple_pp"
unit = "V"
max = 0.1
requirement = "REQ-ELEC-011"
""")
    rc = verify_mod.main(["--project", str(project)])
    assert rc == 0
    result = json.loads((project / "out/verify/spice.regulator.json").read_text())
    assert result["status"] == "pass"
    assert result["level"] == "L2"
    assert {m["name"] for m in result["measurements"]} == {"vout_dc", "ripple_pp"}
    assert all(m["pass"] for m in result["measurements"])


def test_spice_seeded_out_of_spec_fails_with_remediation(verify_mod, project):
    _write_divider(project, "regulator", """\
[[measurement]]
name = "vout_dc"
unit = "V"
equals = 3.3
tol = 0.066
requirement = "REQ-ELEC-010"
remediation = "vout_dc must be 3.3 V +/- 2%; check the feedback divider."

[[measurement]]
name = "ripple_pp"
unit = "V"
max = 0.1
requirement = "REQ-ELEC-011"
""")
    rc = verify_mod.main(["--project", str(project)])
    assert rc == 1
    result = json.loads((project / "out/verify/spice.regulator.json").read_text())
    assert result["status"] == "fail"
    vout = next(m for m in result["measurements"] if m["name"] == "vout_dc")
    assert vout["pass"] is False
    assert "3.3" in vout["remediation"] or "feedback" in vout["remediation"]
    # the in-spec ripple measurement still ran and still passed
    ripple = next(m for m in result["measurements"] if m["name"] == "ripple_pp")
    assert ripple["pass"] is True


def test_netlist_with_shell_command_is_refused_and_never_run(verify_mod, project):
    spice_dir = project / "analysis" / "spice"
    (spice_dir / "malicious.cir").write_text(SHELL_CIR)
    (spice_dir / "malicious.limits.toml").write_text("""\
[[measurement]]
name = "vout_dc"
unit = "V"
min = 0
""")
    rc = verify_mod.main(["--project", str(project)])
    assert rc == 2  # refused -> internal error, never a pass
    result = json.loads((project / "out/verify/spice.malicious.json").read_text())
    assert result["status"] == "error"
    assert "shell" in result["error"].lower()
    # the shell command was never actually executed
    assert not (project / "shell_marker.txt").exists()
    assert not (project / "analysis" / "spice" / "shell_marker.txt").exists()


def test_no_netlists_is_a_clean_skip(verify_mod, tmp_path):
    rc = verify_mod.main(["--project", str(tmp_path)])
    assert rc == 0


def test_missing_sidecar_limits_file_errors(verify_mod, project):
    (project / "analysis" / "spice" / "nolimits.cir").write_text(DIVIDER_CIR)
    rc = verify_mod.main(["--project", str(project)])
    assert rc == 2
    result = json.loads((project / "out/verify/spice.nolimits.json").read_text())
    assert result["status"] == "error"
    assert "limits" in result["error"].lower()


def test_control_block_shell_detector_is_text_scoped(verify_mod):
    assert verify_mod.refuses_shell(SHELL_CIR) is not None
    assert verify_mod.refuses_shell(DIVIDER_CIR) is None
    # "shell" mentioned outside a .control block must not trigger a false refusal
    assert verify_mod.refuses_shell("* this comment talks about a shell command\n.control\nrun\n.endc\n") is None
