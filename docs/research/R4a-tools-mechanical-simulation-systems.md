# R4a — Tool landscape: mechanical CAD, rendering, simulation, systems

- Date accessed: 2026-09-25 · Author: research agent (Phase 1) · Scope: versions, licences, macOS arm64 install paths, Python support, security and MCP vetting for Forge's mechanical/CAE/SysML toolchain.

Tag legend: **[V]** verified in a primary source (link given) · **[L]** verified by a local read-only command (command given) · **[R]** reported by a secondary source · **[U]** unverified.

Local commands used (all read-only): `curl -s https://pypi.org/pypi/<pkg>[/<ver>]/json`, `gh api repos/<o>/<r>[/releases/latest|/commits|/tags|/contents/...]`, `brew info --json=v2 [--cask] <name>`, `curl -s https://api.anaconda.org/package/conda-forge/<pkg>`, `curl -s https://api.osv.dev/v1/query`, Docker Hub tag API, Blender Gitea API, and HTTP range reads of wheel central directories (no wheel downloaded or installed).

## Summary table

| Tool | Latest stable | Release date | Licence | macOS arm64 install | Maintained? (last release / last commit) | Security notes | Forge rec. |
|---|---|---|---|---|---|---|---|
| build123d | 0.13.0 (OCP 8); 0.11.1 is the last on OCP 7.9 used by the MCP ecosystem | 2026-09-21 (0.13.0); 2026-07-02 (0.11.1) | Apache-2.0 | `uv` wheel (pure py3) | Yes: 2026-09-21 / 2026-09-23 | No OSV advisories | **Adopt**, pin 0.11.1 now (see decisions) |
| cadquery-ocp / cadquery-ocp-novtk (OCP wheels) | 8.0.1.0.0 (OCCT 8.0.1) | 2026-09-05 | Apache-2.0 (bindings); OCCT LGPL-2.1 w/ exception [U] | `uv` wheels cp311–cp314 macOS arm64 | Yes: PyPI 2026-09-05; OCP repo 2026-09-24 | No OSV advisories; 7.9.3.1.1 macOS wheel reported broken [R] | **Adopt** novtk 7.9.3.1 |
| CadQuery | 2.8.0 | 2026-06-20 | Apache-2.0 | `uv` (needs cadquery-ocp <8.0) | Yes: 2026-06-20 / 2026-09-23 | none found | Optional (separate env; conflicts with build123d 0.13) |
| ocp_vscode (OCP CAD Viewer) | 4.1.0 | 2026-09-15 (GH) / 2026-09-16 (PyPI) | Apache-2.0 | `uv` + VS Code ext | Yes | Opens local websocket viewer | Optional (human viewing only; not headless) |
| build123d-mcp | 0.3.87 | 2026-09-24 | Apache-2.0 | `uv tool` (py3 wheel) | Very active (87 releases since 2026-04-30) | exec() of model code; Python-level sandbox only; see vetting | **Adopt with hardening**, pin exact |
| FreeCAD | 1.1.3 (next: 26.3, branches 2026-09-30) | 2026-07-25 | LGPL-2.1 | brew cask `freecad` (DMG, bundled py3.11) | Yes: weekly builds to 2026-09-23 | 7 GHSAs 2026-07-23 (5 high) fixed ≤1.1.2; Windows-only one fixed in 26.3.0 | Optional (FEM/TechDraw); pin ≥1.1.3 |
| neka-nat/freecad-mcp | 0.1.24 | 2026-09-17 | MIT | `uvx` + FreeCAD addon | Yes: 2026-09-24 | Arbitrary Python via `execute_code`; unauthenticated XML-RPC on localhost; no read-only mode | Defer (use freecadcmd scripts instead) |
| Autodesk Fusion connector | n/a (built into Fusion) | announced 2026-04-28 | Proprietary | Fusion desktop + Claude Desktop | Vendor-maintained | Local MCP exposes live design; write-capable | Avoid for Phase 1 (licence) |
| Blender | 5.2.2 LTS | 2026-09-15 | GPL-2.0-or-later (binaries GPL-3 compatible) | brew cask `blender` (330 MB DMG) | Yes | `-Y/--disable-autoexec` is default | Optional (presentation renders) |
| Blender MCP (Blender Lab) | v1.0.3 | 2026-09-11 | GPL-3.0-or-later | `.mcpb` or `uv run blender-mcp` + add-on | Yes | Runs LLM code in Blender with no guards (vendor warning) | Defer |
| CalculiX (ccx) | 2.23 | conda-forge first build 2025-11-07 | GPL-2.0 (upstream) / GPL-2.0-or-later (conda-forge) | conda-forge `calculix` osx-arm64; bundled inside FreeCAD.app; no brew formula | Yes (conda build 2026-08-12) | none found | **Adopt** via conda-forge (pixi/micromamba) |
| gmsh | 4.15.2 | 2026-03-24 | GPL-2.0-or-later (with linking exception) | `uv` wheel `gmsh` (34 MB, arm64) or brew `gmsh` | Yes | none found | **Adopt** (pip wheel) |
| Elmer FEM | 26.2 | 2026-04-28 | GPL-2 / LGPL-2.1 (mixed) | Source/Docker/nix; no brew/conda-forge | Yes: 2026-09-24 | none checked [U] | Defer |
| OpenFOAM (ESI/OpenCFD) | v2606 | 2026-06-26 | GPL-3.0 | Docker `opencfd/openfoam-run:2606` (arm64 native); or `gerlero/openfoam-app` native | Yes | Run in container `--network none` | Defer (Docker when needed) |
| OpenFOAM (Foundation) | 14 | 2026-07-14 | GPL-3.0 | macOS via Multipass VM | Yes | — | Defer |
| FEniCSx (dolfinx) | 0.11.0 | conda-forge 2026-06-23 | LGPL-3.0 | conda-forge osx-arm64 | Yes | — | Defer (optional) |
| PyVista | 0.49.0 | 2026-09-08 | MIT | `uv` (VTK wheels cp310–cp314 arm64) | Yes | VTK <9.5.1 has glTF CVEs | Adopt (headless renders) |
| VTK | 9.7.0 | 2026-08-15 | BSD-3 | `uv` wheel ~98 MB | Yes | CVE-2025-57106/7/8 fixed in 9.5.1 | Adopt, ≥9.5.1 |
| meshio | 5.3.5 | 2024-01-31 | MIT | `uv` | Stale (last commit 2024-01-31) | — | Optional |
| trimesh | 5.1.0 | 2026-08-31 | MIT | `uv` | Yes | — | Adopt (mesh checks) |
| pyrender | 0.1.45 | 2021-02-18 | MIT | `uv` | Stale (last commit 2022-04-30) | — | Avoid |
| SysML v2 Pilot Implementation | 2026-08 (Eclipse plugin 0.62.0) | 2026-09-11 | EPL-2.0 | Jupyter kernel via conda-forge `jupyter-sysml-kernel` 0.62.0 + Java 21 | Yes (monthly) | — | Adopt for CI parse/validate (via kernel) — or spec42 |
| SysML v2 API & Services | 2026-04 | 2026-05-14 | EPL-2.0 | JVM service | Low activity (license-only change) | — | Defer |
| Syside (Sensmetry) | syside (Automator) 0.10.3 | 2026-07-20 | Proprietary (Editor free; Solo/Business paid) | PyPI abi3 cp312 arm64 wheel | Yes | Paid; CI only on Business tier | Optional (needs owner approval) |
| spec42 (elan8) | v0.53.1 | 2026-09-24 | MIT | GitHub release archives | Very active | New, small project | Evaluate (open-source CI checker) |

## Findings

### 1. build123d, CadQuery, OCP wheels — Python-version matrix (critical)

- build123d latest is **0.13.0**, published 2026-09-21; release notes say it upgrades the kernel to OCP 8.0.1.0.0 and is otherwise identical to 0.12.0 [V](https://github.com/gumyr/build123d/releases/tag/v0.13.0). 0.12.0 was 2026-09-18, 0.11.1 was 2026-07-02 [L] (`gh api repos/gumyr/build123d/releases`).
- build123d 0.13.0 requires Python `>=3.11,<3.15` and `cadquery-ocp-novtk>=8.0,<8.1`, `ocpsvg>=0.7,<0.8`, `ocp_gordon>=0.3.1,<0.4` [L] (`curl pypi.org/pypi/build123d/json`). 0.11.0/0.11.1/0.12.0 all require `cadquery-ocp-novtk>=7.9,<8.0` and Python `>=3.10,<3.15` [L].
- build123d's own CI runs Python 3.14 on `macos-14` (arm64) and 3.11 on Linux [L] (`gh api repos/gumyr/build123d/contents/.github/workflows/test.yml`).
- **OCP macOS arm64 wheel matrix** [L] (`curl pypi.org/pypi/cadquery-ocp[-novtk]/<ver>/json`):

  | Wheel | cp310 | cp311 | cp312 | cp313 | cp314 | Needs VTK |
  |---|---|---|---|---|---|---|
  | cadquery-ocp 7.9.3.1 (2026-02-15) | yes | yes | yes | yes | **no** | vtk==9.5.2 (no cp314 arm64 wheel) |
  | cadquery-ocp 7.9.3.1.1 (2026-05-28) | yes | yes | yes | yes | yes | vtk==9.6.2 |
  | cadquery-ocp 8.0.1.0.0 (2026-09-05) | — | yes | yes | yes | yes | vtk==9.6.2 |
  | cadquery-ocp-novtk 7.9.3.1 | yes | yes | yes | yes | yes | none |
  | cadquery-ocp-novtk 7.9.3.1.1 | yes | yes | yes | yes | yes | none |
  | cadquery-ocp-novtk 8.0.1.0.0 | — | yes | yes | yes | yes | none |

  OCP wheel is ~60 MB download, ~217 MB unpacked (140 MB `OCP.cpython-313-darwin.so`) [L] (range-read of wheel central directory).
- All other build123d runtime deps have cp314 arm64 wheels or pure-Python wheels (numpy 2.5.3, scipy 1.18.1, scikit-learn 1.9.1, fonttools, lib3mf py3, etc.); ezdxf 1.4.4 ships arm64 C-extension wheels only to cp313 but also a pure `py3` wheel, so 3.14 falls back to pure Python [L].
- **Conclusion: Python 3.14 is technically installable for build123d on macOS arm64; 3.12 is the safer default** because the build123d-mcp README calls 3.12 a "conservative default" while listing 3.11–3.14 as supported [V](https://github.com/pzfreo/build123d-mcp/blob/v0.3.87/README.md), its CI covers 3.12/3.13/3.14 on macos-latest [L] (`ci.yml` at the tag), and agentcad's quick start tells users to create a 3.12 venv [V](https://github.com/jdilla1277/agentcad). A system-Python 3.14 is not a blocker, but Forge should pin its own interpreter via `uv` regardless.
- **Known-bad wheel:** build123d-mcp's `pyproject.toml` excludes `cadquery-ocp-novtk 7.9.3.1.1`, saying its macOS wheel lacks `OCP.GccEnt` so build123d fails to import [R] (maintainer comment in [pyproject.toml](https://github.com/pzfreo/build123d-mcp/blob/v0.3.87/pyproject.toml)). I found no upstream issue; the Python stub `OCP/GccEnt/__init__.py` is present in both wheels, so the defect (if real) is inside the monolithic `.so` [L] (range read) — **unverified; needs a smoke test** `python -c "import build123d, OCP.GccEnt"`. The constraint lives in `[tool.uv]`, so it is **not** part of published metadata: `uv tool run build123d-mcp` from PyPI will resolve 7.9.3.1.1 unless Forge adds its own constraint [L] (published `requires_dist` shows no such exclusion).
- CadQuery 2.8.0 (2026-06-20) requires `cadquery-ocp>=7.9.3.1,<8.0` plus `casadi`, `nlopt`, `numba`, `trame*` [L]. casadi ships a `cp311-abi3` arm64 wheel (works on 3.14), numba 0.67.0 and nlopt 2.11.0 have cp314 arm64 wheels [L]. CadQuery (OCP <8) and build123d 0.13 (OCP ≥8) **cannot share one environment**; build123d 0.11.x and CadQuery 2.8 can (both OCP 7.9) but one uses `cadquery-ocp` and the other `cadquery-ocp-novtk` — both install a top-level `OCP` package, so mixing is fragile [U].
- OCP GitHub has a newer tag 8.0.1.1 (2026-09-24, a regression fix) not yet on PyPI [V](https://github.com/CadQuery/OCP/releases/tag/8.0.1.1).
- **ocp_vscode** 4.1.0 (Apache-2.0) is a three.js viewer in VS Code or standalone (`ocp_viewer`, served at 127.0.0.1:3939); `save_screenshot` needs a running viewer, so it is **not headless** [V](https://github.com/bernhard-42/vscode-ocp-cad-viewer). The GitHub release text says "not yet on PyPI" but PyPI does have 4.1.0 (2026-09-16) [L].

### 2. Headless rendering options (no GUI)

| Option | Output | Headless on macOS? | Notes |
|---|---|---|---|
| build123d `ExportSVG`/`ExportDXF` + `project_to_viewport()` | 2D vector with visible/hidden edges | Yes (pure OCCT) | No native raster export [V](https://build123d.readthedocs.io/en/latest/import_export.html). Rasterise SVG with `resvg-py` (what build123d-mcp does) [V](https://github.com/pzfreo/build123d-mcp/blob/v0.3.87/pyproject.toml). Deterministic; best for drawing checks. |
| VTK offscreen (direct or via PyVista `off_screen=True`) | Shaded PNG | Yes in a logged-in macOS session [R]; on Linux uses Xvfb/OSMesa/EGL | build123d-mcp's `render_view` drives VTK in a bounded subprocess and starts Xvfb only if present [V](https://github.com/pzfreo/build123d-mcp/blob/v0.3.87/src/build123d_mcp/tools/render.py); its CI runs on macos-latest [L]. |
| trimesh + pyrender | PNG | pyrender offscreen needs EGL/OSMesa; pyglet needs a display [V](https://pyrender.readthedocs.io/en/latest/examples/offscreen.html); no macOS headless path documented | pyrender last commit 2022-04-30 [L] → avoid. trimesh itself is fine for mesh metrics. |
| Blender CLI `blender -b file.blend -P script.py -o out -f 1` | Photoreal PNG (Cycles/EEVEE) | Yes | Flags verified in manual [V](https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html); `-Y/--disable-autoexec` is default. Heavy (≈1+ GB). For presentation, not verification. |
| ocp_vscode / ocp_viewer | Browser view + screenshot | No (needs browser viewer) | Human review only. |

### 3. build123d-mcp (github.com/pzfreo/build123d-mcp) — vetting

- **Exists.** Apache-2.0, 93 stars, created 2026-04-30, latest release **v0.3.87 on 2026-09-24**, tag commit `61443b83868a204b40d335936c1c26b52b7e84b8` (lightweight tag); main is already bumped to `0.3.88.dev0` [L] (`gh api repos/pzfreo/build123d-mcp/...`). 87 GitHub releases in <5 months; contributors: pzfreo 390 commits, github-actions 83, five others ≤2 [L]. Listed in the official MCP Registry as `io.github.pzfreo/build123d-mcp` [V](https://github.com/pzfreo/build123d-mcp/blob/v0.3.87/README.md).
- PyPI `build123d-mcp 0.3.87`: wheel sha256 `88ee44d23c0f9174754622777a727398542bc9ee859e10a69a0f4ee8d4e1bf0d`, sdist sha256 `35b70487aba6b70b50a09f2491343c65246754f06204aec59f059c91adde8fba`; requires Python `>=3.11,<3.15` [L].
- **Dependencies** [L]: `mcp>=2,<3` (latest 2.2.0), `build123d>=0.10,<0.12` (so **not** compatible with build123d 0.12/0.13), `vtk>=9.3`, `bd_warehouse` (gumyr), `resvg-py`, `build123d-drafting-helpers>=0.10.0`, `quiddity>=0.3.4,<0.4`, `augura>=0.1.6`, `defusedxml`, `scipy`, `pillow`; extra `http` → `uvicorn`. **`build123d-drafting-helpers`, `quiddity`, `augura` are all single-maintainer packages by the same author** (Paul Fremantle), first published 2026-05/06/09, with 44/16/8 releases respectively [L] — supply-chain concentration; hash-lock all of them.
- **Tools (≈47 registered)** [L] (`grep` of `server.py` at the tag) and [V](https://github.com/pzfreo/build123d-mcp/blob/v0.3.87/llms.md): `execute`, `execute_file`, `render_view` (PNG/SVG/DXF; iso/top/front/side; clip planes = section views; face/edge highlight labels), `measure` (volume, area, bbox, topology, centre of mass, density/material), `validate`, `design_audit`, `verify_spec`/`suggest_spec` (experimental), `clearance`, `interference`, `cross_sections`, `analyze_printability`, `inspect_part`, `find_holes`/`find_hole_patterns`/`find_bosses`/`find_countersinks`/`recognise_features`, `compare`/`shape_compare`, `diff_snapshot`, `save_snapshot`/`restore_snapshot`, `export` (STEP/STL/DXF/SVG; labelled STEP assemblies), `import_cad_file` (STEP/STL), drawing tools (`prepare_drawing`, `inspect_drawing`, `lint_drawing`, `render_drawing`, `view_axes`, `suggest_view_layout`), `search_library`/`load_part` (bd_warehouse), `repair_hints`/`repair_advice`/`last_error`, `session_state`, `health_check`, `reset`, `version`, `workflow_hints`, `install_skill`. Resources: `build123d://quickref`, `://selectors`, `://drafting`, `://session`, `://bd_warehouse`.
- **Execution model** [V](https://github.com/pzfreo/build123d-mcp/blob/v0.3.87/docs/adr/0002-worker-subprocess-crash-containment.md): model-authored code runs via `exec()` in a **persistent spawned worker subprocess**; parent SIGKILLs and restarts it on crash/timeout (state lost). Heavy native ops (render, mesh gate, design audit) run in further hard-bounded subprocesses. `--in-process` fallback trades that away.
- **Sandbox (Python-level only)** [V](https://github.com/pzfreo/build123d-mcp/blob/v0.3.87/src/build123d_mcp/security.py): AST import allowlist (build123d, bd_warehouse, build123d_drafting, draftwright, math, numpy, decimal, fractions, statistics, random, collections, itertools, functools, copy, operator, struct, typing, abc, dataclasses, enum, re, string, textwrap, pprint, json, base64, hashlib, **io**, warnings, contextlib, **inspect**) plus curated OCP submodules; bare-name calls to `open/eval/exec/compile/__import__/getattr/vars/...` blocked; dunder attributes blocked except `__name__/__doc__/__class__`; restricted builtins; default exec timeout 120 s. The module docstring itself says it is **not a complete sandbox** and ctypes/C-extensions/build123d internals are unrestricted; `inspect.getmembers` is an acknowledged escape path.
  - **Finding from code review [L]:** `io` is allowlisted and the AST check only blocks `open` when called as a bare name (`ast.Name`), so `io.open(...)` appears to pass both layers → probable arbitrary file read/write under the user's account. Not exploited/tested (research-only). Treat the server as **arbitrary code execution**.
  - `security.md` is stale (still describes a daemon-thread timeout) versus the ADR/worker design [L].
- **Filesystem:** tool-level file I/O (`export`, `render_view(save_to=)`, `import_cad_file`, drawing tools) is restricted to CWD, `$TMPDIR` and `/tmp` after `realpath` [V](https://github.com/pzfreo/build123d-mcp/blob/v0.3.87/src/build123d_mcp/tools/_paths.py). `install_skill` **writes into `.claude/skills/*/SKILL.md`, `AGENTS.md`, `.cursor/rules/`** — an MCP tool that edits agent-instruction files [V](https://github.com/pzfreo/build123d-mcp/blob/v0.3.87/src/build123d_mcp/tools/install_skill.py). Forge must hide it.
- **Network:** no `requests/urllib/socket` use found in server/worker/render/install_skill modules [L] (grep); stdio default; HTTP mode has **no auth** (README warns) [V]. The MCP SDK 2.x is outside the OSV ranges for the 2026-07 HTTP/WebSocket advisories (those affect 1.x <1.27.2/1.28.1) [L] (OSV query).
- **Hardening flags available** [L] (`cli.py`): `--tools <names>` (exact allowlist), `--disable-tool-groups`, `--exec-timeout`, `--memory-limit-mb` (RLIMIT_DATA), `--cpu-limit-s` (RLIMIT_CPU), `--library`, `--allow-imports`, `--allow-all-imports`, `--no-sandbox`, `--in-process`, `--transport`, `--viewer-socket`, `--experimental`.
- **Repo hygiene notes** [L]: repo root contains a committed 19.6 MB binary `mcp-publisher` and a `.coverage` file; not shipped in the wheel (hatch packages only `src/build123d_mcp`) [L] (pyproject). Pin to the PyPI wheel hash, not the git tree.
- **Other CAD copilots with deterministic critique** (GitHub, 2025–2026):
  - `earthtojake/text-to-cad` — MIT, 16.3k stars, v0.6.6 (2026-09-21); skills library (CAD, DFM with cited rules, DfAM mesh checks, engineering drawing PDF, DXF, URDF/SDF, slicer, SendCutSend pre-check, Bambu upload); ships as a **Claude Code plugin** (`claude plugin install cad@text-to-cad`); engine is PyPI `cadgen 0.6.6` which pins `build123d>=0.11.1,<0.12`, `cadquery-ocp-novtk>=7.9,<8` [V](https://github.com/earthtojake/text-to-cad) [L]. Strong candidate to *mine for patterns*; the Bambu/SendCutSend skills have external side effects — do not install wholesale.
  - `jdilla1277/agentcad` — Apache-2.0, 137 stars, v0.6.0 (2026-09-11); CLI + MCP, build123d scripts → STEP, PNG, metrics, validation, diffing, JSON on stdout [V](https://github.com/jdilla1277/agentcad). Evaluate as a CLI (no MCP needed).
  - `gchen19/AnkusDrive` — Apache-2.0, 6 stars, v0.5.6 (2026-09-23); FreeCAD CLI+MCP with 280+ tools incl. FEM, CFD via container, headless drawing PDF via reportlab/svglib [V](https://github.com/gchen19/AnkusDrive). Too new/large-surface; watch.
  - `partcad/partcad` — Apache-2.0, 496 stars, 0.8.123 (2026-09-23), package manager for hardware parts [L]. Optional.
  - `Adam-CAD/CADAM` — GPL-3.0, 5.2k stars, web text-to-CAD app [L]; `er-fo/CADAgent` — MIT, 93 stars [L]; `rishigundakaram/cadquery-mcp-server` — 20 stars, no licence, last push 2025-06-29 [L] → avoid.

### 4. FreeCAD

- Latest stable **1.1.3**, released 2026-07-25; 1.1 released 2026-03-24 [V](https://github.com/FreeCAD/FreeCAD/releases/tag/1.1.3) [V](https://freecad.github.io/Website/download/releases/1-1/). Licence LGPL-2.1 [L] (`gh api repos/FreeCAD/FreeCAD`). Weekly dev builds continue (weekly-2026.09.23) [L].
- **Versioning change:** FreeCAD moves to CalVer YY.N; first CalVer release **26.3 branches 2026-09-30**, shipping ~4–6 weeks later [V](https://blog.freecad.org/2026/06/26/new-freecad-versioning-scheme-and-development-cycle/). Plan to re-pin in Nov–Dec 2026.
- **macOS arm64:** `brew install --cask freecad` → `FreeCAD_1.1.3-macOS-arm64-py311.dmg`, 619 MB, sha256 `f5c0ece7cd7c932466d6effadc0fc6e179b0538a9d9a6a77a6769eae3af2667c` [L] (`brew info --json=v2 --cask freecad`; `gh api .../releases/latest`). Minimum macOS 12 [V](https://freecad.github.io/Website/download/releases/1-1/). Bundled Python **3.11** [V] (filename + [recipe.yaml](https://github.com/FreeCAD/FreeCAD/blob/1.1.3/package/rattler-build/recipe.yaml) `python>=3.11,<3.12`). Also on conda-forge (`freecad` 1.1.3 and dev builds for py311–py314 osx-arm64) [L].
- **Bundled solvers:** the macOS bundle script copies `freecad`, `freecadcmd`, **`ccx`**, **`gmsh`**, `python`, `pip`, `dot` into the app [V](https://github.com/FreeCAD/FreeCAD/blob/1.1.3/package/rattler-build/osx/create_bundle.sh); the recipe's run deps include `calculix`, `gmsh`, `ifcopenshell` [V]. (The FreeCAD wiki's macOS FEM section is marked possibly out of date [V](https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/FEM_Install.md).)
- **FEM 1.1:** new result pipelines, Elmer static current solver, CalculiX 2D electrostatics, many new ccx keywords, `Fem.frdToVTK`, Netgen gains local refinement/2nd-order [V](https://blog.freecad.org/2025/09/09/what-is-new-in-fem-for-freecad-1-1/).
- **Assembly 1.1:** part insertion, joint-motion simulation/animation, BOM [V](https://freecad.github.io/Website/download/releases/1-1/).
- **TechDraw headless:** issue #5710 (headless SVG/PDF export) is **still open**; per-view SVG via `TechDraw.viewPartAsSvg` works in `freecadcmd`, but full-page PDF export requires the GUI (`TechDrawGui.exportPageAsPdf`) [V](https://github.com/FreeCAD/FreeCAD/issues/5710). Workarounds: run the GUI under a virtual display (Linux Xvfb container) [U], or compose drawings outside TechDraw (build123d drafting → SVG → PDF, or AnkusDrive's reportlab/svglib approach [R]).
- **Security:** 7 GitHub advisories published 2026-07-23 — incl. high-severity arbitrary code execution when opening untrusted `.FCStd` (eval in BIM Project Manager / TechDraw template; unsandboxed import in `PropertyPythonObject::Restore`) and path-traversal file write; patched in 1.1.1/1.1.2; a Windows DLL-hijack fixed in 26.3.0 [L] (`gh api repos/FreeCAD/FreeCAD/security-advisories`). **Pin ≥1.1.3; treat any third-party .FCStd as untrusted code.**
- **FreeCAD MCP servers** [L] (`gh search repos "freecad mcp"`, `gh api`):

  | Repo | Stars | Licence | Last commit | Tools | Arbitrary Python? | Read-only mode? |
  |---|---|---|---|---|---|---|
  | neka-nat/freecad-mcp (PyPI `freecad-mcp` 0.1.24, 2026-09-17; tag v0.1.24 `751974609a401660a58a1772ef16f3afbeba9ba1`; wheel sha256 `1e050ca6…3583`) | 2,458 | MIT | 2026-09-24 | 17: create/list/reload document, create/edit/delete/get objects, `get_view` screenshot, `execute_code`, `execute_code_async`, `execute_code_headless` (spawns `freecadcmd`), parts library, `run_fem_analysis` (CalculiX) [V](https://github.com/neka-nat/freecad-mcp/blob/main/docs/tools.md) | Yes (GUI thread and headless) | No (only `--only-text-feedback`, `--host`, `--freecadcmd`) [L] |
  | blwfish/freecad-mcp v8.2.0 | 51 | LGPL-2.1 | 2026-09-24 | 32 tools incl. CAM | Yes (README: full Python/filesystem/OS access by design) | No; also phones GitHub daily for update checks [V](https://github.com/blwfish/freecad-mcp) |
  | gchen19/AnkusDrive v0.5.6 | 6 | Apache-2.0 | 2026-09-23 | 280+ | Yes (`run script.py`) | No [U] |
  | sandraschi/freecad-mcp v0.6.0 | 31 | MIT | 2026-09-18 | headless + FluidX3D/OpenFOAM | [U] | [U] |
  | contextform/freecad-mcp | 129 | none | 2025-08-15 | — | [U] | — |
  | bonninr/freecad_mcp | 228 | MIT | 2025-03-20 (stale) | — | — | — |

  neka-nat's addon runs an **unauthenticated XML-RPC server** (default localhost, port 9875; optional 0.0.0.0 with IP allowlist; refuses browser-originated requests) [V](https://github.com/neka-nat/freecad-mcp/blob/main/docs/configuration.md). **Recommendation: none for Phase 1.** Every candidate is an arbitrary-code-execution bridge with no read-only mode; Forge gets the same capability with less privilege by invoking pinned, reviewed `freecadcmd` scripts through Bash (per-command permission prompts, no long-lived listener). If an MCP is later required, neka-nat 0.1.24 pinned by wheel hash is the best-maintained.

### 5. Official Claude connectors for Autodesk Fusion and Blender; Fusion personal-use terms

- Anthropic's "Claude for Creative Work" (2026-04-28) announced nine connectors incl. **Autodesk Fusion** and **Blender** [V](https://www.anthropic.com/news/claude-for-creative-work). Fusion connector is for users "with a Fusion subscription"; Blender connector is MCP-based and usable by other LLMs [V]. Anthropic donated to Blender (post updated 2026-05-01) [V].
- **Fusion connector**: listed in Claude's directory as a **local MCP server / desktop extension published by Autodesk**; Fusion must be installed and running locally, MCP server enabled in Fusion preferences, Claude Desktop configured [V](https://claude.com/connectors/autodesk-fusion). Setting path Preferences › General › API › Fusion MCP Server and default port 27182 [R](https://onemetrik.com/market-insights/claude-autodesk-fusion/) [R](https://www.promptarmor.com/connectors/autodesk-fusion). Whether it works with the free personal-use licence or with Claude Code (vs Desktop) — [U] (Autodesk pages return HTTP 403 to automated fetches).
- **Fusion for personal use terms** (Autodesk's own page, via Wayback snapshot 2026-09-02) [V](http://web.archive.org/web/20260902132508/https://www.autodesk.com/products/fusion-360/personal): personal, **non-commercial** home-based projects only; individuals earning **< US$1,000/yr**; not for primary employment, company environments or commercial training; users above the cap or doing commercial work must convert to a paid subscription; free as a **3-year** term; limited CAM, single-user data management, limited electronics/PCB, limited 2D drawings, forum support only, **limited import/export file types**. The page did not state an active-document cap (commonly reported as 10) → [U].
- **Implication:** a product-engineering organisation doing commercial work is ineligible for the personal licence; Fusion would require a paid subscription and owner approval. **Avoid for Phase 1.**
- **Blender MCP (official, Blender Lab)**: repo `projects.blender.org/lab/blender_mcp`, created 2026-02-21, 25 stars; latest release **v1.0.3 (2026-09-11)**, tag commit `2cea8d566dde07fbac28a61d698909d69724e853`, assets `blender-1.0.3.mcpb`, `mcp-1.0.3.zip` [L] (Gitea API). Licence GPL-3.0-or-later; add-on requires **Blender ≥5.1.0**; the add-on declares network permission for a local TCP socket [V](https://projects.blender.org/lab/blender_mcp). Architecture: MCP client ⇄ stdio ⇄ `blender-mcp` ⇄ TCP ⇄ add-on [V]. Tools include `execute_blender_code`, `execute_blender_code_for_cli` (background Blender), blend-file summaries, API/manual doc search, screenshots, `render_thumbnail_to_path`, `render_viewport_to_path` [V](https://projects.blender.org/lab/blender_mcp/src/branch/main/readme_tools.rst). Vendor warns it executes LLM code **without guards** and suggests VMs [V](https://www.blender.org/lab/mcp-server/). Python package pins `mcp[cli]>=1.2.0,<2` — Forge must constrain `mcp>=1.28.1` to clear 2026-07 SDK advisories [L] (OSV). Note `main` pyproject still says 1.0.2 at tag v1.0.3 time [L]. Third-party `ahujasid/blender-mcp` is a different project [R].

### 6. Blender

- **5.2.2 LTS, released 2026-09-15**; macOS Apple Silicon DMG 330 MB; requires macOS 13+ and Apple Silicon (Intel dropped from 5.0) [V](https://www.blender.org/download/) [V](https://www.blender.org/download/requirements/). `brew install --cask blender` → 5.2.2 DMG, sha256 `dc4125399b8bfefe…` [L]. Licence GPL-2.0-or-later source, binaries GPL-3 compatible; outputs unrestricted [V](https://www.blender.org/about/license/).
- Headless: `blender -b <file> -P script.py -E CYCLES -o //out_#### -f 1 --python-exit-code 1`; auto-exec of embedded scripts is disabled by default (`-Y`) [V](https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html).

### 7. Simulation stack

- **CalculiX** latest **2.23**, GPL-2 [V](http://www.dhondt.de/); official site offers Linux executables and source only [V]. macOS arm64: **conda-forge `calculix` 2.23** (osx-arm64 builds, latest 2026-08-12, ~2 MB + arpack/openblas/gfortran deps) [L]; **no Homebrew formula** (`brew search calculix` returns nothing) [L]; also bundled inside FreeCAD.app [V].
- **gmsh 4.15.2** (2026-03-24), GPL-2.0-or-later with linking exception [V](https://gmsh.info/). PyPI wheel `gmsh-4.15.2-py2.py3-none-macosx_12_0_arm64.whl` 34 MB, sha256 `f6649b3e59f49272e7ee8ab282ecb4d1a6e0d627e86cf3e3b1a83fd07417e4f8` — Python-version-independent, so works on 3.12–3.14 [L]. Homebrew `gmsh` 4.15.2 bottle exists but pulls opencascade, fltk, cairo etc. [L]. Prefer the pip wheel.
- **Elmer FEM** release **26.2** (2026-04-28); GPL-2 / LGPL-2.1 mixed licensing [V](https://github.com/ElmerCSC/elmerfem/releases/tag/release-26.2). Not on Homebrew or conda-forge [L]; source/Docker/nix only; AnkusDrive reports no practical macOS build [R]. Defer.
- **OpenFOAM**: ESI/OpenCFD **v2606** released 2026-06-26, macOS via Docker Hub images [V](https://www.openfoam.com/current-release); `opencfd/openfoam-run:2606` has native **arm64** (251 MB compressed) and `openfoam-default` arm64 ≈367 MB compressed (latest tag 2512) [L] (Docker Hub API). Foundation **OpenFOAM 14** released 2026-07-14; macOS route is Multipass VM [V](https://openfoam.org/download/) [R](https://openfoam.org/release/14/). Native macOS app `gerlero/openfoam-app` v2.2.2 (2026-09-01), GPL-3.0, `openfoam2606-app-arm64.zip` 257 MB [L]. conda-forge `openfoam` has no osx-arm64 builds [L].
- **FEniCSx** dolfinx 0.11.0 on conda-forge osx-arm64 (2026-06-23), LGPL-3.0 [L]. Optional.
- **PyVista 0.49.0** (MIT, 2026-09-08) + **VTK 9.7.0** (BSD, cp310–cp314 arm64, ~98 MB) [L]. VTK < 9.5.1 has three glTF-loader memory-safety CVEs (CVE-2025-57106/57107/57108) [L] (OSV). **meshio 5.3.5** (2024-01-31, last commit 2024-01-31) is stale [L]; **trimesh 5.1.0** active [L].
- **Simulation MCP servers** [L] (`gh search repos`): `webworn/openfoam-mcp-server` (121 stars, non-standard licence, last push 2026-01-18, education-oriented); `OFFTECH/gmsh-mcp-server` (0 stars, GPL-3.0, new); no CalculiX MCP found. neka-nat's `run_fem_analysis` is the only FEM tool among mainstream CAD MCPs. **Recommendation: none** — drive ccx/gmsh as CLIs from reviewed scripts; results are files (`.frd`, `.dat`, `.msh`) Forge can parse deterministically.

### 8. Systems (SysML v2)

- **OMG status:** KerML 1.0, SysML 2.0 and Systems Modeling API & Services 1.0 were **formally adopted by OMG as of 30 June 2025**; editorially updated March 2026 for ISO submission [V](https://github.com/Systems-Modeling/SysML-v2-Release).
- **Pilot Implementation** latest **2026-08** (published 2026-09-11), Eclipse plugin 0.62.0; now EPL-2.0 (was LGPL) [V](https://github.com/Systems-Modeling/SysML-v2-Pilot-Implementation/releases/tag/2026-08) [V](https://github.com/Systems-Modeling/SysML-v2-Release/releases/tag/2026-08). Distribution: Eclipse plugins (Java 21, Eclipse 2025-12) and a **Jupyter kernel** — `conda install jupyter-sysml-kernel=0.62.0 -c conda-forge` + Java 21 [V](https://github.com/Systems-Modeling/SysML-v2-Release/blob/master/install/jupyter/install.sh); conda-forge has 0.62.0 (2026-09-11, noarch) [L]. **No official CLI**; headless CI options: execute a notebook with the SysML kernel (`jupyter nbconvert --execute`) [U — pattern not documented upstream], or build the Maven project and call the interactive API from Java [U].
- **API & Services** 2026-04 (2026-05-14) — license-only change since 2025-04 [V](https://github.com/Systems-Modeling/SysML-v2-API-Services/releases/tag/2026-04).
- **Syside (Sensmetry):** Free = Syside Editor (VS Code extension); **Solo** (paid per user/month, 30-day trial) = Modeler + Automator (Python API, CLI, validation, diagram export); **Business** (quote) adds CI/CD integration, air-gapped, floating licences; free for academia; "Innovation Support" for startups/OSS [V](https://sensmetry.com/syside-pricing/) [V](https://sensmetry.com/syside/). PyPI `syside` 0.10.3 (2026-07-20), `LicenseRef-Proprietary`, abi3 cp312 arm64 wheel, requires Python ≥3.12 [L]. The old open-source LSP `sensmetry/sysml-2ls` was **archived 2025-10-02** [L]. `sysand` (package manager) is open-source (MIT OR Apache-2.0 on PyPI 0.2.1) [L].
- **Other open textual tooling** [L]: `elan8/spec42` (MIT, v0.53.1, 2026-09-24) — LSP + CLI `spec42 check` with text/JSON/SARIF/JUnit output for CI [V](https://github.com/elan8/spec42); `daltskin/sysml-v2-lsp` (MIT, v0.27.0, includes an MCP server); `daltskin/sysml-v2-grammar` (ANTLR4, MIT); `eclipse-syson/syson` (EPL-2.0, v2026.9.0, web graphical modeller); `Open-MBEE/OpenSysML` (Go, Apache-2.0, v0.8.1); `ansys/pysam-sysml2` (MIT, API client); `MontiCore/sysmlv2` (no licence file). Conformance of these to the Pilot is **[U]**.

### 9. Mechanical copilots / DFM tools — note only (not verified in depth)

- Leo AI — engineering copilot (commercial) [U]
- CADAgent (`er-fo/CADAgent`, MIT, 93 stars) — conversational CAD [L]
- Zoo (KittyCAD) Text-to-CAD API — commercial API; `KittyCAD/text-to-cad-ui` MIT UI [L]
- CADAM (Adam-CAD) — GPL-3.0 web text-to-CAD [L]
- Xometry / Protolabs instant-quote DFM — commercial web services requiring uploads of CAD [U]
- SendCutSend pre-check (as text-to-cad skill) [V](https://github.com/earthtojake/text-to-cad)

### 10. Disk footprint estimates (machine has ~45 GiB free)

| Item | Download | Installed (estimate) | Basis |
|---|---|---|---|
| FreeCAD 1.1.3 .app (incl. ccx, gmsh, Python 3.11) | 619 MB DMG [L] | ~1.5–2.5 GB [U] | DMG size; conda env contents |
| Blender 5.2.2 | 330 MB DMG [V] | ~1–1.5 GB [U] | — |
| OpenFOAM v2606 Docker (`openfoam-run`, arm64) | 251 MB compressed [L] | ~0.8–1.2 GB image [U] + Docker VM overhead | Docker Hub |
| OpenFOAM `openfoam-default` / dev image | 367 / 328 MB compressed [L] | ~1.5–2 GB [U] | — |
| CalculiX via conda-forge (with arpack/openblas/gfortran/openmp) | ~2 MB pkg + ~30–60 MB deps [U] | ~100–200 MB [U] | conda API |
| gmsh wheel | 34 MB [L] | ~100 MB [U] | PyPI |
| build123d env (OCP ~217 MB unpacked [L] + numpy/scipy/sklearn/sympy) | ~150 MB | ~0.8–1.2 GB [U] | wheel inspection |
| VTK wheel | 98–102 MB [L] | ~300–400 MB [U] | PyPI |
| Two uv envs (project CAD + build123d-mcp) | — | ~2–2.5 GB [U] | uv hard-links shared wheels from cache |

Adopt-set (build123d env + MCP env + gmsh + CalculiX) ≈ 3 GB; adding FreeCAD + Blender + one OpenFOAM image ≈ +4–6 GB. Comfortably within 45 GiB but Docker Desktop's VM disk should be capped.

## Implications for Forge

1. **Python:** create project environments with `uv` pinned to **CPython 3.12** (`uv python pin 3.12`), not the system 3.14. 3.14 works for build123d + OCP wheels on arm64, but 3.12 is the ecosystem's tested default and avoids ezdxf/other fallbacks; revisit 3.13/3.14 at Phase 2. The FreeCAD-embedded interpreter is separate (3.11) — never mix it with the project env.
2. **CAD kernel pin (now):** `build123d==0.11.1` (wheel sha256 `4e95fa7c…a89e10`) + `cadquery-ocp-novtk==7.9.3.1` (cp312 arm64 sha256 `a070f990…c1f0e3`) with an explicit constraint `cadquery-ocp-novtk!=7.9.3.1.1`, hash-locked via `uv lock`/`uv export --require-hashes`. Rationale: build123d-mcp 0.3.87, cadgen 0.6.6, quiddity and augura all cap `build123d<0.12`. Add a CI smoke test `python -c "import build123d, OCP.GccEnt"`.
3. **Defer build123d 0.13 / OCP 8** until build123d-mcp raises its cap (track releases); then move both together. Do not install CadQuery in the same env; if needed, give it its own env.
4. **build123d-mcp: adopt with hardening.** Pin `build123d-mcp==0.3.87` by wheel hash (never `@latest`), run via `uv tool run --python 3.12 --constraint <forge-constraints.txt>` (or a Forge-owned locked venv), launch with `--tools` allowlist excluding `install_skill`, `execute_file`, `bank_candidate`, `load_part`/`search_library` unless needed; set `--memory-limit-mb` and `--cpu-limit-s`; stdio only; never `--no-sandbox`/`--allow-all-imports`/`--transport http`. Treat `execute` as arbitrary code execution (probable `io.open` bypass): run it under an OS sandbox (macOS `sandbox-exec` profile or a `--network none` container with a single writable output dir). Report the `io.open` finding upstream via a private channel after owner approval.
5. **Deterministic verification path:** render checks via build123d `project_to_viewport` → SVG (→ PNG with resvg) and VTK/PyVista offscreen PNGs; geometry metrics via build123d/trimesh. Do not use pyrender or ocp_vscode for automation.
6. **FreeCAD:** optional install `brew install --cask freecad` pinned to **1.1.3** (sha256 `f5c0ece7…2667c`); use `freecadcmd` scripts for FEM (ccx/gmsh bundled) and per-view TechDraw SVG. Do **not** rely on headless TechDraw PDF. Adopt **no FreeCAD MCP** in Phase 1. Treat third-party `.FCStd` as untrusted code (2026-07 GHSAs). Re-evaluate when 26.3 ships (~Nov 2026).
7. **Simulation:** install `gmsh==4.15.2` from PyPI (hash above) and **CalculiX 2.23 from conda-forge** via a locked pixi/micromamba env (hash-locked conda lockfile). Defer Elmer, FEniCSx, OpenFOAM; when CFD is needed, use `opencfd/openfoam-run:2606` pinned by digest, run `--network none --read-only`. No simulation MCP servers.
8. **Blender:** optional, for presentation renders only, headless `blender -b -P` with `--factory-startup` and default `-Y`. Defer the Blender Lab MCP (unguarded code exec); if adopted, pin v1.0.3 (`2cea8d56…`) and constrain `mcp>=1.28.1`.
9. **Autodesk Fusion:** avoid — personal-use licence excludes commercial/company use and caps revenue at US$1,000; the connector needs Fusion running + Claude Desktop. Requires owner approval of a paid subscription.
10. **SysML v2:** adopt the open-source path: Pilot `jupyter-sysml-kernel==0.62.0` (conda-forge, Java 21) for reference parse/validate, and evaluate `spec42` CLI (MIT, SARIF/JUnit) as the CI gate. Syside Solo/Business is paid → owner approval required; the free Editor is not usable in CI.
11. **Supply-chain:** add all single-maintainer transitive deps (build123d-drafting-helpers, quiddity, augura, resvg-py) to Forge's review list; lock exact versions + sha256; enable OSV scanning in CI (VTK ≥9.5.1, mcp ≥1.28.1 for any 1.x consumer).

## Not found / discrepancies

- **cadquery-ocp-novtk 7.9.3.1.1 "broken macOS wheel"** — only reported in build123d-mcp's pyproject comment; no upstream issue found; Python stub for `OCP.GccEnt` exists in the wheel. Unverified without installing.
- **build123d-mcp `security.md`** describes a daemon-thread timeout that the ADR/worker code has superseded — documentation drift.
- **ocp_vscode 4.1.0** GitHub release text says "not yet on PyPI"; PyPI has had it since 2026-09-16.
- **blender_mcp** tag v1.0.3 exists while `mcp/pyproject.toml` and `manifest.json` on main still read 1.0.2.
- **Blender MCP requirement:** blender.org lab page and add-on manifest say Blender ≥5.1; a secondary source says ≥4.2 — primary source (5.1) wins.
- **Fusion "10 active documents" cap** — not on Autodesk's personal-use page snapshot; unverified. Autodesk pages block automated fetches (HTTP 403); Fusion MCP port/preference path only from secondary sources.
- **Anthropic post** says Anthropic joined the Blender Development Fund per press, but the post's 2026-05-01 update characterises it as a one-time donation.
- **"syside-cli"** — no PyPI package by that name; Syside CLI ships inside paid Syside Modeler. `sysml2`, `pysysml2`, `sysml-v2` not on PyPI; `sysmlv2` on PyPI is a placeholder (0.0.1) — avoid (name-squatting risk).
- **conda-forge `openfoam`** has no osx-arm64 builds; **Homebrew** has no `calculix-ccx`, `elmer` or `openfoam` formula.
- **OpenCFD `openfoam-default`** Docker repo has no 2606 tag yet (latest 2512); `openfoam-run:2606` exists.
- **Elmer** GitHub licence shows NOASSERTION; `license_texts/` contains GPL-2 and LGPL-2.1.
- Not researched in depth due to budget: Leo AI, Xometry/Protolabs DFM specifics, Blender security advisories, SysML Pilot headless CLI patterns, exact installed sizes (all marked [U]).

## Sources

| # | Title | URL | Type | Accessed |
|---|---|---|---|---|
| 1 | build123d v0.13.0 release | https://github.com/gumyr/build123d/releases/tag/v0.13.0 | Release page | 2026-09-25 |
| 2 | build123d PyPI JSON | https://pypi.org/pypi/build123d/json | Registry | 2026-09-25 |
| 3 | build123d import/export docs | https://build123d.readthedocs.io/en/latest/import_export.html | Docs | 2026-09-25 |
| 4 | cadquery-ocp / -novtk PyPI JSON | https://pypi.org/pypi/cadquery-ocp-novtk/json | Registry | 2026-09-25 |
| 5 | CadQuery/OCP releases | https://github.com/CadQuery/OCP/releases | Release page | 2026-09-25 |
| 6 | CadQuery 2.8.0 release | https://github.com/CadQuery/cadquery/releases/tag/v2.8.0 | Release page | 2026-09-25 |
| 7 | vscode-ocp-cad-viewer README | https://github.com/bernhard-42/vscode-ocp-cad-viewer | Repo | 2026-09-25 |
| 8 | build123d-mcp README (v0.3.87) | https://github.com/pzfreo/build123d-mcp/blob/v0.3.87/README.md | Repo | 2026-09-25 |
| 9 | build123d-mcp pyproject | https://github.com/pzfreo/build123d-mcp/blob/v0.3.87/pyproject.toml | Repo | 2026-09-25 |
| 10 | build123d-mcp security.py | https://github.com/pzfreo/build123d-mcp/blob/v0.3.87/src/build123d_mcp/security.py | Source | 2026-09-25 |
| 11 | build123d-mcp ADR 0002 | https://github.com/pzfreo/build123d-mcp/blob/v0.3.87/docs/adr/0002-worker-subprocess-crash-containment.md | Source | 2026-09-25 |
| 12 | build123d-mcp llms.md | https://github.com/pzfreo/build123d-mcp/blob/v0.3.87/llms.md | Docs | 2026-09-25 |
| 13 | build123d-mcp _paths.py | https://github.com/pzfreo/build123d-mcp/blob/v0.3.87/src/build123d_mcp/tools/_paths.py | Source | 2026-09-25 |
| 14 | build123d-mcp install_skill.py | https://github.com/pzfreo/build123d-mcp/blob/v0.3.87/src/build123d_mcp/tools/install_skill.py | Source | 2026-09-25 |
| 15 | text-to-cad | https://github.com/earthtojake/text-to-cad | Repo | 2026-09-25 |
| 16 | agentcad | https://github.com/jdilla1277/agentcad | Repo | 2026-09-25 |
| 17 | AnkusDrive | https://github.com/gchen19/AnkusDrive | Repo | 2026-09-25 |
| 18 | FreeCAD 1.1.3 release | https://github.com/FreeCAD/FreeCAD/releases/tag/1.1.3 | Release page | 2026-09-25 |
| 19 | FreeCAD 1.1 notes | https://freecad.github.io/Website/download/releases/1-1/ | Project site | 2026-09-25 |
| 20 | FreeCAD versioning blog | https://blog.freecad.org/2026/06/26/new-freecad-versioning-scheme-and-development-cycle/ | Project blog | 2026-09-25 |
| 21 | FreeCAD FEM 1.1 blog | https://blog.freecad.org/2025/09/09/what-is-new-in-fem-for-freecad-1-1/ | Project blog | 2026-09-25 |
| 22 | FreeCAD macOS bundle script | https://github.com/FreeCAD/FreeCAD/blob/1.1.3/package/rattler-build/osx/create_bundle.sh | Source | 2026-09-25 |
| 23 | FreeCAD recipe.yaml | https://github.com/FreeCAD/FreeCAD/blob/1.1.3/package/rattler-build/recipe.yaml | Source | 2026-09-25 |
| 24 | FreeCAD issue #5710 | https://github.com/FreeCAD/FreeCAD/issues/5710 | Issue | 2026-09-25 |
| 25 | FreeCAD security advisories | https://github.com/FreeCAD/FreeCAD/security/advisories | Advisories | 2026-09-25 |
| 26 | FreeCAD FEM install wiki | https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/FEM_Install.md | Docs | 2026-09-25 |
| 27 | neka-nat/freecad-mcp tools | https://github.com/neka-nat/freecad-mcp/blob/main/docs/tools.md | Docs | 2026-09-25 |
| 28 | neka-nat/freecad-mcp configuration | https://github.com/neka-nat/freecad-mcp/blob/main/docs/configuration.md | Docs | 2026-09-25 |
| 29 | blwfish/freecad-mcp | https://github.com/blwfish/freecad-mcp | Repo | 2026-09-25 |
| 30 | Claude for Creative Work | https://www.anthropic.com/news/claude-for-creative-work | Vendor post | 2026-09-25 |
| 31 | Autodesk Fusion connector listing | https://claude.com/connectors/autodesk-fusion | Vendor page | 2026-09-25 |
| 32 | Fusion personal use (Wayback 2026-09-02) | http://web.archive.org/web/20260902132508/https://www.autodesk.com/products/fusion-360/personal | Vendor page (archived) | 2026-09-25 |
| 33 | onemetrik — Claude Autodesk Fusion | https://onemetrik.com/market-insights/claude-autodesk-fusion/ | Secondary | 2026-09-25 |
| 34 | PromptArmor — Fusion connector | https://www.promptarmor.com/connectors/autodesk-fusion | Secondary | 2026-09-25 |
| 35 | Blender Lab MCP server | https://www.blender.org/lab/mcp-server/ | Project site | 2026-09-25 |
| 36 | blender_mcp repo | https://projects.blender.org/lab/blender_mcp | Repo | 2026-09-25 |
| 37 | Blender download | https://www.blender.org/download/ | Project site | 2026-09-25 |
| 38 | Blender requirements | https://www.blender.org/download/requirements/ | Project site | 2026-09-25 |
| 39 | Blender licence | https://www.blender.org/about/license/ | Project site | 2026-09-25 |
| 40 | Blender CLI arguments | https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html | Docs | 2026-09-25 |
| 41 | CalculiX home | http://www.dhondt.de/ | Project site | 2026-09-25 |
| 42 | conda-forge calculix | https://anaconda.org/conda-forge/calculix | Registry | 2026-09-25 |
| 43 | Gmsh home | https://gmsh.info/ | Project site | 2026-09-25 |
| 44 | Elmer FEM release 26.2 | https://github.com/ElmerCSC/elmerfem/releases/tag/release-26.2 | Release page | 2026-09-25 |
| 45 | OpenFOAM v2606 current release | https://www.openfoam.com/current-release | Project site | 2026-09-25 |
| 46 | OpenFOAM Foundation download | https://openfoam.org/download/ | Project site | 2026-09-25 |
| 47 | OpenFOAM 14 release | https://openfoam.org/release/14/ | Project site | 2026-09-25 |
| 48 | opencfd Docker Hub | https://hub.docker.com/r/opencfd/openfoam-run | Registry | 2026-09-25 |
| 49 | gerlero/openfoam-app | https://github.com/gerlero/openfoam-app | Repo | 2026-09-25 |
| 50 | pyrender offscreen docs | https://pyrender.readthedocs.io/en/latest/examples/offscreen.html | Docs | 2026-09-25 |
| 51 | OSV API (vtk, mcp) | https://api.osv.dev/v1/query | Advisory DB | 2026-09-25 |
| 52 | SysML v2 Release README | https://github.com/Systems-Modeling/SysML-v2-Release | Repo | 2026-09-25 |
| 53 | SysML v2 Pilot 2026-08 | https://github.com/Systems-Modeling/SysML-v2-Pilot-Implementation/releases/tag/2026-08 | Release page | 2026-09-25 |
| 54 | SysML Jupyter install.sh | https://github.com/Systems-Modeling/SysML-v2-Release/blob/master/install/jupyter/install.sh | Source | 2026-09-25 |
| 55 | SysML v2 API Services 2026-04 | https://github.com/Systems-Modeling/SysML-v2-API-Services/releases/tag/2026-04 | Release page | 2026-09-25 |
| 56 | Syside product page | https://sensmetry.com/syside/ | Vendor page | 2026-09-25 |
| 57 | Syside pricing | https://sensmetry.com/syside-pricing/ | Vendor page | 2026-09-25 |
| 58 | spec42 | https://github.com/elan8/spec42 | Repo | 2026-09-25 |
| 59 | Homebrew cask/formula JSON (freecad, blender, gmsh) | local `brew info --json=v2` | Local | 2026-09-25 |
