#!/usr/bin/env python3
"""designing-circuits verify entrypoint (CONTRACTS.md §9, elec domain, ``.control`` shell refused).

    forge-python skills/designing-circuits/scripts/verify.py --project <root> [--changed <path> ...] [--fast]

For every ``analysis/spice/<name>.cir`` with a sidecar ``analysis/spice/<name>.limits.toml``:

1. **Refuses to run** any netlist whose ``.control`` block contains a ``shell`` command --
   ngspice's ``shell`` front-end command runs ``/bin/sh -c`` unconditionally, and ``-n``
   does not disable it (ADR-001 D11, CROSSCHECK C17). The netlist is never executed.
2. Runs ``ngspice -b -n`` **inside ``srt``**, with network denied entirely and filesystem
   writes confined to this project's ``out/verify/`` (including ngspice's own scratch
   files, via ``TMPDIR``) -- see ``references/spice-limits-format.md`` for why a bare
   ``allowWrite: ["/tmp"]`` is NOT sufficient confinement.
3. Parses ``.meas`` results from the ngspice log and checks each one named in the sidecar
   TOML against its declared limit (min/max, or equals+tol -- e.g. regulator output
   3.3 V +/- 2%, ripple, dissipation).
4. Writes one ``out/verify/spice.<name>.json`` per netlist via ``forge.checkresult.Check``.

Missing ``ngspice`` or ``srt`` -> exit 2 with the toolchain-install fix, never a fake pass.
No ``analysis/spice/*.cir`` files (or none match ``--changed``) -> exit 0, ``[SKIP] ...``.
Runs on ``forge-python`` (stdlib only needed here: no CAD libraries required).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lib"))

from forge.checkresult import Check  # noqa: E402  (path must be set up first)
from forge.tools import find_tool, forge_home, tool_env  # noqa: E402

try:
    import tomllib
except ImportError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]

_CONTROL_BLOCK = re.compile(r"(?is)\.control\b(.*?)\.endc\b")
_SHELL_CMD = re.compile(r"(?im)^\s*shell\b")
_MEAS_RESULT = re.compile(r"^(\S+)\s*=\s*([+-]?\d*\.?\d+(?:[eE][+-]?\d+)?)\b")
_NGSPICE_VERSION = re.compile(r"ngspice-([\w.]+)")


def refuses_shell(netlist_text: str) -> str | None:
    """Returns a reason string if the netlist must be refused, else None."""
    for m in _CONTROL_BLOCK.finditer(netlist_text):
        if _SHELL_CMD.search(m.group(1)):
            return "the .control block contains a 'shell' command, which runs /bin/sh -c"
    return None


def find_netlists(project: Path, changed: list[str] | None) -> list[Path]:
    spice_dir = project / "analysis" / "spice"
    if not spice_dir.exists():
        return []
    all_cir = sorted(spice_dir.glob("*.cir"))
    if changed is None:
        return all_cir
    changed_resolved = {Path(c).resolve() for c in changed}
    changed_strs = {Path(c).as_posix() for c in changed}
    out = []
    for cir in all_cir:
        limits = cir.with_name(cir.stem + ".limits.toml")
        if (cir.resolve() in changed_resolved or limits.resolve() in changed_resolved
                or any(s.startswith("analysis/spice") for s in changed_strs)):
            out.append(cir)
    return out


def load_measurement_specs(limits_path: Path) -> list[dict[str, Any]]:
    data = tomllib.loads(limits_path.read_text())
    return data.get("measurement", [])


def parse_meas_results(log_text: str) -> dict[str, float]:
    results: dict[str, float] = {}
    for line in log_text.splitlines():
        m = _MEAS_RESULT.match(line.strip())
        if m:
            try:
                results[m.group(1)] = float(m.group(2))
            except ValueError:
                continue
    return results


def ngspice_version(ngspice_path: str) -> str:
    try:
        proc = subprocess.run([ngspice_path, "-v"], capture_output=True, text=True, timeout=10)
        m = _NGSPICE_VERSION.search(proc.stdout + proc.stderr)
        return m.group(1) if m else "unknown"
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def _srt_settings(out_dir: Path, read_dir: Path | None = None) -> dict[str, Any]:
    deny_read = ["~/.ssh", "~/.aws", "~/.config/gh", "~/.netrc", "~/.npmrc",
                 "~/.pypirc", "~/Library/Keychains", "~/.gnupg"]
    allow_read: list[str] = []
    if sys.platform.startswith("linux"):
        # glibc's tmpfile() ignores TMPDIR and always uses /tmp, which srt/bwrap
        # mounts read-only ("tmpfile(): Read-only file system"). Denying /tmp makes
        # srt mount a private tmpfs there: ngspice gets scratch space, nothing it
        # writes reaches the host /tmp, and only the netlist directory is
        # re-allowed for reading (re-allowing the whole project would re-bind
        # out/verify read-only over its write grant).
        # (macOS tmpfile() honours TMPDIR, redirected into out/verify below.)
        deny_read.append("/tmp")
        if read_dir is not None:
            allow_read.append(str(read_dir))
    return {
        "network": {"allowedDomains": [], "deniedDomains": ["*"]},
        "filesystem": {
            "denyRead": deny_read,
            "allowRead": allow_read,
            # Confined to out/verify/ ONLY -- never the host's /tmp.
            "allowWrite": [str(out_dir)],
            "denyWrite": [],
        },
    }


def run_ngspice_sandboxed(cir: Path, project: Path, out_dir: Path, *, srt_path: str, ngspice_path: str) -> str:
    scratch = out_dir / f".spice-tmp-{cir.stem}"
    scratch.mkdir(parents=True, exist_ok=True)
    raw = out_dir / f"spice.{cir.stem}.raw"
    log = out_dir / f"spice.{cir.stem}.log"
    settings_fd, settings_file = tempfile.mkstemp(suffix=".json")
    try:
        with os.fdopen(settings_fd, "w") as fh:
            json.dump(_srt_settings(out_dir, cir.parent), fh)
        inner = (f"TMPDIR={scratch} SPICE_ASCIIRAWFILE=1 "
                 f"{ngspice_path} -b -n -r {raw} -o {log} {cir}")
        # srt itself needs bwrap/socat (Linux) from $FORGE_HOME/bin, which is not always on PATH.
        proc = subprocess.run([srt_path, "--settings", settings_file, "-c", inner],
                              capture_output=True, text=True, timeout=120, cwd=project, env=tool_env())
    finally:
        try:
            os.unlink(settings_file)
        except OSError:
            pass
    if not log.exists():
        raise RuntimeError(
            f"the ngspice sandbox (srt) produced no log (exit {proc.returncode}): "
            f"{(proc.stderr or proc.stdout or 'no output').strip()[:300]}")
    return log.read_text()


def verify_one(cir: Path, project: Path, out_dir: Path, *, srt_path: str, ngspice_path: str) -> int:
    check_id = f"spice.{cir.stem}"
    chk = Check(check_id, str(cir.relative_to(project)), project=project, level="L2")
    try:
        reason = refuses_shell(cir.read_text())
        if reason:
            raise RuntimeError(f"netlist refused, never executed: {reason}")
        limits_path = cir.with_name(cir.stem + ".limits.toml")
        if not limits_path.exists():
            raise RuntimeError(
                f"no sidecar {limits_path.name}; every analysis/spice/*.cir needs a "
                "[[measurement]] limits file (references/spice-limits-format.md)"
            )
        specs = load_measurement_specs(limits_path)
        if not specs:
            raise RuntimeError(f"{limits_path.name} declares no [[measurement]] entries")
        log_text = run_ngspice_sandboxed(cir, project, out_dir, srt_path=srt_path, ngspice_path=ngspice_path)
        chk.tool("ngspice", ngspice_version(ngspice_path))
        parsed = parse_meas_results(log_text)
        for spec in specs:
            name = spec.get("name")
            if not name:
                raise RuntimeError(f"{limits_path.name}: a [[measurement]] entry has no 'name'")
            unit = spec.get("unit", "1")
            value = parsed.get(name)
            if value is None:
                raise RuntimeError(
                    f"ngspice produced no '.meas' result named {name!r} for {cir.name} "
                    f"(check the .cir has a matching .meas line; log tail: "
                    f"{log_text.strip().splitlines()[-3:] if log_text else 'EMPTY LOG'})"
                )
            limit_kwargs: dict[str, Any] = {}
            for key in ("min", "max", "equals", "tol"):
                if key in spec:
                    limit_kwargs[key] = spec[key]
            remediation = spec.get(
                "remediation",
                f"{name} measured {value} {unit}, outside the limit declared in {limits_path.name} "
                f"(requirement {spec.get('requirement', '?')}). Adjust the design or the limit, with a source.",
            )
            chk.measure(name, value, unit, requirement=spec.get("requirement"),
                       remediation=remediation, **limit_kwargs)
        return chk.finish()
    except Exception as exc:  # noqa: BLE001 -- fail closed, one netlist's error must not kill the loop
        return chk.error(f"{type(exc).__name__}: {exc}")


def main(argv: list[str]) -> int:
    # Declares this entrypoint's check_id namespace so PostToolUse can bind a
    # fix message to the check that owns it, by check_id rather than which
    # out/verify/*.json file happens to have the newest mtime (M7, review #1).
    print("[FORGE_CHECK_ID_PREFIX] spice.")
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True, type=Path)
    ap.add_argument("--changed", nargs="*", default=None)
    ap.add_argument("--fast", action="store_true")
    ns = ap.parse_args(argv)
    project = ns.project.resolve()

    netlists = find_netlists(project, ns.changed)
    if not netlists:
        suffix = " matching --changed" if ns.changed is not None else ""
        print(f"[SKIP] no analysis/spice/*.cir files{suffix}")
        return 0

    ngspice_path = find_tool("ngspice")
    if not ngspice_path:
        print(f"[ERROR] ngspice not found in {forge_home() / 'bin'} or on PATH; run "
              "plugins/forge/toolchain/install.sh elec (R4b: brew install ngspice)", file=sys.stderr)
        return 2
    srt_path = find_tool("srt")
    if not srt_path:
        print("[ERROR] srt (sandbox-runtime) not found; run "
              "plugins/forge/toolchain/install.sh core (npm @anthropic-ai/sandbox-runtime)", file=sys.stderr)
        return 2

    out_dir = project / "out" / "verify"
    out_dir.mkdir(parents=True, exist_ok=True)

    codes = [verify_one(cir, project, out_dir, srt_path=srt_path, ngspice_path=ngspice_path) for cir in netlists]
    if any(c == 2 for c in codes):
        return 2
    if any(c == 1 for c in codes):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
