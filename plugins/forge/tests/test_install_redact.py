"""toolchain/install.sh's redact(): machine-specific paths must never reach
INSTALL-LOG.md (N13, review #2). Sources the real script (with its trailing
``main "$@"`` call stripped, so nothing actually installs) into a bash
subshell and pipes lines through the real ``redact`` function -- proving the
function itself, not a reimplementation of it."""
from __future__ import annotations

import shlex
import subprocess
from pathlib import Path

import pytest

INSTALL_SH = Path(__file__).resolve().parents[1] / "toolchain" / "install.sh"


@pytest.fixture
def redact_env(tmp_path):
    """A scratch copy of install.sh (main() stripped, so nothing installs),
    at the same repo-relative depth as the real one so its own REPO_ROOT
    computation (three directories up from toolchain/) resolves correctly.
    Returns (redact(line, forge_home=...), repo_root)."""
    script = INSTALL_SH.read_text()
    assert 'main "$@"' in script, "install.sh's structure changed; update this test's stripping"
    no_main = script.replace('main "$@"', "")  # never invoke main -- only source function defs

    repo_root = tmp_path / "repo"
    fake_toolchain = repo_root / "plugins" / "forge" / "toolchain"
    fake_toolchain.mkdir(parents=True)
    fake_install = fake_toolchain / "install.sh"
    fake_install.write_text(no_main)

    def redact(line: str, *, forge_home: str = "/root/.forge") -> str:
        cmd = f"source {shlex.quote(str(fake_install))}; printf '%s\\n' {shlex.quote(line)} | redact"
        proc = subprocess.run(
            ["bash", "-c", cmd],
            env={"FORGE_HOME": forge_home, "PATH": "/usr/bin:/bin"},
            capture_output=True, text=True, timeout=20,
        )
        assert proc.returncode == 0, f"redact() failed: {proc.stderr}"
        return proc.stdout.strip()

    return redact, str(repo_root)


def test_seeded_wrong_macos_home_path_is_redacted(redact_env):
    """The exact defect N13 names: a /Users/<name>/... path must not survive."""
    redact, _ = redact_env
    out = redact("Removing: /Users/samisayyed/Library/Caches/Homebrew/bootsnap/abc")
    assert "/Users/samisayyed" not in out, out
    assert out == "Removing: ~/Library/Caches/Homebrew/bootsnap/abc"


def test_seeded_wrong_root_home_path_is_redacted(redact_env):
    redact, _ = redact_env
    out = redact("linked /root/.forge/bin/git -> /root/.forge/envs/core/.pixi/envs/default/bin/git")
    assert "/root/" not in out, out
    assert out == "linked ~/.forge/bin/git -> ~/.forge/envs/core/.pixi/envs/default/bin/git"


def test_forge_home_value_is_redacted_to_tilde_forge(redact_env):
    """$FORGE_HOME itself (whatever custom value it resolves to) becomes ~/.forge."""
    redact, _ = redact_env
    out = redact("wrote /custom/forge/home/bin/tsci", forge_home="/custom/forge/home")
    assert "/custom/forge/home" not in out, out
    assert out == "wrote ~/.forge/bin/tsci"


def test_pass_case_repo_root_and_unrelated_text_still_handled(redact_env):
    """Positive case: $REPO_ROOT redaction (pre-existing behaviour) and
    ordinary text without any machine path both survive unchanged."""
    redact, repo_root = redact_env
    out = redact(f"running {repo_root}/plugins/forge/toolchain/smoke.py")
    assert out == "running <repo>/plugins/forge/toolchain/smoke.py"

    plain = redact("added 303 packages in 32s")
    assert plain == "added 303 packages in 32s"
