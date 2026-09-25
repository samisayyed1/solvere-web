"""``forge lint skills`` (CONTRACTS.md SS12-13, brief SS3.3): SKILL.md hygiene.

Skills are built in parallel by a different Forge builder, so this module
never fails on a *missing* skills directory or a not-yet-built skill --
it skips. It only fails on a skill that exists and breaks a rule:

1. frontmatter ``name`` equals the folder name;
2. the folder name is gerund kebab-case (``^[a-z]+ing(-[a-z0-9]+)*$``),
   except the CONTRACTS SS13 exceptions ``new-project`` and ``init``;
3. ``description`` is <= 1024 characters and states when NOT to use the
   skill (brief SS3.3: "trigger-rich descriptions, including cases where
   the skill should not fire");
4. the body (everything after the closing ``---``) is < 500 lines;
5. ``references/`` is at most one level deep;
6. ``allowed-tools`` never grants bare ``Bash``, ``Bash(*)`` or a wildcard,
   and never grants an interpreter (``forge-python``, ``python``,
   ``python3``) except for one named script under
   ``${CLAUDE_SKILL_DIR}/scripts/`` or ``${CLAUDE_PLUGIN_ROOT}/skills/<s>/scripts/``
   (review #1, M3: ``forge-python *`` runs any code);
7. the CONTRACTS SS13 side-effect skills set ``disable-model-invocation: true``;
8. every CONTRACTS SS9 registered ``scripts/verify.py`` that exists has an
   ``if __name__ == "__main__"`` entrypoint;
9. a skill that a judge agent (``verification-evaluator``, ``red-team``)
   loads grants no interpreter at all (review #1, M2: judges are read-only).
10. ``context:``, if set, is a value the platform actually recognises
    (only ``fork`` is documented -- R1a SS8); a typo like ``context: frok``
    silently falls back to the default rather than forking the skill, which
    used to pass this lint (S20).
"""

from __future__ import annotations

import re
from pathlib import Path

from ..checks import CheckResult
from .frontmatter import FrontmatterError, as_list, parse_frontmatter, split_frontmatter

__all__ = ["lint_skill_dir", "lint_skills_dir", "REGISTERED_VERIFY_ENTRYPOINTS"]

_GERUND_RE = re.compile(r"^[a-z]+ing(-[a-z0-9]+)*$")
_NAME_EXCEPTIONS = {"new-project", "init"}
_SIDE_EFFECT_SKILLS = {"new-project", "init", "releasing-designs", "testing-on-hardware"}
_WHEN_NOT_PHRASES = (
    "when not to use",
    "do not use",
    "don't use",
    "not for",
    "never use",
    "avoid using",
    "should not be used",
    "not when",
    "not use this",
    "not intended for",
)
MAX_DESCRIPTION_LEN = 1024
MAX_BODY_LINES = 500

# CONTRACTS.md SS9 "Registered entrypoints" table -- the exact relative
# paths (from the skills/ directory) every listed owner must create.
REGISTERED_VERIFY_ENTRYPOINTS = (
    "writing-requirements/scripts/verify.py",
    "tracing-requirements/scripts/verify.py",
    "modeling-systems/scripts/verify.py",
    "verifying-geometry/scripts/verify.py",
    "checking-dfm/scripts/verify.py",
    "stacking-tolerances/scripts/verify.py",
    "running-fea/scripts/verify.py",
    "designing-circuits/scripts/verify.py",
    "checking-ecad/scripts/verify.py",
    "building-firmware/scripts/verify.py",
    "gardening-docs/scripts/verify.py",
)

_BARE_BASH_TOKENS = {"bash", "*"}
# The command portion itself is wildcarded, e.g. "Bash(*)" or "Bash(* foo)".
# A trailing arg wildcard on a *scoped* command, e.g.
# "Bash(${CLAUDE_PLUGIN_ROOT}/bin/forge-drc *)" (R1a's own narrow-grant
# example), is fine and must NOT be flagged.
_BASH_WILDCARD_CMD_RE = re.compile(r"^bash\(\s*\*")
_MAIN_GUARD_RE = re.compile(r"""if\s+__name__\s*==\s*["']__main__["']""")


_VALID_CONTEXT_VALUES = {"fork"}

_INTERPRETERS = {"forge-python", "python", "python3"}
_SCOPED_SCRIPT_RE = re.compile(
    r"^(\$\{CLAUDE_SKILL_DIR\}/scripts/|\$\{CLAUDE_PLUGIN_ROOT\}/skills/[a-z0-9-]+/scripts/)[A-Za-z0-9_.-]+\.py$")
_BASH_RULE_RE = re.compile(r"^bash\((.*)\)$", re.IGNORECASE | re.DOTALL)
JUDGE_AGENTS = ("verification-evaluator", "red-team")


def _interpreter_grant(token: str) -> str | None:
    """``None`` if ``token`` does not grant an interpreter; ``"scoped"`` if it
    grants one for exactly one named skill script; ``"broad"`` otherwise."""
    m = _BASH_RULE_RE.match(token.strip())
    if not m:
        return None
    parts = m.group(1).split()
    if not parts:
        return None
    prog = parts[0][:-2] if parts[0].endswith(":*") else parts[0]
    if prog.rsplit("/", 1)[-1] not in _INTERPRETERS:
        return None
    if len(parts) < 2:
        return "broad"
    script = parts[1][:-2] if parts[1].endswith(":*") else parts[1]
    if not _SCOPED_SCRIPT_RE.match(script):
        return "broad"
    extra = parts[2:]
    if extra and extra[-1] == "*":
        extra = extra[:-1]  # a trailing argument wildcard is fine
    if any("*" in a for a in extra):
        return "broad"
    return "scoped"


def _bad_allowed_tools(value) -> list[str]:
    """Flag bare ``Bash``, ``Bash(*)``, any wildcarded command, and any
    interpreter grant that is not scoped to one named skill script."""
    bad = []
    for token in as_list(value):
        low = token.lower()
        if low in _BARE_BASH_TOKENS or _BASH_WILDCARD_CMD_RE.match(low) or _interpreter_grant(token) == "broad":
            bad.append(token)
    return bad


def _judge_skills(plugin_root: Path) -> set[str]:
    names: set[str] = set()
    for agent in JUDGE_AGENTS:
        path = plugin_root / "agents" / f"{agent}.md"
        if not path.is_file():
            continue
        try:
            fm_text, _ = split_frontmatter(path.read_text())
            fm = parse_frontmatter(fm_text)
        except (FrontmatterError, OSError):
            continue
        names.update(as_list(fm.get("skills")))
    return names


def lint_skill_dir(skill_dir: Path) -> list[CheckResult]:
    skill_dir = Path(skill_dir)
    name = skill_dir.name
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return [
            CheckResult(
                id=f"skills.skill_md:{name}",
                status="fail",
                rule="each skills/<name>/ directory has a SKILL.md",
                measured="<missing>",
                expected="SKILL.md present",
                fix=f"Add {skill_md}.",
            )
        ]

    text = skill_md.read_text(encoding="utf-8", errors="replace")
    try:
        fm_text, body = split_frontmatter(text)
        fm = parse_frontmatter(fm_text)
    except FrontmatterError as exc:
        return [
            CheckResult(
                id=f"skills.frontmatter:{name}",
                status="fail",
                rule="SKILL.md opens with a parseable '---' frontmatter block",
                measured=str(exc),
                expected="valid frontmatter",
                fix=f"Fix the frontmatter in {skill_md}: {exc}",
            )
        ]

    results: list[CheckResult] = []

    # 1. name == folder name
    fm_name = fm.get("name")
    if fm_name == name:
        results.append(
            CheckResult(
                id=f"skills.name_matches_dir:{name}",
                status="pass",
                rule="frontmatter name == folder name",
                measured=fm_name,
                expected=name,
            )
        )
    else:
        results.append(
            CheckResult(
                id=f"skills.name_matches_dir:{name}",
                status="fail",
                rule="frontmatter name == folder name (CONTRACTS SS12)",
                measured=fm_name,
                expected=name,
                fix=f"Set 'name: {name}' in {skill_md} (or rename the folder to match).",
            )
        )

    # 2. gerund naming, except new-project/init
    if name in _NAME_EXCEPTIONS:
        results.append(
            CheckResult(
                id=f"skills.gerund_name:{name}",
                status="pass",
                rule="gerund kebab-case name, except new-project/init (CONTRACTS SS13)",
                measured=name,
                expected="exempt",
            )
        )
    elif _GERUND_RE.match(name):
        results.append(
            CheckResult(
                id=f"skills.gerund_name:{name}",
                status="pass",
                rule="gerund kebab-case name",
                measured=name,
                expected="matches ^[a-z]+ing(-[a-z0-9]+)*$",
            )
        )
    else:
        results.append(
            CheckResult(
                id=f"skills.gerund_name:{name}",
                status="fail",
                rule=(
                    "skill folder names are gerund kebab-case, e.g. 'modeling-cad-parts' (brief SS3.3), "
                    "except new-project/init (CONTRACTS SS13)"
                ),
                measured=name,
                expected="matches ^[a-z]+ing(-[a-z0-9]+)*$",
                fix=f"Rename {skill_dir} to a gerund form (e.g. '<verb>ing[-noun...]').",
            )
        )

    # 3. description length + when-not-to-use wording
    desc = fm.get("description")
    desc_str = desc if isinstance(desc, str) else ""
    if len(desc_str) <= MAX_DESCRIPTION_LEN:
        results.append(
            CheckResult(
                id=f"skills.description_length:{name}",
                status="pass",
                rule=f"description <= {MAX_DESCRIPTION_LEN} characters",
                measured=len(desc_str),
                expected=f"<= {MAX_DESCRIPTION_LEN}",
            )
        )
    else:
        results.append(
            CheckResult(
                id=f"skills.description_length:{name}",
                status="fail",
                rule=f"description <= {MAX_DESCRIPTION_LEN} characters (CONTRACTS SS12)",
                measured=len(desc_str),
                expected=f"<= {MAX_DESCRIPTION_LEN}",
                fix=f"Shorten the description in {skill_md} to {MAX_DESCRIPTION_LEN} characters or fewer.",
            )
        )

    has_when_not = any(phrase in desc_str.lower() for phrase in _WHEN_NOT_PHRASES)
    if has_when_not:
        results.append(
            CheckResult(
                id=f"skills.when_not_to_use:{name}",
                status="pass",
                rule="description states when NOT to use the skill (brief SS3.3)",
                measured=True,
                expected=True,
            )
        )
    else:
        results.append(
            CheckResult(
                id=f"skills.when_not_to_use:{name}",
                status="fail",
                rule=(
                    "description states when NOT to use the skill (brief SS3.3: 'trigger-rich descriptions, "
                    "including cases where the skill should not fire')"
                ),
                measured=False,
                expected=True,
                fix=f"Add a when-not-to-use clause to the description in {skill_md} (e.g. 'Do not use for ...').",
            )
        )

    # 4. body length
    body_lines = len(body.splitlines())
    if body_lines < MAX_BODY_LINES:
        results.append(
            CheckResult(
                id=f"skills.body_length:{name}",
                status="pass",
                rule=f"SKILL.md body < {MAX_BODY_LINES} lines, details in references/ (CONTRACTS SS12)",
                measured=body_lines,
                expected=f"< {MAX_BODY_LINES}",
            )
        )
    else:
        results.append(
            CheckResult(
                id=f"skills.body_length:{name}",
                status="fail",
                rule=f"SKILL.md body < {MAX_BODY_LINES} lines, details in references/ (CONTRACTS SS12)",
                measured=body_lines,
                expected=f"< {MAX_BODY_LINES}",
                fix=f"{skill_md} body has {body_lines} lines; move detail into references/ and keep SKILL.md short.",
            )
        )

    # 5. references/ at most one level deep
    refs_dir = skill_dir / "references"
    if refs_dir.is_dir():
        deep = sorted(
            str(p.relative_to(refs_dir))
            for p in refs_dir.rglob("*")
            if p.is_file() and len(p.relative_to(refs_dir).parts) > 2
        )
        if deep:
            results.append(
                CheckResult(
                    id=f"skills.references_depth:{name}",
                    status="fail",
                    rule="references/ is at most one level deep (brief SS3.3)",
                    measured=deep,
                    expected="path depth <= 2 under references/",
                    fix=f"Flatten {', '.join(deep)} under {refs_dir} to at most one subdirectory level.",
                )
            )
        else:
            results.append(
                CheckResult(
                    id=f"skills.references_depth:{name}",
                    status="pass",
                    rule="references/ is at most one level deep",
                    measured=0,
                    expected="path depth <= 2",
                )
            )

    # 6. allowed-tools never bare Bash / Bash(*) / a wildcard
    allowed_tools = fm.get("allowed-tools")
    if allowed_tools is not None:
        bad = _bad_allowed_tools(allowed_tools)
        if bad:
            results.append(
                CheckResult(
                    id=f"skills.allowed_tools:{name}",
                    status="fail",
                    rule=(
                        "allowed-tools: must never grant bare Bash, Bash(*), a wildcard, or an interpreter "
                        "(forge-python/python) beyond one named skill script "
                        "(CONTRACTS SS12: skill grants aren't trust-gated)"
                    ),
                    measured=bad,
                    expected="no bare Bash / Bash(*) / wildcard entries",
                    fix=(
                        f"Narrow the allowed-tools entries {bad} in {skill_md} to specific commands, e.g. "
                        "'Bash(~/.forge/bin/forge-python ${CLAUDE_SKILL_DIR}/scripts/verify.py:*)'."
                    ),
                )
            )
        else:
            results.append(
                CheckResult(
                    id=f"skills.allowed_tools:{name}",
                    status="pass",
                    rule="allowed-tools: has no bare Bash / Bash(*) / wildcard / broad interpreter entries",
                    measured=as_list(allowed_tools),
                    expected="none",
                )
            )

    # 7. side-effect skills require disable-model-invocation: true
    if name in _SIDE_EFFECT_SKILLS:
        dmi = fm.get("disable-model-invocation")
        if dmi is True:
            results.append(
                CheckResult(
                    id=f"skills.disable_model_invocation:{name}",
                    status="pass",
                    rule="side-effect skills set disable-model-invocation: true (CONTRACTS SS13)",
                    measured=dmi,
                    expected=True,
                )
            )
        else:
            results.append(
                CheckResult(
                    id=f"skills.disable_model_invocation:{name}",
                    status="fail",
                    rule=(
                        "side-effect skills set disable-model-invocation: true (CONTRACTS SS13: new-project, "
                        "init, releasing-designs, testing-on-hardware)"
                    ),
                    measured=dmi,
                    expected=True,
                    fix=f"Set 'disable-model-invocation: true' in {skill_md}.",
                )
            )

    # 8. registered verify.py entrypoints must be executable-by-python
    verify_py = skill_dir / "scripts" / "verify.py"
    entrypoint_rel = f"{name}/scripts/verify.py"
    if entrypoint_rel in REGISTERED_VERIFY_ENTRYPOINTS and verify_py.exists():
        content = verify_py.read_text(encoding="utf-8", errors="replace")
        if _MAIN_GUARD_RE.search(content):
            results.append(
                CheckResult(
                    id=f"skills.verify_entrypoint:{name}",
                    status="pass",
                    rule="registered scripts/verify.py is executable-by-python (has an __main__ guard, CONTRACTS SS9)",
                    measured=True,
                    expected=True,
                )
            )
        else:
            results.append(
                CheckResult(
                    id=f"skills.verify_entrypoint:{name}",
                    status="fail",
                    rule="registered scripts/verify.py is executable-by-python (has an __main__ guard, CONTRACTS SS9)",
                    measured=False,
                    expected=True,
                    fix=f"Add an `if __name__ == '__main__':` entrypoint to {verify_py}.",
                )
            )

    # 10. context: value, if set, must be a recognised value.
    context_val = fm.get("context")
    if context_val is not None:
        if context_val in _VALID_CONTEXT_VALUES:
            results.append(
                CheckResult(
                    id=f"skills.context_value:{name}",
                    status="pass",
                    rule=f"context: is one of {sorted(_VALID_CONTEXT_VALUES)} when set (R1a SS8)",
                    measured=context_val,
                    expected=sorted(_VALID_CONTEXT_VALUES),
                )
            )
        else:
            results.append(
                CheckResult(
                    id=f"skills.context_value:{name}",
                    status="fail",
                    rule=f"context: is one of {sorted(_VALID_CONTEXT_VALUES)} when set (R1a SS8)",
                    measured=context_val,
                    expected=sorted(_VALID_CONTEXT_VALUES),
                    fix=(
                        f"{skill_md} sets context: {context_val!r}, which the platform does not "
                        f"recognise and silently ignores. Set 'context: fork' or remove the field."
                    ),
                )
            )

    return results


def lint_skills_dir(directory: Path) -> list[CheckResult]:
    directory = Path(directory)
    if not directory.exists():
        return [
            CheckResult(
                id="skills.dir",
                status="skip",
                rule="skills directory exists",
                measured=str(directory),
                expected="directory present (owned by another Forge builder)",
            )
        ]
    # Every subdirectory is expected to be a skill; lint_skill_dir itself
    # fails (not skips) one with no SKILL.md, so a stray/half-built folder
    # is caught rather than silently ignored.
    skill_dirs = sorted(p for p in directory.iterdir() if p.is_dir() and not p.name.startswith("."))
    if not skill_dirs:
        return [
            CheckResult(
                id="skills.dir",
                status="skip",
                rule="skills directory has at least one skill",
                measured=0,
                expected=">= 1 (none built yet)",
            )
        ]
    results: list[CheckResult] = []
    for d in skill_dirs:
        results.extend(lint_skill_dir(d))
    judge_skills = _judge_skills(directory.parent)
    for d in skill_dirs:
        if d.name not in judge_skills or not (d / "SKILL.md").is_file():
            continue
        try:
            fm_text, _ = split_frontmatter((d / "SKILL.md").read_text())
            granted = as_list(parse_frontmatter(fm_text).get("allowed-tools"))
        except (FrontmatterError, OSError):
            continue
        interp = [t for t in granted if _interpreter_grant(t)]
        results.append(CheckResult(
            id=f"skills.judge_no_interpreter:{d.name}",
            status="fail" if interp else "pass",
            rule="a skill loaded by a judge agent grants no interpreter (judges are read-only, ADR-001 D6)",
            measured=interp,
            expected="no forge-python/python grants",
            fix=None if not interp else f"Remove {interp} from allowed-tools in {d / 'SKILL.md'}.",
        ))
    return results
