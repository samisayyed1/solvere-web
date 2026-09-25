#!/usr/bin/env python3
"""Offline dry-run of a case's free graders against hand-made run outcomes.

``claude plugin eval`` graders cannot be unit-tested inside the harness, so
this module re-implements the four free grader types (regex, tool_used,
tool_order, file_exists) closely enough to prove, without any model call,
that every grader passes on a good outcome and fails on a wrong one:

* ``load_case(case_dir)`` merges ``case.yaml`` graders, ``prompt.md``
  frontmatter and ``graders/*.md`` the way the harness documents it.
* ``Outcome`` is one simulated run: workspace files after the run, which of
  them the agent *created*, the tool calls (name + input), the final message.
* ``grade(grader, outcome)`` returns True/False (None for paid ``llm`` /
  ``baseline`` graders, which are judged by a model and not simulated).

``selftest.json`` in a case directory lists outcome variants
(``good`` plus ``bad-*``); ``tests/evals/test_graders.py`` asserts ``good``
passes every free grader, each ``bad-*`` fails exactly the graders it names,
and every free grader is failed by at least one bad variant.

Regex semantics follow the harness: JavaScript regexes, ``flags`` (i, m, s),
``match`` of ``contains`` (default), ``not_contains`` or ``count:N``. Patterns
are translated to Python ``re``; constructs that differ between the two
engines (``(?<name>``, ``\\d`` under ``u``, ``[^]``, inline ``(?i)``) are
rejected so a pattern that passes here means the same thing in the harness.
``tool_used`` input matching runs over ``JSON.stringify(input)`` (compact
separators, non-ASCII kept), like the harness.
"""

from __future__ import annotations

import copy
import fnmatch
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:  # PyYAML is in forge-python (the canonical test runner); uv runs need --with pyyaml
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None

FREE_TYPES = {"regex", "tool_used", "tool_order", "file_exists"}
PAID_TYPES = {"llm", "baseline"}
_BAD_JS = [(re.compile(r"\(\?<[A-Za-z]"), "named groups (?<name>) differ between JS and Python"),
           (re.compile(r"\[\^\]"), "[^] is JS-only"),
           (re.compile(r"\(\?[imsx]+\)"), "inline flags are not supported by the harness; use flags:")]


class CaseError(ValueError):
    pass


# ------------------------------------------------------------------ loading

def _frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end < 0:
        raise CaseError("unterminated frontmatter")
    head = text[3:end]
    body = text[end + 4:].lstrip("\n")
    return (yaml.safe_load(head) or {}), body


def load_case(case_dir: Path) -> dict[str, Any]:
    if yaml is None:
        raise CaseError("PyYAML is required (run under ~/.forge/bin/forge-python or uv --with pyyaml)")
    case: dict[str, Any] = {}
    cy = case_dir / "case.yaml"
    if cy.is_file():
        case = yaml.safe_load(cy.read_text()) or {}
    pm = case_dir / "prompt.md"
    prompt = None
    if pm.is_file():
        fm, prompt = _frontmatter(pm.read_text())
        case.setdefault("execution", {})
        for k in ("model", "max_turns", "timeout_seconds", "allowed_tools", "append_system_prompt", "env"):
            if k in fm:
                case["execution"][k] = fm.pop(k)
        case.update(fm)
    case.setdefault("name", case_dir.name)
    case["prompt"] = prompt if prompt is not None else (case.get("execution") or {}).get("prompt")
    graders = list(case.get("graders") or [])
    gdir = case_dir / "graders"
    if gdir.is_dir():
        for g in sorted(gdir.glob("*.md")):
            fm, body = _frontmatter(g.read_text())
            fm["name"] = g.stem
            if fm.get("type") in PAID_TYPES and body.strip():
                fm.setdefault("criteria", body.strip())
            elif fm.get("type") == "regex" and "pattern" not in fm and body.strip():
                fm["pattern"] = body.strip()
            graders.append(fm)
    case["graders"] = graders
    return case


# ------------------------------------------------------------------ outcome

@dataclass
class Outcome:
    files: dict[str, str] = field(default_factory=dict)        # workspace path -> content after the run
    created: list[str] = field(default_factory=list)            # paths the agent created
    tools: list[dict[str, Any]] = field(default_factory=list)  # [{"tool": name, "input": {...}}]
    last_message: str = ""

    def trace(self) -> str:
        lines = []
        for t in self.tools:
            lines.append(json.dumps({"type": "assistant", "message": {"content": [
                {"type": "tool_use", "name": t["tool"], "input": t.get("input", {})}]}}, ensure_ascii=False))
        lines.append(json.dumps({"type": "assistant", "message": {"content": [
            {"type": "text", "text": self.last_message}]}}, ensure_ascii=False))
        return "\n".join(lines)


def _merge(base: dict[str, Any], over: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(base)
    for k, v in over.items():
        if k in ("files", "edits"):
            merged = dict(out.get(k, {}))
            merged.update(copy.deepcopy(v))
            out[k] = merged
        elif k in ("base", "expect", "why"):
            continue
        else:
            out[k] = copy.deepcopy(v)
    return out


def outcome_spec(variants: dict[str, Any], name: str) -> dict[str, Any]:
    v = variants[name]
    return _merge(outcome_spec(variants, v["base"]), v) if v.get("base") else v


def build_outcome(spec: dict[str, Any], base_files: dict[str, str] | None = None) -> Outcome:
    """Workspace after the run = scaffold output (base_files) + edits + files (None deletes)."""
    files = dict(base_files or {})
    for path, pairs in (spec.get("edits") or {}).items():
        text = files[path]
        for old, new in pairs:
            if old not in text:
                raise CaseError(f"edit for {path}: {old!r} not in the scaffolded file")
            text = text.replace(old, new)
        files[path] = text
    written = []
    for path, content in (spec.get("files") or {}).items():
        if content is None:
            files.pop(path, None)
            continue
        files[path] = json.dumps(content, indent=2) if isinstance(content, (dict, list)) else content
        written.append(path)
    created = spec.get("created")
    if created is None:
        created = [p for p in written if p not in (base_files or {})]
    return Outcome(files=files, created=list(created), tools=list(spec.get("tools", [])),
                   last_message=spec.get("last_message", ""))


def outcome_from_variant(variants: dict[str, Any], name: str,
                         base_files: dict[str, str] | None = None) -> Outcome:
    return build_outcome(outcome_spec(variants, name), base_files)


def scaffold_files(case_dir: Path, workdir: Path) -> dict[str, str]:
    """Run the case's real scaffold_script in <workdir>/home/cwd (throwaway HOME) and read the result."""
    import os
    import subprocess
    home = workdir / "home"
    cwd = home / "cwd"
    cwd.mkdir(parents=True, exist_ok=True)
    script = case_dir.resolve() / "scaffold.sh"
    if not script.is_file():
        return {}
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(home)}
    subprocess.run(["bash", str(script)], cwd=cwd, env=env, check=True, capture_output=True, timeout=60)
    out: dict[str, str] = {}
    for p in cwd.rglob("*"):
        if p.is_file() and ".git" not in p.relative_to(cwd).parts:
            try:
                out[p.relative_to(cwd).as_posix()] = p.read_text()
            except UnicodeDecodeError:
                continue
    return out


# ------------------------------------------------------------------ regex

def js_regex(pattern: str, flags: str = "") -> re.Pattern[str]:
    for bad, why in _BAD_JS:
        if bad.search(pattern):
            raise CaseError(f"pattern {pattern!r}: {why}")
    f = 0
    for ch in flags or "":
        if ch == "i":
            f |= re.IGNORECASE
        elif ch == "m":
            f |= re.MULTILINE
        elif ch == "s":
            f |= re.DOTALL
        elif ch in "gu":
            pass
        else:
            raise CaseError(f"unsupported regex flag {ch!r}")
    return re.compile(pattern, f)


def _target_text(target: Any, outcome: Outcome) -> str | None:
    if target in (None, "last_message"):
        return outcome.last_message
    if target == "trace":
        return outcome.trace()
    if target == "files":
        return "\n".join(outcome.created)
    if isinstance(target, dict) and target.get("source") == "file":
        return outcome.files.get(target["path"])
    if target == "mock_calls":
        return ""
    raise CaseError(f"unknown target {target!r}")


def _grade_regex(g: dict[str, Any], outcome: Outcome) -> bool:
    text = _target_text(g.get("target"), outcome)
    if text is None:  # file target that does not exist: the harness fails the grader
        return False
    rx = js_regex(g["pattern"], g.get("flags", ""))
    match = str(g.get("match", "contains"))
    if match == "contains":
        return rx.search(text) is not None
    if match == "not_contains":
        return rx.search(text) is None
    if match.startswith("count:"):
        return len(rx.findall(text)) == int(match.split(":", 1)[1])
    raise CaseError(f"unknown match {match!r}")


def _stringify(inp: Any) -> str:
    return json.dumps(inp, separators=(",", ":"), ensure_ascii=False)


def _calls(tool: str, input_match: str | None, outcome: Outcome) -> list[int]:
    rx = js_regex(input_match) if input_match else None
    return [i for i, t in enumerate(outcome.tools)
            if t["tool"] == tool and (rx is None or rx.search(_stringify(t.get("input", {}))))]


def _grade_tool_used(g: dict[str, Any], outcome: Outcome) -> bool:
    n = len(_calls(g["tool"], g.get("input_match"), outcome))
    lo = int(g.get("min", 1))
    hi = g.get("max")
    return n >= lo and (hi is None or n <= int(hi))


def _grade_tool_order(g: dict[str, Any], outcome: Outcome) -> bool:
    def first(spec: Any) -> int | None:
        if isinstance(spec, str):
            spec = {"tool": spec}
        idx = _calls(spec["tool"], spec.get("input_match"), outcome)
        return idx[0] if idx else None
    a, b = first(g["before"]), first(g["after"])
    return a is not None and b is not None and a < b


def _grade_file_exists(g: dict[str, Any], outcome: Outcome) -> bool:
    pat = g["path"]
    hit = any(fnmatch.fnmatchcase(p, pat) or fnmatch.fnmatchcase(p, pat.replace("**/", "")) for p in outcome.created)
    return hit if g.get("exists", True) else not hit


def grade(g: dict[str, Any], outcome: Outcome) -> bool | None:
    t = g.get("type")
    if t in PAID_TYPES:
        return None
    if t == "regex":
        return _grade_regex(g, outcome)
    if t == "tool_used":
        return _grade_tool_used(g, outcome)
    if t == "tool_order":
        return _grade_tool_order(g, outcome)
    if t == "file_exists":
        return _grade_file_exists(g, outcome)
    raise CaseError(f"unknown grader type {t!r}")


def grade_all(case: dict[str, Any], outcome: Outcome) -> dict[str, bool | None]:
    return {g["name"]: grade(g, outcome) for g in case["graders"]}


def main() -> int:  # pragma: no cover - convenience CLI
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("case_dir", type=Path)
    ns = ap.parse_args()
    case = load_case(ns.case_dir)
    variants = json.loads((ns.case_dir / "selftest.json").read_text())["variants"]
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        base = scaffold_files(ns.case_dir, Path(td))
    for name in variants:
        res = grade_all(case, outcome_from_variant(variants, name, base))
        print(name, {k: v for k, v in res.items()})
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
