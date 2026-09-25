"""``forge lint agents`` (CONTRACTS.md SS12, ADR-001 SS6): agent-frontmatter hygiene.

Checks, per ``agents/<name>.md``:

1. Only the fields CONTRACTS SS12 lists appear in frontmatter; ``hooks``,
   ``mcpServers``, ``permissionMode`` and ``initialPrompt`` are rejected by
   name (plugin agents ignore them silently at runtime -- ADR-001 SS6 -- so
   their presence is always a authoring mistake, not a real grant).
2. Judges (``verification-evaluator``, ``red-team``) are ``model: opus``,
   ``effort: xhigh``, carry no ``memory:`` field, exclude Write/Edit/
   NotebookEdit/Agent from ``tools:``, include all four in
   ``disallowedTools:``, and set ``omitClaudeMd: true``.
3. Makers (every other agent) are ``model: sonnet`` and ``memory: project``.
4. Every agent's ``description`` is at least 80 characters.
5. No agent file sets ``isolation:`` (ADR-001 SS6: ``isolation: worktree`` is
   only for parallel writers, and it is set per-workflow -- never as a
   default baked into an agent's own frontmatter, or a maker's edits land in
   a throwaway worktree instead of the real tree).
"""

from __future__ import annotations

from pathlib import Path

from ..checks import CheckResult
from .frontmatter import FrontmatterError, as_list, parse_frontmatter, split_frontmatter

__all__ = ["lint_agent_file", "lint_agents_dir", "ALLOWED_FIELDS", "JUDGE_NAMES"]

ALLOWED_FIELDS = {
    "name",
    "description",
    "tools",
    "disallowedTools",
    "model",
    "effort",
    "maxTurns",
    "memory",
    "isolation",
    "omitClaudeMd",
    "color",
    "skills",
    "background",
}
EXPLICITLY_REJECTED_FIELDS = {"hooks", "mcpServers", "permissionMode", "initialPrompt"}
JUDGE_NAMES = {"verification-evaluator", "red-team"}
JUDGE_REQUIRED_DISALLOWED = {"Write", "Edit", "NotebookEdit", "Agent"}
MIN_DESCRIPTION_LEN = 80


def _agent_name(path: Path, fm: dict) -> str:
    name = fm.get("name")
    if isinstance(name, str) and name:
        return name
    return path.stem


def _field_eq(check_id: str, rule: str, measured, expected, fix: str) -> CheckResult:
    if measured == expected:
        return CheckResult(id=check_id, status="pass", rule=rule, measured=measured, expected=expected)
    return CheckResult(id=check_id, status="fail", rule=rule, measured=measured, expected=expected, fix=fix)


def lint_agent_file(path: Path) -> list[CheckResult]:
    path = Path(path)
    rel = str(path)
    text = path.read_text(encoding="utf-8", errors="replace")
    try:
        fm_text, _body = split_frontmatter(text)
        fm = parse_frontmatter(fm_text)
    except FrontmatterError as exc:
        return [
            CheckResult(
                id=f"agents.frontmatter:{path.name}",
                status="fail",
                rule="agent file opens with a parseable '---' frontmatter block",
                measured=str(exc),
                expected="valid frontmatter",
                fix=f"Fix the frontmatter in {rel}: {exc}",
            )
        ]

    name = _agent_name(path, fm)
    is_judge = name in JUDGE_NAMES
    results: list[CheckResult] = []

    # 1. only allowed fields; hooks/mcpServers/permissionMode/initialPrompt named explicitly.
    present = set(fm)
    unknown = present - ALLOWED_FIELDS
    rejected = sorted(unknown & EXPLICITLY_REJECTED_FIELDS)
    other_unknown = sorted(unknown - EXPLICITLY_REJECTED_FIELDS)
    if rejected:
        results.append(
            CheckResult(
                id=f"agents.rejected_fields:{name}",
                status="fail",
                rule=(
                    "plugin agents ignore hooks/mcpServers/permissionMode/initialPrompt at runtime "
                    "(ADR-001 SS6, R1a SS10); they must not appear in frontmatter"
                ),
                measured=rejected,
                expected="none of hooks, mcpServers, permissionMode, initialPrompt",
                fix=(
                    f"Remove {', '.join(rejected)} from {rel} frontmatter. Policy for plugin agents lives in "
                    "hooks/hooks.json (matched on agent_type) and the product repo's .claude/settings.json, "
                    "not in agent frontmatter."
                ),
            )
        )
    else:
        results.append(
            CheckResult(
                id=f"agents.rejected_fields:{name}",
                status="pass",
                rule="no hooks/mcpServers/permissionMode/initialPrompt fields",
                measured=[],
                expected=[],
            )
        )
    if other_unknown:
        results.append(
            CheckResult(
                id=f"agents.allowed_fields:{name}",
                status="fail",
                rule="agent frontmatter uses only: " + ", ".join(sorted(ALLOWED_FIELDS)) + " (CONTRACTS SS12)",
                measured=other_unknown,
                expected="subset of the allowed fields",
                fix=f"Remove or rename unknown field(s) {', '.join(other_unknown)} in {rel}.",
            )
        )
    else:
        results.append(
            CheckResult(
                id=f"agents.allowed_fields:{name}",
                status="pass",
                rule="agent frontmatter uses only allowed fields",
                measured=sorted(present),
                expected="subset of the allowed fields",
            )
        )

    # 1b. isolation: is never set on an agent file (ADR-001 SS6): worktree isolation is
    # for parallel writers and is configured per-workflow, never baked into an agent's
    # own frontmatter as a default.
    if "isolation" in fm:
        results.append(
            CheckResult(
                id=f"agents.no_isolation:{name}",
                status="fail",
                rule=(
                    "agent frontmatter must not set 'isolation:' -- worktree isolation is for "
                    "parallel writers only, and is set per-workflow, never by default on the "
                    "agent (ADR-001 SS6)"
                ),
                measured=fm.get("isolation"),
                expected="field absent",
                fix=(
                    f"Remove 'isolation:' from {rel}. If this agent needs worktree isolation for a "
                    "specific parallel-write workflow, set it on that workflow instead, not on the agent."
                ),
            )
        )
    else:
        results.append(
            CheckResult(
                id=f"agents.no_isolation:{name}",
                status="pass",
                rule="agent frontmatter does not set 'isolation:'",
                measured=None,
                expected="field absent",
            )
        )

    # 2. description length
    desc = fm.get("description")
    desc_len = len(desc) if isinstance(desc, str) else 0
    if desc_len >= MIN_DESCRIPTION_LEN:
        results.append(
            CheckResult(
                id=f"agents.description_length:{name}",
                status="pass",
                rule=f"description is at least {MIN_DESCRIPTION_LEN} characters",
                measured=desc_len,
                expected=f">= {MIN_DESCRIPTION_LEN}",
            )
        )
    else:
        results.append(
            CheckResult(
                id=f"agents.description_length:{name}",
                status="fail",
                rule=(
                    f"description is at least {MIN_DESCRIPTION_LEN} characters, with concrete trigger phrases "
                    "and a when-not-to-use clause (brief SS3.2)"
                ),
                measured=desc_len,
                expected=f">= {MIN_DESCRIPTION_LEN}",
                fix=(
                    f"Lengthen the description in {rel} to at least {MIN_DESCRIPTION_LEN} characters: add "
                    "concrete trigger phrases and state when this agent should NOT be used."
                ),
            )
        )

    tools = as_list(fm.get("tools"))
    disallowed = as_list(fm.get("disallowedTools"))

    if is_judge:
        results.extend(_lint_judge(rel, name, fm, tools, disallowed))
    else:
        results.extend(_lint_maker(rel, name, fm))

    return results


def _lint_judge(rel: str, name: str, fm: dict, tools: list[str], disallowed: list[str]) -> list[CheckResult]:
    out: list[CheckResult] = []
    out.append(
        _field_eq(
            f"agents.judge_model:{name}",
            "judges use model: opus (ADR-001 D9, CONTRACTS SS12)",
            fm.get("model"),
            "opus",
            f"Set 'model: opus' for judge agent {name} in {rel}.",
        )
    )
    out.append(
        _field_eq(
            f"agents.judge_effort:{name}",
            "judges use effort: xhigh (ADR-001 D9)",
            fm.get("effort"),
            "xhigh",
            f"Set 'effort: xhigh' for judge agent {name} in {rel}.",
        )
    )

    has_memory = "memory" in fm and fm.get("memory") not in (None, "", [])
    if has_memory:
        out.append(
            CheckResult(
                id=f"agents.judge_no_memory:{name}",
                status="fail",
                rule=(
                    "judges carry no 'memory:' field -- memory: auto-grants Write/Edit, which would break "
                    "read-only review (ADR-001 SS6 deviation from the brief)"
                ),
                measured=fm.get("memory"),
                expected="field absent",
                fix=f"Remove the 'memory:' field from {rel}; judges must stay read-only.",
            )
        )
    else:
        out.append(
            CheckResult(
                id=f"agents.judge_no_memory:{name}",
                status="pass",
                rule="judges carry no 'memory:' field",
                measured=None,
                expected="field absent",
            )
        )

    forbidden_in_tools = sorted(set(tools) & JUDGE_REQUIRED_DISALLOWED)
    if forbidden_in_tools:
        out.append(
            CheckResult(
                id=f"agents.judge_tools:{name}",
                status="fail",
                rule="judges' tools: must not include Write, Edit, NotebookEdit or Agent",
                measured=forbidden_in_tools,
                expected="none of Write, Edit, NotebookEdit, Agent",
                fix=f"Remove {', '.join(forbidden_in_tools)} from the tools: list in {rel}.",
            )
        )
    else:
        out.append(
            CheckResult(
                id=f"agents.judge_tools:{name}",
                status="pass",
                rule="judges' tools: excludes Write/Edit/NotebookEdit/Agent",
                measured=tools,
                expected="excludes those four",
            )
        )

    missing_disallowed = sorted(JUDGE_REQUIRED_DISALLOWED - set(disallowed))
    if missing_disallowed:
        out.append(
            CheckResult(
                id=f"agents.judge_disallowed:{name}",
                status="fail",
                rule="judges' disallowedTools: must include Write, Edit, NotebookEdit and Agent (ADR-001 D6)",
                measured=disallowed,
                expected=sorted(JUDGE_REQUIRED_DISALLOWED),
                fix=f"Add {', '.join(missing_disallowed)} to disallowedTools: in {rel}.",
            )
        )
    else:
        out.append(
            CheckResult(
                id=f"agents.judge_disallowed:{name}",
                status="pass",
                rule="judges' disallowedTools: includes Write/Edit/NotebookEdit/Agent",
                measured=disallowed,
                expected=sorted(JUDGE_REQUIRED_DISALLOWED),
            )
        )

    omit = fm.get("omitClaudeMd")
    if omit is True:
        out.append(
            CheckResult(
                id=f"agents.judge_omit_claudemd:{name}",
                status="pass",
                rule="judges set omitClaudeMd: true (ADR-001 D6)",
                measured=omit,
                expected=True,
            )
        )
    else:
        out.append(
            CheckResult(
                id=f"agents.judge_omit_claudemd:{name}",
                status="fail",
                rule="judges set omitClaudeMd: true (ADR-001 D6)",
                measured=omit,
                expected=True,
                fix=f"Set 'omitClaudeMd: true' for judge agent {name} in {rel}.",
            )
        )
    return out


def _lint_maker(rel: str, name: str, fm: dict) -> list[CheckResult]:
    out: list[CheckResult] = []
    out.append(
        _field_eq(
            f"agents.maker_memory:{name}",
            "maker agents use memory: project (brief SS3.2)",
            fm.get("memory"),
            "project",
            f"Set 'memory: project' for maker agent {name} in {rel}.",
        )
    )
    out.append(
        _field_eq(
            f"agents.maker_model:{name}",
            "maker agents use model: sonnet (ADR-001 D9)",
            fm.get("model"),
            "sonnet",
            f"Set 'model: sonnet' for maker agent {name} in {rel}.",
        )
    )
    return out


def lint_agents_dir(directory: Path) -> list[CheckResult]:
    directory = Path(directory)
    if not directory.exists():
        return [
            CheckResult(
                id="agents.dir",
                status="skip",
                rule="agents directory exists",
                measured=str(directory),
                expected="directory present",
            )
        ]
    files = sorted(directory.glob("*.md"))
    if not files:
        return [
            CheckResult(
                id="agents.dir",
                status="warn",
                rule="agents directory has at least one agent .md file",
                measured=0,
                expected=">= 1",
                fix=f"Add agent .md files under {directory}.",
            )
        ]
    results: list[CheckResult] = []
    for f in files:
        results.extend(lint_agent_file(f))
    return results
