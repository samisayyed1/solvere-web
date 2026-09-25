#!/usr/bin/env python3
"""Verify entrypoint for rendering-products (CONTRACTS.md §9).

For each ``analysis/render_packs/<name>.toml``: runs the PyVista
engineering render pack (orthographic projection, shared scale across
every view) and checks every view was produced at the same window size
and the same ``parallel_scale_mm`` -- the numeric form of "consistent
camera and lighting", re-derives ``scale_mm_per_pixel`` independently
from the manifest rather than trusting it, and sanity-checks the scale
bar fits in frame. If the spec opts into ``[marketing]``, also runs the
optional Blender render and checks it produced a plausible image (but
never fails the whole check just because Blender/an opt-out marketing
render is unavailable when it was never requested).

    forge-python skills/rendering-products/scripts/verify.py --project <root> [--changed <path> ...]
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lib"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from forge.checkresult import Check, CheckContractError  # noqa: E402
from forge.tools import find_tool, forge_home  # noqa: E402
from render_pack import render_pack  # noqa: E402

_SAFE = re.compile(r"[^a-z0-9_]+")
# Real executable paths per platform (install.sh): the macOS cask, then the Linux tarball.
BLENDER_REAL_PATHS = (
    Path("/Applications/Blender.app/Contents/MacOS/Blender"),
    forge_home() / "opt" / "blender" / "blender",
)
BLENDER_RENDER_PY = Path(__file__).resolve().parent / "blender_render.py"


def _safe_name(name: str) -> str:
    slug = _SAFE.sub("_", name.strip().lower()).strip("_")
    return slug or "pack"


def _resolve_blender() -> Path | None:
    """Resolve the REAL Blender executable path -- invoking it through the
    ~/.forge/bin/blender symlink was found to crash headlessly (see blender_render.py)."""
    for real in BLENDER_REAL_PATHS:
        if real.exists():
            return real
    found = find_tool("blender")  # $FORGE_HOME/bin/blender first, then PATH
    return Path(found).resolve() if found else None


def _find_spec_files(project: Path, changed: list[str]) -> list[Path]:
    specs_dir = project / "analysis" / "render_packs"
    if changed:
        out = []
        for c in changed:
            p = (project / c).resolve() if not Path(c).is_absolute() else Path(c)
            try:
                p.relative_to(specs_dir.resolve())
            except ValueError:
                continue
            if p.suffix == ".toml" and p.exists():
                out.append(p)
        return sorted(out)
    if not specs_dir.is_dir():
        return []
    return sorted(specs_dir.glob("*.toml"))


def _run_one(spec_path: Path, project: Path) -> int:
    try:
        spec = tomllib.loads(spec_path.read_text())
    except tomllib.TOMLDecodeError as exc:
        chk = Check(f"mech.render_pack_{_safe_name(spec_path.stem)}", str(spec_path), level="L1", project=project)
        return chk.error(f"{spec_path}: invalid TOML: {exc}")

    if "pack" not in spec or "name" not in spec["pack"]:
        chk = Check(f"mech.render_pack_{_safe_name(spec_path.stem)}", str(spec_path), level="L1", project=project)
        return chk.error(f"{spec_path}: missing [pack] table or [pack].name")

    name = spec["pack"]["name"]
    check_id = f"mech.render_pack_{_safe_name(name)}"
    target = str(spec_path.relative_to(project)) if spec_path.is_relative_to(project) else str(spec_path)
    chk = Check(check_id, target, level="L1", project=project)

    try:
        manifest_path = render_pack(project, spec_path)
        manifest = json.loads(manifest_path.read_text())
        views = manifest.get("views", [])

        out_dir = manifest_path.parent
        missing = [v["name"] for v in views if not (out_dir / v["file"]).exists()
                   or (out_dir / v["file"]).stat().st_size < 1000]
        chk.measure(
            "views_present", len(views) - len(missing), "1", min=len(views) if views else 1,
            remediation=(
                f"Render(s) {missing} missing or implausibly small under {out_dir}. Re-run render_pack.py "
                f"for {spec_path.name}."
            ),
        )

        sizes = {(v["width_px"], v["height_px"]) for v in views}
        scales = {v["parallel_scale_mm"] for v in views}
        chk.measure(
            "consistent_window_size", len(sizes), "1", equals=1,
            remediation=(
                f"Views use {len(sizes)} different window sizes ({sizes}) -- an engineering render pack "
                "must use one consistent size/framing across all views."
            ),
        )
        chk.measure(
            "consistent_camera_scale", len(scales), "1", equals=1,
            remediation=(
                f"Views use {len(scales)} different orthographic parallel_scale_mm values ({scales}) -- "
                "this is what 'consistent camera' means numerically here; all views must share one scale."
            ),
        )

        recompute_mismatches = []
        for v in views:
            expected = round((2.0 * v["parallel_scale_mm"]) / v["height_px"], 6)
            if abs(expected - v["scale_mm_per_pixel"]) > 1e-6:
                recompute_mismatches.append(v["name"])
        chk.measure(
            "scale_mm_per_pixel_correct", len(views) - len(recompute_mismatches), "1", min=len(views) if views else 1,
            remediation=(
                f"View(s) {recompute_mismatches} report a scale_mm_per_pixel that does not match "
                "2*parallel_scale_mm/height_px recomputed independently -- the manifest may be stale or "
                "hand-edited. Re-run render_pack.py."
            ),
        )

        scale_bar_mm = manifest.get("scale_bar_length_mm", 0)
        bar_fits = []
        for v in views:
            bar_px = scale_bar_mm / v["scale_mm_per_pixel"] if v["scale_mm_per_pixel"] else 1e9
            if not (10 <= bar_px <= 0.9 * v["width_px"]):
                bar_fits.append(v["name"])
        chk.measure(
            "scale_bar_fits_in_frame", len(views) - len(bar_fits), "1", min=len(views) if views else 1,
            remediation=(
                f"Scale bar ({scale_bar_mm} mm) does not fit sensibly in view(s) {bar_fits} (too small to "
                f"read or wider than 90% of the frame). Adjust [scale_bar].length_mm in {spec_path.name}."
            ),
        )

        marketing_cfg = spec.get("marketing", {})
        if marketing_cfg.get("enabled"):
            blender = _resolve_blender()
            if blender is None:
                chk.measure(
                    "marketing_render_present", 0, "1", min=1,
                    remediation=(
                        "[marketing].enabled = true but no Blender executable was found. Install it "
                        "(plugins/forge/toolchain/install.sh, optional tier T5) or set enabled = false."
                    ),
                )
            else:
                import tempfile
                from build123d import export_stl
                from render_pack import _build_part
                pack_cfg = spec["pack"]
                part = _build_part(
                    float(pack_cfg["length_mm"]), float(pack_cfg["width_mm"]), float(pack_cfg["height_mm"]),
                    pack_cfg.get("hole_diameter_mm"),
                )
                tmp = Path(tempfile.mkdtemp(prefix="forge-marketing-"))
                stl_path = tmp / "part.stl"
                export_stl(part, str(stl_path))
                marketing_png = out_dir / "marketing.png"
                r = subprocess.run(
                    [str(blender), "-b", "--factory-startup", "-P", str(BLENDER_RENDER_PY), "--",
                     "--stl", str(stl_path), "--out", str(marketing_png)],
                    capture_output=True, text=True, timeout=180,
                )
                ok = r.returncode == 0 and marketing_png.exists() and marketing_png.stat().st_size > 1000
                chk.measure(
                    "marketing_render_present", 1 if ok else 0, "1", min=1,
                    remediation=(
                        f"Blender marketing render failed (exit {r.returncode}) or produced an implausibly "
                        f"small file. stderr tail: {r.stderr[-800:]}"
                    ),
                )

        chk.tool("pyvista", __import__("pyvista").__version__)
        return chk.finish(notes=(
            f"{len(views)} views at parallel_scale_mm={next(iter(scales), '?')}, "
            f"scale_bar_length_mm={scale_bar_mm}. Orthographic projection makes mm-per-pixel exact and "
            "independently recomputable, rather than eyeballed from the image."
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

    spec_files = _find_spec_files(project, ns.changed)
    if not spec_files:
        print("[SKIP] no analysis/render_packs/*.toml files to check")
        return 0

    worst = 0
    for path in spec_files:
        rc = _run_one(path, project)
        worst = max(worst, rc)
    return worst


if __name__ == "__main__":
    sys.exit(main())
