"""lib/forge/template_files.py: what a scaffolder copies out of templates/project/
must never include gitignored or generated files (D3, review #2)."""
from __future__ import annotations

import subprocess
from pathlib import Path

from forge.template_files import list_template_files


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)


def _init_repo(root: Path) -> None:
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "config", "user.name", "Forge Test")


def test_seeded_wrong_generated_file_is_excluded_under_git(tmp_path):
    """The specific defect D3 names: a stray out/verify/*.json left in the
    template tree (gitignored, never committed) must never be copied."""
    tpl = tmp_path / "templates" / "project"
    tpl.mkdir(parents=True)
    _init_repo(tpl.parent.parent)  # repo root above templates/, like the real layout
    (tpl / ".gitignore").write_text("out/\n__pycache__/\n.pytest_cache/\n")
    (tpl / "CLAUDE.md").write_text("# {{PROJECT_NAME}}\n")
    (tpl / "out" / "verify").mkdir(parents=True)
    (tpl / "out" / "verify" / "gardening.docs.json").write_text("{}")
    (tpl / "cad").mkdir()
    (tpl / "cad" / ".gitkeep").write_text("")
    _git(tpl.parent.parent, "add", "-A")
    _git(tpl.parent.parent, "commit", "-q", "-m", "seed template")

    files = list_template_files(tpl)
    rels = {p.as_posix() for p in files}
    assert "CLAUDE.md" in rels
    assert "cad/.gitkeep" in rels
    assert not any(r.startswith("out/") for r in rels), rels
    assert "out/verify/gardening.docs.json" not in rels


def test_real_template_dir_never_yields_an_out_file(templates_dir):
    """The real templates/project/, proven able to fail: temporarily drop a
    stray gitignored file into it (as happened for real -- the stray
    templates/project/out/ this fix also deletes) and confirm it is excluded."""
    stray = templates_dir / "out" / "verify" / "seeded_stray.json"
    stray.parent.mkdir(parents=True, exist_ok=True)
    stray.write_text("{}")
    try:
        files = list_template_files(templates_dir)
        rels = {p.as_posix() for p in files}
        assert not any(r.startswith("out/") for r in rels), rels
        assert "CLAUDE.md" in rels  # sanity: real content still listed
    finally:
        stray.unlink()
        # clean up the directories we created, but only if they're now empty
        for d in (stray.parent, stray.parent.parent):
            try:
                d.rmdir()
            except OSError:
                pass


def test_non_git_fallback_uses_explicit_exclude_list(tmp_path):
    """Outside a git work tree, the explicit exclude list still keeps
    generated/cache dirs out (no .gitignore to consult)."""
    tpl = tmp_path / "no-git-template"
    tpl.mkdir()
    (tpl / "CLAUDE.md").write_text("# X\n")
    (tpl / "__pycache__").mkdir()
    (tpl / "__pycache__" / "x.pyc").write_text("junk")
    (tpl / "out").mkdir()
    (tpl / "out" / "x.json").write_text("{}")
    (tpl / ".pytest_cache").mkdir()
    (tpl / ".pytest_cache" / "v").write_text("junk")

    files = list_template_files(tpl)
    rels = {p.as_posix() for p in files}
    assert rels == {"CLAUDE.md"}
