"""Tests for forge.lintlib.frontmatter: the narrow stdlib YAML-subset
parser every other lint rule depends on."""

from __future__ import annotations

import pytest

from forge.lintlib.frontmatter import (
    FrontmatterError,
    as_list,
    parse_frontmatter,
    split_frontmatter,
    split_tool_tokens,
)


def test_split_frontmatter_returns_yaml_and_body():
    text = "---\nname: foo\n---\nbody line 1\nbody line 2\n"
    fm, body = split_frontmatter(text)
    assert fm == "name: foo"
    assert body.strip() == "body line 1\nbody line 2"


def test_split_frontmatter_FAILS_without_opening_delimiter():
    with pytest.raises(FrontmatterError):
        split_frontmatter("name: foo\n---\nbody\n")


def test_split_frontmatter_FAILS_without_closing_delimiter():
    with pytest.raises(FrontmatterError):
        split_frontmatter("---\nname: foo\nbody with no close\n")


def test_parse_scalar_and_quoted_values():
    fm = parse_frontmatter('name: foo\ntitle: "Quoted Value"\nother: \'single\'\n')
    assert fm == {"name": "foo", "title": "Quoted Value", "other": "single"}


def test_parse_booleans():
    fm = parse_frontmatter("omitClaudeMd: true\nsomething: false\n")
    assert fm["omitClaudeMd"] is True
    assert fm["something"] is False


def test_parse_block_list():
    fm = parse_frontmatter("tools:\n  - Read\n  - Grep\n  - Glob\nmodel: sonnet\n")
    assert fm["tools"] == ["Read", "Grep", "Glob"]
    assert fm["model"] == "sonnet"


def test_parse_inline_list():
    fm = parse_frontmatter("tools: [Read, Grep, Glob]\n")
    assert fm["tools"] == ["Read", "Grep", "Glob"]


def test_parse_empty_block_list_is_empty_list():
    fm = parse_frontmatter("tools:\nmodel: sonnet\n")
    assert fm["tools"] == []


def test_parse_FAILS_on_unexpected_indentation():
    with pytest.raises(FrontmatterError):
        parse_frontmatter("name: foo\n  stray indented line\n")


def test_parse_FAILS_on_missing_colon():
    with pytest.raises(FrontmatterError):
        parse_frontmatter("this line has no colon\n")


def test_split_tool_tokens_respects_parentheses():
    tokens = split_tool_tokens("Bash(git push *) Read, Grep")
    assert tokens == ["Bash(git push *)", "Read", "Grep"]


def test_split_tool_tokens_handles_comma_only():
    assert split_tool_tokens("Read, Grep, Glob") == ["Read", "Grep", "Glob"]


def test_as_list_normalizes_list_string_and_none():
    assert as_list(["Read", "Grep"]) == ["Read", "Grep"]
    assert as_list("Read, Grep") == ["Read", "Grep"]
    assert as_list(None) == []
    assert as_list(True) == []
