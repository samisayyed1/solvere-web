#!/usr/bin/env python3
"""SysML v2 textual model validity, via ``spec42 check`` (CONTRACTS §9).

Invocation:
    forge-python skills/modeling-systems/scripts/verify.py --project <root> [--changed <path> ...] [--fast]

Runs ``spec42 check --format json --warnings-as-errors`` over every
``model/**/*.sysml`` file and turns each diagnostic into a measurement under
check_id ``systems.sysml_check``. A file with zero errors and zero warnings
passes; anything else -- a parse error, an unresolved reference, a warning --
fails, because ``--warnings-as-errors`` is always on (CONTRACTS §9 table:
"spec42 check", builder brief: "with --warnings-as-errors").

If the ``spec42`` binary is missing, this exits 2 (never a silent pass) with
the fix, per CONTRACTS §10.

Standard library only (subprocess + json).
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lib"))

from forge.checkresult import Check, CheckContractError  # noqa: E402
from forge.tools import find_tool, forge_home  # noqa: E402

MODEL_REL = Path("model")
CHECK_ID = "systems.sysml_check"


def _find_spec42() -> str | None:
    return find_tool("spec42")


def _severity_name(sev: int) -> str:
    return {1: "error", 2: "warning", 3: "information", 4: "hint"}.get(sev, f"severity{sev}")


_COMMENT_BLOCK_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
_COMMENT_LINE_RE = re.compile(r"//[^\n]*")


def _has_definitions(text: str) -> bool:
    """False for an empty file or one containing only comments/whitespace.

    spec42 reports zero diagnostics for such a file -- there is nothing to
    be wrong with -- which used to read as a clean PASS (S4). A model file
    with no actual definition is not verified; it is empty."""
    stripped = _COMMENT_BLOCK_RE.sub("", text)
    stripped = _COMMENT_LINE_RE.sub("", stripped)
    return bool(stripped.strip())


def run(project: Path, changed: list[str] | None) -> int:
    model_dir = project / MODEL_REL
    if not model_dir.exists():
        print(f"[SKIP] no {MODEL_REL}/ in this project")
        return 0
    sysml_files = sorted(model_dir.rglob("*.sysml"))
    if changed:
        changed_resolved = {Path(c).resolve() for c in changed}
        sysml_files = [f for f in sysml_files if f.resolve() in changed_resolved]
        if not sysml_files:
            print("[SKIP] no changed *.sysml files under model/")
            return 0
    if not sysml_files:
        print(f"[SKIP] no *.sysml files under {MODEL_REL}/")
        return 0

    spec42 = _find_spec42()
    chk = Check(CHECK_ID, str(MODEL_REL), level="L1", project=project)
    if spec42 is None:
        return chk.error(
            "spec42 not found on PATH or at ~/.forge/bin/spec42. Install it: "
            "plugins/forge/toolchain/install.sh systems (CONTRACTS §10)."
        )

    proc = subprocess.run(
        [spec42, "check", str(model_dir), "--format", "json", "--warnings-as-errors"],
        capture_output=True, text=True, timeout=120,
    )
    chk.tool("spec42", _spec42_version(spec42))

    try:
        report = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return chk.error(
            f"spec42 check did not return valid JSON (exit {proc.returncode}). "
            f"stderr: {proc.stderr.strip()[:500]}"
        )

    documents = report.get("documents", [])
    if not documents:
        return chk.error("spec42 check returned no documents; check model/ contains valid *.sysml files")

    for doc in documents:
        uri = doc.get("uri", "")
        rel = _uri_to_rel(uri, project)
        diags = doc.get("diagnostics", [])
        errors_or_warnings = [d for d in diags if d.get("severity", 3) in (1, 2)]

        file_path = project / rel
        text = file_path.read_text() if file_path.exists() else ""
        if not _has_definitions(text):
            chk.measure(
                f"{rel}.has_definitions", False, "1", equals=True, location=rel,
                remediation=(
                    f"{rel} has no definitions -- it is empty or contains only comments. "
                    "A model file must define at least one package/part/requirement/etc.; "
                    "add real model content or remove the empty file."
                ),
            )
            continue

        clean = not errors_or_warnings
        if clean:
            chk.measure(f"{rel}.clean", True, "1", equals=True, location=rel)
        else:
            for d in errors_or_warnings:
                line = d.get("range", {}).get("start", {}).get("line", 0) + 1
                col = d.get("range", {}).get("start", {}).get("character", 0) + 1
                sev = _severity_name(d.get("severity", 1))
                code = d.get("code", "unknown")
                msg = d.get("message", "")
                chk.measure(
                    f"{rel}.{code}.L{line}C{col}", False, "1", equals=True, location=f"{rel}:{line}:{col}",
                    remediation=(
                        f"spec42 {sev} [{code}] at {rel}:{line}:{col}: {msg}. Fix the model "
                        f"({sev} severity is treated as a failure -- --warnings-as-errors)."
                    ),
                )

    return chk.finish()


def _spec42_version(spec42_bin: str) -> str:
    try:
        out = subprocess.run([spec42_bin, "--version"], capture_output=True, text=True, timeout=10)
        return (out.stdout or out.stderr).strip() or "unknown"
    except Exception:  # noqa: BLE001
        return "unknown"


def _uri_to_rel(uri: str, project: Path) -> str:
    path = uri
    if path.startswith("file://"):
        path = path[len("file://"):]
    try:
        return str(Path(path).resolve().relative_to(project.resolve()))
    except ValueError:
        return path


def main(argv: list[str]) -> int:
    # Declares this entrypoint's check_id namespace so PostToolUse can bind a
    # fix message to the check that owns it, by check_id rather than which
    # out/verify/*.json file happens to have the newest mtime (M7, review #1).
    print(f"[FORGE_CHECK_ID_PREFIX] {CHECK_ID}")
    project = Path(".")
    changed: list[str] = []
    i = 0
    while i < len(argv):
        if argv[i] == "--project":
            project = Path(argv[i + 1]); i += 2
        elif argv[i] == "--changed":
            changed.append(argv[i + 1]); i += 2
        elif argv[i] == "--fast":
            i += 1
        else:
            i += 1
    try:
        return run(project.resolve(), changed or None)
    except CheckContractError as exc:
        print(f"[ERROR] {CHECK_ID}: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001 -- fail closed
        print(f"[ERROR] {CHECK_ID}: internal error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
