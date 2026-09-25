"""plugins/forge/skills/init/scripts/scaffold.py -- must never overwrite an
existing file."""

from __future__ import annotations


def test_init_never_overwrites_existing_claude_md(tmp_path, init_mod, templates_dir, forge_root):
    target = tmp_path / "existing-repo"
    target.mkdir()
    sentinel = "# My pre-existing project instructions\nDo not touch this line.\n"
    (target / "CLAUDE.md").write_text(sentinel)

    report = init_mod.init(target, name="Existing Thing", forge_root=forge_root, templates_dir=templates_dir)

    assert (target / "CLAUDE.md").read_text() == sentinel, "init must never overwrite an existing file"
    assert (target / "CLAUDE.md") in report.conflicts


def test_init_writes_missing_files(tmp_path, init_mod, templates_dir, forge_root):
    target = tmp_path / "existing-repo-2"
    target.mkdir()
    report = init_mod.init(target, name="X", forge_root=forge_root, templates_dir=templates_dir)
    assert (target / "forge.toml").exists()
    assert (target / "forge.toml") in report.written
    assert (target / ".claude" / "settings.json") in report.written


def test_init_merges_gitignore_without_dropping_existing_lines(tmp_path, init_mod, templates_dir, forge_root):
    target = tmp_path / "existing-repo-3"
    target.mkdir()
    (target / ".gitignore").write_text("my-custom-ignore/\n")

    init_mod.init(target, name="X", forge_root=forge_root, templates_dir=templates_dir)

    text = (target / ".gitignore").read_text()
    assert "my-custom-ignore/" in text
    assert "out/" in text  # merged in from the template


def test_init_does_not_double_add_gitignore_lines_on_rerun(tmp_path, init_mod, templates_dir, forge_root):
    target = tmp_path / "existing-repo-4"
    target.mkdir()
    (target / ".gitignore").write_text("x/\n")
    init_mod.init(target, name="X", forge_root=forge_root, templates_dir=templates_dir)
    first = (target / ".gitignore").read_text()
    init_mod.init(target, name="X", forge_root=forge_root, templates_dir=templates_dir)
    second = (target / ".gitignore").read_text()
    assert first == second


def test_init_multiple_existing_files_all_survive(tmp_path, init_mod, templates_dir, forge_root):
    target = tmp_path / "existing-repo-5"
    target.mkdir()
    (target / "CLAUDE.md").write_text("keep me\n")
    (target / "Makefile").write_text("keep-me-too:\n\t@true\n")
    (target / "RISKS.md").write_text("my risks\n")

    report = init_mod.init(target, name="X", forge_root=forge_root, templates_dir=templates_dir)

    assert (target / "CLAUDE.md").read_text() == "keep me\n"
    assert (target / "Makefile").read_text() == "keep-me-too:\n\t@true\n"
    assert (target / "RISKS.md").read_text() == "my risks\n"
    conflict_names = {p.name for p in report.conflicts}
    assert {"CLAUDE.md", "Makefile", "RISKS.md"} <= conflict_names
