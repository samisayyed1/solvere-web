"""plugins/forge/skills/new-project/scripts/scaffold.py"""

from __future__ import annotations

import pytest


def test_scaffold_writes_expected_top_level_files(scaffolded_project):
    for name in ("CLAUDE.md", "AGENTS.md", "ASSUMPTIONS.md", "RISKS.md", "Makefile",
                 "forge.toml", ".mcp.json", ".gitignore"):
        assert (scaffolded_project / name).is_file(), name


def test_scaffold_writes_expected_directories(scaffolded_project):
    for name in ("requirements", "model", "params", "cad", "ecad", "firmware", "app",
                 "analysis", "mfg", "bom", "compliance", "tests", "evidence", "reviews",
                 "docs/decisions", "release", ".claude/rules"):
        assert (scaffolded_project / name).is_dir(), name


def test_scaffold_refuses_nonempty_directory(tmp_path, new_project_mod, templates_dir, forge_root):
    target = tmp_path / "occupied"
    target.mkdir()
    (target / "existing-file.txt").write_text("don't touch me\n")

    with pytest.raises(new_project_mod.ScaffoldError):
        new_project_mod.scaffold(target, name="X", forge_root=forge_root, templates_dir=templates_dir)

    # the existing file must survive untouched, and nothing else was written
    assert (target / "existing-file.txt").read_text() == "don't touch me\n"
    assert not (target / "CLAUDE.md").exists()


def test_scaffold_accepts_empty_existing_directory(tmp_path, new_project_mod, templates_dir, forge_root):
    target = tmp_path / "empty-but-exists"
    target.mkdir()
    written = new_project_mod.scaffold(target, name="X", forge_root=forge_root, templates_dir=templates_dir)
    assert written
    assert (target / "CLAUDE.md").exists()


def test_scaffold_never_copies_gitignored_or_generated_template_files(
    tmp_path, new_project_mod, templates_dir, forge_root
):
    """D3, review #2: a stray gitignored file left in templates/project/ (the
    real bug -- templates/project/out/verify/gardening.docs.json) must never
    land in a scaffolded project."""
    stray = templates_dir / "out" / "verify" / "seeded_stray.json"
    stray.parent.mkdir(parents=True, exist_ok=True)
    stray.write_text("{}")
    pycache = templates_dir / "cad" / "__pycache__"
    pycache.mkdir(parents=True, exist_ok=True)
    (pycache / "seeded.pyc").write_bytes(b"junk")
    try:
        target = tmp_path / "clean-project"
        new_project_mod.scaffold(target, name="X", forge_root=forge_root, templates_dir=templates_dir)
        assert not (target / "out").exists()
        assert not any((target / "cad").rglob("__pycache__"))
        assert not any((target / "cad").rglob("*.pyc"))
        assert (target / "CLAUDE.md").exists()  # sanity: real content still scaffolded
    finally:
        stray.unlink()
        for d in (stray.parent, stray.parent.parent):
            try:
                d.rmdir()
            except OSError:
                pass
        (pycache / "seeded.pyc").unlink()
        pycache.rmdir()


def test_scaffold_cli_exit_code_on_nonempty_dir(tmp_path):
    import subprocess
    import sys
    from pathlib import Path

    script = (Path(__file__).resolve().parent.parent.parent
              / "skills" / "new-project" / "scripts" / "scaffold.py")
    target = tmp_path / "cli-occupied"
    target.mkdir()
    (target / "x.txt").write_text("x")
    proc = subprocess.run(
        [sys.executable, str(script), str(target), "--skip-doctor"],
        capture_output=True, text=True,
    )
    assert proc.returncode == 1
    assert "non-empty" in proc.stderr
