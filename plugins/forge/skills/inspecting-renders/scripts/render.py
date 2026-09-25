#!/usr/bin/env python3
"""Question-first render inspection (CADCodeVerify-style, docs/research/R3 §1).

**Refuses to render** unless ``analysis/renders/<part>-questions.toml``
already exists with 10-20 yes/no questions written *before* any render is
produced -- the questions must come from the requirements, not be
back-fitted to whatever the render happens to show.

Renders the real part named by the questions file's ``[part]`` table (a
build123d module or a STEP file, via ``forge_cad.load`` -- never
placeholder/demo geometry): standard views (front, top, right, iso), one
section view and one exploded view with PyVista offscreen. Writes an
answers template (``<part>-answers.toml``) where every answer must cite a
render file and, where possible, a numeric check id -- a render is a second
layer, never the only evidence (docs/brief/FORGE-BRIEF.md §0 "numbers beat
pictures").

    forge-python ${CLAUDE_SKILL_DIR}/scripts/render.py --project <root> --part <name>
"""
from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path

# CONTRACTS §10: skills/<skill>/scripts/x.py -> plugins/forge/lib
_LIB_DIR = Path(__file__).resolve().parents[3] / "lib"
if str(_LIB_DIR) not in sys.path:
    sys.path.insert(0, str(_LIB_DIR))

MIN_QUESTIONS = 10
MAX_QUESTIONS = 20


class RenderRefused(RuntimeError):
    """The precondition (a written questions file, naming real geometry) was not met."""


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


def load_part_spec(project: Path, part: str) -> dict:
    """S11: the questions file must name the real part to render -- a build123d
    module or a STEP file -- so a render can never silently fall back to
    placeholder/demo geometry that has nothing to do with the design being
    inspected. Optional `mate_module`/`mate_step` names a second body (e.g. a
    mating part) shown alongside it for the section/exploded views."""
    q_path = project / "analysis" / "renders" / f"{part}-questions.toml"
    data = tomllib.loads(q_path.read_text())
    part_tbl = data.get("part")
    if not isinstance(part_tbl, dict):
        raise RenderRefused(
            f"{q_path} has no [part] table. Add [part] module = \"cad/<file>.py\" (or step = "
            "\"cad/out/<file>.step\") naming the real geometry to render -- this skill never renders "
            "placeholder/demo geometry in place of the part being inspected."
        )
    if ("module" in part_tbl) == ("step" in part_tbl):
        raise RenderRefused(f"{q_path}: [part] needs exactly one of module = <path.py> or step = <path.step>")
    return part_tbl


def load_geometry(project: Path, part_tbl: dict):
    """Loads the shape(s) [part] names, via forge_cad (the same loader
    verifying-geometry/checking-dfm use) -- never a hard-coded demo."""
    from forge_cad import load

    def _one(key_module: str, key_step: str):
        if key_module in part_tbl:
            return load.load_part(project / part_tbl[key_module])
        if key_step in part_tbl:
            return load.load_step(project / part_tbl[key_step])
        return None

    try:
        primary = _one("module", "step")
        mate = _one("mate_module", "mate_step")
    except (FileNotFoundError, load.PartLoadError) as exc:
        raise RenderRefused(f"[part] geometry failed to load: {exc}") from exc
    return primary, mate


def render_views(project: Path, part: str, part_tbl: dict) -> dict[str, Path]:
    """Renders the part [part] names (a real build123d module or STEP file,
    S11) -- never placeholder/demo geometry. `mate_module`/`mate_step`
    optionally names a second body shown alongside it (e.g. a mating part),
    used for a meaningful exploded view; without one, "exploded" still
    renders the real part (there is nothing else to separate from it)."""
    import pyvista as pv

    pv.OFF_SCREEN = True
    out_dir = project / "out" / "renders" / part
    out_dir.mkdir(parents=True, exist_ok=True)

    primary_solid, mate_solid = load_geometry(project, part_tbl)
    bbox = primary_solid.bounding_box()
    size = bbox.size
    length_mm, width_mm, height_mm = size.X, size.Y, size.Z

    import tempfile
    tmp = Path(tempfile.mkdtemp(prefix="forge-render-"))
    from build123d import export_stl
    primary_stl = tmp / "primary.stl"
    export_stl(primary_solid, str(primary_stl))
    primary_mesh = pv.read(str(primary_stl))

    mate_mesh = None
    if mate_solid is not None:
        mate_stl = tmp / "mate.stl"
        export_stl(mate_solid, str(mate_stl))
        mate_mesh = pv.read(str(mate_stl))
        mate_mesh_offset = mate_mesh.translate((0, 0, max(height_mm, 1.0) * 2), inplace=False)

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

    combined = [primary_mesh] + ([mate_mesh] if mate_mesh is not None else [])
    colors = ["tan", "steelblue"][: len(combined)]
    _shot("front", "xz", combined, colors, scale_bar_mm=length_mm)
    _shot("top", "xy", combined, colors, scale_bar_mm=length_mm)
    _shot("right", "yz", combined, colors, scale_bar_mm=width_mm)
    _shot("iso", "iso", combined, colors, scale_bar_mm=length_mm)

    # section view: clip the primary part at its mid-plane and show the cut
    clipped = primary_mesh.clip(normal="x", origin=primary_mesh.center)
    _shot("section", "iso", [clipped] + ([mate_mesh] if mate_mesh is not None else []), colors)

    # exploded view: with a mate, translate it away along +z; with only one
    # body there is nothing to separate it from, so this still shows the
    # real part rather than fabricating a second one to move.
    if mate_mesh is not None:
        _shot("exploded", "iso", [primary_mesh, mate_mesh_offset], colors)
    else:
        _shot("exploded", "iso", [primary_mesh], colors[:1])

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
            'deviation_note = ""    # REQUIRED (>= 10 chars) whenever answer = "no": say what was actually found',
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
    ns = ap.parse_args()
    project = ns.project.resolve()

    try:
        questions = load_questions(project, ns.part)
        part_tbl = load_part_spec(project, ns.part)
    except RenderRefused as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    files = render_views(project, ns.part, part_tbl)
    template = write_answers_template(project, ns.part, questions, files)
    print(f"OK rendered {len(files)} views to {project / 'out' / 'renders' / ns.part}")
    print(f"OK answers template: {template}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
