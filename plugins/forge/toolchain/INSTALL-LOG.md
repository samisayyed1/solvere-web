# Forge toolchain install log
free disk: 43 GiB

### core (2026-09-24T20:35:18Z)
`uv python install 3.12 3.13`
    Downloading cpython-3.13.13-macos-aarch64-none (download) (23.9MiB)
     Downloaded cpython-3.13.13-macos-aarch64-none (download)
    Installed 2 versions in 1.44s
     + cpython-3.12.13-macos-aarch64-none (python3.12)
     + cpython-3.13.13-macos-aarch64-none (python3.13)
`brew install pixi`
    ✔︎ Bottle Manifest pixi (0.81.0)
    ==> Would install 1 formula:
    pixi 0.81.0
    ==> Fetching downloads for: pixi
    ✔︎ Bottle pixi (0.81.0)
    ==> Pouring pixi--0.81.0.arm64_sequoia.bottle.1.tar.gz
    🍺  /opt/homebrew/Cellar/pixi/0.81.0: 12 files, 130.4MB
    ==> `brew cleanup` has not been run in the last 30 days, running now...
    Disable this behaviour by setting `HOMEBREW_NO_INSTALL_CLEANUP=1`.
    Hide these hints with `HOMEBREW_NO_ENV_HINTS=1` (see `man brew`).
    Removing: /Users/samisayyed/Library/Caches/Homebrew/bootsnap/cbcc7a28608961f53179008c4df6fbdd0012109a271c795809dd4641a0f4d195... (1,062 files, 9.7MB)
    Removing: /Users/samisayyed/Library/Caches/Homebrew/bootsnap/e298d09ce383e614c780fa9d8c85003a8a8837c3aa47aca90a8be1de5482c665... (1,070 files, 9.8MB)
    ==> Caveats
    zsh completions have been installed to:
      /opt/homebrew/share/zsh/site-functions
`npm install --prefix /Users/samisayyed/.forge/envs/node --ignore-scripts --no-audit --no-fund`
    npm warn Could not resolve dependency:
    npm warn peer @tscircuit/alphabet@"^0.0.24" from jscad-electronics@0.0.178
    npm warn node_modules/circuit-json-to-gltf/node_modules/jscad-electronics
    npm warn   jscad-electronics@"^0.0.178" from circuit-json-to-gltf@0.0.133
    npm warn   node_modules/circuit-json-to-gltf
    npm warn
    npm warn Conflicting peer dependency: @tscircuit/alphabet@0.0.24
    npm warn node_modules/@tscircuit/alphabet
    npm warn   peer @tscircuit/alphabet@"^0.0.24" from jscad-electronics@0.0.178
    npm warn   node_modules/circuit-json-to-gltf/node_modules/jscad-electronics
    npm warn     jscad-electronics@"^0.0.178" from circuit-json-to-gltf@0.0.133
    npm warn     node_modules/circuit-json-to-gltf
    npm warn deprecated prebuild-install@7.1.3: No longer maintained. Please contact the author of the relevant native addon; alternatives are available.
    
    added 303 packages in 32s
`npm ci --prefix /Users/samisayyed/.forge/envs/node --ignore-scripts --no-audit --no-fund`
    npm warn Could not resolve dependency:
    npm warn peer circuit-json@"^0.0.426" from jscad-electronics@0.0.178
    npm warn node_modules/circuit-json-to-gltf/node_modules/jscad-electronics
    npm warn   jscad-electronics@"^0.0.178" from circuit-json-to-gltf@0.0.133
    npm warn   node_modules/circuit-json-to-gltf
    npm warn
    npm warn Conflicting peer dependency: circuit-json@0.0.426
    npm warn node_modules/circuit-json
    npm warn   peer circuit-json@"^0.0.426" from jscad-electronics@0.0.178
    npm warn   node_modules/circuit-json-to-gltf/node_modules/jscad-electronics
    npm warn     jscad-electronics@"^0.0.178" from circuit-json-to-gltf@0.0.133
    npm warn     node_modules/circuit-json-to-gltf
    npm warn deprecated prebuild-install@7.1.3: No longer maintained. Please contact the author of the relevant native addon; alternatives are available.
    
    added 303 packages in 6s
linked /Users/samisayyed/.forge/bin/srt -> /Users/samisayyed/.forge/envs/node/node_modules/.bin/srt
wrote /Users/samisayyed/.forge/bin/tsci (telemetry disabled)

### mech (2026-09-24T20:36:26Z)
`uv lock --project <repo>/plugins/forge/toolchain/python/cad --python 3.12`
    Using CPython 3.12.13
    Resolved 95 packages in 1.90s
`uv sync --project <repo>/plugins/forge/toolchain/python/cad --locked --python 3.12`
     + skidl==2.3.0
     + stack-data==0.6.3
     + svgelements==1.9.6
     + svgpathtools==1.8.0
     + svgwrite==1.4.3
     + sympy==1.14.0
     + threadpoolctl==3.7.0
     + traitlets==5.16.1
     + trianglesolver==1.2
     + trimesh==5.1.0
     + typing-extensions==4.16.0
     + urllib3==2.8.0
     + vtk==9.7.0
     + wcwidth==0.9.1
     + webcolors==24.8.0
linked /Users/samisayyed/.forge/bin/forge-python -> /Users/samisayyed/.forge/envs/cad/bin/python
`/Users/samisayyed/.forge/envs/cad/bin/python <repo>/plugins/forge/toolchain/smoke/smoke_cad.py`
    Matplotlib is building the font cache; this may take a moment.
    volume=964.6571 mm3 expected=964.6571 mm3 rel_err=2.36e-16 step=19090 B png=12891 B out=/var/folders/_3/_mn031bx0r93tnmtx1w8jn0r0000gn/T/forge-smoke-cad-19hh19p7 -> PASS
`uv lock --project <repo>/plugins/forge/toolchain/python/build123d-mcp --python 3.12`
    Using CPython 3.12.13
    Resolved 94 packages in 3.07s
`uv sync --project <repo>/plugins/forge/toolchain/python/build123d-mcp --locked --python 3.12`
     + svgpathtools==1.8.0
     + svgwrite==1.4.3
     + sympy==1.14.0
     + threadpoolctl==3.7.0
     + traitlets==5.16.1
     + trianglesolver==1.2
     + trimesh==5.1.0
     + truststore==0.10.4
     + typing-extensions==4.16.0
     + typing-inspection==0.4.4
     + urllib3==2.8.0
     + uvicorn==0.53.0
     + vtk==9.7.0
     + wcwidth==0.9.1
     + webcolors==24.8.0
linked /Users/samisayyed/.forge/bin/build123d-mcp -> /Users/samisayyed/.forge/envs/build123d-mcp/bin/build123d-mcp
`brew install --cask freecad`
    Trust other specific casks and commands with:
      brew trust --cask <user>/<tap>/<cask>
      brew trust --command <user>/<tap>/<command>
    Whole-tap trust is broader and includes all current and future formulae,
    casks and commands from the listed taps. Trust whole taps with:
      brew trust stripe/stripe-cli supabase/tap
    Untap them with:
      brew untap stripe/stripe-cli supabase/tap
    For more information, see:
      https://docs.brew.sh/Tap-Trust
    ==> Fetching downloads for: freecad
    ✔︎ Cask freecad (1.1.3)
    ==> Installing Cask freecad
    ==> Moving App 'FreeCAD.app' to '/Applications/FreeCAD.app'
    🍺  freecad was successfully installed!
linked /Users/samisayyed/.forge/bin/freecadcmd -> /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd

### elec (2026-09-24T20:46:26Z)
`brew install --cask kicad`
    Whole-tap trust is broader and includes all current and future formulae,
    casks and commands from the listed taps. Trust whole taps with:
      brew trust stripe/stripe-cli supabase/tap
    Untap them with:
      brew untap stripe/stripe-cli supabase/tap
    For more information, see:
      https://docs.brew.sh/Tap-Trust
    ==> Fetching downloads for: kicad
    ✔︎ Cask kicad (10.0.6)
    ==> Installing Cask kicad
    ==> Moving Generic Artifact 'demos' to '/Library/Application Support/kicad/demos'
    Error: kicad: Failure while executing; `/usr/bin/sudo -E -- mkdir -p -- /Library/Application\ Support/kicad` exited with 1. Here's the output:
    sudo: a terminal is required to read the password; either use the -S option to read from standard input or configure an askpass helper
    sudo: a password is required
    ==> Purging files for version 10.0.6 of Cask kicad
free disk: 36 GiB

### elec (2026-09-24T20:49:53Z)
sha256 ok: 3c4db6ed80c33884c2fc3d99c5872e7f153630682f54c32ee18571cafc346cb0--kicad-unified-universal-10.0.6.dmg
`hdiutil attach -nobrowse -readonly -mountpoint /var/folders/_3/_mn031bx0r93tnmtx1w8jn0r0000gn/T/tmp.lsMLXibeD1 /Users/samisayyed/Library/Caches/Homebrew/downloads/3c4db6ed80c33884c2fc3d99c5872e7f153630682f54c32ee18571cafc346cb0--kicad-unified-universal-10.0.6.dmg`
    expected   CRC32 $1373EA94
    /dev/disk6          	GUID_partition_scheme          	
    /dev/disk6s1        	EFI                            	
    /dev/disk6s2        	Apple_HFS                      	/private/var/folders/_3/_mn031bx0r93tnmtx1w8jn0r0000gn/T/tmp.lsMLXibeD1
KiCad 10.0.6 installed to /Applications/KiCad (demos: /Users/samisayyed/.forge/opt/kicad-demos)
linked /Users/samisayyed/.forge/bin/kicad-cli -> /Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli
`brew install ngspice`
    ==> Pouring libxmu--1.3.1.arm64_sequoia.bottle.tar.gz
    🍺  /opt/homebrew/Cellar/libxmu/1.3.1: 37 files, 458.2KB
    ==> Installing ngspice dependency: libxpm
    ==> Pouring libxpm--3.5.19.arm64_sequoia.bottle.tar.gz
    🍺  /opt/homebrew/Cellar/libxpm/3.5.19: 57 files, 386KB
    ==> Installing ngspice dependency: libxaw
    ==> Pouring libxaw--1.0.16_1.arm64_sequoia.bottle.tar.gz
    🍺  /opt/homebrew/Cellar/libxaw/1.0.16_1: 89 files, 2MB
    ==> Installing ngspice
    ==> Pouring ngspice--47.arm64_sequoia.bottle.tar.gz
    🍺  /opt/homebrew/Cellar/ngspice/47: 29 files, 6.0MB
    ==> Caveats
    ==> ngspice
    If you need the graphical plotting functions you need to install X11 with:
      brew install --cask xquartz
`uv lock --project <repo>/plugins/forge/toolchain/python/kicad-mcp-pro --python 3.13`
    Using CPython 3.13.13
    Resolved 97 packages in 1.37s
`uv sync --project <repo>/plugins/forge/toolchain/python/kicad-mcp-pro --locked --python 3.13`
     + rpds-py==2026.6.3
     + sexpdata==1.0.2
     + shellingham==1.5.4
     + sniffio==1.3.1
     + sse-starlette==3.4.11
     + starlette==1.7.0
     + structlog==26.1.0
     + typer==0.27.2
     + typing-extensions==4.16.0
     + typing-inspection==0.4.4
     + uncalled-for==0.4.0
     + urllib3==2.8.0
     + uvicorn==0.53.0
     + watchfiles==1.3.0
     + websockets==17.1
kicad-mcp-pro wheel sha256 pinned in uv.lock

### sim + systems conda env (CalculiX, SysML v2 kernel, Java 21) (2026-09-24T20:50:46Z)
`pixi install --manifest-path /Users/samisayyed/.forge/envs/conda/pixi.toml`
    ✔ The default environment has been installed.
`pixi install --locked --manifest-path /Users/samisayyed/.forge/envs/conda/pixi.toml`
    ✔ The default environment has been installed.
linked /Users/samisayyed/.forge/bin/ccx -> /Users/samisayyed/.forge/envs/conda/.pixi/envs/default/bin/ccx
linked /Users/samisayyed/.forge/bin/forge-jupyter -> /Users/samisayyed/.forge/envs/conda/.pixi/envs/default/bin/jupyter
`python3 <repo>/plugins/forge/toolchain/smoke/smoke_ccx.py /Users/samisayyed/.forge/envs/conda/.pixi/envs/default/bin/ccx`
    tip deflection FEA=0.19012 mm hand(EB)=0.19048 mm diff=-0.19% (tolerance 3%, shear adds ~0.8%) work=/var/folders/_3/_mn031bx0r93tnmtx1w8jn0r0000gn/T/forge-smoke-ccx-t3r7miz7 -> PASS

### render (2026-09-24T20:51:07Z)
`brew install --cask blender`
      brew trust --cask <user>/<tap>/<cask>
      brew trust --command <user>/<tap>/<command>
    Whole-tap trust is broader and includes all current and future formulae,
    casks and commands from the listed taps. Trust whole taps with:
      brew trust stripe/stripe-cli supabase/tap
    Untap them with:
      brew untap stripe/stripe-cli supabase/tap
    For more information, see:
      https://docs.brew.sh/Tap-Trust
    ==> Fetching downloads for: blender
    ✔︎ Cask blender (5.2.2)
    ==> Installing Cask blender
    ==> Moving App 'Blender.app' to '/Applications/Blender.app'
    ==> Linking Command Wrapper 'blender' to '/opt/homebrew/bin/blender'
    🍺  blender was successfully installed!
linked /Users/samisayyed/.forge/bin/blender -> /Applications/Blender.app/Contents/MacOS/Blender

### systems (spec42) (2026-09-24T20:51:40Z)
`curl -fsSL -o /Users/samisayyed/.forge/downloads/spec42-0.53.1-darwin-arm64.tar.gz https://github.com/elan8/spec42/releases/download/v0.53.1/spec42-0.53.1-darwin-arm64.tar.gz`
sha256 ok: spec42-0.53.1-darwin-arm64.tar.gz
`tar -xzf /Users/samisayyed/.forge/downloads/spec42-0.53.1-darwin-arm64.tar.gz -C /Users/samisayyed/.forge/opt/spec42`
linked /Users/samisayyed/.forge/bin/spec42 -> /Users/samisayyed/.forge/opt/spec42/spec42

### embedded-sim (Renode) (2026-09-24T20:51:45Z)
`curl -fsSL -o /Users/samisayyed/.forge/downloads/renode-1.17.0.osx-arm64-portable.dmg https://github.com/renode/renode/releases/download/v1.17.0/renode-1.17.0.osx-arm64-portable.dmg`
sha256 ok: renode-1.17.0.osx-arm64-portable.dmg
`hdiutil attach -nobrowse -readonly -mountpoint /var/folders/_3/_mn031bx0r93tnmtx1w8jn0r0000gn/T/tmp.FkfjyrAivF /Users/samisayyed/.forge/downloads/renode-1.17.0.osx-arm64-portable.dmg`
    Checksumming  (Apple_Free : 3)…
                        (Apple_Free : 3): verified   CRC32 $00000000
    Checksumming disk image (Apple_APFS : 4)…
             disk image (Apple_APFS : 4): verified   CRC32 $9436637B
    Checksumming  (Apple_Free : 5)…
                        (Apple_Free : 5): verified   CRC32 $00000000
    Checksumming GPT Partition Data (Backup GPT Table : 6)…
    GPT Partition Data (Backup GPT Table: verified   CRC32 $C5D4C50C
    Checksumming GPT Header (Backup GPT Header : 7)…
      GPT Header (Backup GPT Header : 7): verified   CRC32 $BCA32693
    verified   CRC32 $D1941D6E
    /dev/disk6          	GUID_partition_scheme          	
    /dev/disk6s1        	Apple_APFS                     	
    /dev/disk7          	EF57347C-0000-11AA-AA11-0030654	
    /dev/disk7s1        	41504653-0000-11AA-AA11-0030654	/private/var/folders/_3/_mn031bx0r93tnmtx1w8jn0r0000gn/T/tmp.FkfjyrAivF
linked /Users/samisayyed/.forge/bin/renode -> /Users/samisayyed/.forge/opt/renode/Renode.app/Contents/MacOS/renode
free disk: 28 GiB
done: --relock elec sim render systems embedded-sim
free disk: 26 GiB

### mech (2026-09-25T05:05:09Z)
`uv sync --project <repo>/plugins/forge/toolchain/python/cad --locked --python 3.12`
    Resolved 95 packages in 16ms
    Checked 92 packages in 19ms
wrapped /Users/samisayyed/.forge/bin/forge-python -> /Users/samisayyed/.forge/envs/cad/bin/python
`/Users/samisayyed/.forge/envs/cad/bin/python <repo>/plugins/forge/toolchain/smoke/smoke_cad.py`
    volume=964.6571 mm3 expected=964.6571 mm3 rel_err=2.36e-16 step=19090 B png=12891 B out=/var/folders/_3/_mn031bx0r93tnmtx1w8jn0r0000gn/T/forge-smoke-cad-hqz1rrhc -> PASS
`uv sync --project <repo>/plugins/forge/toolchain/python/build123d-mcp --locked --python 3.12`
    Resolved 94 packages in 4ms
    Checked 89 packages in 15ms
linked /Users/samisayyed/.forge/bin/build123d-mcp -> /Users/samisayyed/.forge/envs/build123d-mcp/bin/build123d-mcp
cask freecad 1.1.3 already installed
linked /Users/samisayyed/.forge/bin/freecadcmd -> /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd

### render (2026-09-25T05:05:15Z)
cask blender 5.2.2 already installed
free disk: 26 GiB

### mech (2026-09-25T05:05:38Z)
`uv sync --project <repo>/plugins/forge/toolchain/python/cad --locked --python 3.12`
    Resolved 95 packages in 4ms
    Checked 92 packages in 14ms
wrapped /Users/samisayyed/.forge/bin/forge-python -> /Users/samisayyed/.forge/envs/cad/bin/python
`/Users/samisayyed/.forge/envs/cad/bin/python <repo>/plugins/forge/toolchain/smoke/smoke_cad.py`
    volume=964.6571 mm3 expected=964.6571 mm3 rel_err=2.36e-16 step=19090 B png=12891 B out=/var/folders/_3/_mn031bx0r93tnmtx1w8jn0r0000gn/T/forge-smoke-cad-n31foz83 -> PASS
`uv sync --project <repo>/plugins/forge/toolchain/python/build123d-mcp --locked --python 3.12`
    Resolved 94 packages in 4ms
    Checked 89 packages in 6ms
linked /Users/samisayyed/.forge/bin/build123d-mcp -> /Users/samisayyed/.forge/envs/build123d-mcp/bin/build123d-mcp
cask freecad 1.1.3 already installed
linked /Users/samisayyed/.forge/bin/freecadcmd -> /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd

### render (2026-09-25T05:05:44Z)
cask blender 5.2.2 already installed
wrapped /Users/samisayyed/.forge/bin/blender -> /Applications/Blender.app/Contents/MacOS/Blender
free disk: 26 GiB
done: mech render
free disk: 26 GiB

### mech (2026-09-25T05:06:58Z)
`uv sync --project <repo>/plugins/forge/toolchain/python/cad --locked --python 3.12`
    Resolved 95 packages in 4ms
    Checked 92 packages in 15ms
wrapped /Users/samisayyed/.forge/bin/forge-python -> /Users/samisayyed/.forge/envs/cad/bin/python
`/Users/samisayyed/.forge/envs/cad/bin/python <repo>/plugins/forge/toolchain/smoke/smoke_cad.py`
    volume=964.6571 mm3 expected=964.6571 mm3 rel_err=2.36e-16 step=19090 B png=12891 B out=/var/folders/_3/_mn031bx0r93tnmtx1w8jn0r0000gn/T/forge-smoke-cad-485lcnba -> PASS
`uv sync --project <repo>/plugins/forge/toolchain/python/build123d-mcp --locked --python 3.12`
    Resolved 94 packages in 4ms
    Checked 89 packages in 6ms
linked /Users/samisayyed/.forge/bin/build123d-mcp -> /Users/samisayyed/.forge/envs/build123d-mcp/bin/build123d-mcp
cask freecad 1.1.3 already installed
linked /Users/samisayyed/.forge/bin/freecadcmd -> /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd

### render (2026-09-25T05:07:04Z)
cask blender 5.2.2 already installed
wrapped /Users/samisayyed/.forge/bin/blender -> /Applications/Blender.app/Contents/MacOS/Blender
free disk: 26 GiB
done: mech render
free disk: 12 GiB
FAIL: free disk 12 GiB < 20 GiB floor
free disk: 12 GiB

### core (linux) (2026-09-25T07:05:45Z)
sha256 ok: pixi-0.81.0-hf01adef_0.conda
`/root/.forge/bin/pixi install --locked --manifest-path /root/.forge/envs/core/pixi.toml`
    The default environment has been installed.
linked /root/.forge/bin/git -> /root/.forge/envs/core/.pixi/envs/default/bin/git
linked /root/.forge/bin/gh -> /root/.forge/envs/core/.pixi/envs/default/bin/gh
linked /root/.forge/bin/uv -> /root/.forge/envs/core/.pixi/envs/default/bin/uv
linked /root/.forge/bin/node -> /root/.forge/envs/core/.pixi/envs/default/bin/node
linked /root/.forge/bin/npm -> /root/.forge/envs/core/.pixi/envs/default/bin/npm
linked /root/.forge/bin/npx -> /root/.forge/envs/core/.pixi/envs/default/bin/npx
`uv python install 3.12 3.13`
    warning: The `UV_NATIVE_TLS` environment variable is deprecated and will be removed in a future release. Use `UV_SYSTEM_CERTS` instead.
    All requested versions already installed
`npm ci --prefix /root/.forge/envs/node --ignore-scripts --no-audit --no-fund`
    npm warn Could not resolve dependency:
    npm warn peer circuit-json@"^0.0.426" from jscad-electronics@0.0.178
    npm warn node_modules/circuit-json-to-gltf/node_modules/jscad-electronics
    npm warn   jscad-electronics@"^0.0.178" from circuit-json-to-gltf@0.0.133
    npm warn   node_modules/circuit-json-to-gltf
    npm warn
    npm warn Conflicting peer dependency: circuit-json@0.0.426
    npm warn node_modules/circuit-json
    npm warn   peer circuit-json@"^0.0.426" from jscad-electronics@0.0.178
    npm warn   node_modules/circuit-json-to-gltf/node_modules/jscad-electronics
    npm warn     jscad-electronics@"^0.0.178" from circuit-json-to-gltf@0.0.133
    npm warn     node_modules/circuit-json-to-gltf
    npm warn deprecated prebuild-install@7.1.3: No longer maintained. Please contact the author of the relevant native addon; alternatives are available.
    
    added 303 packages in 8s
linked /root/.forge/bin/srt -> /root/.forge/envs/node/node_modules/.bin/srt
wrote /root/.forge/bin/tsci (telemetry disabled)

### mech (linux) (2026-09-25T07:05:55Z)
`uv sync --project <repo>/plugins/forge/toolchain/python/cad --locked --python 3.12`
    warning: The `UV_NATIVE_TLS` environment variable is deprecated and will be removed in a future release. Use `UV_SYSTEM_CERTS` instead.
    Resolved 95 packages in 2ms
    Checked 90 packages in 3ms
`/root/.forge/bin/pixi install --locked --manifest-path /root/.forge/envs/conda/pixi.toml`
    The default environment has been installed.
wrote /root/.forge/bin/forge-python (private lib path /root/.forge/lib)
`/root/.forge/bin/forge-python <repo>/plugins/forge/toolchain/smoke/smoke_cad.py`
    [0m[33m2026-09-25 07:05:59.135 (   0.683s) [    7F5E506C2740]vtkXOpenGLRenderWindow.:1450  WARN| bad X server connection. DISPLAY=[0m
    [0m[33m2026-09-25 07:05:59.136 (   0.684s) [    7F5E506C2740]vtkOpenGLRenderWindow.c:669   WARN| Failed to load EGL! Please install the EGL library from your distribution's package manager.[0m
    [0m[33m2026-09-25 07:05:59.136 (   0.684s) [    7F5E506C2740]vtkOSOpenGLRenderWindow:150   WARN| libOSMesa not found. It appears that OSMesa is not installed in your system. Please install the OSMesa library from your distribution's package manager.[0m
    [0m[33m2026-09-25 07:05:59.136 (   0.684s) [    7F5E506C2740]vtkOpenGLRenderWindow.c:669   WARN| Failed to load EGL! Please install the EGL library from your distribution's package manager.[0m
    [0m[33m2026-09-25 07:05:59.137 (   0.684s) [    7F5E506C2740]vtkOSOpenGLRenderWindow:150   WARN| libOSMesa not found. It appears that OSMesa is not installed in your system. Please install the OSMesa library from your distribution's package manager.[0m
FAIL: CAD smoke test failed
free disk: 12 GiB

### mech (linux) (2026-09-25T07:06:51Z)
`uv sync --project <repo>/plugins/forge/toolchain/python/cad --locked --python 3.12`
    warning: The `UV_NATIVE_TLS` environment variable is deprecated and will be removed in a future release. Use `UV_SYSTEM_CERTS` instead.
    Resolved 95 packages in 1ms
    Checked 90 packages in 0.75ms
`/root/.forge/bin/pixi install --locked --manifest-path /root/.forge/envs/conda/pixi.toml`
    Error:   × lock file not up-to-date with the workspace
    
free disk: 12 GiB

### mech (linux) (2026-09-25T07:07:04Z)
`uv sync --project <repo>/plugins/forge/toolchain/python/cad --locked --python 3.12`
    warning: The `UV_NATIVE_TLS` environment variable is deprecated and will be removed in a future release. Use `UV_SYSTEM_CERTS` instead.
    Resolved 95 packages in 1ms
    Checked 90 packages in 0.79ms
`/root/.forge/bin/pixi install --locked --manifest-path /root/.forge/envs/conda/pixi.toml`
    The default environment has been installed.
wrote /root/.forge/bin/forge-python (private lib path /root/.forge/lib)
`/root/.forge/bin/forge-python <repo>/plugins/forge/toolchain/smoke/smoke_cad.py`
    [0m[33m2026-09-25 07:07:08.202 (   0.725s) [    7F41F3440740]vtkXOpenGLRenderWindow.:1450  WARN| bad X server connection. DISPLAY=[0m
    volume=964.6571 mm3 expected=964.6571 mm3 rel_err=2.36e-16 step=19090 B png=15112 B out=/tmp/forge-smoke-cad-wqp9gezp -> PASS
`uv sync --project <repo>/plugins/forge/toolchain/python/build123d-mcp --locked --python 3.12`
    warning: The `UV_NATIVE_TLS` environment variable is deprecated and will be removed in a future release. Use `UV_SYSTEM_CERTS` instead.
    Resolved 94 packages in 1ms
    Checked 89 packages in 0.69ms
linked /root/.forge/bin/build123d-mcp -> /root/.forge/envs/build123d-mcp/bin/build123d-mcp
`/root/.forge/bin/pixi install --locked --manifest-path /root/.forge/envs/freecad/pixi.toml`
    The default environment has been installed.
wrapped /root/.forge/bin/freecadcmd -> /root/.forge/envs/freecad/.pixi/envs/default/bin/freecadcmd
free disk: 12 GiB
done: mech
free disk: 12 GiB

### core (linux) (2026-09-25T07:07:15Z)
sha256 ok: pixi-0.81.0-hf01adef_0.conda
`/root/.forge/bin/pixi install --locked --manifest-path /root/.forge/envs/core/pixi.toml`
    The default environment has been installed.
linked /root/.forge/bin/git -> /root/.forge/envs/core/.pixi/envs/default/bin/git
linked /root/.forge/bin/gh -> /root/.forge/envs/core/.pixi/envs/default/bin/gh
linked /root/.forge/bin/uv -> /root/.forge/envs/core/.pixi/envs/default/bin/uv
linked /root/.forge/bin/node -> /root/.forge/envs/core/.pixi/envs/default/bin/node
linked /root/.forge/bin/npm -> /root/.forge/envs/core/.pixi/envs/default/bin/npm
linked /root/.forge/bin/npx -> /root/.forge/envs/core/.pixi/envs/default/bin/npx
`uv python install 3.12 3.13`
    warning: The `UV_NATIVE_TLS` environment variable is deprecated and will be removed in a future release. Use `UV_SYSTEM_CERTS` instead.
    All requested versions already installed
`npm ci --prefix /root/.forge/envs/node --ignore-scripts --no-audit --no-fund`
    npm warn Could not resolve dependency:
    npm warn peer circuit-json@"^0.0.426" from jscad-electronics@0.0.178
    npm warn node_modules/circuit-json-to-gltf/node_modules/jscad-electronics
    npm warn   jscad-electronics@"^0.0.178" from circuit-json-to-gltf@0.0.133
    npm warn   node_modules/circuit-json-to-gltf
    npm warn
    npm warn Conflicting peer dependency: circuit-json@0.0.426
    npm warn node_modules/circuit-json
    npm warn   peer circuit-json@"^0.0.426" from jscad-electronics@0.0.178
    npm warn   node_modules/circuit-json-to-gltf/node_modules/jscad-electronics
    npm warn     jscad-electronics@"^0.0.178" from circuit-json-to-gltf@0.0.133
    npm warn     node_modules/circuit-json-to-gltf
    npm warn deprecated prebuild-install@7.1.3: No longer maintained. Please contact the author of the relevant native addon; alternatives are available.
    
    added 303 packages in 10s
linked /root/.forge/bin/srt -> /root/.forge/envs/node/node_modules/.bin/srt
wrote /root/.forge/bin/tsci (telemetry disabled)

### mech (linux) (2026-09-25T07:07:26Z)
`uv sync --project <repo>/plugins/forge/toolchain/python/cad --locked --python 3.12`
    warning: The `UV_NATIVE_TLS` environment variable is deprecated and will be removed in a future release. Use `UV_SYSTEM_CERTS` instead.
    Resolved 95 packages in 2ms
    Checked 90 packages in 1ms
`/root/.forge/bin/pixi install --locked --manifest-path /root/.forge/envs/conda/pixi.toml`
    The default environment has been installed.
wrote /root/.forge/bin/forge-python (private lib path /root/.forge/lib)
`/root/.forge/bin/forge-python <repo>/plugins/forge/toolchain/smoke/smoke_cad.py`
    [0m[33m2026-09-25 07:07:30.163 (   0.708s) [    7F53A30F0740]vtkXOpenGLRenderWindow.:1450  WARN| bad X server connection. DISPLAY=[0m
    volume=964.6571 mm3 expected=964.6571 mm3 rel_err=2.36e-16 step=19090 B png=15112 B out=/tmp/forge-smoke-cad-p6aybior -> PASS
`uv sync --project <repo>/plugins/forge/toolchain/python/build123d-mcp --locked --python 3.12`
    warning: The `UV_NATIVE_TLS` environment variable is deprecated and will be removed in a future release. Use `UV_SYSTEM_CERTS` instead.
    Resolved 94 packages in 2ms
    Checked 89 packages in 0.83ms
linked /root/.forge/bin/build123d-mcp -> /root/.forge/envs/build123d-mcp/bin/build123d-mcp
`/root/.forge/bin/pixi install --locked --manifest-path /root/.forge/envs/freecad/pixi.toml`
    The default environment has been installed.
wrapped /root/.forge/bin/freecadcmd -> /root/.forge/envs/freecad/.pixi/envs/default/bin/freecadcmd

### elec (linux) (2026-09-25T07:07:31Z)
`python3 <repo>/plugins/forge/toolchain/linux/debfetch.py install --lock <repo>/plugins/forge/toolchain/linux/debs.lock.json --prefix /root/.forge/opt/kicad --cache /root/.forge/downloads/debs`
    installed 118 debs into /root/.forge/opt/kicad
KiCad 10.0.6 unpacked to /root/.forge/opt/kicad (demos: /root/.forge/opt/kicad-demos)
ngspice 47 already built
linked /root/.forge/bin/ngspice -> /root/.forge/opt/ngspice-47/bin/ngspice
`uv sync --project <repo>/plugins/forge/toolchain/python/kicad-mcp-pro --locked --python 3.13`
    warning: The `UV_NATIVE_TLS` environment variable is deprecated and will be removed in a future release. Use `UV_SYSTEM_CERTS` instead.
    Resolved 97 packages in 2ms
    Checked 93 packages in 1ms
kicad-mcp-pro wheel sha256 pinned in uv.lock

### sim + systems conda env (linux: CalculiX, SysML v2 kernel, Java 21) (2026-09-25T07:07:46Z)
`/root/.forge/bin/pixi install --locked --manifest-path /root/.forge/envs/conda/pixi.toml`
    The default environment has been installed.
linked /root/.forge/bin/ccx -> /root/.forge/envs/conda/.pixi/envs/default/bin/ccx
linked /root/.forge/bin/forge-jupyter -> /root/.forge/envs/conda/.pixi/envs/default/bin/jupyter
`python3 <repo>/plugins/forge/toolchain/smoke/smoke_ccx.py /root/.forge/envs/conda/.pixi/envs/default/bin/ccx`
    tip deflection FEA=0.19012 mm hand(EB)=0.19048 mm diff=-0.19% (tolerance 3%, shear adds ~0.8%) work=/tmp/forge-smoke-ccx-ika8e_j6 -> PASS

### render (linux) (2026-09-25T07:07:46Z)
sha256 ok: blender-5.2.2-linux-x64.tar.xz
`tar -xJf /root/.forge/downloads/blender-5.2.2-linux-x64.tar.xz -C /root/.forge/opt/blender --strip-components=1`
wrapped /root/.forge/bin/blender -> /root/.forge/opt/blender/blender

### systems (linux: spec42 from pinned tag) (2026-09-25T07:08:05Z)
git pin ok: spec42@v0.53.1 = f0d268fcd84dbaa3626b0616e34b0610957d61c8
git pin ok: sysml-domain-libraries@v0.3.0 = e91156d43e2d2a92d983744551bc9a3e99787c03
git pin ok: mbse-methodology@v0.2.0 = 00e21183a86171bbf9851e71c12c18b49d65d9e1
`bash scripts/fetch-stdlib-bundle.sh`
    Using existing stdlib KPAR cache at /root/.forge/src/spec42/.cache/sysml-stdlib-kpar-2026-04
    Finished `release` profile [optimized] target(s) in 0.24s
linked /root/.forge/bin/spec42 -> /root/.forge/opt/spec42/spec42

### embedded-sim (linux: Renode) (2026-09-25T07:08:06Z)
sha256 ok: renode-1.17.0.linux-portable.tar.gz
`tar -xzf /root/.forge/downloads/renode-1.17.0.linux-portable.tar.gz -C /root/.forge/opt/renode --strip-components=1`
linked /root/.forge/bin/renode -> /root/.forge/opt/renode/renode
free disk: 13 GiB
done: all
