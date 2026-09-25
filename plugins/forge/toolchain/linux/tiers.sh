# shellcheck shell=bash
# Linux-x86_64 tiers for install.sh (ADR-001 §8.L). Sourced by install.sh, which defines
# log/die/step/run/link/wrap/sha_check/fetch/git_at_commit/uv_env/ngspice_smoke and the pins.
#
# No root and no apt: conda-forge via pixi lockfiles, official tarballs, the KiCad PPA
# unpacked in user space (debfetch.py), and source builds from pinned git tags where no
# official Linux binary is reachable (ngspice 47: conda-forge stops at 41; spec42: GitHub
# release assets are not always downloadable, and the tag commit is pinned instead).

PIXI="$BIN/pixi"

pixi_env() { # manifest-dir env-name -- install a locked conda-forge env to $ENVS/<env-name>
  local src="$HERE/$1" dst="$ENVS/$2"
  mkdir -p "$dst"; cp "$src/pixi.toml" "$dst/"
  if [ "$RELOCK" = 1 ]; then run "$PIXI" lock --manifest-path "$dst/pixi.toml"; cp "$dst/pixi.lock" "$src/"; fi
  [ -f "$src/pixi.lock" ] || die "$src/pixi.lock missing (run with --relock once, then commit it)"
  cp "$src/pixi.lock" "$dst/"
  run "$PIXI" install --locked --manifest-path "$dst/pixi.toml"
}

linux_tier_core() {
  step "core (linux)"
  mkdir -p "$DL" "$BIN"
  local f x
  f="$DL/$(basename "$PIXI_CONDA_URL")"
  fetch "$PIXI_CONDA_URL" "$f"; sha_check "$f" "$PIXI_CONDA_SHA"
  x=$(mktemp -d)
  # A .conda file is a zip of zstd tarballs. Unpack it with a pinned zstandard wheel so no
  # zstd binary is needed on the host.
  command -v uv >/dev/null || die "uv is required to bootstrap pixi on Linux (install uv ${UV_BOOTSTRAP:-0.11.17} first)"
  python3 "$HERE/linux/unconda.py" "$f" "$x" || die "could not unpack the pixi conda package"
  install -m 0755 "$x/bin/pixi" "$PIXI"; rm -rf "$x"
  "$PIXI" --version | grep -q "pixi ${BREW_PIXI}" || die "pixi is not ${BREW_PIXI}"
  pixi_env conda-core core
  local c="$ENVS/core/.pixi/envs/default/bin" b
  for b in git gh uv node npm npx bwrap socat; do link "$c/$b" "$b"; done
  export PATH="$BIN:$PATH"
  run uv python install "$PY_CAD" "$PY_KICAD_MCP"
  mkdir -p "$ENVS/node"
  cp "$HERE/node/package.json" "$HERE/node/package-lock.json" "$ENVS/node/"
  run npm ci --prefix "$ENVS/node" --ignore-scripts --no-audit --no-fund
  link "$ENVS/node/node_modules/.bin/srt" srt
  printf '#!/bin/sh\nTSCI_TELEMETRY_DISABLED=1 exec "%s" "$@"\n' "$ENVS/node/node_modules/.bin/tsci" > "$BIN/tsci"
  chmod +x "$BIN/tsci"; log "wrote $BIN/tsci (telemetry disabled)"
}

linux_tier_mech() {
  step "mech (linux)"
  export PATH="$BIN:$PATH"
  uv_env cad cad "$PY_CAD"
  # gmsh and OCP dlopen libGLU, libXft and libOpenGL, and VTK renders offscreen through
  # surfaceless EGL with Mesa's llvmpipe; a headless Linux host may have none of these. The
  # locked conda env ships them. Only these roots and the dependencies they resolve from the
  # conda env are exposed on the private path $FORGE_HOME/lib, so nothing else in the conda
  # env can shadow the CAD env's own libraries.
  pixi_env conda conda
  local clib="$ENVS/conda/.pixi/envs/default/lib" l dep
  rm -rf "${FORGE_HOME:?}/lib"; mkdir -p "$FORGE_HOME/lib"
  for l in libGLU.so.1 libXft.so.2 libOpenGL.so.0 libEGL.so.1 libEGL_mesa.so.0 libGL.so.1 libGLX_mesa.so.0; do
    [ -e "$clib/$l" ] || die "conda env lacks $l"
    ln -sf "$clib/$l" "$FORGE_HOME/lib/$l"
    for dep in $(LD_LIBRARY_PATH="$clib" ldd "$clib/$l" | awk -v c="$clib/" 'index($3, c) == 1 {print $1}'); do
      # A library the host already provides stays the host's.
      ldconfig -p 2>/dev/null | grep -q "^[[:space:]]*$dep " && continue
      ln -sf "$clib/$dep" "$FORGE_HOME/lib/$dep"
    done
  done
  rm -f "$BIN/forge-python"
  printf '#!/bin/sh\nLD_LIBRARY_PATH="%s${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" __EGL_VENDOR_LIBRARY_DIRS="%s" exec "%s" "$@"\n' \
    "$FORGE_HOME/lib" "$ENVS/conda/.pixi/envs/default/share/glvnd/egl_vendor.d" "$ENVS/cad/bin/python" > "$BIN/forge-python"
  chmod +x "$BIN/forge-python"; log "wrote $BIN/forge-python (private lib path $FORGE_HOME/lib)"
  run "$BIN/forge-python" "$HERE/smoke/smoke_cad.py" || die "CAD smoke test failed"
  uv_env build123d-mcp build123d-mcp "$PY_CAD"
  link "$ENVS/build123d-mcp/bin/build123d-mcp" build123d-mcp
  pixi_env conda-freecad freecad
  wrap "$ENVS/freecad/.pixi/envs/default/bin/freecadcmd" freecadcmd
  "$BIN/freecadcmd" --version 2>&1 | grep -q "FreeCAD ${CASK_FREECAD}" || die "freecadcmd is not ${CASK_FREECAD}"
}

linux_install_kicad() {
  local k="$OPT/kicad"
  run python3 "$HERE/linux/debfetch.py" install --lock "$HERE/linux/debs.lock.json" --prefix "$k" --cache "$DL/debs"
  python3 -c 'import json,sys; l=json.load(open(sys.argv[1])); sys.exit(0 if any(d["package"]=="kicad" and d["sha256"]==sys.argv[2] for d in l["debs"]) else 1)' \
    "$HERE/linux/debs.lock.json" "$KICAD_DEB_SHA" || die "debs.lock.json does not pin kicad .deb sha256 $KICAD_DEB_SHA"
  rm -f "$BIN/kicad-cli"
  {
    printf '#!/bin/sh\n'
    printf '# KiCad %s unpacked in user space (ADR-001 §8.L): point the loader and KiCad at the prefix.\n' "$CASK_KICAD"
    printf 'export LD_LIBRARY_PATH="%s/usr/lib/x86_64-linux-gnu:%s/usr/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"\n' "$k" "$k"
    printf 'export KICAD_STOCK_DATA_HOME="%s/usr/share/kicad"\n' "$k"
    printf 'export KICAD10_SYMBOL_DIR="%s/usr/share/kicad/symbols"\n' "$k"
    printf 'export KICAD10_FOOTPRINT_DIR="%s/usr/share/kicad/footprints"\n' "$k"
    printf 'export KICAD10_3DMODEL_DIR="%s/usr/share/kicad/3dmodels"\n' "$k"
    printf 'export KICAD10_TEMPLATE_DIR="%s/usr/share/kicad/template"\n' "$k"
    printf 'exec "%s/usr/bin/kicad-cli" "$@"\n' "$k"
  } > "$BIN/kicad-cli"
  chmod +x "$BIN/kicad-cli"
  ln -sfn "$k/usr/share/kicad/demos" "$OPT/kicad-demos"
  "$BIN/kicad-cli" version 2>&1 | grep -q "^${CASK_KICAD}" || die "kicad-cli is not ${CASK_KICAD}"
  log "KiCad ${CASK_KICAD} unpacked to $k (demos: $OPT/kicad-demos)"
}

linux_install_ngspice() {
  local src="$FORGE_HOME/src/ngspice" prefix="$OPT/ngspice-${BREW_NGSPICE}"
  if [ -x "$prefix/bin/ngspice" ] && "$prefix/bin/ngspice" -v 2>&1 | grep -q "ngspice-${BREW_NGSPICE}"; then
    log "ngspice ${BREW_NGSPICE} already built"
  else
    pixi_env conda-build build
    mkdir -p "$FORGE_HOME/src"
    git_at_commit "$NGSPICE_GIT" "$NGSPICE_TAG" "$NGSPICE_COMMIT" "$src"
    run "$PIXI" run --manifest-path "$ENVS/build/pixi.toml" bash -c "set -e; cd '$src'; ./autogen.sh; mkdir -p release; cd release; \
../configure --prefix='$prefix' --without-x --with-readline=yes --disable-debug --enable-openmp=no; make -j\$(nproc); make install" \
      || die "ngspice build failed"
  fi
  link "$prefix/bin/ngspice" ngspice
}

linux_tier_elec() {
  step "elec (linux)"
  export PATH="$BIN:$PATH"
  linux_install_kicad
  linux_install_ngspice
  ngspice_smoke
  uv_env kicad-mcp-pro kicad-mcp-pro "$PY_KICAD_MCP"
  grep -q "$KICAD_MCP_WHEEL_SHA" "$HERE/python/kicad-mcp-pro/uv.lock" || die "kicad-mcp-pro wheel hash not in uv.lock"
  log "kicad-mcp-pro wheel sha256 pinned in uv.lock"
}

linux_tier_sim() {
  step "sim + systems conda env (linux: CalculiX, SysML v2 kernel, Java 21)"
  pixi_env conda conda
  local cbin="$ENVS/conda/.pixi/envs/default/bin"
  link "$cbin/ccx" ccx
  link "$cbin/jupyter" forge-jupyter
  run python3 "$HERE/smoke/smoke_ccx.py" "$cbin/ccx" || die "CalculiX smoke failed"
}

linux_tier_render() {
  step "render (linux)"
  local f
  f="$DL/$(basename "$BLENDER_LINUX_URL")"
  fetch "$BLENDER_LINUX_URL" "$f"; sha_check "$f" "$BLENDER_LINUX_SHA"
  [ -n "$OPT" ] || die "OPT is empty"
  rm -rf "${OPT:?}/blender"; mkdir -p "$OPT/blender"
  run tar -xJf "$f" -C "$OPT/blender" --strip-components=1
  wrap "$OPT/blender/blender" blender
  "$BIN/blender" -b --factory-startup --version 2>&1 | grep -q "Blender ${CASK_BLENDER}" || die "blender is not ${CASK_BLENDER}"
}

linux_tier_systems() {
  step "systems (linux: spec42 from pinned tag)"
  export PATH="$BIN:$PATH"
  local src="$FORGE_HOME/src/spec42" tgt="$FORGE_HOME/src/spec42-target"
  command -v cargo >/dev/null || die "cargo (rustup) is required to build spec42 on Linux; its rust-toolchain.toml pins the exact Rust"
  mkdir -p "$FORGE_HOME/src" "$OPT/spec42"
  git_at_commit "$SPEC42_GIT" "$SPEC42_TAG" "$SPEC42_COMMIT" "$src"
  # spec42 embeds three library sets at build time. Its release CI downloads them as GitHub
  # release assets; here they come from the same upstream git tags, pinned by commit. The
  # build packs the two elan8 libraries from sibling checkouts (crates/library_catalog/build.rs).
  git_at_commit https://github.com/elan8/sysml-domain-libraries v0.3.0 "$SPEC42_DOMAIN_COMMIT" "$FORGE_HOME/src/sysml-domain-libraries"
  git_at_commit https://github.com/elan8/mbse-methodology v0.2.0 "$SPEC42_METHOD_COMMIT" "$FORGE_HOME/src/mbse-methodology"
  local stdlib_head
  stdlib_head=$(git ls-remote https://github.com/Systems-Modeling/SysML-v2-Release 'refs/tags/2026-04^{}' | awk '{print $1}')
  [ -n "$stdlib_head" ] || stdlib_head=$(git ls-remote https://github.com/Systems-Modeling/SysML-v2-Release refs/tags/2026-04 | awk '{print $1}')
  [ "$stdlib_head" = "$SPEC42_STDLIB_COMMIT" ] || die "SysML-v2-Release tag 2026-04 is at $stdlib_head, pinned $SPEC42_STDLIB_COMMIT"
  (cd "$src" && run bash scripts/fetch-stdlib-bundle.sh) || die "SysML stdlib fetch failed"
  (cd "$src" && CARGO_TARGET_DIR="$tgt" cargo build --locked --release --bin spec42) 2>&1 | tail -n 5 | redact | tee -a "$LOG"
  [ -x "$tgt/release/spec42" ] || die "spec42 build failed"
  install -m 0755 "$tgt/release/spec42" "$OPT/spec42/spec42"
  rm -rf "${tgt:?}"  # ~2 GiB of build products; only the binary is kept
  link "$OPT/spec42/spec42" spec42
  "$BIN/spec42" --version 2>&1 | grep -q "spec42 ${SPEC42_VER}" || die "spec42 is not ${SPEC42_VER}"
}

linux_tier_embedded_sim() {
  step "embedded-sim (linux: Renode)"
  local f
  f="$DL/$(basename "$RENODE_LINUX_URL")"
  fetch "$RENODE_LINUX_URL" "$f"; sha_check "$f" "$RENODE_LINUX_SHA"
  [ -n "$OPT" ] || die "OPT is empty"
  rm -rf "${OPT:?}/renode"; mkdir -p "$OPT/renode"
  run tar -xzf "$f" -C "$OPT/renode" --strip-components=1
  link "$OPT/renode/renode" renode
  "$BIN/renode" --version 2>&1 | grep -q "v${RENODE_VER}" || die "renode is not ${RENODE_VER}"
}
