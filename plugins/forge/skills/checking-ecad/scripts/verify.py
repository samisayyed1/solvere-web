#!/usr/bin/env python3
"""checking-ecad verify entrypoint (CONTRACTS.md §9, elec domain: ERC/DRC + fab DFM).

    forge-python skills/checking-ecad/scripts/verify.py --project <root> [--changed <path> ...] [--fast]

For every `<stem>` under `ecad/` that has a `.kicad_sch` and/or `.kicad_pcb`:

1. Runs `kicad-cli sch erc --format json --exit-code-violations` and/or
   `kicad-cli pcb drc --format json --exit-code-violations` (never `--save-board`, so
   review mode can never mutate the board).
2. Counts violations by KiCad's `type` field, subtracts any covered by a valid waiver in
   `ecad/waivers.toml` (references/waivers-format.md), and fails on anything left over.
   A waiver missing `reason` or `approver` makes the whole check ERROR (rejected), never
   silently un-applied.
3. Runs `kicad-cli pcb export stats --format json` and checks the board's *measured*
   minima (track width, track clearance, drill diameter) against the fab-house floor in
   `references/fab_rules.toml` (numbers sourced to R5d), for whichever fab
   `params/params.toml`'s `[manufacturing] pcb_fab` names (default: "jlcpcb").

Human sign-off before fabrication is a separate, human gate (SKILL.md; enforced by the
release hook) -- this script only checks what a machine can check.

Missing `kicad-cli` -> exit 2 with the toolchain-install fix, never a fake pass.
No `ecad/*.kicad_sch`/`*.kicad_pcb` (or none match `--changed`) -> exit 0, `[SKIP] ...`.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lib"))

from forge.checkresult import Check  # noqa: E402

try:
    import tomllib
except ImportError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]

REFERENCES_DIR = Path(__file__).resolve().parents[1] / "references"
_NUMBER = re.compile(r"[-+]?\d*\.?\d+")
_NON_SLUG = re.compile(r"[^a-z0-9_]+")


def _slug(stem: str) -> str:
    """A board stem (which may contain spaces, e.g. a vendored KiCad demo) into a valid
    check_id segment: ``^[a-z0-9_]+$`` (forge.checkresult._CHECK_ID)."""
    slug = _NON_SLUG.sub("_", stem.lower()).strip("_")
    return slug or "board"


class EcadCheckError(RuntimeError):
    """A structural problem (bad waiver, missing tool) that must fail the whole check closed."""


def find_boards(project: Path) -> dict[str, dict[str, Path]]:
    """Returns ``{stem: {"sch": Path|None, "pcb": Path|None}}`` for every board under ecad/."""
    ecad_dir = project / "ecad"
    if not ecad_dir.exists():
        return {}
    boards: dict[str, dict[str, Path]] = {}
    for sch in sorted(ecad_dir.rglob("*.kicad_sch")):
        boards.setdefault(sch.stem, {})["sch"] = sch
    for pcb in sorted(ecad_dir.rglob("*.kicad_pcb")):
        boards.setdefault(pcb.stem, {})["pcb"] = pcb
    return boards


def filter_by_changed(boards: dict[str, dict[str, Path]], changed: list[str] | None) -> dict[str, dict[str, Path]]:
    if changed is None:
        return boards
    changed_resolved = {Path(c).resolve() for c in changed}
    changed_strs = {Path(c).as_posix() for c in changed}
    out = {}
    for stem, paths in boards.items():
        hit = any(p.resolve() in changed_resolved for p in paths.values())
        hit = hit or any(s.startswith("ecad/") for s in changed_strs)
        if hit:
            out[stem] = paths
    return out


def load_waivers(project: Path) -> list[dict[str, Any]]:
    path = project / "ecad" / "waivers.toml"
    if not path.exists():
        return []
    data = tomllib.loads(path.read_text())
    waivers = data.get("waiver", [])
    for w in waivers:
        reason = str(w.get("reason", "")).strip()
        approver = str(w.get("approver", "")).strip()
        if not reason or not approver:
            raise EcadCheckError(
                f"waiver for rule_id={w.get('rule_id', '?')!r} is missing 'reason' and/or "
                "'approver' -- rejected. Every waiver needs both (references/waivers-format.md)."
            )
    return waivers


def load_fab_rules(fab: str) -> dict[str, Any]:
    data = tomllib.loads((REFERENCES_DIR / "fab_rules.toml").read_text())
    if fab not in data:
        raise EcadCheckError(f"unknown pcb_fab {fab!r}; known fabs: {sorted(k for k in data if isinstance(data[k], dict))}")
    return data[fab]


def choose_fab(project: Path) -> str:
    params_path = project / "params" / "params.toml"
    if params_path.exists():
        try:
            data = tomllib.loads(params_path.read_text())
            fab = data.get("manufacturing", {}).get("pcb_fab")
            if fab:
                return str(fab)
        except Exception:  # noqa: BLE001 -- fall through to the default
            pass
    return "jlcpcb"


def run_kicad_cli(argv: list[str], *, timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(argv, capture_output=True, text=True, timeout=timeout)


def _flatten_violations(report: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalises both the ERC shape (``sheets[].violations[]``) and the DRC shape
    (top-level ``violations``/``unconnected_items``/``schematic_parity``) into one flat list."""
    out: list[dict[str, Any]] = []
    for sheet in report.get("sheets", []):
        out.extend(sheet.get("violations", []))
    for key in ("violations", "unconnected_items", "schematic_parity"):
        out.extend(report.get(key, []))
    return out


def apply_waivers(violations: list[dict[str, Any]], waivers: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Returns (unwaived violations, {rule_id: count actually waived})."""
    remaining_cap = {w["rule_id"]: w.get("max_count") for w in waivers}
    waived_ids = set(remaining_cap)
    unwaived: list[dict[str, Any]] = []
    waived_count: dict[str, int] = {}
    for v in violations:
        rid = v.get("type", "?")
        cap = remaining_cap.get(rid)
        if rid in waived_ids and (cap is None or waived_count.get(rid, 0) < cap):
            waived_count[rid] = waived_count.get(rid, 0) + 1
        else:
            unwaived.append(v)
    return unwaived, waived_count


def _num(text: str) -> float:
    m = _NUMBER.search(text)
    if not m:
        raise EcadCheckError(f"could not parse a number out of board-stats field {text!r}")
    return float(m.group())


def check_erc_drc(chk: Check, board_paths: dict[str, Path], project: Path, out_dir: Path,
                   waivers: list[dict[str, Any]], kicad_cli: str) -> None:
    if "sch" in board_paths:
        erc_json = out_dir / f"erc.{board_paths['sch'].stem}.json"
        run_kicad_cli([kicad_cli, "sch", "erc", "--format", "json", "--exit-code-violations",
                      "-o", str(erc_json), str(board_paths["sch"])])
        report = json.loads(erc_json.read_text()) if erc_json.exists() else {}
        violations = _flatten_violations(report)
        unwaived, waived = apply_waivers(violations, waivers)
        errors = sum(1 for v in unwaived if v.get("severity") == "error")
        warnings = sum(1 for v in unwaived if v.get("severity") != "error")
        remediation = (
            f"{len(unwaived)} unwaived ERC violation(s) (of {len(violations)} total, "
            f"{sum(waived.values())} waived). Fix them, or add a reasoned, approved waiver "
            "in ecad/waivers.toml (references/waivers-format.md)."
        )
        chk.measure("erc_errors", errors, "1", max=0, requirement=None, location=str(board_paths["sch"]),
                   remediation=remediation)
        chk.measure("erc_warnings", warnings, "1", max=0, requirement=None, location=str(board_paths["sch"]),
                   remediation=remediation)

    if "pcb" in board_paths:
        drc_json = out_dir / f"drc.{board_paths['pcb'].stem}.json"
        run_kicad_cli([kicad_cli, "pcb", "drc", "--format", "json", "--exit-code-violations",
                      "-o", str(drc_json), str(board_paths["pcb"])])  # never --save-board
        report = json.loads(drc_json.read_text()) if drc_json.exists() else {}
        violations = _flatten_violations(report)
        unwaived, waived = apply_waivers(violations, waivers)
        errors = sum(1 for v in unwaived if v.get("severity") == "error")
        warnings = sum(1 for v in unwaived if v.get("severity") != "error")
        remediation = (
            f"{len(unwaived)} unwaived DRC violation(s) (of {len(violations)} total, "
            f"{sum(waived.values())} waived). Fix them, or add a reasoned, approved waiver "
            "in ecad/waivers.toml (references/waivers-format.md)."
        )
        chk.measure("drc_errors", errors, "1", max=0, requirement=None, location=str(board_paths["pcb"]),
                   remediation=remediation)
        chk.measure("drc_warnings", warnings, "1", max=0, requirement=None, location=str(board_paths["pcb"]),
                   remediation=remediation)


def check_fab_dfm(chk: Check, pcb: Path, out_dir: Path, fab: str, fab_rules: dict[str, Any], kicad_cli: str) -> None:
    stats_json = out_dir / f"stats.{pcb.stem}.json"
    run_kicad_cli([kicad_cli, "pcb", "export", "stats", "--format", "json", "--units", "mm",
                   "-o", str(stats_json), str(pcb)])
    if not stats_json.exists():
        raise EcadCheckError(f"kicad-cli pcb export stats produced no output for {pcb}")
    stats = json.loads(stats_json.read_text())["board"]

    pairs = [
        ("min_track_width", "min_track_width_mm", "mm"),
        ("min_track_clearance", "min_track_clearance_mm", "mm"),
        ("min_drill_diameter", "min_drill_diameter_mm", "mm"),
    ]
    for stats_key, rule_key, unit in pairs:
        if stats_key not in stats or rule_key not in fab_rules:
            continue
        measured = _num(stats[stats_key])
        floor = float(fab_rules[rule_key])
        chk.measure(
            f"dfm_{stats_key}", measured, unit, min=floor, location=str(pcb),
            remediation=(
                f"{stats_key.replace('_', ' ')} is {measured} {unit}, below the {fab} floor of "
                f"{floor} {unit} ({fab_rules.get('source', 'references/fab_rules.toml')}). "
                "Widen the feature, or choose a different fab tier with a sourced update to fab_rules.toml."
            ),
        )


def verify_board(stem: str, board_paths: dict[str, Path], project: Path, out_dir: Path,
                  waivers: list[dict[str, Any]], fab: str, fab_rules: dict[str, Any], kicad_cli: str) -> int:
    chk = Check(f"ecad.{_slug(stem)}", f"ecad/{stem}", project=project, level="L1")
    try:
        check_erc_drc(chk, board_paths, project, out_dir, waivers, kicad_cli)
        if "pcb" in board_paths:
            check_fab_dfm(chk, board_paths["pcb"], out_dir, fab, fab_rules, kicad_cli)
        return chk.finish()
    except Exception as exc:  # noqa: BLE001 -- fail closed
        return chk.error(f"{type(exc).__name__}: {exc}")


def main(argv: list[str]) -> int:
    # Declares this entrypoint's check_id namespace so PostToolUse can bind a
    # fix message to the check that owns it, by check_id rather than which
    # out/verify/*.json file happens to have the newest mtime (M7, review #1).
    print("[FORGE_CHECK_ID_PREFIX] ecad.")
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True, type=Path)
    ap.add_argument("--changed", nargs="*", default=None)
    ap.add_argument("--fast", action="store_true")
    ns = ap.parse_args(argv)
    project = ns.project.resolve()

    boards = filter_by_changed(find_boards(project), ns.changed)
    if not boards:
        suffix = " matching --changed" if ns.changed is not None else ""
        print(f"[SKIP] no ecad/*.kicad_sch or *.kicad_pcb{suffix}")
        return 0

    kicad_cli = shutil.which("kicad-cli") or str(Path.home() / ".forge" / "bin" / "kicad-cli")
    if not Path(kicad_cli).exists() and not shutil.which("kicad-cli"):
        print("[ERROR] kicad-cli not found; run plugins/forge/toolchain/install.sh elec "
              "(brew install --cask kicad)", file=sys.stderr)
        return 2

    out_dir = project / "out" / "verify"
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        waivers = load_waivers(project)
    except EcadCheckError as exc:
        # A malformed waivers.toml is a structural failure for every board in this run.
        chk = Check("ecad.waivers", "ecad/waivers.toml", project=project, level="L1")
        return chk.error(str(exc))

    fab = choose_fab(project)
    try:
        fab_rules = load_fab_rules(fab)
    except EcadCheckError as exc:
        chk = Check("ecad.fab_rules", "params/params.toml", project=project, level="L1")
        return chk.error(str(exc))

    codes = [
        verify_board(stem, paths, project, out_dir, waivers, fab, fab_rules, kicad_cli)
        for stem, paths in sorted(boards.items())
    ]
    if any(c == 2 for c in codes):
        return 2
    if any(c == 1 for c in codes):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
