---
name: rendering-products
description: Generate an engineering render pack (PyVista, orthographic projection so every view shares one exact mm-per-pixel scale, plus a scale bar) and an optional Blender marketing render. Use when the user asks for "product renders", "a render pack", "marketing images", "hero shot", or when analysis/render_packs/*.toml changes. Also fires from the mechanical.md path rule on analysis/**. Do NOT use for question-first requirements-driven inspection (see inspecting-renders) or as dimensional evidence (see verifying-geometry, stacking-tolerances) -- renders here are for a human or marketing audience, not acceptance.
paths:
  - "analysis/render_packs/**"
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(${CLAUDE_SKILL_DIR}/scripts/render_pack.py:*), Bash(${CLAUDE_SKILL_DIR}/scripts/verify.py:*), Bash(forge-python ${CLAUDE_SKILL_DIR}/scripts/render_pack.py:*), Bash(forge-python ${CLAUDE_SKILL_DIR}/scripts/verify.py:*)
---

# Rendering products

**Non-negotiable rules, read first:**
1. Every render pack lives at `analysis/render_packs/<name>.toml` and declares `[pack]` naming the **real part to render**: exactly one of `module = "cad/<file>.py"` (a build123d script exposing `build()`/`PART`) or `step = "cad/out/<file>.step"`, loaded through `forge_cad.load` (the same loader `verifying-geometry`/`checking-dfm`/`inspecting-renders` use). `render_pack.py` refuses (exit 2) a spec with neither or both, and never falls back to a parametric box built from typed-in dimensions (S12) -- the render pack shows the actual design, not a stand-in shape. Plus an optional `[scale_bar]` and `[marketing]`.
2. "Consistent camera and lighting" is made **numeric, not eyeballed**: every view uses the same orthographic (`parallel_projection`) camera scale and the same window size, recorded in `manifest.json` and re-derived independently by `verify.py` rather than trusted from the file. A render pack whose views were framed differently fails the check.
3. The scale bar's claim is the manifest's `scale_mm_per_pixel` (`= 2 * parallel_scale_mm / height_px`, exact for an orthographic camera), not a pixel measured off the PNG. The bar drawn on each image is for a human reader; the manifest is the evidence.
4. The optional Blender marketing render (`[marketing].enabled = true`) is never required for the check to pass unless a spec explicitly turns it on -- and once it's on, a failure to produce it *does* fail the check (no silent skip once requested).
5. Run `scripts/verify.py` after every spec edit.

## File format

```toml
[pack]
name = "bracket_pack"
module = "cad/bracket.py"   # or: step = "cad/out/bracket.step"

[scale_bar]
length_mm = 20.0          # must be readable and fit within the frame -- verify.py checks both
                           # (default: 25% of the part's longer in-plane bounding-box dimension)

[marketing]
enabled = false           # true to also run the optional Blender render
```

## Running

```
forge-python ${CLAUDE_SKILL_DIR}/scripts/verify.py --project <root> [--changed analysis/render_packs/bracket_pack.toml]
```

Writes `out/renders/products/<name>/{front,top,right,iso}.png`, `manifest.json`, and (if `[marketing].enabled`) `marketing.png`; `out/verify/mech.render_pack_<name>.json` with measurements `views_present`, `consistent_window_size`, `consistent_camera_scale`, `scale_mm_per_pixel_correct`, `scale_bar_fits_in_frame`, and (when requested) `marketing_render_present`. No `analysis/render_packs/*.toml` files means `[SKIP]` and exit 0.

## Running the optional Blender marketing render directly

```
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P ${CLAUDE_SKILL_DIR}/scripts/blender_render.py -- \
    --stl <path.stl> --out <path.png> [--width 1600 --height 1200]
```

**Invoke the real executable path, not the `~/.forge/bin/blender` symlink.** Verified empirically: running the identical script through the forge-bin symlink produced `couldn't find 'scripts/modules'` and Blender crashed before any Python code ran (it resolves its bundled `scripts/`/`datafiles/` relative to how it was invoked, and a symlink outside the `.app` bundle breaks that). `verify.py`'s `_resolve_blender()` handles this by preferring the real path and falling back to `Path.resolve()` on the symlink.

## What this skill refuses

- A spec with no `[pack].module`/`[pack].step` (or both), or one that names geometry that fails to load -- exit 2, never a fallback to placeholder/demo geometry.
- Calling two views "consistent" because they look similar -- the check compares the numeric `parallel_scale_mm` and window size, not pixels.
- Trusting a `manifest.json` it didn't just regenerate -- `verify.py` always re-runs `render_pack.py` rather than parsing a possibly stale file, and independently recomputes `scale_mm_per_pixel` rather than trusting the stored value.
- Silently skipping the marketing render because Blender isn't installed, when the spec asked for one -- that is a failure with a remediation (install Blender via the optional toolchain tier, or turn `[marketing].enabled` off).
- Treating any render here as a substitute for a numeric geometry or tolerance check.
