#!/usr/bin/env python3
"""Engineering render pack: PyVista offscreen, orthographic (parallel) projection so every
view shares an exact, computable mm-per-pixel scale -- consistent camera/lighting across
views plus a numerically verifiable scale bar (not a pixel-guessed one).

    forge-python ${CLAUDE_SKILL_DIR}/scripts/render_pack.py --project <root> --spec analysis/render_packs/<name>.toml

Reads a render-pack spec TOML (geometry + scale bar length), renders
front/top/right/iso at a shared orthographic scale and window size, and
writes ``out/renders/products/<name>/manifest.json`` recording each view's
``parallel_scale_mm`` and derived ``scale_mm_per_pixel`` -- the claim
``verify.py`` actually checks (docs/brief/FORGE-BRIEF.md §0: numbers beat
pictures). The drawn scale-bar line/text in each PNG is for a human
reader; the manifest is the evidence.
"""
from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path

WINDOW_SIZE = (800, 600)
VIEWS = [
    ("front", "xz"),
    ("top", "xy"),
    ("right", "yz"),
    ("iso", "iso"),
]


def _build_part(length_mm: float, width_mm: float, height_mm: float, hole_diameter_mm: float | None):
    from build123d import BuildPart, Box, Cylinder, Location

    with BuildPart() as bp:
        Box(length_mm, width_mm, height_mm)
        if hole_diameter_mm:
            with Location((0, 0, 0)):
                Cylinder(radius=hole_diameter_mm / 2, height=height_mm * 3, mode=__import__("build123d").Mode.SUBTRACT)
    return bp.part


def render_pack(project: Path, spec_path: Path) -> Path:
    import pyvista as pv
    import tempfile
    from build123d import export_stl

    spec = tomllib.loads(spec_path.read_text())
    pack = spec["pack"]
    name = pack["name"]
    length_mm = float(pack["length_mm"])
    width_mm = float(pack["width_mm"])
    height_mm = float(pack["height_mm"])
    hole_mm = pack.get("hole_diameter_mm")
    scale_bar_mm = float(spec.get("scale_bar", {}).get("length_mm", max(length_mm, width_mm) * 0.25))

    part = _build_part(length_mm, width_mm, height_mm, hole_mm)
    tmp = Path(tempfile.mkdtemp(prefix="forge-render-pack-"))
    stl_path = tmp / "part.stl"
    export_stl(part, str(stl_path))
    mesh = pv.read(str(stl_path))

    out_dir = project / "out" / "renders" / "products" / name
    out_dir.mkdir(parents=True, exist_ok=True)

    # a shared parallel_scale (half the vertical extent of the view volume, in mm) keeps
    # every view at the SAME mm-per-pixel -- that is what "consistent camera" means here,
    # made numeric rather than eyeballed.
    diag = (length_mm ** 2 + width_mm ** 2 + height_mm ** 2) ** 0.5
    parallel_scale_mm = diag * 0.65

    manifest = {"pack": name, "scale_bar_length_mm": scale_bar_mm, "views": []}
    pv.OFF_SCREEN = True
    for view_name, camera in VIEWS:
        pl = pv.Plotter(off_screen=True, window_size=list(WINDOW_SIZE))
        pl.set_background("white")
        pl.add_mesh(mesh, color="lightsteelblue", show_edges=True, edge_color="black", line_width=1,
                     specular=0.5, smooth_shading=True)
        pl.camera_position = camera
        pl.enable_parallel_projection()
        pl.camera.parallel_scale = parallel_scale_mm
        pl.add_axes()

        scale_mm_per_pixel = (2.0 * parallel_scale_mm) / WINDOW_SIZE[1]
        bar_px = scale_bar_mm / scale_mm_per_pixel
        pl.add_text(
            f"scale bar: {scale_bar_mm:.1f} mm ({bar_px:.0f} px @ {scale_mm_per_pixel:.4f} mm/px)",
            position="lower_left", font_size=9, color="black",
        )

        img_path = out_dir / f"{view_name}.png"
        pl.screenshot(str(img_path))
        pl.close()

        manifest["views"].append({
            "name": view_name, "file": img_path.name, "width_px": WINDOW_SIZE[0], "height_px": WINDOW_SIZE[1],
            "parallel_scale_mm": parallel_scale_mm, "scale_mm_per_pixel": round(scale_mm_per_pixel, 6),
        })

    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest_path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", type=Path, default=Path.cwd())
    ap.add_argument("--spec", type=Path, required=True)
    ns = ap.parse_args()
    project = ns.project.resolve()
    spec_path = ns.spec if ns.spec.is_absolute() else project / ns.spec
    manifest = render_pack(project, spec_path)
    print(f"OK {manifest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
