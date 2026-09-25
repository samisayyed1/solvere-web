#!/usr/bin/env python3
"""Verify entrypoint for inspecting-renders (CONTRACTS.md §9).

For each ``analysis/renders/<part>-questions.toml``: refuses (exit 2) if
the questions file is missing or malformed -- **this is the seeded-wrong
case "render run without a questions file" and it must never pass**.
Otherwise checks that every standard render exists and is non-blank, and
if an answers file has been written, that every answer cites an existing
render file and (per CONTRACTS.md §0) that renders never stand in as the
only evidence for a numeric claim.

    forge-python skills/inspecting-renders/scripts/verify.py --project <root> [--changed <path> ...]
"""
from __future__ import annotations

import argparse
import re
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lib"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from forge.checkresult import Check, CheckContractError  # noqa: E402
from render import MAX_QUESTIONS, MIN_QUESTIONS  # noqa: E402

_SAFE = re.compile(r"[^a-z0-9_]+")
REQUIRED_VIEWS = ["front", "top", "right", "iso", "section", "exploded"]
MIN_PNG_BYTES = 1000
MIN_STD_DEV = 3.0  # a near-blank render has ~0 pixel variance


def _safe_name(name: str) -> str:
    slug = _SAFE.sub("_", name.strip().lower()).strip("_")
    return slug or "part"


def _find_parts(project: Path, changed: list[str]) -> list[str]:
    renders_dir = project / "analysis" / "renders"
    if changed:
        parts = set()
        for c in changed:
            p = Path(c).name
            m = re.match(r"(.+)-questions\.toml$", p) or re.match(r"(.+)-answers\.toml$", p)
            if m:
                parts.add(m.group(1))
        return sorted(parts)
    if not renders_dir.is_dir():
        return []
    parts = set()
    for f in renders_dir.glob("*-questions.toml"):
        parts.add(f.stem[: -len("-questions")])
    for f in renders_dir.glob("*-answers.toml"):
        parts.add(f.stem[: -len("-answers")])
    return sorted(parts)


def _run_one(part: str, project: Path) -> int:
    check_id = f"mech.render_inspection_{_safe_name(part)}"
    q_path = project / "analysis" / "renders" / f"{part}-questions.toml"
    target = str(q_path.relative_to(project)) if q_path.is_relative_to(project) else str(q_path)
    chk = Check(check_id, target, level="L1", project=project)

    if not q_path.exists():
        return chk.error(
            f"{q_path} does not exist -- refusing to score render inspection for {part!r} without a "
            "questions file written before rendering (question-first, CADCodeVerify-style). This is "
            "the seeded-wrong case this check exists to catch: rendering (or claiming to have inspected "
            "renders) without a questions file must never pass."
        )
    try:
        data = tomllib.loads(q_path.read_text())
    except tomllib.TOMLDecodeError as exc:
        return chk.error(f"{q_path}: invalid TOML: {exc}")
    questions = data.get("question", [])
    if not (MIN_QUESTIONS <= len(questions) <= MAX_QUESTIONS):
        return chk.error(
            f"{q_path} has {len(questions)} questions; must have between {MIN_QUESTIONS} and "
            f"{MAX_QUESTIONS}, written from the requirements before rendering."
        )
    part_tbl = data.get("part")
    if not isinstance(part_tbl, dict) or ("module" in part_tbl) == ("step" in part_tbl):
        return chk.error(
            f"{q_path} has no valid [part] table. It must set exactly one of module = \"cad/<file>.py\" "
            "or step = \"cad/out/<file>.step\" naming the real geometry rendered -- this skill never "
            "renders placeholder/demo geometry in place of the part being inspected (S11)."
        )

    render_dir = project / "out" / "renders" / part
    try:
        import numpy as np
        from PIL import Image

        missing_views = []
        blank_views = []
        for view in REQUIRED_VIEWS:
            p = render_dir / f"{view}.png"
            if not p.exists() or p.stat().st_size < MIN_PNG_BYTES:
                missing_views.append(view)
                continue
            arr = np.asarray(Image.open(p).convert("L"))
            if arr.std() < MIN_STD_DEV:
                blank_views.append(view)

        chk.measure(
            "required_views_present", len(REQUIRED_VIEWS) - len(missing_views), "1", min=len(REQUIRED_VIEWS),
            remediation=(
                f"Render(s) {missing_views} missing or implausibly small under {render_dir}. Run "
                f"render.py --project {project} --part {part} to (re)generate the standard views, "
                "section view and exploded view."
            ),
        )
        chk.measure(
            "views_non_blank", len(REQUIRED_VIEWS) - len(blank_views), "1", min=len(REQUIRED_VIEWS),
            remediation=(
                f"Render(s) {blank_views} have near-zero pixel variance (std < {MIN_STD_DEV}) -- they "
                "look blank. Check the camera position and that geometry is actually in frame."
            ),
        )

        a_path = project / "analysis" / "renders" / f"{part}-answers.toml"
        if a_path.exists():
            adata = tomllib.loads(a_path.read_text())
            answers = adata.get("answer", [])
            q_ids = {q["id"] for q in questions}
            answered_ids = {a.get("question_id") for a in answers}
            unanswered = q_ids - answered_ids
            bad_evidence = []
            empty_answers = []
            undocumented_no = []
            for a in answers:
                qid = a.get("question_id", "?")
                ans = a.get("answer", "").strip().lower()
                if ans not in ("yes", "no"):
                    empty_answers.append(qid)
                    continue
                ev = a.get("evidence_file", "").strip()
                if not ev or not (project / ev).exists():
                    bad_evidence.append(qid)
                # S11: a "no" answer is, by construction, a deviation from the
                # requirement the question was written from -- it must carry its
                # own written note, not just leave the top-level [deviations]
                # blob to (maybe) mention it. "no" + "none found" must never pass.
                if ans == "no" and len(a.get("deviation_note", "").strip()) < 10:
                    undocumented_no.append(qid)

            chk.measure(
                "questions_answered", len(q_ids) - len(unanswered), "1", min=len(q_ids),
                remediation=(
                    f"Question id(s) {sorted(unanswered)} in {q_path.name} have no matching [[answer]] "
                    f"block in {a_path.name}. Every question must be answered."
                ),
            )
            chk.measure(
                "answers_have_yes_no", len(answers) - len(empty_answers), "1", min=len(answers) if answers else 0,
                remediation=(
                    f"Answer(s) for {empty_answers} are not 'yes' or 'no' in {a_path.name}. Every answer "
                    "must be a definite yes or no, not left blank."
                ),
            ) if answers else None
            chk.measure(
                "answers_cite_existing_evidence", len(answers) - len(bad_evidence), "1",
                min=len(answers) if answers else 0,
                remediation=(
                    f"Answer(s) for {bad_evidence} do not cite an evidence_file that exists under "
                    f"{project}. Every answer must point at a real render file (or a numeric_check id "
                    "for a dimensional claim -- renders are never dimensional acceptance on their own)."
                ),
            ) if answers else None
            chk.measure(
                "no_answers_have_deviation_notes", len(answers) - len(undocumented_no), "1",
                min=len(answers) if answers else 0,
                remediation=(
                    f"Answer(s) for {undocumented_no} are 'no' with no (or a too-short) deviation_note. "
                    "A 'no' answer is itself a deviation from the requirement the question was written "
                    "from -- write what was actually found, don't leave it for the [deviations] summary "
                    "to (maybe) mention."
                ),
            ) if answers else None
            deviations = adata.get("deviations", {}).get("notes", None)
            if deviations is None:
                chk.error(f"{a_path}: missing [deviations] section -- every answer set must list deviations (even if none found)")
                return 2

        chk.tool("pyvista", __import__("pyvista").__version__)
        return chk.finish(notes=(
            f"{len(questions)} questions in {q_path.name}. Renders are never dimensional acceptance "
            "(docs/brief/FORGE-BRIEF.md §0) -- numeric_check ids on answers point at the real evidence."
        ))
    except CheckContractError as exc:
        return chk.error(str(exc))
    except Exception as exc:  # noqa: BLE001 -- fail closed, never a silent pass
        return chk.error(f"{type(exc).__name__}: {exc}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", type=Path, default=Path.cwd())
    ap.add_argument("--changed", action="append", default=[])
    ap.add_argument("--fast", action="store_true")
    ns = ap.parse_args()
    project = ns.project.resolve()

    parts = _find_parts(project, ns.changed)
    if not parts:
        print("[SKIP] no analysis/renders/*-questions.toml or *-answers.toml files to check")
        return 0

    worst = 0
    for part in parts:
        rc = _run_one(part, project)
        worst = max(worst, rc)
    return worst


if __name__ == "__main__":
    sys.exit(main())
