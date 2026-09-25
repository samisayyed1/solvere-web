#!/usr/bin/env python3
"""Verify entrypoint for intaking-datasheets (CONTRACTS.md §9, §2).

For each ``docs/datasheets/<name>-intake.toml``: runs the intake, then
checks that every matched param landed in ``params/params.toml`` with
``status = "datasheet"`` and a **real page reference** (CONTRACTS.md §2:
"required, with a page ref for datasheets") -- a param sourced from a
datasheet with no page marker (``p.unknown``) is a seeded-wrong case this
check must FAIL, not accept -- and that every param the datasheet was
silent on has a caliper-measurement procedure written under
``docs/measurements/``.

    forge-python skills/intaking-datasheets/scripts/verify.py --project <root> [--changed <path> ...]
"""
from __future__ import annotations

import argparse
import re
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lib"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from forge.checkresult import Check, CheckContractError  # noqa: E402
from intake import IntakeError, _load_text, append_params, extract, write_measurement_procedures  # noqa: E402

_SAFE = re.compile(r"[^a-z0-9_]+")
_PAGE_REF = re.compile(r"p\.\s*\d+")


def _safe_name(name: str) -> str:
    slug = _SAFE.sub("_", name.strip().lower()).strip("_")
    return slug or "datasheet"


def _find_spec_files(project: Path, changed: list[str]) -> list[Path]:
    ds_dir = project / "docs" / "datasheets"
    if changed:
        out = []
        for c in changed:
            p = (project / c).resolve() if not Path(c).is_absolute() else Path(c)
            try:
                p.relative_to(ds_dir.resolve())
            except ValueError:
                continue
            if p.name.endswith("-intake.toml") and p.exists():
                out.append(p)
        return sorted(out)
    if not ds_dir.is_dir():
        return []
    return sorted(ds_dir.glob("*-intake.toml"))


def _read_params(project: Path) -> dict:
    params_path = project / "params" / "params.toml"
    if not params_path.exists():
        return {}
    try:
        return tomllib.loads(params_path.read_text())
    except tomllib.TOMLDecodeError:
        return {}


def _lookup(params: dict, dotted_id: str) -> dict | None:
    node = params
    for part in dotted_id.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node if isinstance(node, dict) and "value" in node else None


def _run_one(spec_path: Path, project: Path) -> int:
    try:
        spec = tomllib.loads(spec_path.read_text())
        doc = spec["datasheet"]["doc"]
    except (tomllib.TOMLDecodeError, KeyError) as exc:
        chk = Check(f"mech.datasheet_{_safe_name(spec_path.stem)}", str(spec_path), level="L1", project=project)
        return chk.error(f"{spec_path}: invalid spec: {exc}")

    check_id = f"mech.datasheet_{_safe_name(doc)}"
    target = str(spec_path.relative_to(project)) if spec_path.is_relative_to(project) else str(spec_path)
    chk = Check(check_id, target, level="L1", project=project)

    try:
        text = _load_text(spec, spec_path, project)
        matched, silent, unit_mismatches = extract(spec, text)
        append_params(project, doc, matched)
        write_measurement_procedures(project, doc, silent)

        params = _read_params(project)
        bad_source = []
        missing_entry = []
        for m in matched:
            entry = _lookup(params, m["id"])
            if entry is None:
                missing_entry.append(m["id"])
                continue
            if entry.get("status") != "datasheet":
                bad_source.append(m["id"])
                continue
            source = entry.get("source", "")
            if not _PAGE_REF.search(source):
                bad_source.append(m["id"])

        chk.measure(
            "matched_params_in_params_toml", len(matched) - len(missing_entry), "1",
            min=len(matched) if matched else 0,
            remediation=(
                f"Param(s) {missing_entry} matched the datasheet but are not present in "
                f"params/params.toml. Re-run intake.py --spec {spec_path.name}."
            ),
        ) if matched else None
        chk.measure(
            "datasheet_params_have_page_ref", len(matched) - len(bad_source), "1",
            min=len(matched) if matched else 0,
            remediation=(
                f"Param(s) {bad_source} in params/params.toml have status != 'datasheet' or a source "
                "string with no page reference (expected 'p.<N>'). A datasheet-sourced value without a "
                "real page number cannot be checked by a human later -- fix the intake spec's page "
                "markers (form-feed '\\f' or '[PAGE n]') in the source text, or the param's source."
            ),
        ) if matched else None

        missing_procedures = []
        for p in silent:
            slug = re.sub(r"[^a-z0-9_]+", "_", p["id"].lower()).strip("_")
            if not (project / "docs" / "measurements" / f"{slug}.md").exists():
                missing_procedures.append(p["id"])
        chk.measure(
            "silent_params_have_measurement_procedure", len(silent) - len(missing_procedures), "1",
            min=len(silent) if silent else 0,
            remediation=(
                f"Param(s) {missing_procedures} are not in the datasheet, but have no caliper-measurement "
                f"procedure under docs/measurements/. Re-run intake.py --spec {spec_path.name}."
            ),
        ) if silent else None

        # S13 (review-2 addendum): the unit is captured from the datasheet text itself and
        # compared to the spec's declared unit (intake.extract's _units_agree), not just
        # trusted from the pattern author's `unit = "..."` field. A mismatched param is
        # never written to params.toml (see intake.append_params's matched-only input).
        chk.measure(
            "matched_params_unit_agrees_with_text", len(unit_mismatches), "1", max=0,
            remediation=(
                "Param(s) matched a number in the datasheet text whose unit disagrees with the "
                "intake spec's declared unit -- never written to params.toml: "
                + "; ".join(f"{u['id']}: text shows {u['text_unit']!r}, spec declares {u['declared_unit']!r}"
                            for u in unit_mismatches)
                + f". Fix the pattern or the unit in {spec_path.name} -- never guess which is right."
            ) if unit_mismatches else None,
        ) if (matched or unit_mismatches) else None

        if not matched and not silent and not unit_mismatches:
            return chk.error(f"{spec_path}: [[param]] list is empty -- nothing to intake or check")

        return chk.finish(notes=(
            f"{len(matched)} matched, {len(silent)} silent (measurement procedures written), "
            f"{len(unit_mismatches)} unit mismatch(es) from {doc!r}."
        ))
    except (IntakeError, CheckContractError) as exc:
        return chk.error(str(exc))
    except Exception as exc:  # noqa: BLE001 -- fail closed, never a silent pass
        return chk.error(f"{type(exc).__name__}: {exc}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", type=Path, default=Path.cwd())
    ap.add_argument("--changed", action="append", default=[])
    ap.add_argument("--fast", action="store_true")
    ns = ap.parse_args()
    project = ns.project.resolve()

    spec_files = _find_spec_files(project, ns.changed)
    if not spec_files:
        print("[SKIP] no docs/datasheets/*-intake.toml files to check")
        return 0

    worst = 0
    for path in spec_files:
        rc = _run_one(path, project)
        worst = max(worst, rc)
    return worst


if __name__ == "__main__":
    sys.exit(main())
