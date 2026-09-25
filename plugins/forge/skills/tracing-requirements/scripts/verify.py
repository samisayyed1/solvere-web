#!/usr/bin/env python3
"""Requirement -> design -> test -> evidence traceability graph (CONTRACTS §6, §9).

Invocation:
    forge-python skills/tracing-requirements/scripts/verify.py --project <root> [--changed <path> ...] [--fast]

Reads ``requirements/requirements.md`` (for the set of valid requirement
IDs), ``requirements/trace.json`` (the requirement -> design/tests/evidence
map) and ``evidence/manifest.json`` (for evidence id existence), then FAILS
(check_id ``requirements.trace_graph``) on:

  - a requirement with no ``trace.json`` entry at all;
  - an **untested requirement**: ``tests`` is empty and ``status`` is not
    ``waived``;
  - a **dangling evidence id**: an id in some requirement's ``evidence[]``
    that does not exist in ``evidence/manifest.json``;
  - an **orphan design or test file**: a source file under a conventional
    design/test directory (``cad/``, ``ecad/``, ``firmware/``, ``app/``,
    ``analysis/``, ``mfg/``, ``tests/``) that is not referenced by any
    requirement's ``design[]``/``tests[]`` entries.

On success (and even on failure, so the graph can be inspected) it writes
``out/trace/trace.graph.json`` (nodes/edges) and
``out/trace/trace.graph.mmd`` (a Mermaid flowchart) -- deliberately *outside*
``out/verify/``, which holds only ``forge.check/1`` result files (CONTRACTS
§3, §9); a graph file living there made ``forge verify`` choke trying to read
it as a check result (M7, review #1).

Standard library only.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lib"))

from forge.checkresult import Check, CheckContractError  # noqa: E402

REQUIREMENTS_REL = Path("requirements/requirements.md")
TRACE_REL = Path("requirements/trace.json")
EVIDENCE_REL = Path("evidence/manifest.json")
CHECK_ID = "requirements.trace_graph"
TRACE_SCHEMA = "forge.trace/1"
VALID_STATUS = {"open", "verified", "failed", "waived"}

# Conventional design/test source directories (templates/project layout).
DESIGN_DIRS = ("cad", "ecad", "firmware", "app", "analysis", "mfg")
TEST_DIRS = ("tests",)
DESIGN_EXTS = {
    ".py", ".c", ".h", ".cpp", ".hpp", ".rs", ".ts", ".tsx", ".js",
    ".kicad_sch", ".kicad_pcb", ".net", ".sysml",
}
IGNORE_DIR_NAMES = {"__pycache__", "out", ".git", "node_modules", ".pytest_cache"}
# Placeholder files kept only so an empty directory survives in git; they are
# never design or test artifacts, so the orphan check must not flag them (M7,
# review #1: "tests/.gitkeep is flagged as an orphan test").
IGNORE_FILE_NAMES = {".gitkeep", ".gitignore"}


def _iter_source_files(project: Path, dirs: tuple[str, ...], exts: set[str] | None) -> list[Path]:
    found: list[Path] = []
    for d in dirs:
        base = project / d
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if not p.is_file():
                continue
            if p.name in IGNORE_FILE_NAMES:
                continue
            if any(part in IGNORE_DIR_NAMES for part in p.relative_to(project).parts):
                continue
            if exts is not None and p.suffix not in exts:
                continue
            found.append(p.relative_to(project))
    return found


def _req_ids_from_requirements_md(text: str) -> list[str]:
    import re
    return re.findall(r"^#{1,6}\s+(REQ-[A-Z]+-\d+)\s*$", text, re.MULTILINE)


def _referenced(paths: list[str], candidate: str) -> bool:
    """True if ``candidate`` (a repo-relative path) is referenced by any of
    ``paths`` (trace.json design/tests entries, which may point at a
    sub-element like ``cad/enclosure.py#lid_lip``)."""
    cand = candidate.replace("\\", "/")
    for ref in paths:
        ref_file = str(ref).replace("\\", "/").split("#", 1)[0]
        if ref_file == cand or ref_file.startswith(cand + "/") or cand.startswith(ref_file):
            return True
    return False


def build_graph(req_ids: list[str], trace: dict, evidence_ids: set[str]) -> dict:
    nodes = [{"id": r, "type": "requirement"} for r in req_ids]
    edges: list[dict] = []
    seen_design: set[str] = set()
    seen_tests: set[str] = set()
    seen_evidence: set[str] = set()
    for req_id, entry in trace.get("requirements", {}).items():
        for d in entry.get("design", []):
            if d not in seen_design:
                nodes.append({"id": d, "type": "design"})
                seen_design.add(d)
            edges.append({"from": req_id, "to": d, "type": "design"})
        for t in entry.get("tests", []):
            if t not in seen_tests:
                nodes.append({"id": t, "type": "test"})
                seen_tests.add(t)
            edges.append({"from": req_id, "to": t, "type": "test"})
        for e in entry.get("evidence", []):
            if e not in seen_evidence:
                nodes.append({"id": e, "type": "evidence"})
                seen_evidence.add(e)
            edges.append({"from": req_id, "to": e, "type": "evidence"})
    return {"schema": "forge.trace_graph/1", "nodes": nodes, "edges": edges}


def render_mermaid(graph: dict) -> str:
    lines = ["flowchart LR"]
    shape = {"requirement": ("([", "])"), "design": ("[", "]"), "test": ("{{", "}}"), "evidence": ("[(", ")]")}
    for n in graph["nodes"]:
        lo, hi = shape.get(n["type"], ("[", "]"))
        safe_id = n["id"].replace('"', "'")
        node_key = _mermaid_key(n["id"])
        lines.append(f'    {node_key}{lo}"{safe_id}"{hi}')
    for e in graph["edges"]:
        lines.append(f"    {_mermaid_key(e['from'])} -->|{e['type']}| {_mermaid_key(e['to'])}")
    return "\n".join(lines) + "\n"


def _mermaid_key(node_id: str) -> str:
    import re
    return "n_" + re.sub(r"[^A-Za-z0-9_]", "_", node_id)


def run(project: Path, changed: list[str] | None) -> int:
    req_path = project / REQUIREMENTS_REL
    trace_path = project / TRACE_REL
    if not req_path.exists() and not trace_path.exists():
        print(f"[SKIP] no {REQUIREMENTS_REL} or {TRACE_REL} in this project")
        return 0
    if changed:
        relevant = {req_path.resolve(), trace_path.resolve()}
        if not any(Path(c).resolve() in relevant for c in changed):
            print("[SKIP] neither requirements.md nor trace.json in --changed set")
            return 0

    chk = Check(CHECK_ID, str(TRACE_REL), level="L1", project=project)

    req_ids = _req_ids_from_requirements_md(req_path.read_text()) if req_path.exists() else []
    if not req_ids:
        print(f"[SKIP] no requirements found in {REQUIREMENTS_REL}")
        return 0

    if trace_path.exists():
        trace = json.loads(trace_path.read_text())
        if trace.get("schema") != TRACE_SCHEMA:
            return chk.error(f"{TRACE_REL} schema is {trace.get('schema')!r}, expected {TRACE_SCHEMA!r}")
    else:
        trace = {"schema": TRACE_SCHEMA, "requirements": {}}

    evidence_path = project / EVIDENCE_REL
    evidence_ids: set[str] = set()
    if evidence_path.exists():
        manifest = json.loads(evidence_path.read_text())
        evidence_ids = {e["id"] for e in manifest.get("entries", [])}

    entries = trace.get("requirements", {})

    all_design_refs: list[str] = []
    all_test_refs: list[str] = []
    for req_id in req_ids:
        loc = f"{TRACE_REL}"
        entry = entries.get(req_id)
        has_entry = entry is not None
        chk.measure(
            f"{req_id}.has_trace_entry", has_entry, "1", equals=True, requirement=req_id, location=loc,
            remediation=(
                f"{req_id} has no entry in {TRACE_REL}. Add design[]/tests[]/evidence[]/status "
                "(status starts 'open')."
            ) if not has_entry else None,
        )
        entry = entry or {}

        status = entry.get("status")
        status_ok = status in VALID_STATUS
        chk.measure(
            f"{req_id}.valid_status", status_ok, "1", equals=True, requirement=req_id, location=loc,
            remediation=(
                f"{req_id} status {status!r} is not one of {sorted(VALID_STATUS)}."
            ) if not status_ok else None,
        )

        tests = entry.get("tests", [])
        design = entry.get("design", [])
        all_design_refs.extend(str(d) for d in design)
        all_test_refs.extend(str(t) for t in tests)

        tested = bool(tests) or status == "waived"
        chk.measure(
            f"{req_id}.tested", tested, "1", equals=True, requirement=req_id, location=loc,
            remediation=(
                f"{req_id} has no tests[] and status is not 'waived' -- it is an untested "
                "requirement. Add a test reference or waive it with a stated reason."
            ) if not tested else None,
        )

        for ev_id in entry.get("evidence", []):
            exists = ev_id in evidence_ids
            chk.measure(
                f"{req_id}.evidence_{ev_id}_exists", exists, "1", equals=True, requirement=req_id, location=loc,
                remediation=(
                    f"{req_id} references evidence id {ev_id!r}, which does not exist in "
                    f"{EVIDENCE_REL}. This is a dangling evidence reference -- fix the id or "
                    "add the missing entry with `forge evidence add`."
                ) if not exists else None,
            )

    # Orphan design/test files: source files not referenced by any requirement.
    for f in _iter_source_files(project, DESIGN_DIRS, DESIGN_EXTS):
        referenced = _referenced(all_design_refs, str(f))
        chk.measure(
            f"orphan.design.{f}", referenced, "1", equals=True, location=str(f),
            remediation=(
                f"{f} is not referenced by any requirement's design[] in {TRACE_REL}. "
                "Every design artifact traces to a requirement -- add the reference, or "
                "remove the file if it is truly unused."
            ) if not referenced else None,
        )
    for f in _iter_source_files(project, TEST_DIRS, None):
        referenced = _referenced(all_test_refs, str(f))
        chk.measure(
            f"orphan.test.{f}", referenced, "1", equals=True, location=str(f),
            remediation=(
                f"{f} is not referenced by any requirement's tests[] in {TRACE_REL}. "
                "Every test traces to a requirement -- add the reference."
            ) if not referenced else None,
        )

    graph = build_graph(req_ids, trace, evidence_ids)
    # Graph files are not forge.check/1 results, so they never go in out/verify/
    # (CONTRACTS §3, §9) -- a stray trace.graph.json there made `forge verify`
    # error out trying to parse it as a check result (M7, review #1).
    graph_dir = project / "out" / "trace"
    graph_dir.mkdir(parents=True, exist_ok=True)
    (graph_dir / "trace.graph.json").write_text(json.dumps(graph, indent=2, ensure_ascii=False) + "\n")
    (graph_dir / "trace.graph.mmd").write_text(render_mermaid(graph))

    return chk.finish()


def main(argv: list[str]) -> int:
    # Declares this entrypoint's check_id namespace so PostToolUse can bind a
    # fix message to the check that owns it, by check_id rather than which
    # out/verify/*.json file happens to have the newest mtime (M7, review #1).
    print(f"[FORGE_CHECK_ID_PREFIX] {CHECK_ID}")
    project = Path(".")
    changed: list[str] = []
    i = 0
    while i < len(argv):
        if argv[i] == "--project":
            project = Path(argv[i + 1]); i += 2
        elif argv[i] == "--changed":
            changed.append(argv[i + 1]); i += 2
        elif argv[i] == "--fast":
            i += 1
        else:
            i += 1
    try:
        return run(project.resolve(), changed or None)
    except CheckContractError as exc:
        print(f"[ERROR] {CHECK_ID}: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001 -- fail closed
        print(f"[ERROR] {CHECK_ID}: internal error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
