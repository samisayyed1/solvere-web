"""writing-adrs/scripts/new_adr.py: sequential numbering, never overwrites."""
from __future__ import annotations

from .conftest import load_skill_module

new_adr = load_skill_module("writing-adrs", "new_adr.py")


def test_first_adr_is_001(tmp_path):
    path_str = _run(tmp_path, "Use tscircuit over atopile")
    assert path_str.endswith("ADR-001-use-tscircuit-over-atopile.md")


def test_numbers_increment_from_existing(tmp_path):
    (tmp_path / "docs" / "decisions").mkdir(parents=True)
    (tmp_path / "docs" / "decisions" / "ADR-001-forge-architecture.md").write_text("x")
    (tmp_path / "docs" / "decisions" / "ADR-007-something.md").write_text("x")
    path_str = _run(tmp_path, "Pin build123d at 0.11.1")
    assert path_str.endswith("ADR-008-pin-build123d-at-0-11-1.md")


def test_never_overwrites_a_colliding_path(tmp_path, monkeypatch):
    """Sequential numbering (max existing + 1) means a fresh call can never
    naturally collide with an existing file -- any pre-existing ADR is
    itself counted, which only pushes the next number forward. Prove the
    defensive out_path.exists() guard directly by forcing next_number() to
    return a number that collides (simulating a race or a hand-numbered
    file), and confirm the target is left untouched."""
    decisions = tmp_path / "docs" / "decisions"
    decisions.mkdir(parents=True)
    sentinel = "# ADR-001 -- Duplicate title\nDo not overwrite this.\n"
    (decisions / "ADR-001-duplicate-title.md").write_text(sentinel)

    monkeypatch.setattr(new_adr, "next_number", lambda adr_dir: 1)

    rc = new_adr.main([
        "--project", str(tmp_path), "--title", "Duplicate title", "--date", "2026-09-25",
    ])
    assert rc == 1
    assert (decisions / "ADR-001-duplicate-title.md").read_text() == sentinel


def _run(tmp_path, title: str) -> str:
    rc_and_path = []
    import io
    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = new_adr.main(["--project", str(tmp_path), "--title", title, "--date", "2026-09-25"])
    assert rc == 0
    return buf.getvalue().strip()
