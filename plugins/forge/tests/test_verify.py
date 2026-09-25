"""forge verify: entrypoint discovery, ladder aggregation and evidence recording (CONTRACTS.md §9)."""
from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path

import pytest

from forge import evidence
from forge.commands import verify

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"  # real plugins/forge/lib, put on subprocess PYTHONPATH


def _write_entrypoint(plugin_root: Path, skill: str, body: str) -> None:
    script = plugin_root / "skills" / skill / "scripts" / "verify.py"
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text(textwrap.dedent(body))


# These fake entrypoints rely on PYTHONPATH (set to the real plugins/forge/lib by the
# `forge_python_env` fixture below) rather than the parents[3]/"lib" convention, because
# the fake plugin_root used here has no lib/ of its own -- only forge_verify's own
# orchestration is under test, not the skills' own import convention.
PASS_ENTRYPOINT = """\
    import sys
    from pathlib import Path
    from forge.checkresult import run_check
    with run_check("demo.pass_check", "demo/target", project=Path(sys.argv[sys.argv.index("--project") + 1])) as chk:
        chk.measure("value", 1.0, "1", min=0.0)
"""

FAIL_ENTRYPOINT = """\
    import sys
    from pathlib import Path
    from forge.checkresult import run_check
    with run_check("demo.fail_check", "demo/target", project=Path(sys.argv[sys.argv.index("--project") + 1])) as chk:
        chk.measure("value", -1.0, "1", min=0.0, remediation="value must be >= 0 (seeded failure)")
"""

ERROR_ENTRYPOINT = """\
    import sys
    sys.exit(2)
"""


@pytest.fixture(autouse=True)
def forge_python_env(monkeypatch):
    monkeypatch.setenv("PYTHONPATH", str(LIB_DIR))


def _forge_toml(*, blocks: str) -> str:
    return "[project]\nname = \"demo\"\ngate = \"G0\"\n\n" + blocks


@pytest.fixture
def project(tmp_path):
    p = tmp_path / "project"
    p.mkdir()
    return p


@pytest.fixture
def plugin_repo(tmp_path):
    """A fake ``forge_root`` containing plugins/forge/skills/<skill>/scripts/verify.py."""
    return tmp_path / "repo"


class NS:
    def __init__(self, *, all=False, changed=None, project=Path("."), fast=False):
        self.all = all
        self.changed = changed
        self.project = project
        self.fast = fast


def test_missing_forge_toml_is_an_error(project, plugin_repo, monkeypatch):
    assert verify.run(NS(all=True, project=project), plugin_repo) == 2


def test_pass_only_aggregates_zero(project, plugin_repo, monkeypatch):
    _write_entrypoint(plugin_repo / "plugins" / "forge", "skill-a", PASS_ENTRYPOINT)
    (project / "forge.toml").write_text(_forge_toml(blocks=textwrap.dedent("""\
        [[verify]]
        domain = "mech"
        paths = ["cad/**"]
        entrypoints = ["skill-a"]
        rung = "numeric"
    """)))
    assert verify.run(NS(all=True, project=project), plugin_repo) == 0
    entries = evidence.load(project)["entries"]
    assert len(entries) == 1 and entries[0]["result"] == "pass" and entries[0]["domain"] == "mech"


def test_fail_aggregates_one_error_aggregates_two(project, plugin_repo, monkeypatch):
    forge_plugin = plugin_repo / "plugins" / "forge"
    _write_entrypoint(forge_plugin, "skill-pass", PASS_ENTRYPOINT)
    _write_entrypoint(forge_plugin, "skill-fail", FAIL_ENTRYPOINT)
    (project / "forge.toml").write_text(_forge_toml(blocks=textwrap.dedent("""\
        [[verify]]
        domain = "mech"
        paths = ["cad/**"]
        entrypoints = ["skill-pass"]
        rung = "numeric"

        [[verify]]
        domain = "elec"
        paths = ["ecad/**"]
        entrypoints = ["skill-fail"]
        rung = "numeric"
    """)))
    # both domains run under --all -> one FAIL, no ERROR -> aggregate exit 1
    assert verify.run(NS(all=True, project=project), plugin_repo) == 1

    # now add an erroring entrypoint -> aggregate exit 2 (error beats fail)
    _write_entrypoint(forge_plugin, "skill-error", ERROR_ENTRYPOINT)
    (project / "forge.toml").write_text(_forge_toml(blocks=textwrap.dedent("""\
        [[verify]]
        domain = "mech"
        paths = ["cad/**"]
        entrypoints = ["skill-pass"]
        rung = "numeric"

        [[verify]]
        domain = "elec"
        paths = ["ecad/**"]
        entrypoints = ["skill-fail"]
        rung = "numeric"

        [[verify]]
        domain = "fw"
        paths = ["firmware/**"]
        entrypoints = ["skill-error"]
        rung = "build"
    """)))
    assert verify.run(NS(all=True, project=project), plugin_repo) == 2


def test_missing_entrypoint_script_is_skip_not_failure(project, plugin_repo, monkeypatch):
    _write_entrypoint(plugin_repo / "plugins" / "forge", "skill-pass", PASS_ENTRYPOINT)
    (project / "forge.toml").write_text(_forge_toml(blocks=textwrap.dedent("""\
        [[verify]]
        domain = "mech"
        paths = ["cad/**"]
        entrypoints = ["skill-pass", "not-built-yet"]
        rung = "numeric"
    """)))
    assert verify.run(NS(all=True, project=project), plugin_repo) == 0


def test_changed_only_runs_matching_domains(project, plugin_repo, monkeypatch):
    forge_plugin = plugin_repo / "plugins" / "forge"
    _write_entrypoint(forge_plugin, "skill-fail", FAIL_ENTRYPOINT)
    (project / "forge.toml").write_text(_forge_toml(blocks=textwrap.dedent("""\
        [[verify]]
        domain = "mech"
        paths = ["cad/**"]
        entrypoints = ["skill-fail"]
        rung = "numeric"

        [[verify]]
        domain = "elec"
        paths = ["ecad/**"]
        entrypoints = ["skill-fail"]
        rung = "numeric"
    """)))
    # only touch ecad/ -> only the elec domain (and its failing check) should run
    assert verify.run(NS(changed=["ecad/reg.py"], project=project), plugin_repo) == 1
    entries = evidence.load(project)["entries"]
    assert len(entries) == 1 and entries[0]["domain"] == "elec"


def test_missing_forge_python_is_an_error_not_a_pass(project, plugin_repo, monkeypatch):
    monkeypatch.setenv("FORGE_PYTHON", str(project / "does-not-exist"))
    _write_entrypoint(plugin_repo / "plugins" / "forge", "skill-pass", PASS_ENTRYPOINT)
    (project / "forge.toml").write_text(_forge_toml(blocks=textwrap.dedent("""\
        [[verify]]
        domain = "mech"
        paths = ["cad/**"]
        entrypoints = ["skill-pass"]
        rung = "numeric"
    """)))
    assert verify.run(NS(all=True, project=project), plugin_repo) == 2
