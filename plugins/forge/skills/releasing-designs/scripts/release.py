#!/usr/bin/env python3
"""releasing-designs: build a versioned release bundle (CONTRACTS.md §13, brief §3.3).

    forge-python skills/releasing-designs/scripts/release.py --project <root> [--version V]

Refuses (exit 1) unless:

1. ``release/APPROVAL.toml`` exists, has every required field, and its ``git_sha`` matches
   ``git rev-parse HEAD`` in the project exactly (a stale approval -- from before the last
   commit -- is rejected, not just a missing one).
2. The gate record it names (``reviews/<gate>.md``) has a **filled** human sign-off line
   (CONTRACTS.md §7) whose Decision is unambiguously ``PASS`` -- not the blank template,
   and not a ``FAIL``.
3. ``evidence/manifest.json`` has no ``UNVERIFIED`` entry and no entry recording
   ``result: "fail"``, and ``out/verify/*.json`` has no ``fail``/``error`` check result
   (ADR-001 SS11, M9 review #1: "UNVERIFIED evidence blocks gates and releases").

Only then does it build ``release/<version>/``: STEP/STL/drawings (if `out/cad/` has any),
Gerbers/drill/pos via ``kicad-cli`` (for every ``ecad/*.kicad_pcb``), the BOM (if `bom/`
has any), firmware binaries with sha256 (if `out/verify/fw_build/` has any), test reports
and the evidence manifest, a changelog, and the git SHA. A category with nothing to bundle
is *noted*, not silently skipped, in ``RELEASE-MANIFEST.json``.

This is a side-effect script (``disable-model-invocation: true`` on the owning skill) --
it is never invoked by the model without the user asking for a release, and it is exit-2
fail-closed on any internal error: it never produces a bundle it can't fully account for.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lib"))

from forge.checkresult import git_sha as _repo_git_sha  # noqa: E402

try:
    import tomllib
except ImportError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]

_SIGNOFF_LINE = re.compile(r"Human sign-off:.*$", re.MULTILINE)
_BLANK_RUN = re.compile(r"_{3,}")
_DECISION = re.compile(r"Decision:\s*(PASS|FAIL)\b(?!\s*/)")


class ReleaseRefused(RuntimeError):
    """A normal, expected reason a release cannot proceed yet (exit 1, not 2)."""


def _read_toml(path: Path) -> dict[str, Any]:
    return tomllib.loads(path.read_text())


def gate_signed_off(gate_md_text: str) -> tuple[bool, str]:
    """Returns (is_filled_and_unambiguous, decision_or_reason)."""
    m = _SIGNOFF_LINE.search(gate_md_text)
    if not m:
        return False, "no 'Human sign-off:' line found in the gate record"
    line = m.group(0)
    if _BLANK_RUN.search(line):
        return False, "sign-off line still has the blank underscore placeholder"
    dec = _DECISION.search(line)
    if not dec:
        return False, "sign-off line has no unambiguous 'Decision: PASS' or 'Decision: FAIL'"
    return True, dec.group(1)


def check_evidence_clean(project: Path) -> None:
    """Refuses (``ReleaseRefused``) when the evidence trail is not clean.

    ADR-001 SS11 / PROGRESS.md M9 (review #1): "UNVERIFIED evidence blocks
    gate records and releases", but nothing enforced it -- ``forge evidence
    add`` could write an UNVERIFIED entry (an error check, or a manifest a
    human hand-edited) and release.py never looked at it. This checks both
    of the release's evidence sources:

    1. ``evidence/manifest.json``: any entry with ``status: "UNVERIFIED"``,
       or any entry recording ``result: "fail"``, blocks the release.
    2. ``out/verify/*.json`` (``forge.check/1`` results): any check whose
       ``status`` is ``fail`` or ``error`` blocks the release, even if it
       was never rolled up into an evidence entry at all -- a release must
       never ship past a check nobody journaled.
    """
    manifest_path = project / "evidence" / "manifest.json"
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            raise ReleaseRefused(f"{manifest_path} is not valid JSON: {exc}") from exc
        for entry in manifest.get("entries", []) if isinstance(manifest, dict) else []:
            if not isinstance(entry, dict):
                continue
            entry_id = entry.get("id", "?")
            artifact = entry.get("artifact", "?")
            if entry.get("status") == "UNVERIFIED":
                raise ReleaseRefused(
                    f"evidence/manifest.json entry {entry_id!r} ({artifact}) is UNVERIFIED -- "
                    "ADR-001 SS11: UNVERIFIED evidence blocks releases. Re-run the check(s) so the "
                    "entry records a real, passing result, or remove the stale entry."
                )
            if entry.get("result") == "fail":
                raise ReleaseRefused(
                    f"evidence/manifest.json entry {entry_id!r} ({artifact}) records a failing "
                    "result -- fix the underlying issue and re-verify before releasing."
                )

    verify_dir = project / "out" / "verify"
    if verify_dir.is_dir():
        for f in sorted(verify_dir.glob("*.json")):
            try:
                data = json.loads(f.read_text())
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(data, dict) or data.get("schema") != "forge.check/1":
                continue
            status = data.get("status")
            if status in ("fail", "error"):
                rel = f.relative_to(project)
                raise ReleaseRefused(
                    f"{rel} is a {status.upper()} check result (check_id "
                    f"{data.get('check_id', '?')!r}) -- fix and re-run it before releasing."
                )


def head_sha(project: Path) -> str:
    proc = subprocess.run(["git", "-C", str(project), "rev-parse", "HEAD"],
                          capture_output=True, text=True, timeout=10)
    if proc.returncode != 0:
        raise ReleaseRefused(f"could not read git HEAD for {project}: {proc.stderr.strip()}")
    return proc.stdout.strip()


def check_approval(project: Path) -> dict[str, Any]:
    """Returns the parsed, validated APPROVAL.toml, or raises ReleaseRefused."""
    approval_path = project / "release" / "APPROVAL.toml"
    if not approval_path.exists():
        raise ReleaseRefused(
            f"{approval_path} is missing. A human must create it (approved_by, date, "
            "git_sha, scope, gate) before any release -- CONTRACTS.md §13."
        )
    try:
        data = _read_toml(approval_path)
    except Exception as exc:  # noqa: BLE001
        raise ReleaseRefused(f"{approval_path} is not valid TOML: {exc}") from exc

    required = ("approved_by", "date", "git_sha", "scope", "gate")
    missing = [f for f in required if not str(data.get(f, "")).strip()]
    if missing:
        raise ReleaseRefused(f"{approval_path} is missing required field(s): {', '.join(missing)}")

    sha = head_sha(project)
    if str(data["git_sha"]) != sha:
        raise ReleaseRefused(
            f"{approval_path} git_sha {data['git_sha']!r} does not match HEAD {sha!r} -- "
            "the approval is stale (the repo moved since it was signed). Get a fresh approval."
        )

    gate = str(data["gate"])
    gate_md = project / "reviews" / f"{gate}.md"
    if not gate_md.exists():
        raise ReleaseRefused(f"reviews/{gate}.md not found for the approved gate {gate!r}")
    signed, info = gate_signed_off(gate_md.read_text())
    if not signed:
        raise ReleaseRefused(f"reviews/{gate}.md is not signed off: {info}")
    if info != "PASS":
        raise ReleaseRefused(f"reviews/{gate}.md was signed off as {info}, not PASS")

    return data


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _copy_if_any(patterns: list[str], src_root: Path, dest: Path) -> list[str]:
    dest.mkdir(parents=True, exist_ok=True)
    copied = []
    for pattern in patterns:
        for f in sorted(src_root.glob(pattern)):
            if f.is_file():
                shutil.copy2(f, dest / f.name)
                copied.append(f.name)
    return copied


def bundle_ecad(project: Path, release_dir: Path, kicad_cli: str | None) -> dict[str, Any]:
    ecad_dir = project / "ecad"
    boards = sorted(ecad_dir.rglob("*.kicad_pcb")) if ecad_dir.exists() else []
    if not boards:
        return {"status": "skipped", "reason": "no ecad/*.kicad_pcb found"}
    if not kicad_cli:
        return {"status": "skipped", "reason": "kicad-cli not found on this machine"}
    per_board = {}
    for pcb in boards:
        out = release_dir / "ecad" / pcb.stem
        out.mkdir(parents=True, exist_ok=True)
        gerbers = out / "gerbers"
        drill = out / "drill"
        pos = out / f"{pcb.stem}.pos"
        subprocess.run([kicad_cli, "pcb", "export", "gerbers", "-o", str(gerbers), str(pcb)],
                       capture_output=True, text=True, timeout=120)
        subprocess.run([kicad_cli, "pcb", "export", "drill", "-o", str(drill), str(pcb)],
                       capture_output=True, text=True, timeout=120)
        subprocess.run([kicad_cli, "pcb", "export", "pos", "-o", str(pos), str(pcb)],
                       capture_output=True, text=True, timeout=120)
        per_board[pcb.stem] = {
            "gerbers": gerbers.exists(), "drill": drill.exists(), "pos": pos.exists(),
        }
    return {"status": "included", "boards": per_board}


def bundle_cad(project: Path, release_dir: Path) -> dict[str, Any]:
    cad_out = project / "out" / "cad"
    if not cad_out.exists():
        return {"status": "skipped", "reason": "no out/cad/ (mechanical-engineer hasn't exported yet)"}
    copied = _copy_if_any(["*.step", "*.stp", "*.stl", "*.pdf"], cad_out, release_dir / "cad")
    if not copied:
        return {"status": "skipped", "reason": "out/cad/ has no .step/.stp/.stl/.pdf"}
    return {"status": "included", "files": copied}


def bundle_bom(project: Path, release_dir: Path) -> dict[str, Any]:
    bom_dir = project / "bom"
    if not bom_dir.exists():
        return {"status": "skipped", "reason": "no bom/ directory"}
    copied = _copy_if_any(["*.csv", "*.json"], bom_dir, release_dir / "bom")
    if not copied:
        return {"status": "skipped", "reason": "bom/ has no .csv/.json"}
    return {"status": "included", "files": copied}


def bundle_firmware(project: Path, release_dir: Path) -> dict[str, Any]:
    fw_build = project / "out" / "verify" / "fw_build"
    if not fw_build.exists():
        return {"status": "skipped", "reason": "no out/verify/fw_build/ (build firmware first)"}
    binaries = [p for p in sorted(fw_build.iterdir())
                if p.is_file() and not p.suffix and not p.name.startswith(".")]
    if not binaries:
        return {"status": "skipped", "reason": "out/verify/fw_build/ has no binaries"}
    dest = release_dir / "firmware"
    dest.mkdir(parents=True, exist_ok=True)
    sums = []
    for b in binaries:
        shutil.copy2(b, dest / b.name)
        sums.append(f"{_sha256(b)}  {b.name}")
    (dest / "SHA256SUMS").write_text("\n".join(sums) + "\n")
    return {"status": "included", "files": [b.name for b in binaries]}


def bundle_evidence(project: Path, release_dir: Path) -> dict[str, Any]:
    manifest = project / "evidence" / "manifest.json"
    dest = release_dir / "evidence"
    dest.mkdir(parents=True, exist_ok=True)
    included = {}
    if manifest.exists():
        shutil.copy2(manifest, dest / "manifest.json")
        included["manifest"] = True
    else:
        included["manifest"] = False
    checks = _copy_if_any(["*.json"], project / "out" / "verify", dest / "checks")
    included["check_reports"] = checks
    status = "included" if (included["manifest"] or checks) else "skipped"
    result = {"status": status, **included}
    if status == "skipped":
        result["reason"] = "no evidence/manifest.json and no out/verify/*.json check reports"
    return result


def bundle_changelog(project: Path, release_dir: Path) -> dict[str, Any]:
    for name in ("CHANGELOG.md", "CHANGELOG.txt"):
        src = project / name
        if src.exists():
            shutil.copy2(src, release_dir / name)
            return {"status": "included", "file": name}
    return {"status": "skipped", "reason": "no CHANGELOG.md/.txt at the project root"}


def build_bundle(project: Path, version: str, approval: dict[str, Any]) -> Path:
    release_dir = project / "release" / version
    release_dir.mkdir(parents=True, exist_ok=True)

    kicad_cli = shutil.which("kicad-cli") or str(Path.home() / ".forge" / "bin" / "kicad-cli")
    if not Path(kicad_cli).exists() and not shutil.which("kicad-cli"):
        kicad_cli = None

    parts = {
        "cad": bundle_cad(project, release_dir),
        "ecad": bundle_ecad(project, release_dir, kicad_cli),
        "bom": bundle_bom(project, release_dir),
        "firmware": bundle_firmware(project, release_dir),
        "evidence": bundle_evidence(project, release_dir),
        "changelog": bundle_changelog(project, release_dir),
    }
    sha = head_sha(project)
    (release_dir / "GIT_SHA.txt").write_text(sha + "\n")

    manifest = {
        "schema": "forge.release/1",
        "version": version,
        "git_sha": sha,
        "approval": approval,
        "parts": parts,
    }
    (release_dir / "RELEASE-MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return release_dir


def default_version(project: Path) -> str:
    proc = subprocess.run(["git", "-C", str(project), "describe", "--tags", "--always", "--dirty"],
                          capture_output=True, text=True, timeout=10)
    if proc.returncode == 0 and proc.stdout.strip():
        return proc.stdout.strip()
    return _repo_git_sha(project)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True, type=Path)
    ap.add_argument("--version", default=None)
    ns = ap.parse_args(argv)
    project = ns.project.resolve()

    try:
        approval = check_approval(project)
        check_evidence_clean(project)
    except ReleaseRefused as exc:
        print(f"[REFUSED] releasing-designs: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 -- fail closed on anything unexpected
        print(f"[ERROR] releasing-designs: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    version = ns.version or default_version(project)
    try:
        release_dir = build_bundle(project, version, approval)
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] releasing-designs: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    print(f"[OK] release bundle written to {release_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
