# R4b — Tool landscape: electronics, embedded, software side

- Date accessed: 2026-09-25 · Author: research agent (Phase 1) · Scope: current state, licensing, install path, security posture and pin targets for Forge's EDA (KiCad/atopile/tscircuit/ngspice), KiCad MCP servers, embedded toolchains/simulators/HIL, and the Claude Code software-side plugins already in use.

Tag legend: **[V]** verified in an official/primary source (URL given) · **[L]** verified by a local read-only command (command given) · **[R]** reported by a secondary source · **[U]** unverified / estimate.

Note on method: the session's WebSearch budget ran out partway through. Everything after that point was checked with `gh api`, `curl` against PyPI, npm and registry JSON, `brew info`, and WebFetch of primary pages. Anything that could not be checked that way is tagged [U].

---

## Summary table

| Tool | Latest stable | Release date | Licence | macOS arm64 install | Maintained? (last release / last commit) | Security notes | Forge rec. |
|---|---|---|---|---|---|---|---|
| KiCad (+ `kicad-cli`) | 10.0.6 | 2026-08-29 | GPL-3.0 | `brew install --cask kicad` (universal DMG, 1.40 GB) | Yes: 10.0.6 on 2026-08-29; mirror pushed 2026-09-24 | Local only. IPC API needs a running GUI. `kicad-cli` is headless and uses argv | **Adopt** |
| atopile (`ato`) | 0.15.9 (PyPI) | 2026-09-12 | MIT (PyPI metadata) | `uv tool install atopile==0.15.9` (cp314 arm64 wheel) | PyPI yes. Public GitHub `main` last commit 2026-03-11. Wheels built from the **private** `atopile/monopile` | Published code is not in the public repo. Product moving to a hosted app (0.16). Telemetry. Deps include `anthropic`/`openai` SDKs | **Defer** (needs owner decision) |
| tscircuit (`tsci`) | tscircuit 0.0.2646 / @tscircuit/cli 0.1.2152 | 2026-09-23 / 2026-09-24 | MIT | `npm i -g tscircuit@<exact>` or `bunx` | Yes, releases daily | PostHog telemetry on by default (`TSCI_TELEMETRY_DISABLED=1` turns it off). Registry/JLC import go over the network | **Adopt** (pinned, telemetry off) |
| SKiDL | 2.3.0 | 2026-07-28 | MIT | `uv pip install skidl==2.3.0` | Yes: commit 2026-08-10 (KiCad 10 README update) | Pure Python | **Optional** (fallback capture) |
| ngspice | 47 | 2026-08-11 | brew: "cannot represent" (mixed BSD-style) | `brew install ngspice` (bottle arm64_sequoia) | Yes | The `.control` language has a `shell` command, so a netlist can run commands. `.spiceinit` is auto-sourced | **Adopt** (sandboxed, `-n`) |
| PySpice | 1.5 | 2021-05-15 | GPL-3.0 | pip | **No**: last commit 2024-01-26 | n/a | **Avoid** |
| InSpice | 1.7.0.7 | 2026-09-17 | PyPI says GPL-3.0-or-later; GitHub says **AGPL-3.0** | pip (Python ≥3.12) | Yes | Licence mismatch | **Defer** |
| kicad-mcp-pro | 3.35.0 | 2026-09-24 | MIT | `uvx kicad-mcp-pro==3.35.0` (pin hash) | Yes (repo created 2026-05-31, about 100+ releases, one main maintainer) | Only server found with a **read-only default profile** (24 tools). No shell. Workspace-confined paths. Sigstore/PyPI attestations. Default profile includes a JLCPCB pricing tool that uses the network | **Optional** (review profile only) |
| mixelpixx/KiCAD-MCP-Server | v2.8.1 | 2026-09-24 | MIT | git clone + `npm install` + KiCad Python (SWIG) | Yes (2.4k stars) | No read-only mode. About 140 routed tools. The GUI driver clicks KiCad UI with **no gate** (destructive flag is advisory only) | **Avoid** |
| Seeed-Studio/kicad-mcp-server | no releases | commit 2026-09-09 | **None (no LICENSE)** | pip install -e into KiCad's bundled Python | Semi | No licence means no right to use. Pollutes KiCad's Python. Downloads parts from PartReel | **Avoid** |
| lamaalrajih/kicad-mcp | no releases | commit 2025-10-17 | MIT | git clone + make | **Stale** | Open issue #57: tools bypass their own PathValidator (fs probing) | **Avoid** |
| Quilter (commercial) | SaaS | n/a | Proprietary | Web | n/a | Free tier: design data used to make training data. Enterprise: never used for training. SOC 2 Type 2 | **Note only** |
| Flux (flux.ai, commercial) | SaaS | n/a | Proprietary | Browser | n/a | ToS: user keeps ownership. ToS is silent on AI training. Deletion within 90 days of cancellation | **Note only** |
| ESP-IDF | v6.1 (also v6.0.3, v5.5.5, v5.3.6, v5.2.8) | 2026-08-27 | Apache-2.0 | EIM installer (tap `espressif/eim`) or git + `install.sh` | Yes | Large toolchain download from Espressif/GitHub | **Adopt later** (one target only) |
| Zephyr RTOS | 4.4.2 (latest stable). LTS = 3.7 (LTS3) | 2026-08-07 | Apache-2.0 | `west` + Zephyr SDK | Yes | Many west modules (supply-chain surface) | **Adopt later** |
| Zephyr SDK | 1.0.1 | 2026-03-25 | Apache-2.0 | tarballs, macOS-aarch64 minimal + per-arch toolchains | Yes (commit 2026-09-08) | Pin tarball SHA-256 | **Adopt later** (ARM only) |
| PlatformIO Core | 6.2.0 | 2026-09-05 | Apache-2.0 | `brew install platformio` or `uv tool install platformio==6.2.0` | Yes | **Telemetry on by default**. Pulls toolchains from the PlatformIO registry at build time | **Optional** |
| Renode | 1.17.0 | 2026-09-07 | MIT (plus third-party parts) | `renode-1.17.0.osx-arm64-portable.dmg` (75.7 MB). No brew formula | Yes | Local simulation | **Adopt** (simulation) |
| QEMU | 11.1.1 | tarball dated 2026-08-27 | GPL-2.0-only | `brew install qemu` | Yes | Local | **Optional** |
| Wokwi CLI | v0.27.1 | 2026-09-16 | CLI MIT. Service proprietary | release binary `wokwi-cli-macos-arm64`, or `curl … \| sh` | Yes | **Simulation runs in Wokwi's cloud (firmware is uploaded)**. Needs a token. Paid tiers. MCP server is experimental | **Optional, needs owner approval** |
| agentic-hil | 0.21.5 | 2026-09-07 | Apache-2.0 | `uv tool install agentic-hil==0.21.5` (skip the one-liner) | Yes (created 2026-06-23, 15 stars) | Bounded MCP tools. Operator config lives outside the workspace. Interlocks for raw debugger and mass erase. **Also exposes `project_config_create/set` and `server_upgrade` tools** | **Adopt for HIL phase** (with deny rules) |
| gstack | 1.89.0.0 upstream. **1.58.5.0 installed** | 2026-09-24 upstream | MIT | git clone + `./setup` (already installed) | Yes (134k stars, 957 open issues) | Telemetry opt-in (local: off). Hourly update check to GitHub. Setup downloads Playwright Chromium. Hooks into settings.json are optional and prompted | **Keep, pinned; don't auto-upgrade** |
| claude-security plugin | 0.11.0 (installed) | n/a | **Proprietary (Anthropic)** | official marketplace | Yes | Runs inside the session | **Adopt** (already installed) |
| security-guidance plugin | 2.0.8 (installed, user scope) | n/a | see repo LICENSE | official marketplace | Yes | Sends diffs to an LLM on every Stop and commit (cost) | **Adopt** (tune env vars) |
| code-review / pr-review-toolkit / plugin-dev / skill-creator / frontend-design / clangd-lsp / pyright-lsp | unversioned (marketplace) | marketplace HEAD 2026-09-24 | Apache-2.0 (marketplace repo) | `/plugin install <name>@claude-plugins-official` | Yes | Anthropic-authored | **Adopt** plugin-dev, skill-creator, code-review. **Optional** for the rest |
| Context7 MCP | @upstash/context7-mcp 4.1.1 | npm modified 2026-09-14 | MIT (MCP client). **Backend private** | hosted `https://mcp.context7.com/mcp`, or `npx` (still calls the hosted API) | Yes | Sends the **user's question/task text** to Upstash. OTEL telemetry | **Defer / optional** (never with confidential context) |
| Official MCP Registry | registry software v1.8.1 | 2026-08-06 | NOASSERTION (repo) | `curl https://registry.modelcontextprotocol.io/v0.1/servers…` | Yes | **Preview**. Metadata only, not a trust signal | **Use for metadata lookup** |

---

## Findings

### 1. KiCad 10 and `kicad-cli`

- **Version.** KiCad 10.0.0 was released on 2026-03-20 [V](https://www.kicad.org/blog/2026/03/Version-10.0.0-Released/). The latest stable is **10.0.6**, released 2026-08-29, a bug-fix release that the project urges users to install promptly [V](https://www.kicad.org/blog/2026/08/KiCad-10.0.6-Release/). KiCad 11 is reported to target February 2027 [R](https://www.kicad.org/blog/).
- **macOS support.** macOS 12 and newer; a unified universal DMG [V](https://www.kicad.org/download/macos/).
- **Homebrew cask.** `kicad` 10.0.6 uses the URL `…/10.0.6/kicad-unified-universal-10.0.6.dmg` with sha256 `ef4dcd4278c46d3efcd28c8db273d5957d68efda028f6bf79b4811fc5302dc68`. It installs `/Applications/KiCad`, symlinks `kicad-cli` into `/opt/homebrew/bin`, and puts demos in `/Library/Application Support/kicad/demos` [L: `brew info --json=v2 --cask kicad`].
- **Size.** The DMG is **1,404,303,659 bytes (≈1.31 GiB)** [L: `gh api repos/KiCad/kicad-source-mirror/releases/tags/10.0.6`]. Installed size including symbol, footprint and 3D-model libraries is estimated at **≈5–8 GiB** [U].
- **Licence.** GPL-3.0 [V](https://github.com/KiCad/kicad-source-mirror).
- **`kicad-cli` subcommands** [V](https://docs.kicad.org/10.0/en/cli/cli.html):
  - Top level: `fp`, `jobset`, `pcb`, `sch`, `sym`, `version`.
  - There is **no** API-server subcommand [V: grep of the same page].
- **Exact syntax for the calls Forge needs** [V](https://docs.kicad.org/10.0/en/cli/cli.html):
  - `kicad-cli sch erc [--output F] [--define-var K=V]… [--format report|json] [--units U] [--severity-all|--severity-error|--severity-warning|--severity-exclusions] [--exit-code-violations] INPUT.kicad_sch`
  - `kicad-cli pcb drc [--output F] [--format report|json] [--all-track-errors] [--schematic-parity] [--units U] [--severity-*] [--exit-code-violations] [--refill-zones] [--save-board] INPUT.kicad_pcb`
    - With `--exit-code-violations`, DRC exits **0 when clean and 5 when violations exist**.
    - `--save-board` writes to the board. Forge must forbid it in review mode.
  - `kicad-cli pcb export gerbers [--output DIR] [--layers L] [--common-layers L] [--no-x2] [--no-netlist] [--subtract-soldermask] [--use-drill-file-origin] [--precision P] [--check-zones] [--variant V] [--board-plot-params] INPUT`
  - `kicad-cli pcb export drill [--output DIR] [--format excellon|gerber] [--drill-origin O] [--excellon-units U] [--excellon-zeros-format Z] [--excellon-separate-th] [--generate-map] [--map-format F] [--generate-report] [--generate-tenting] INPUT`
  - `kicad-cli pcb export pos [--output F] [--side front|back|both] [--format ascii|csv|gerber] [--units U] [--smd-only] [--exclude-fp-th] [--exclude-dnp] [--use-drill-file-origin] [--variant V] INPUT`
  - `kicad-cli sch export bom [--output F] [--preset P] [--format-preset FP] [--fields …] [--labels …] [--group-by …] [--sort-field …] [--filter …] [--exclude-dnp] [--variant V] … INPUT`
  - `kicad-cli sch export netlist [--output F] [--format kicadsexpr|kicadxml|cadstar|orcadpcb2|spice|spicemodel|pads|allegro] [--variant V] INPUT`
  - Plots: `sch export pdf|svg|dxf|ps|hpgl`, `pcb export pdf|svg|dxf|ps|hpgl`.
  - 3D: `pcb export step|stpz|glb|vrml|brep|ply|stl|u3d|xao|3dpdf`. For example, `pcb export step [--no-dnp] [--subst-models] [--board-only] [--drill-origin|--grid-origin] [--include-tracks|--include-pads|--include-zones|--include-silkscreen|--include-soldermask] [--fuse-shapes] [--no-optimize-step] INPUT`.
  - Fabrication exchange: `pcb export ipc2581|odb|ipcd356|gencad|stats`.
  - Other: `pcb render` (raytraced image) and `pcb import` (Altium, Eagle, PADS and others).
  - Housekeeping: `fp|sym|sch|pcb upgrade`.
  - **Jobsets:** `kicad-cli jobset run [--stop-on-error] [--file JOB.kicad_jobset] [--output <destination>] PROJECT.kicad_pro`.
- **IPC API.** Protobuf over NNG on a Unix socket. It needs a running KiCad instance and executes on the GUI thread [V](https://dev-docs.kicad.org/en/apis-and-binding/ipc-api/). The Python client `kicad-python` 0.8.0 (MIT) was released 2026-08-30 [L: `curl -s https://pypi.org/pypi/kicad-python/json`]. Consequence: headless CI must use `kicad-cli`, not IPC.

### 2. atopile

- **PyPI.** Latest is **0.15.9** (2026-09-12). It requires Python **>=3.14,<3.15**, and ships cp314 macOS arm64 wheels [L: `curl -s https://pypi.org/pypi/atopile/json`].
- **Dependencies.** They include `anthropic`, `openai`, `mcp[cli]`, `keyring`, `fastapi-github-oidc`, `kicadcliwrapper` and `atopile-easyeda2kicad` [L: same].
- **Provenance: public source does not match what is published.**
  - The PyPI Sigstore attestation for the 0.15.9 arm64 wheel names the build workflow `github.com/atopile/monopile/.github/workflows/deploy.yml@refs/tags/v0.15.9` [L: `curl https://pypi.org/integrity/atopile/0.15.9/<wheel>/provenance`].
  - `gh api repos/atopile/monopile` returns 404, so that repo is private or absent [L].
  - Public `atopile/atopile` `main` was last committed 2026-03-11. Its latest GitHub release is v0.12.5 (2026-01-20) and its latest tag v0.14.1004 [L: `gh api repos/atopile/atopile/...`].
  - The public README still says MIT [V](https://github.com/atopile/atopile).
- **Hosted pivot.**
  - atopile.io titles itself "atopile 0.16 — Design electronics with code" [L: `curl -s https://atopile.io/`].
  - `packages.atopile.io` now 301-redirects to `app.atopile.io`, which redirects to `start.atopile.io` (the hosted workspace) [L: `curl -sI`].
  - The docs front page points to the browser workspace [V](https://docs.atopile.io/).
  - A third-party project reports that 0.16+ is a hosted app and that the last open CLI (0.15.x) can no longer reach the registry or part-picker without an account [R](https://github.com/m9h/ato-heater-pid).
- **Telemetry.** The public source (March 2026) sends PostHog telemetry to `telemetry.atopileapi.com`. Opt-out is `ATO_DISABLE_TELEMETRY` or CI detection [V](https://github.com/atopile/atopile/blob/main/src/atopile/telemetry.py). The 0.15.9 dependency list has no `posthog`, so the behaviour of 0.15.9 is **[U]**.
- **KiCad output.** Builds update a `.kicad_pcb`, and KiCad is optional for building [V](https://github.com/atopile/atopile).
- **LCSC/JLC part-picking.** Reported to depend on the atopile backend [R](https://github.com/m9h/ato-heater-pid).

### 3. tscircuit

- **Versions.**
  - npm `tscircuit` 0.0.2646 (MIT, bins `tsci`/`tscircuit`, 45 MB unpacked, modified 2026-09-23).
  - `@tscircuit/cli` 0.1.2152 (modified 2026-09-24, 49 MB unpacked).
  - [L: `npm view tscircuit …`, `npm view @tscircuit/cli …`]
- **Repos.** `tscircuit/tscircuit` and `tscircuit/cli` are both MIT and have no GitHub Releases; versioning is npm-only [L: `gh api`].
- **Export.** `tsci export <file> -f <fmt>`. Formats include `circuit-json`, `schematic-svg`, `pcb-svg`, `gerbers`, `readable-netlist`, `specctra-dsn`, `glb`, `step`, `kicad_sch`, `kicad_pcb`, `kicad_zip`, `kicad-library` and `spice` [V](https://docs.tscircuit.com/command-line/tsci-export).
- **Build.** `tsci build [file] --kicad-project | --kicad-project-zip --svgs --glbs --routing-disabled --ci` [V](https://docs.tscircuit.com/command-line/tsci-build).
- **Network.** The CLI has `login`, `push`, `clone`, `registry` and `import` (JLCPCB or registry search) commands [V](https://github.com/tscircuit/cli). Whether plain `tsci build` makes network calls is **[U]**.
- **Telemetry.** On by default: PostHog at `us.i.posthog.com`. `TSCI_TELEMETRY_DISABLED=1` disables it [V](https://github.com/tscircuit/cli/blob/main/lib/telemetry/index.ts).

### 4. ngspice, SKiDL, PySpice, InSpice

- **ngspice 47** was released 2026-08-11 [V](https://ngspice.sourceforge.io/news.html). brew has formula `ngspice` 47 with an arm64_sequoia bottle and depends on `libngspice` [L: `brew info --json=v2 ngspice`].
- **Batch mode** [V](https://sourceforge.net/p/ngspice/ngspice/ci/master/tree/man/man1/ngspice.1):
  - `ngspice -b -n -r out.raw -o out.log circuit.cir`.
  - `-b` is batch mode, `-r` the rawfile, `-o` the log, `-n` skips `.spiceinit`.
  - `SPICE_ASCIIRAWFILE=1` gives an ASCII rawfile.
  - For parsing, prefer an ASCII rawfile or `wrdata` in a `.control` block. The manual describes `set filetype=ascii` [V](https://ngspice.sourceforge.io/docs/ngspice-html-manual/manual.xhtml).
- **Security.** The ngspice front-end registers a `shell` command ("Fork a shell, or execute the command") [V](https://sourceforge.net/p/ngspice/ngspice/ci/master/tree/src/frontend/commands.c). An untrusted netlist can therefore run host commands, so run ngspice sandboxed with `-n`.
- **SKiDL** 2.3.0: MIT, released 2026-07-28. README updated for KiCad 10 on 2026-08-10 [L: PyPI + `gh api repos/devbisme/skidl/commits`].
- **PySpice** 1.5 dates from 2021 and its last commit was 2024-01-26, so it is stale [L].
- **InSpice** 1.7.0.7 (2026-09-17, Python ≥3.12) [L]. PyPI licence is GPL-3.0-or-later, but GitHub (`Innovoltive/InSpice` now resolves to `insim-ai/InSpice`) reports **AGPL-3.0** [L: `gh api repos/Innovoltive/InSpice`].

### 5. KiCad MCP servers

| Server | Stars | Last commit | Licence | Transport | Read-only default? | Can write or execute | Open security items |
|---|---|---|---|---|---|---|---|
| **oaslananka/kicad-mcp-pro** 3.35.0 (tag `mcp-server-v3.35.0` = `f641a92596ab7adc1e134287578b1ae5ff9580ad`) | 102 | 2026-09-24 | MIT | stdio (default). Streamable HTTP is opt-in, bound to 127.0.0.1, optional bearer token plus Origin/CORS checks. Legacy SSE off | **Yes.** `default` and `review` profiles run in `readonly` mode with 24 tools. `build`+`write` exposes plan/apply/rollback. `release`+`manufacturing` gates the final package as HUMAN_ONLY. `expert` has 387 tools | Via `kicad-cli` (argv list, no shell), KiCad IPC (`kicad-python`), and file writes confined to the workspace. The expert catalog includes Freerouting autoroute, ngspice simulation and LCSC assignment | None published. #779 tracks Tauri/RustSec advisories (GUI app only) |
| mixelpixx/KiCAD-MCP-Server v2.8.1 | 2,441 | 2026-09-24 | MIT | stdio (Node + Python) | **No** | About 140 routed tools plus direct tools. SWIG `pcbnew`. The GUI driver clicks the KiCad UI with no allow-list and no confirmation. JLCPCB and DigiKey APIs. Freerouting via Java/Docker | #412 "GUI driver hardening follow-ups" is open |
| Seeed-Studio/kicad-mcp-server | 134 | 2026-09-09 | **none** | stdio (FastMCP) | No (analysis-focused) | S-expression editing, Gerber export, PartReel downloads (host-allowlisted) | No licence at all |
| lamaalrajih/kicad-mcp | 524 | 2025-10-17 | MIT | stdio | No | Opens KiCad, generates files | #57 path-validator bypass is open |
| mixelpixx/Konnect v0.12.1 | 768 | 2026-09-24 | **AGPL-3.0** (commercial licence available) | native KiCad 10 plugin, Rust, IPC API, 217 tools | Unknown | Full design and manufacturing | Not reviewed [U] |
| ProductOfAmerica/mcp-server-kicad v0.20.1 | 10 | 2026-08-15 | MIT | stdio (109 tools across 5 servers) | Unknown | Byte-preserving writes to `.kicad_sch`/`.kicad_pcb` | Not reviewed [U] |

Sources for the table:
- kicad-mcp-pro:
  - Profiles and tool lists [V](https://github.com/oaslananka/kicad-mcp-pro/blob/main/docs/agents/progressive-disclosure.md) and the generated snapshot [V](https://github.com/oaslananka/kicad-mcp-pro/blob/main/docs/evidence/progressive-disclosure-profile-snapshot.json).
  - Threat model [V](https://github.com/oaslananka/kicad-mcp-pro/blob/main/docs/security/threat-model.md).
  - README, including the note that telemetry is off by default and that JLCPCB is the default live sourcing [V](https://github.com/oaslananka/kicad-mcp-pro).
  - PyPI wheel sha256 `b2297186a61dfbf5fe57fce26a6b8d7fc5b0877514444a26d5b5786f50e017a0`. The attestation publisher is GitHub `oaslananka/kicad-mcp-pro`, workflow `publish-python.yml`. Classifiers list Python 3.13 and 3.14 [L: PyPI JSON + integrity API].
  - The default-profile tool list includes `lib_get_bom_with_pricing` and `dfm_run_manufacturer_check`. Treat the first as network-egressing [U: exact endpoint not traced].
- Other servers: mixelpixx [V](https://github.com/mixelpixx/KiCAD-MCP-Server) with the GUI-driver docstring in `python/commands/gui_driver.py`; Seeed [V](https://github.com/Seeed-Studio/kicad-mcp-server); lamaalrajih #57 [V](https://github.com/lamaalrajih/kicad-mcp/issues/57); MCP registry search for kicad [L: `curl 'https://registry.modelcontextprotocol.io/v0.1/servers?search=kicad&version=latest'`].

### 6. Commercial EDA (note only)

- **Quilter** (AI PCB layout).
  - Priced per project by unrouted pins, not per seat; you pay for approved designs; no annual licence [V](https://www.quilter.ai/pricing).
  - Exports native files for Altium, Allegro, Xpedition and KiCad.
  - Managed cloud is SOC 2 Type 2, and self-hosted is available [V](https://www.quilter.ai/pricing).
  - Free tier: academic, personal or eligible professional use (<10 people, <$50K revenue). On this tier, board metadata and/or input files are used to generate training "puzzles". Enterprise designs are never used for training [V](https://www.quilter.ai/free-ai-pcb-design).
- **Flux** (flux.ai): browser-based AI PCB design.
  - Plans: Explore (free), Build, Pro, Teams (per editor), Enterprise (custom, SOC 2) [V](https://www.flux.ai/p/pricing).
  - Around $20/editor/month entry with metered "ACU" AI usage [R](https://www.protoflow.ai/blog/flux-ai-pricing).
  - ToS: the user keeps ownership; Flux gets a licence to store, parse and display; content is deleted within 90 days of cancellation; California law. The ToS does not mention AI training [V](https://docs.flux.ai/legal/terms-of-service).
  - New projects are private by default [V](https://docs.flux.ai/faq/private-and-public-projects).
- Both require uploading design IP, so they are **not for use without owner approval**.

### 7. Embedded toolchains and simulators

- **ESP-IDF.**
  - Recent releases [L: `gh api repos/espressif/esp-idf/releases`]:
    - v6.1: 2026-08-27
    - v6.0: 2026-03-20; v6.0.3: 2026-09-02
    - v5.5: 2025-07-21; v5.5.5: 2026-07-17
    - v5.4: 2025-01-04; v5.4.4: 2026-04-17
    - v5.3.6: 2026-09-15
    - v5.2.8: 2026-09-11
  - Support policy: 30 months per minor release, split into a 12-month service period and an 18-month maintenance period (critical and security fixes only). New projects should start on an in-service release [V](https://github.com/espressif/esp-idf/blob/master/SUPPORT_POLICY.md).
  - Derived from that policy [U, derived]: v6.1 and v6.0 are in service; v5.5 and v5.4 are in maintenance; v5.3 and v5.2 are near end of life.
  - Installer: EIM (ESP-IDF Installation Manager) v0.19.0, 2026-09-01, Apache-2.0, with a Homebrew tap `espressif/homebrew-eim` [L: `gh api`].
- **Zephyr.**
  - Latest stable **4.4.x**: 4.4.0 on 2026-04-14, EOL 2027-04-12. Patch v4.4.2 on 2026-08-07.
  - 4.3 reaches EOL 2026-10-15.
  - **Current LTS is 3.7 (LTS3)**, EOL 2029-07-27; latest patch v3.7.2, with v3.7.3-rc1 on 2026-08-06.
  - Next release is 4.5 in October 2026. **LTS4 = 4.6 in April 2027** [V](https://github.com/zephyrproject-rtos/zephyr/blob/main/doc/releases/index.rst) [L: `gh api …/releases`].
- **Zephyr SDK 1.0.1** (2026-03-25), macOS-aarch64 assets [L: `gh api repos/zephyrproject-rtos/sdk-ng/releases/tags/v1.0.1`]:
  - `minimal` 88 MB
  - `arm-zephyr-eabi` 90 MB
  - `hosttools` 85 MB
  - full GNU bundle 1.81 GB
  - LLVM 375 MB
  - All sizes are compressed.
- **PlatformIO Core.**
  - 6.2.0 (2026-09-05), Apache-2.0; brew formula 6.2.0 [L].
  - `enable_telemetry` defaults to **Yes**; turn it off with `pio settings set enable_telemetry No`. The update check runs every 7 days [V](https://docs.platformio.org/en/latest/core/userguide/cmd_settings.html).
  - platform-espressif32 is at v7.1.3 (2026-09-11) [L].
- **Renode** 1.17.0 (2026-09-07). Assets include `renode-1.17.0.osx-arm64-portable.dmg` at 75.7 MB. LICENSE is MIT with a note on third-party components. There is no brew formula [L: `gh api …/releases/tags/v1.17.0`, `brew info renode` → not found].
- **QEMU** 11.1.1: brew formula 11.1.1 (GPL-2.0-only, arm64_sequoia bottle). The upstream tarball is dated 2026-08-27 [L: `brew info`, `curl -sI https://download.qemu.org/qemu-11.1.1.tar.xz`]. ESP-IDF v6.1 also offers on-request `qemu-xtensa` and `qemu-riscv32` forks [L: tools.json].
- **Wokwi.**
  - `wokwi-cli` v0.27.1 (2026-09-16) is MIT. There is a macOS arm64 binary of about 58 MB [L]. The documented install is `curl -L https://wokwi.com/ci/install.sh | sh`. It needs `WOKWI_CLI_TOKEN`. It has an **experimental `wokwi-cli mcp`** server [V](https://github.com/wokwi/wokwi-cli).
  - Wokwi CI uploads the firmware binary to Wokwi's cloud, which simulates it and says it deletes the firmware afterwards [V](https://docs.wokwi.com/wokwi-ci/getting-started).
  - Monthly CI minutes per the docs: Free 50, Hobby/Hobby+ 200, Pro 2,000. The pricing page lists Pro at €20/seat/month with 2,000 minutes and does not list CI minutes for Hobby [V](https://wokwi.com/pricing) (a discrepancy).
  - The free plan has public projects only [V](https://wokwi.com/pricing).

### 8. HIL for agents

- **Agentic HIL exists**: `agentic-hil/agentic-hil`.
  - v0.21.5 (2026-09-07; tag commit `ae9cdd7a594dd486bd4f2c1405ca55a9123ded71`), Apache-2.0, 15 stars, repo created 2026-06-23 [L: `gh api`].
  - PyPI wheel sha256 `f8f04cd8606dab4f0abb6790ff4b28c9fce5c3482e66dd46afc9e79b0b94377e`, trusted-published from `workflow.yml` [L: PyPI integrity API].
  - Listed in the MCP registry as `io.github.agentic-hil/agentic-hil` [L].
- **What it does** [V](https://github.com/agentic-hil/agentic-hil):
  - Bounded MCP tools over **stdio only**: probe, flash, reset, UART/CAN stimulus and read, debug sessions, reports and logs.
  - One authoritative config per project, stored **outside the repo** and out of reach of the agent's file tools.
  - `allow_raw_debugger_commands` and `allow_mass_erase` default to false and are interlocked: flashing is refused while either is true.
  - Over MCP an agent can narrow its authority but never widen it; `agentic-hil grant|revoke` runs from the operator shell.
  - Actions are leased machine-wide and written to a SHA-256 audit chain.
  - Backends: OpenOCD, pyOCD and STM32CubeProgrammer, on macOS, Linux and Windows.
- **Caveats** [V](https://github.com/agentic-hil/agentic-hil/blob/master/docs/installation.md):
  - The one-line installer registers the MCP server and skill for **every** agent CLI on PATH and edits the shell profile. Use `--no-path`, `--no-agent-install` and `--version` instead.
  - CI covers Python 3.10–3.13; 3.14 is untested.
  - No esptool backend was found (ESP32 only via OpenOCD) [U].
  - The MCP tools include `project_config_create`, `project_config_set`, `project_config_adopt_hardware` and `server_upgrade` [V](https://github.com/agentic-hil/agentic-hil/blob/master/docs/mcp-tools.md). Forge should deny these in its permission profile so bench config stays operator-only.
- **Other HIL-for-agents projects** (all small or new; none reviewed in depth) [L: registry search + `gh api`]:
  - `es617/dbgprobe-mcp-server` (MIT, 10 stars, last push 2026-03)
  - `microhenrio/openocd-mcp` (MIT, 4 stars)
  - `powerdragonfire/platformio.mcp` (MIT, 3 stars, created 2026-09-16)
  - `embeddedci-com/embeddedci-python` (Apache-2.0, 0 stars; drives a "BenchPod" bench)
  - Wokwi's experimental MCP

### 9. Software side

- **gstack.**
  - Upstream VERSION is **1.89.0.0** (commit `06ed920a…`, 2026-09-24) [L: `gh api repos/garrytan/gstack/contents/VERSION`]. The local install is **1.58.5.0** (commit `11de390b…`, 2026-06-25) [L: `cat ~/.claude/skills/gstack/VERSION; git log -1`]. `~/.gstack/last-update-check` records "UPGRADE_AVAILABLE 1.58.5.0 1.87.0.0" [L].
  - Licence is MIT [L: LICENSE].
  - Install is `git clone --depth 1 … && ./setup` [L: README]. `setup` runs `bun install`, downloads Playwright Chromium (`bunx playwright install chromium`), and can add plan-tune hooks to `~/.claude/settings.json` after a prompt that defaults to No [L: `grep setup`].
  - Telemetry is opt-in (skill name, duration, OS, version) to Supabase [L: README]. The local config says `telemetry=off` and `auto_upgrade=false` [L: `gstack-config get`].
  - The update check curls `raw.githubusercontent.com/garrytan/gstack/main/VERSION` and only POSTs to Supabase if telemetry is on [L: `bin/gstack-update-check`].
  - Local footprint: skill dir 1.1 GiB (727 MiB of it `node_modules`); Playwright cache 2.6 GiB, possibly shared [L: `du -sh`].
  - Open issues include #1081 (undisclosed hourly GitHub call in skill preambles), #1080 (consent wording) and #1150 (session tracking not gated by the telemetry config) [V](https://github.com/garrytan/gstack/issues).
- **Official marketplace** (`anthropics/claude-plugins-official`): 313 plugins, HEAD `8286e2db…` (2026-09-24). The local clone was last updated 2026-09-13 with 295 plugins [L: `gh api …/marketplace.json`; `~/.claude/plugins/known_marketplaces.json`]. No KiCad or EDA plugins; the only hardware-related one is `cwc-makers` (Cardputer onboarding) [L]. Plugins relevant to Forge:
  - `code-review`: multi-agent PR review with confidence scoring [V](https://github.com/anthropics/claude-plugins-official).
  - `pr-review-toolkit`: specialised review agents.
  - `security-guidance` [V](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/security-guidance):
    - Upstream 2.0.8; 2.0.8 installed at user scope.
    - Three layers: regex warnings on Edit/Write, an LLM diff review on every Stop (default model `claude-opus-4-7`), and an agentic review on commit.
    - Env switches: `ENABLE_STOP_REVIEW=0` and others.
  - **"Claude Security" = `claude-security`** 0.11.0 (installed). Proprietary Anthropic licence; a multi-agent scan and patch workflow [L: LICENSE via `gh api`].
  - `frontend-design`: a skill.
  - `plugin-dev`: 7 skills plus agents and commands for building plugins.
  - `skill-creator`: create, eval and benchmark skills.
  - `hookify`: hook rules from markdown.
  - `clangd-lsp`, `pyright-lsp`: code intelligence for firmware C and Python.
  - `context7`: Upstash, hosted HTTP MCP.
- **Context7.**
  - `@upstash/context7-mcp` 4.1.1 is MIT [L: `npm view`].
  - The README says the API backend, parser and crawler are **private** [V](https://github.com/upstash/context7). The tools `resolve-library-id` and `query-docs` both send a required `query` containing the user's question or task [V](https://github.com/upstash/context7).
  - The local package calls `https://context7.com/api` (overridable with `CONTEXT7_API_URL`), and OTEL telemetry is disabled only by `OTEL_SDK_DISABLED=true` [V](https://github.com/upstash/context7/blob/master/packages/mcp/src/lib/constants.ts).
  - The marketplace plugin points at `https://mcp.context7.com/mcp?client=claude-code-plugin` [L: `.mcp.json` via `gh api`].
- **Official MCP registry.**
  - Status is **preview**. API **v0.1 frozen** since 2025-10-24; GA is still pending [V](https://github.com/modelcontextprotocol/registry). The registry server software is at v1.8.1 (2026-08-06) [L].
  - Query: `GET https://registry.modelcontextprotocol.io/v0.1/servers?search=<substr>&version=latest&limit=N` returns `server.json` entries (name, version, repository, packages with registryType/identifier/version/transport, remotes) plus `_meta.…official.{status,publishedAt,isLatest}`. Paginate with `cursor` [L: curl]. Live docs are at `/docs`.
  - Publishing requires namespace auth (GitHub OAuth/OIDC, DNS or HTTP), which proves namespace ownership only, not safety [V](https://github.com/modelcontextprotocol/registry).

### 10. Already installed locally [L]

- `claude plugin list`:
  - `claude-security@claude-plugins-official` 0.11.0 (user, enabled)
  - `security-guidance` 2.0.8 (user, enabled), plus three 2.0.7 project-scope entries for `~/Glowtech-Final*`
  - `supabase` 0.1.14 (project, disabled)
- `claude mcp list`: only `stitch` (`https://stitch.googleapis.com/mcp`, HTTP, connected).
- `~/.claude/plugins/known_marketplaces.json`: only `claude-plugins-official` (github `anthropics/claude-plugins-official`, updated 2026-09-13).
- `~/.claude/settings.json`: `defaultMode: "auto"`, `skipDangerousModePermissionPrompt: true`, no hooks. These are permissive defaults that Forge's least-privilege profile should override at project scope.
- gstack is present at `~/.claude/skills/gstack`.
- Not from a command: the session environment also exposed claude.ai-managed plugin connectors (engineering/data/design/marketing/productivity: github, slack, notion and others). They do not appear in `installed_plugins.json` [L: session notice only].

### 11. Disk-footprint estimate (machine has ~45 GiB free)

| Item | Measured download | Installed estimate |
|---|---|---|
| KiCad 10.0.6 (with libraries and 3D models) | 1.31 GiB DMG [L] | 5–8 GiB [U] |
| ESP-IDF v6.1, one target family (repo + submodules + tools + venv) | 689 MB of "always" tool archives for macOS arm64 [L: tools.json v6.1]; repo pack 458 MB [L] | 3.5–5 GiB [U] |
| Zephyr workspace (west, all modules) + SDK ARM-only | SDK minimal+arm+hosttools ≈ 263 MB compressed [L]; zephyr repo pack 965 MB [L] | 1 GiB SDK + 4–6 GiB workspace; less with a west project filter [U] |
| Zephyr SDK full GNU bundle | 1.81 GB compressed [L] | 6–8 GiB [U] (avoid) |
| PlatformIO + one platform (e.g. espressif32 with IDF framework) | n/a | 2–4 GiB [U] |
| Renode 1.17.0 | 75.7 MB [L] | ~0.3 GiB [U] |
| QEMU 11.1.1 (brew with dependencies) | tarball 142 MB [L] | 0.5–1 GiB [U] |
| ngspice 47 (brew) | n/a | <0.1 GiB [U] |
| gstack (already present) | n/a | 1.1 GiB + 2.6 GiB Playwright cache [L] |

A full stack of about 20–28 GiB is feasible but leaves little headroom for build artefacts and Docker images. **Install one embedded path at a time.**

---

## Implications for Forge

1. **KiCad.** Install **KiCad 10.0.6** via `brew install --cask kicad` and verify the cask sha256 `ef4dcd42…dc68`. Make **`kicad-cli` the primary, MCP-free interface** for ERC, DRC, fabrication, BOM, netlist, STEP and jobsets. Wrap it in Forge-owned scripts that:
   - call it with argv lists;
   - always pass `--format json --exit-code-violations`;
   - never pass `--save-board` in review mode;
   - write only inside the project workspace.
   KiCad jobsets (`.kicad_jobset`) are a good fit for reproducible release packages.
2. **Code-first capture.** Default to **tscircuit**: pin `tscircuit@0.0.2646` and `@tscircuit/cli@0.1.2152` with lockfile integrity hashes, set `TSCI_TELEMETRY_DISABLED=1`, and never run `tsci login`, `push` or `import` without approval. Keep **SKiDL 2.3.0** as a pure-Python fallback. **Defer atopile**: its published 0.15.9 wheels are built from a private repo, the product is moving to a hosted 0.16, and registry/part-picking reportedly needs an account. If the owner still wants it, pin `atopile==0.15.9` with the arm64 wheel hash from PyPI, set `ATO_DISABLE_TELEMETRY=1`, and vendor all packages and parts offline.
3. **Simulation.** Install **ngspice 47** (`brew install ngspice`) and always run it as `ngspice -b -n -r <raw> -o <log>` with `SPICE_ASCIIRAWFILE=1`, inside a network-less sandbox, because the `shell` control command can execute code. Avoid PySpice (stale). Defer InSpice until the GPL/AGPL mismatch is resolved.
4. **KiCad MCP.** **Optional** `kicad-mcp-pro==3.35.0`:
   - Pin the wheel with `--require-hashes` sha256 `b2297186a61dfbf5fe57fce26a6b8d7fc5b0877514444a26d5b5786f50e017a0`; source tag `mcp-server-v3.35.0` = commit `f641a92596ab7adc1e134287578b1ae5ff9580ad`.
   - Run over stdio only, with `KICAD_MCP_PROFILE=review`, `KICAD_MCP_OPERATING_MODE=readonly`, `KICAD_MCP_WORKSPACE_ROOT=<project>`, and telemetry unset.
   - Block network egress or deny `lib_get_bom_with_pricing`.
   - Treat `build`/`write` as a separately approved profile, and never use `expert`/`full`.
   - Re-vet on every bump: the project is 4 months old, has one main maintainer and releases about daily.
   - **Avoid** mixelpixx (no read-only mode, ungated GUI clicks), Seeed (no licence), lamaalrajih (stale, open traversal bug). Defer Konnect (AGPL).
5. **Embedded, phase order.**
   - **(a) Renode 1.17.0** (portable DMG; pin the file SHA-256 at download) for simulation-first CI.
   - **(b) Zephyr 4.4.x**, or **3.7 LTS** for long-lived products, with **SDK 1.0.1 minimal + `arm-zephyr-eabi` only**, pinned via a `west.yml` manifest with explicit revisions and a project filter.
   - **(c) ESP-IDF v6.1** (in service) through EIM, installing only the needed target's tools. v5.5.x only if a dependency requires it.
   - PlatformIO 6.2.0 is optional. If used, run `pio settings set enable_telemetry No` and pin `platform = espressif32@7.1.3`-style exact versions.
   - QEMU 11.1.1 is optional.
6. **Wokwi.** Owner approval is required: it uploads firmware to a cloud service, has paid tiers, and its MCP is experimental. Use the pinned release binary, never `curl | sh`.
7. **HIL.** Adopt **agentic-hil 0.21.5** for the HIL phase:
   - `uv tool install --python 3.13 agentic-hil==0.21.5` with the hash above, `--no-path` and no auto agent-install. Register the MCP server manually at project scope.
   - The operator creates the bench config outside the workspace.
   - Add Claude Code permission `deny` rules for `project_config_create`, `project_config_set`, `project_config_adopt_hardware` and `server_upgrade`.
   - Keep `allow_raw_debugger_commands` and `allow_mass_erase` false.
8. **Software side.**
   - **gstack:** keep 1.58.5.0 pinned to its commit for now, with telemetry off and auto-upgrade off. Review the 1.58 → 1.89 changelog before upgrading. Don't let `setup` add hooks.
   - **Keep** `claude-security` 0.11.0 and `security-guidance` 2.0.8. For multi-agent worktrees set `ENABLE_STOP_REVIEW=0`, as its README advises.
   - **Add** `plugin-dev` and `skill-creator` (to build Forge itself) and `code-review`. Optional: `pr-review-toolkit`, `clangd-lsp`, `pyright-lsp`, `hookify`.
   - Record the marketplace commit (`8286e2db…`) in Forge's lockfile.
   - **Context7:** defer or make it optional. It is hosted, its backend is private, and every query leaves the machine. Never enable it on confidential projects.
9. **MCP registry.** Use it as a **metadata index only**. Forge's vetting script should fetch `v0.1/servers?search=…&version=latest`, compare its `packages[].identifier/version` against PyPI/npm provenance, and record hashes. Registry presence is not a trust signal.
10. **Local hardening.** The user settings have `defaultMode: auto` and `skipDangerousModePermissionPrompt: true`. Forge's project `.claude/settings.json` should set explicit allow and deny lists for its tools rather than rely on these.

---

## Not found / discrepancies

- **atopile:**
  - PyPI 0.15.9 (built from private `atopile/monopile`) does not match public GitHub (`main` last commit 2026-03-11; latest Release v0.12.5).
  - The "hosted 0.16, account required" claim comes only from a third-party README [R]. atopile.io confirms "0.16", but pricing and terms were not readable (JS-rendered site) [U].
  - Whether 0.15.9 has telemetry is [U].
- **InSpice** licence: PyPI says GPL-3.0-or-later, GitHub says AGPL-3.0. The repo moved from `Innovoltive` to `insim-ai`.
- **Seeed-Studio/kicad-mcp-server** has no LICENSE file (GitHub `license: null`).
- **Wokwi** Hobby CI minutes: the docs say 200 per month; the pricing page lists none.
- **Zephyr LTS4:** a WebFetch summary claimed "5.0 in Oct 2027". The primary `index.rst` says **LTS4 = 4.6 (April 2027)**; 5.0 (October 2027) is the start of the 5.x cycle.
- **Flux AI-training claim:** a search result that said inputs are never used for training came from `flux-ai.ai`, an unrelated image-generator company. The flux.ai ToS is silent on training.
- **ngspice licence:** brew reports `LicenseRef-Homebrew-cannot-represent`; the exact licence mix was not verified [U].
- **gstack, tscircuit and tscircuit/cli** publish no GitHub Releases (VERSION file or npm only). **kicad-mcp-pro** registry entries for 3.10–3.17 point to an older repo URL, `oaslananka/kicad-mcp`.
- Installed-size figures for KiCad, ESP-IDF, the Zephyr workspace and PlatformIO are estimates [U]. The web search budget ran out before official size figures could be found.
- The name "Claude Security plugin" resolves to `claude-security` in the official marketplace. "Agentic HIL" resolves to `agentic-hil/agentic-hil`. Both were found.
- Not reviewed: Konnect, ProductOfAmerica/mcp-server-kicad, bunnyf/pcb-mcp, unmateria/MCP-Kicad, and whether tscircuit's autorouter or `tsci build` makes network calls [U].

## Sources

| # | Title | URL | Type | Accessed |
|---|---|---|---|---|
| 1 | KiCad 10.0.6 Release | https://www.kicad.org/blog/2026/08/KiCad-10.0.6-Release/ | official | 2026-09-25 |
| 2 | Version 10.0.0 Released | https://www.kicad.org/blog/2026/03/Version-10.0.0-Released/ | official | 2026-09-25 |
| 3 | KiCad macOS download | https://www.kicad.org/download/macos/ | official | 2026-09-25 |
| 4 | KiCad 10 CLI reference | https://docs.kicad.org/10.0/en/cli/cli.html | official docs | 2026-09-25 |
| 5 | KiCad IPC API dev docs | https://dev-docs.kicad.org/en/apis-and-binding/ipc-api/ | official docs | 2026-09-25 |
| 6 | KiCad release assets 10.0.6 | https://github.com/KiCad/kicad-source-mirror/releases/tag/10.0.6 | official (gh api) | 2026-09-25 |
| 7 | atopile README | https://github.com/atopile/atopile | primary repo | 2026-09-25 |
| 8 | atopile PyPI + provenance | https://pypi.org/project/atopile/ | registry | 2026-09-25 |
| 9 | atopile telemetry.py | https://github.com/atopile/atopile/blob/main/src/atopile/telemetry.py | source | 2026-09-25 |
| 10 | atopile docs | https://docs.atopile.io/ | official docs | 2026-09-25 |
| 11 | m9h/ato-heater-pid README | https://github.com/m9h/ato-heater-pid | secondary | 2026-09-25 |
| 12 | tsci export docs | https://docs.tscircuit.com/command-line/tsci-export | official docs | 2026-09-25 |
| 13 | tsci build docs | https://docs.tscircuit.com/command-line/tsci-build | official docs | 2026-09-25 |
| 14 | tscircuit CLI README / telemetry | https://github.com/tscircuit/cli | source | 2026-09-25 |
| 15 | ngspice news | https://ngspice.sourceforge.io/news.html | official | 2026-09-25 |
| 16 | ngspice man page | https://sourceforge.net/p/ngspice/ngspice/ci/master/tree/man/man1/ngspice.1 | source | 2026-09-25 |
| 17 | ngspice commands.c (shell) | https://sourceforge.net/p/ngspice/ngspice/ci/master/tree/src/frontend/commands.c | source | 2026-09-25 |
| 18 | kicad-mcp-pro README | https://github.com/oaslananka/kicad-mcp-pro | primary repo | 2026-09-25 |
| 19 | kicad-mcp-pro profiles | https://github.com/oaslananka/kicad-mcp-pro/blob/main/docs/agents/progressive-disclosure.md | primary docs | 2026-09-25 |
| 20 | kicad-mcp-pro threat model | https://github.com/oaslananka/kicad-mcp-pro/blob/main/docs/security/threat-model.md | primary docs | 2026-09-25 |
| 21 | mixelpixx KiCAD-MCP-Server | https://github.com/mixelpixx/KiCAD-MCP-Server | primary repo | 2026-09-25 |
| 22 | Seeed kicad-mcp-server | https://github.com/Seeed-Studio/kicad-mcp-server | primary repo | 2026-09-25 |
| 23 | lamaalrajih kicad-mcp issue #57 | https://github.com/lamaalrajih/kicad-mcp/issues/57 | primary repo | 2026-09-25 |
| 24 | Quilter pricing | https://www.quilter.ai/pricing | vendor | 2026-09-25 |
| 25 | Quilter free tier | https://www.quilter.ai/free-ai-pcb-design | vendor | 2026-09-25 |
| 26 | Flux pricing | https://www.flux.ai/p/pricing | vendor | 2026-09-25 |
| 27 | Flux Terms of Service | https://docs.flux.ai/legal/terms-of-service | vendor | 2026-09-25 |
| 28 | ProtoFlow on Flux pricing | https://www.protoflow.ai/blog/flux-ai-pricing | secondary | 2026-09-25 |
| 29 | ESP-IDF support policy | https://github.com/espressif/esp-idf/blob/master/SUPPORT_POLICY.md | official | 2026-09-25 |
| 30 | ESP-IDF releases | https://github.com/espressif/esp-idf/releases | official (gh api) | 2026-09-25 |
| 31 | Zephyr releases index.rst | https://github.com/zephyrproject-rtos/zephyr/blob/main/doc/releases/index.rst | official | 2026-09-25 |
| 32 | Zephyr SDK 1.0.1 | https://github.com/zephyrproject-rtos/sdk-ng/releases/tag/v1.0.1 | official (gh api) | 2026-09-25 |
| 33 | PlatformIO settings | https://docs.platformio.org/en/latest/core/userguide/cmd_settings.html | official docs | 2026-09-25 |
| 34 | Renode 1.17.0 | https://github.com/renode/renode/releases/tag/v1.17.0 | official (gh api) | 2026-09-25 |
| 35 | QEMU downloads | https://download.qemu.org/ | official | 2026-09-25 |
| 36 | wokwi-cli README | https://github.com/wokwi/wokwi-cli | primary repo | 2026-09-25 |
| 37 | Wokwi CI getting started | https://docs.wokwi.com/wokwi-ci/getting-started | official docs | 2026-09-25 |
| 38 | Wokwi pricing | https://wokwi.com/pricing | vendor | 2026-09-25 |
| 39 | agentic-hil README | https://github.com/agentic-hil/agentic-hil | primary repo | 2026-09-25 |
| 40 | agentic-hil MCP tools | https://github.com/agentic-hil/agentic-hil/blob/master/docs/mcp-tools.md | primary docs | 2026-09-25 |
| 41 | agentic-hil installation | https://github.com/agentic-hil/agentic-hil/blob/master/docs/installation.md | primary docs | 2026-09-25 |
| 42 | gstack repo / issues | https://github.com/garrytan/gstack | primary repo | 2026-09-25 |
| 43 | claude-plugins-official marketplace | https://github.com/anthropics/claude-plugins-official | official | 2026-09-25 |
| 44 | security-guidance README | https://github.com/anthropics/claude-plugins-official/tree/main/plugins/security-guidance | official | 2026-09-25 |
| 45 | Context7 README / constants.ts | https://github.com/upstash/context7 | primary repo | 2026-09-25 |
| 46 | MCP registry README | https://github.com/modelcontextprotocol/registry | official | 2026-09-25 |
| 47 | MCP registry API | https://registry.modelcontextprotocol.io/v0.1/servers | official API | 2026-09-25 |
| 48 | kicad-python PyPI | https://pypi.org/project/kicad-python/ | registry | 2026-09-25 |
| 49 | SKiDL repo | https://github.com/devbisme/skidl | primary repo | 2026-09-25 |
| 50 | InSpice PyPI | https://pypi.org/project/InSpice/ | registry | 2026-09-25 |
