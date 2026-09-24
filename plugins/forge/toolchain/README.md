# Forge toolchain

Pinned, hash-locked engineering tools (ADR-001 §8). Small reproducible files live here. Heavy environments live in `$FORGE_HOME` (default `~/.forge`): `envs/`, `bin/`, `opt/`, `downloads/`.

| Tier | Contents | Lock |
|---|---|---|
| core | CPython 3.12 + 3.13 (uv), pixi 0.81.0, `srt` (@anthropic-ai/sandbox-runtime 0.0.77), tscircuit 0.0.2646 + @tscircuit/cli 0.1.2152 | `node/package-lock.json` |
| mech | CAD env (build123d 0.11.1, cadquery-ocp-novtk 7.9.3.1, trimesh, PyVista, VTK 9.7.0, gmsh 4.15.2, ezdxf, SKiDL), build123d-mcp 0.3.87, FreeCAD 1.1.3 | `python/cad/uv.lock`, `python/build123d-mcp/uv.lock` |
| elec | KiCad 10.0.6 (`kicad-cli`), ngspice 47, kicad-mcp-pro 3.35.0 (Python 3.13) | `python/kicad-mcp-pro/uv.lock` |
| sim / systems | CalculiX 2.23, jupyter-sysml-kernel 0.62.0, OpenJDK 21 (conda-forge) | `conda/pixi.lock` |
| render | Blender 5.2.2 LTS | brew cask version check |
| systems | spec42 0.53.1 | sha256 in `install.sh` |
| embedded-sim | Renode 1.17.0 | sha256 in `install.sh` |

- **Install / reinstall:** `./install.sh core mech elec sim render systems embedded-sim`. By default this installs exactly what the lockfiles say. `--relock` is for maintainers only, and bumping a pin needs an ADR update. The script refuses to continue on any version or sha256 mismatch, or if free disk would fall below 25 GiB.
- **Check:** `forge doctor` verifies every entry in `manifest.json`: version command plus regex, pins, and the MCP lock.
- **CLIs:** the command-line tools are linked in `~/.forge/bin`, so add that directory to `PATH`. `tsci` always runs with telemetry disabled.
- **Smoke tests** (`smoke/`) each compare a measured value with a hand calculation and include a negative control:
  - CAD volume;
  - an ngspice RC step response;
  - a CalculiX cantilever deflection.
  
  The results are in `INSTALL-LOG.md` and `manifest.json`.

**Deviations from a plain `brew install`:**
- **KiCad:** the cask needs `sudo` to copy demos into `/Library`. The installer mounts the identical cask DMG instead, verified against the cask's sha256, copies the suite to `/Applications/KiCad`, and puts the demos in `~/.forge/opt/kicad-demos`.
- **kicad-mcp-pro 3.35.0** requires Python ≥ 3.13, so it gets its own 3.13 environment. Everything else uses 3.12.
- **No MCP server is registered with Claude Code by this installer.** Servers run only through `forge-mcp-guard` once `security/mcp-lock.json` holds an approved entry.
