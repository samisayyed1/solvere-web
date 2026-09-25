#!/usr/bin/env python3
"""Question-first render inspection (CADCodeVerify-style, docs/research/R3 §1).

**Refuses to render** unless ``analysis/renders/<part>-questions.toml``
already exists with 10-20 yes/no questions written *before* any render is
produced -- the questions must come from the requirements, not be
back-fitted to whatever the render happens to show.

Renders standard views (front, top, right, iso), one section view and one
exploded view with PyVista offscreen, then writes an answers template
(``<part>-answers.toml``) where every answer must cite a render file and,
where possible, a numeric check id -- a render is a second layer, never
the only evidence (docs/brief/FORGE-BRIEF.md §0 "numbers beat pictures").

    forge-python ${CLAUDE_SKILL_DIR}/scripts/render.py --project <root> --part <name> \\
        [--step <path.step>] [--length-mm 80 --width-mm 40 --height-mm 10]
"""
from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path

MIN_QUESTIONS = 10
MAX_QUESTIONS = 20


class RenderRefused(RuntimeError):
    """The precondition (a written questions file) was not met."""


def load_questions(project: Path, part: str) -> list[dict]:
    q_path = project / "analysis" / "renders" / f"{part}-questions.toml"
    if not q_path.exists():
        raise RenderRefused(
            f"{q_path} does not exist. Write {MIN_QUESTIONS}-{MAX_QUESTIONS} yes/no validation "
            "questions from the requirements BEFORE rendering anything -- this skill refuses to "
            "render without them (question-first, CADCodeVerify-style; docs/research/R3)."
        )
    try:
        data = tomllib.loads(q_path.read_text())
    except tomllib.TOMLDecodeError as exc:
        raise RenderRefused(f"{q_path}: invalid TOML: {exc}") from exc
    questions = data.get("question", [])
    if not (MIN_QUESTIONS <= len(questions) <= MAX_QUESTIONS):
        raise RenderRefused(
            f"{q_path} has {len(questions)} questions; must have between {MIN_QUESTIONS} and "
            f"{MAX_QUESTIONS}."
        )
    for i, q in enumerate(questions):
        if "id" not in q or "text" not in q:
            raise RenderRefused(f"{q_path}: question #{i + 1} missing 'id' or 'text'")
    return questions


def _build_demo_assembly(length_mm: float, width_mm: float, height_mm: float):
    """A tiny two-part 'assembly' (plate + pin) so the exploded view has something to explode."""
    from build123d import BuildPart, Box, Cylinder, Location

    with BuildPart() as plate:
        Box(length_mm, width_mm, height_mm)
    with BuildPart() as pin:
        Cylinder(radius=min(length_mm, width_mm) * 0.08, height=height_mm * 3)
    return plate.part, pin.part


def render_views(project: Path, part: str, *, length_mm: float, width_mm: float, height_mm: float) -> dict[str, Path]:
    import pyvista as pv

    pv.OFF_SCREEN = True
    out_dir = project / "out" / "renders" / part
    out_dir.mkdir(parents=True, exist_ok=True)

    plate_solid, pin_solid = _build_demo_assembly(length_mm, width_mm, height_mm)

    import tempfile
    tmp = Path(tempfile.mkdtemp(prefix="forge-render-"))
    from build123d import export_stl
    plate_stl = tmp / "plate.stl"
    pin_stl = tmp / "pin.stl"
    export_stl(plate_solid, str(plate_stl))
    export_stl(pin_solid, str(pin_stl))

    plate_mesh = pv.read(str(plate_stl))
    pin_mesh = pv.read(str(pin_stl))
    pin_mesh_offset = pin_mesh.translate((0, 0, height_mm * 2), inplace=False)

    files: dict[str, Path] = {}

    def _shot(name: str, camera: str, meshes: list, colors: list, scale_bar_mm: float | None = None):
        pl = pv.Plotter(off_screen=True, window_size=[640, 480])
        pl.set_background("white")
        for mesh, color in zip(meshes, colors):
            pl.add_mesh(mesh, color=color, show_edges=True, edge_color="black", line_width=1)
        pl.camera_position = camera
        pl.add_axes()
        if scale_bar_mm:
            pl.add_text(f"scale ref: {scale_bar_mm:.0f} mm cube edge", position="lower_left", font_size=8)
        path = out_dir / f"{name}.png"
        pl.screenshot(str(path))
        pl.close()
        files[name] = path

    combined = [plate_mesh, pin_mesh]
    colors = ["tan", "steelblue"]
    _shot("front", "xz", combined, colors, scale_bar_mm=length_mm)
    _shot("top", "xy", combined, colors, scale_bar_mm=length_mm)
    _shot("right", "yz", combined, colors, scale_bar_mm=width_mm)
    _shot("iso", "iso", combined, colors, scale_bar_mm=length_mm)

    # section view: clip the plate at its mid-plane and show the cut
    clipped = plate_mesh.clip(normal="x", origin=plate_mesh.center)
    _shot("section", "iso", [clipped, pin_mesh], colors)

    # exploded view: pin translated away from the plate along +z
    _shot("exploded", "iso", [plate_mesh, pin_mesh_offset], colors)

    return files


def write_answers_template(project: Path, part: str, questions: list[dict], render_files: dict[str, Path]) -> Path:
    out_path = project / "analysis" / "renders" / f"{part}-answers.toml"
    if out_path.exists():
        return out_path  # never overwrite an in-progress answer set
    lines = [
        f'part = "{part}"',
        "# Every answer must cite an evidence_file (a render that exists in out/renders/<part>/)",
        "# and, where a numeric check applies, a numeric_check id (an out/verify/<check_id>.json).",
        "# Renders are never dimensional acceptance -- a numeric check must back any dimensional claim.",
        "",
    ]
    for q in questions:
        lines += [
            "[[answer]]",
            f'question_id = "{q["id"]}"',
            f'question_text = "{q["text"]}"',
            'answer = ""            # "yes" or "no" -- fill in after inspecting the renders',
            'evidence_file = ""     # e.g. "out/renders/{}/iso.png" (must exist)'.format(part),
            'numeric_check = ""     # e.g. "geometry.min_wall" (out/verify/<id>.json), or "" if purely visual',
            "",
        ]
    lines.append("[deviations]")
    lines.append('notes = ""   # list every deviation from the requirements found while answering, even minor ones')
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n")
    return out_path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", type=Path, default=Path.cwd())
    ap.add_argument("--part", required=True)
    ap.add_argument("--length-mm", type=float, default=80.0)
    ap.add_argument("--width-mm", type=float, default=40.0)
    ap.add_argument("--height-mm", type=float, default=10.0)
    ns = ap.parse_args()
    project = ns.project.resolve()

    try:
        questions = load_questions(project, ns.part)
    except RenderRefused as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    files = render_views(project, ns.part, length_mm=ns.length_mm, width_mm=ns.width_mm, height_mm=ns.height_mm)
    template = write_answers_template(project, ns.part, questions, files)
    print(f"OK rendered {len(files)} views to {project / 'out' / 'renders' / ns.part}")
    print(f"OK answers template: {template}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
