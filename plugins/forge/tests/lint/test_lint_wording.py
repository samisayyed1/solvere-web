"""Tests for `forge lint wording` (CONTRACTS.md SS4, ADR-001 D15)."""

from __future__ import annotations

from forge.lintlib import wording


def _write(tmp_path, name, content):
    p = tmp_path / name
    p.write_text(content)
    return p


def test_validated_with_L4_citation_PASSES(tmp_path):
    p = _write(tmp_path, "report.md", "The enclosure wall is validated at L4 by bench measurement.\n")
    r = wording.lint_wording_file(p)
    assert r.status == "pass"


def test_validated_without_evidence_level_FAILS(tmp_path):
    """The seeded-wrong case named in the build brief: '\"validated\" without L4'."""
    p = _write(tmp_path, "report.md", "The enclosure design is validated for production.\n")
    r = wording.lint_wording_file(p)
    assert r.status == "fail"
    assert "validated" in r.measured[0]
    assert "report.md:1" in r.measured[0]


def test_certified_with_L5_citation_PASSES(tmp_path):
    p = _write(tmp_path, "report.md", "The board is certified (L5, TUV report #123).\n")
    assert wording.lint_wording_file(p).status == "pass"


def test_certified_without_L5_citation_FAILS(tmp_path):
    p = _write(tmp_path, "report.md", "The board is certified for sale in the EU.\n")
    assert wording.lint_wording_file(p).status == "fail"


def test_production_ready_with_L4_only_still_FAILS(tmp_path):
    """'production-ready' needs L5 specifically -- an L4 citation isn't enough."""
    p = _write(tmp_path, "report.md", "This build is production-ready (L4 tested).\n")
    assert wording.lint_wording_file(p).status == "fail"


def test_production_ready_with_L5_citation_PASSES(tmp_path):
    p = _write(tmp_path, "report.md", "This build is production-ready (L5 sign-off attached).\n")
    assert wording.lint_wording_file(p).status == "pass"


def test_negated_not_validated_PASSES(tmp_path):
    p = _write(tmp_path, "report.md", "This part is not validated yet; treat every number as L1.\n")
    assert wording.lint_wording_file(p).status == "pass"


def test_negated_never_been_validated_PASSES(tmp_path):
    p = _write(tmp_path, "report.md", "The firmware has never been validated on real hardware.\n")
    assert wording.lint_wording_file(p).status == "pass"


def test_negated_nothing_validated_PASSES(tmp_path):
    p = _write(tmp_path, "report.md", "Nothing here is validated; all figures are simulated (L2).\n")
    assert wording.lint_wording_file(p).status == "pass"


def test_word_inside_fenced_code_block_is_IGNORED(tmp_path):
    p = _write(
        tmp_path,
        "report.md",
        "Some text.\n\n```\nstatus = \"validated\"  # example params.toml value, not a real claim\n```\n",
    )
    assert wording.lint_wording_file(p).status == "pass"


def test_word_inside_inline_code_span_is_IGNORED(tmp_path):
    p = _write(tmp_path, "report.md", "Never set `status = \"validated\"` yourself.\n")
    assert wording.lint_wording_file(p).status == "pass"


def test_word_inside_blockquote_is_IGNORED(tmp_path):
    p = _write(tmp_path, "report.md", "> The rule: nothing is validated without L4 evidence.\n")
    assert wording.lint_wording_file(p).status == "pass"


def test_default_scope_collects_reviews_docs_release_and_root_md(tmp_path):
    (tmp_path / "reviews").mkdir()
    (tmp_path / "reviews" / "G2.md").write_text("ok\n")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "note.md").write_text("ok\n")
    (tmp_path / "release").mkdir()
    (tmp_path / "release" / "CHANGELOG.md").write_text("ok\n")
    (tmp_path / "README.md").write_text("ok\n")
    (tmp_path / "not-scoped").mkdir()
    (tmp_path / "not-scoped" / "note.md").write_text("ok\n")

    found = wording.default_scope(tmp_path)
    found_names = {str(p.relative_to(tmp_path)) for p in found}
    assert found_names == {
        "reviews/G2.md",
        "docs/note.md",
        "release/CHANGELOG.md",
        "README.md",
    }


def test_default_scope_excludes_research_and_brief_but_keeps_other_docs(tmp_path):
    """docs/research/** and docs/brief/** quote external sources / the owner's brief
    verbatim, so the wording rule exempts them (an explicit, documented exemption
    list, not an ad hoc skip). Everything else under docs/ is still in scope."""
    (tmp_path / "docs" / "research").mkdir(parents=True)
    (tmp_path / "docs" / "research" / "R1-quote.md").write_text(
        "The vendor datasheet claims the part is certified for automotive use.\n"
    )
    (tmp_path / "docs" / "brief").mkdir(parents=True)
    (tmp_path / "docs" / "brief" / "BRIEF.md").write_text(
        "The owner's brief says the prototype is validated already.\n"
    )
    (tmp_path / "docs" / "standards").mkdir(parents=True)
    (tmp_path / "docs" / "standards" / "compliance.md").write_text(
        "Forge's own claim: the enclosure is certified for sale.\n"
    )

    found = wording.default_scope(tmp_path)
    found_names = {str(p.relative_to(tmp_path)) for p in found}
    assert found_names == {"docs/standards/compliance.md"}


def test_is_exempt_matches_prefixes_and_not_lookalikes(tmp_path):
    (tmp_path / "docs" / "research").mkdir(parents=True)
    (tmp_path / "docs" / "brief").mkdir(parents=True)
    (tmp_path / "docs" / "research-notes").mkdir(parents=True)  # lookalike, not exempt
    exempt = tmp_path / "docs" / "research" / "R1.md"
    exempt.write_text("ok\n")
    exempt2 = tmp_path / "docs" / "brief" / "FORGE-BRIEF.md"
    exempt2.write_text("ok\n")
    lookalike = tmp_path / "docs" / "research-notes" / "note.md"
    lookalike.write_text("ok\n")

    assert wording.is_exempt(tmp_path, exempt) is True
    assert wording.is_exempt(tmp_path, exempt2) is True
    assert wording.is_exempt(tmp_path, lookalike) is False


def test_no_files_in_scope_is_SKIP():
    results = wording.lint_wording([])
    assert len(results) == 1
    assert results[0].status == "skip"


def test_collect_markdown_files_expands_directories(tmp_path):
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "a.md").write_text("ok\n")
    (tmp_path / "sub" / "b.txt").write_text("ignored\n")
    found = wording.collect_markdown_files([tmp_path / "sub"])
    assert [p.name for p in found] == ["a.md"]
