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


# --- S9 (review-2 addendum): SI-prefix unit normalisation of limits ---

def test_si_unit_scale_converts_mv_and_rejects_garbage(verify_mod):
    assert verify_mod.si_unit_scale("V") == 1.0
    assert verify_mod.si_unit_scale("mV") == pytest.approx(1e-3)
    assert verify_mod.si_unit_scale("kOhm") == pytest.approx(1e3)
    assert verify_mod.si_unit_scale("1") == 1.0
    with pytest.raises(ValueError):
        verify_mod.si_unit_scale("Vrms")
    with pytest.raises(ValueError):
        verify_mod.si_unit_scale("dB")


def test_seeded_mv_limit_against_a_50mv_ripple_fails_not_passes(verify_mod, project):
    """S9 seeded-wrong case: a limit declared in mV compared against a real 0.05 V (50 mV)
    ripple. Before the fix, the raw 0.0499923 (still volts) was compared directly to
    max = 40 and passed (recorded as "0.0499923 mV") -- the true 49.99 mV is over the
    40 mV limit and must FAIL."""
    _write_divider(project, "regulator", """\
[[measurement]]
name = "vout_dc"
unit = "V"
equals = 2.5
tol = 0.05
requirement = "REQ-ELEC-010"

[[measurement]]
name = "ripple_pp"
unit = "mV"
max = 40
requirement = "REQ-ELEC-011"
""")
    rc = verify_mod.main(["--project", str(project)])
    assert rc == 1
    result = json.loads((project / "out/verify/spice.regulator.json").read_text())
    assert result["status"] == "fail"
    ripple = next(m for m in result["measurements"] if m["name"] == "ripple_pp")
    assert ripple["pass"] is False
    assert ripple["unit"] == "mV"
    assert ripple["value"] == pytest.approx(49.9923, abs=0.01)
    assert ripple["limit"]["max"] == 40


def test_mv_limit_against_a_below_spec_ripple_passes(verify_mod, project):
    """Pass case for the same mV normalisation: a 40 mV limit against the real ~50 mV
    ripple's decimillivolt cousin -- raise the limit comfortably above the converted
    measurement and it must pass."""
    _write_divider(project, "regulator", """\
[[measurement]]
name = "vout_dc"
unit = "V"
equals = 2.5
tol = 0.05
requirement = "REQ-ELEC-010"

[[measurement]]
name = "ripple_pp"
unit = "mV"
max = 100
requirement = "REQ-ELEC-011"
""")
    rc = verify_mod.main(["--project", str(project)])
    assert rc == 0
    result = json.loads((project / "out/verify/spice.regulator.json").read_text())
    ripple = next(m for m in result["measurements"] if m["name"] == "ripple_pp")
    assert ripple["pass"] is True
    assert ripple["value"] == pytest.approx(49.9923, abs=0.01)


def test_unrecognised_unit_errors_instead_of_silently_comparing_raw(verify_mod, project):
    _write_divider(project, "regulator", """\
[[measurement]]
name = "vout_dc"
unit = "Vrms"
equals = 2.5
tol = 0.05
requirement = "REQ-ELEC-010"
""")
    rc = verify_mod.main(["--project", str(project)])
    assert rc == 2
    result = json.loads((project / "out/verify/spice.regulator.json").read_text())
    assert result["status"] == "error"
    assert "Vrms" in result["error"]


def test_control_block_shell_detector_is_text_scoped(verify_mod):
    assert verify_mod.refuses_shell(SHELL_CIR) is not None
    assert verify_mod.refuses_shell(DIVIDER_CIR) is None
    # "shell" mentioned outside a .control block must not trigger a false refusal
    assert verify_mod.refuses_shell("* this comment talks about a shell command\n.control\nrun\n.endc\n") is None
