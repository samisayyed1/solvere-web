#!/usr/bin/env bash
# Forge toolchain installer (ADR-001 §8). Idempotent and tiered; refuses to continue on any
# version or hash mismatch.
#
#   ./install.sh [--relock] core|mech|elec|sim|render|systems|embedded-sim|all ...
#
# Default mode installs exactly what the committed lockfiles say. --relock re-resolves
# (maintainers only) and rewrites the lockfiles in this directory.
# Heavy environments live outside the repo under $FORGE_HOME (default ~/.forge).
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FORGE_HOME="${FORGE_HOME:-$HOME/.forge}"
ENVS="$FORGE_HOME/envs"; BIN="$FORGE_HOME/bin"; OPT="$FORGE_HOME/opt"; DL="$FORGE_HOME/downloads"
LOG="$HERE/INSTALL-LOG.md"
RELOCK=0
MIN_FREE_GIB=25

# ---- pins (single source of truth for non-lockfile artifacts) --------------------------------
PY_CAD=3.12; PY_KICAD_MCP=3.13
CASK_KICAD=10.0.6; CASK_FREECAD=1.1.3; CASK_BLENDER=5.2.2
BREW_NGSPICE=47; BREW_PIXI=0.81.0
SPEC42_VER=0.53.1
SPEC42_URL="https://github.com/elan8/spec42/releases/download/v${SPEC42_VER}/spec42-${SPEC42_VER}-darwin-arm64.tar.gz"
SPEC42_SHA=33100ed09d33cd6263ce62742b1721d52df83054ba524033f9a0980eb83f7228
RENODE_VER=1.17.0
RENODE_URL="https://github.com/renode/renode/releases/download/v${RENODE_VER}/renode-${RENODE_VER}.osx-arm64-portable.dmg"
RENODE_SHA=63b1fb691207f503cea937e4ec8fad3e068a517d0abac3c24c0206c62f6c4d12
KICAD_MCP_WHEEL_SHA=b2297186a61dfbf5fe57fce26a6b8d7fc5b0877514444a26d5b5786f50e017a0

log()  { printf '%s\n' "$*" | tee -a "$LOG"; }
die()  { log "FAIL: $*"; exit 1; }
step() { log ""; log "### $* ($(date -u +%Y-%m-%dT%H:%M:%SZ))"; }
run()  { log "\`$*\`"; "$@" 2>&1 | tail -n 15 | sed 's/^/    /' | tee -a "$LOG"; return "${PIPESTATUS[0]}"; }

check_disk() {
  local free; free=$(df -g / | awk 'NR==2{print $4}')
  log "free disk: ${free} GiB"
  [ "$free" -ge "$MIN_FREE_GIB" ] || die "free disk ${free} GiB < ${MIN_FREE_GIB} GiB floor"
}

sha_check() { # file expected
  local got; got=$(shasum -a 256 "$1" | awk '{print $1}')
  [ "$got" = "$2" ] || die "sha256 mismatch for $1: got $got expected $2"
  log "sha256 ok: $(basename "$1")"
}

link() { mkdir -p "$BIN"; ln -sf "$1" "$BIN/$2"; log "linked $BIN/$2 -> $1"; }

brew_cask() { # name pinned-version
  local v; v=$(brew info --cask --json=v2 "$1" | python3 -c 'import json,sys;print(json.load(sys.stdin)["casks"][0]["version"])')
  [ "$v" = "$2" ] || die "cask $1 offers $v, pinned $2 — update the pin via ADR, don't drift"
  if brew list --cask "$1" >/dev/null 2>&1; then log "cask $1 $v already installed"; else run brew install --cask "$1"; fi
}

brew_formula() { # name pinned-version
  local v; v=$(brew info --json=v2 "$1" | python3 -c 'import json,sys;print(json.load(sys.stdin)["formulae"][0]["versions"]["stable"])')
  [ "$v" = "$2" ] || die "formula $1 offers $v, pinned $2"
  if brew list --formula "$1" >/dev/null 2>&1; then log "formula $1 already installed"; else run brew install "$1"; fi
}

uv_env() { # project-dir env-name python
  local proj="$HERE/python/$1"
  export UV_PROJECT_ENVIRONMENT="$ENVS/$2"
  if [ "$RELOCK" = 1 ]; then run uv lock --project "$proj" --python "$3"; fi
  [ -f "$proj/uv.lock" ] || die "$proj/uv.lock missing (run with --relock once, then commit it)"
  run uv sync --project "$proj" --locked --python "$3"
  unset UV_PROJECT_ENVIRONMENT
}

tier_core() {
  step "core"
  run uv python install "$PY_CAD" "$PY_KICAD_MCP"
  brew_formula pixi "$BREW_PIXI"
  mkdir -p "$ENVS/node"
  cp "$HERE/node/package.json" "$ENVS/node/"
  if [ "$RELOCK" = 1 ]; then
    run npm install --prefix "$ENVS/node" --ignore-scripts --no-audit --no-fund
    cp "$ENVS/node/package-lock.json" "$HERE/node/"
  fi
  [ -f "$HERE/node/package-lock.json" ] || die "node/package-lock.json missing"
  cp "$HERE/node/package-lock.json" "$ENVS/node/"
  run npm ci --prefix "$ENVS/node" --ignore-scripts --no-audit --no-fund
  link "$ENVS/node/node_modules/.bin/srt" srt
  printf '#!/bin/sh\nTSCI_TELEMETRY_DISABLED=1 exec "%s" "$@"\n' "$ENVS/node/node_modules/.bin/tsci" > "$BIN/tsci"
  chmod +x "$BIN/tsci"; log "wrote $BIN/tsci (telemetry disabled)"
}

tier_mech() {
  step "mech"
  uv_env cad cad "$PY_CAD"
  link "$ENVS/cad/bin/python" forge-python
  run "$ENVS/cad/bin/python" "$HERE/smoke/smoke_cad.py" || die "CAD smoke test failed"
  uv_env build123d-mcp build123d-mcp "$PY_CAD"
  link "$ENVS/build123d-mcp/bin/build123d-mcp" build123d-mcp
  brew_cask freecad "$CASK_FREECAD"
  link /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd freecadcmd
}

install_kicad() {
  # The brew cask copies demos to /Library via sudo, which an agent can't do. Instead, install
  # the identical official DMG, verified against the cask's pinned sha256: the app suite goes to
  # /Applications/KiCad and the demos to $OPT.
  if [ -x /Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli ] && \
     /Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli version 2>/dev/null | grep -q "^${CASK_KICAD}"; then
    log "KiCad ${CASK_KICAD} already installed"; return
  fi
  local url sha f mnt
  url=$(brew info --cask --json=v2 kicad | python3 -c 'import json,sys;print(json.load(sys.stdin)["casks"][0]["url"])')
  sha=$(brew info --cask --json=v2 kicad | python3 -c 'import json,sys;print(json.load(sys.stdin)["casks"][0]["sha256"])')
  case "$url" in *"/${CASK_KICAD}/"*) ;; *) die "kicad cask URL $url is not version ${CASK_KICAD}";; esac
  f="$(brew --cache --cask kicad 2>/dev/null || true)"
  if [ ! -f "$f" ]; then mkdir -p "$DL"; f="$DL/$(basename "$url")"; [ -f "$f" ] || run curl -fsSL -o "$f" "$url"; fi
  sha_check "$f" "$sha"
  mnt=$(mktemp -d)
  run hdiutil attach -nobrowse -readonly -mountpoint "$mnt" "$f"
  rm -rf /Applications/KiCad "$OPT/kicad-demos"
  cp -R "$mnt/KiCad" /Applications/KiCad
  [ -d "$mnt/demos" ] && cp -R "$mnt/demos" "$OPT/kicad-demos"
  hdiutil detach "$mnt" >/dev/null
  log "KiCad ${CASK_KICAD} installed to /Applications/KiCad (demos: $OPT/kicad-demos)"
}

tier_elec() {
  step "elec"
  install_kicad
  link /Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli kicad-cli
  brew_formula ngspice "$BREW_NGSPICE"
  local out; out=$(cd "$HERE/smoke" && ngspice -b -n rc.cir 2>&1 | tr -d '\r')
  local v; v=$(printf '%s\n' "$out" | awk -F'=' '/^vtau/{gsub(/ /,"",$2); print $2}')
  python3 - "$v" <<'PY' || die "ngspice smoke failed"
import math, sys
v = float(sys.argv[1]); exp = 1 - math.exp(-1); err = abs(v - exp) / exp
assert abs(v - 1.05 * exp) / (1.05 * exp) >= 0.005, "negative control: check cannot fail"
print(f"ngspice v(out)@tau={v:.5f} V expected={exp:.5f} V rel_err={err:.2e} -> {'PASS' if err < 0.005 else 'FAIL'}")
sys.exit(0 if err < 0.005 else 1)
PY
  uv_env kicad-mcp-pro kicad-mcp-pro "$PY_KICAD_MCP"
  grep -q "$KICAD_MCP_WHEEL_SHA" "$HERE/python/kicad-mcp-pro/uv.lock" || die "kicad-mcp-pro wheel hash not in uv.lock"
  log "kicad-mcp-pro wheel sha256 pinned in uv.lock"
}

tier_sim() {
  step "sim + systems conda env (CalculiX, SysML v2 kernel, Java 21)"
  mkdir -p "$ENVS/conda"
  cp "$HERE/conda/pixi.toml" "$ENVS/conda/"
  if [ "$RELOCK" = 1 ]; then
    run pixi install --manifest-path "$ENVS/conda/pixi.toml"
    cp "$ENVS/conda/pixi.lock" "$HERE/conda/"
  fi
  [ -f "$HERE/conda/pixi.lock" ] || die "conda/pixi.lock missing"
  cp "$HERE/conda/pixi.lock" "$ENVS/conda/"
  run pixi install --locked --manifest-path "$ENVS/conda/pixi.toml"
  local cbin="$ENVS/conda/.pixi/envs/default/bin"
  link "$cbin/ccx" ccx
  link "$cbin/jupyter" forge-jupyter
  run python3 "$HERE/smoke/smoke_ccx.py" "$cbin/ccx" || die "CalculiX smoke failed"
}

tier_render() {
  step "render"
  brew_cask blender "$CASK_BLENDER"
  link /Applications/Blender.app/Contents/MacOS/Blender blender
}

tier_systems() {
  step "systems (spec42)"
  mkdir -p "$DL" "$OPT/spec42"
  local f="$DL/$(basename "$SPEC42_URL")"
  [ -f "$f" ] || run curl -fsSL -o "$f" "$SPEC42_URL"
  sha_check "$f" "$SPEC42_SHA"
  run tar -xzf "$f" -C "$OPT/spec42"
  link "$(find "$OPT/spec42" -type f -name spec42 -perm -u+x | head -n1)" spec42
}

tier_embedded_sim() {
  step "embedded-sim (Renode)"
  mkdir -p "$DL" "$OPT"
  local f="$DL/$(basename "$RENODE_URL")"
  [ -f "$f" ] || run curl -fsSL -o "$f" "$RENODE_URL"
  sha_check "$f" "$RENODE_SHA"
  local mnt; mnt=$(mktemp -d)
  run hdiutil attach -nobrowse -readonly -mountpoint "$mnt" "$f"
  rm -rf "$OPT/renode"; mkdir -p "$OPT/renode"
  cp -R "$mnt"/. "$OPT/renode/"
  hdiutil detach "$mnt" >/dev/null
  link "$(find "$OPT/renode" -type f -name renode -perm -u+x | head -n1)" renode
}

main() {
  [ "$#" -gt 0 ] || { sed -n '2,10p' "$0"; exit 2; }
  [ "$(uname -s)-$(uname -m)" = "Darwin-arm64" ] || die "this installer targets macOS arm64"
  [ -f "$LOG" ] || printf '# Forge toolchain install log\n' > "$LOG"
  mkdir -p "$ENVS" "$BIN" "$OPT" "$DL"
  check_disk
  for t in "$@"; do
    case "$t" in
      --relock) RELOCK=1 ;;
      core) tier_core ;; mech) tier_mech ;; elec) tier_elec ;; sim) tier_sim ;;
      render) tier_render ;; systems) tier_systems ;; embedded-sim) tier_embedded_sim ;;
      all) tier_core; tier_mech; tier_elec; tier_sim; tier_render; tier_systems; tier_embedded_sim ;;
      *) die "unknown tier: $t" ;;
    esac
  done
  check_disk
  log "done: $*"
}
main "$@"
