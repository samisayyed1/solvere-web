"""Tests for hooks/user_prompt_submit.py (brief §3.4: lightweight, never blocks)."""

from __future__ import annotations

from .hookutil import forge_project, non_forge_project, run_hook


def test_noop_outside_forge_project(non_forge_project):
    result = run_hook("user_prompt_submit.py", {"cwd": str(non_forge_project), "prompt": "check the wall thickness"})
    assert result.returncode == 0
    assert result.raw_stdout == ""


def test_no_keyword_match_is_silent(forge_project):
    result = run_hook("user_prompt_submit.py", {"cwd": str(forge_project), "prompt": "what's the weather like"})
    assert result.returncode == 0
    assert result.raw_stdout == ""


def test_keyword_match_suggests_a_skill(forge_project):
    result = run_hook("user_prompt_submit.py", {"cwd": str(forge_project), "prompt": "please check the min wall on this part"})
    assert result.returncode == 0
    assert "/forge:verifying-geometry" in result.raw_stdout


def test_output_is_plain_text_not_json(forge_project):
    """R1a §17: plain stdout (not a {...} JSON object) is what becomes context
    for UserPromptSubmit; this hook deliberately does not emit JSON."""
    result = run_hook("user_prompt_submit.py", {"cwd": str(forge_project), "prompt": "run the ears lint on requirements"})
    assert result.returncode == 0
    text = result.raw_stdout.strip()
    assert text and not (text.startswith("{") and text.endswith("}"))


def test_empty_prompt_is_silent(forge_project):
    result = run_hook("user_prompt_submit.py", {"cwd": str(forge_project), "prompt": ""})
    assert result.returncode == 0
    assert result.raw_stdout == ""


def test_never_blocks_even_on_gated_looking_language(forge_project):
    """This hook only ever suggests; it must never return a blocking exit code."""
    result = run_hook("user_prompt_submit.py", {
        "cwd": str(forge_project), "prompt": "release the design and flash the firmware to hardware now",
    })
    assert result.returncode == 0
