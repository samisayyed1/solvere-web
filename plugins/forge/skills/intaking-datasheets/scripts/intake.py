#!/usr/bin/env python3
"""Turn a datasheet's text into params/params.toml entries with a page reference, and,
where the datasheet is silent on a param, a caliper-measurement procedure.

Input is plain text -- either already extracted (``text_file``) or a PDF
(``--pdf``, converted with the system ``pdftotext -layout``, which is what
inserts the ``\\f`` page-break characters this script splits on). A datasheet
with no page breaks at all (a single pasted blob) cannot be cited with a
real page number -- the resulting param entry gets ``source = "<doc>, p.unknown"``,
which ``verify.py`` (CONTRACTS.md §2: "required, with a page ref for
datasheets") correctly fails, rather than silently accepting it.

    forge-python ${CLAUDE_SKILL_DIR}/scripts/intake.py --project <root> --spec docs/datasheets/<name>-intake.toml

Never invents a value: a pattern that doesn't match anywhere in the text
produces a measurement procedure in docs/measurements/, not a guessed number.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path


class IntakeError(RuntimeError):
    pass


def _load_text(spec: dict, spec_path: Path, project: Path) -> str:
    ds = spec["datasheet"]
    if "pdf" in ds:
        pdf_path = project / ds["pdf"]
        if not pdf_path.exists():
            raise IntakeError(f"{pdf_path} does not exist")
        try:
            r = subprocess.run(["pdftotext", "-layout", str(pdf_path), "-"],
                                capture_output=True, text=True, timeout=60, check=True)
        except FileNotFoundError as exc:
            raise IntakeError(
                "pdftotext not found on PATH (poppler). Install it, or pre-extract the PDF to text "
                "yourself and point [datasheet].text_file at it instead."
            ) from exc
        except subprocess.CalledProcessError as exc:
            raise IntakeError(f"pdftotext failed on {pdf_path}: {exc.stderr}") from exc
        return r.stdout
    if "text_file" in ds:
        text_path = project / ds["text_file"]
        if not text_path.exists():
            raise IntakeError(f"{text_path} does not exist")
        return text_path.read_text()
    raise IntakeError(f"{spec_path}: [datasheet] must set either 'pdf' or 'text_file'")


def _pages(text: str) -> list[str]:
    """Split on form-feed page breaks (pdftotext's convention); falls back to
    '[PAGE n]' markers; a document with neither is treated as one unnumbered page."""
    if "\f" in text:
        return text.split("\f")
    if re.search(r"\[PAGE\s+\d+\]", text):
        parts = re.split(r"\[PAGE\s+\d+\]", text)
        return [p for p in parts if p.strip()] or [text]
    return [text]


def extract(spec: dict, text: str) -> tuple[list[dict], list[dict]]:
    """Returns (matched, silent) param records."""
    pages = _pages(text)
    matched: list[dict] = []
    silent: list[dict] = []
    for p in spec.get("param", []):
        pattern = re.compile(p["pattern"])
        found = None
        for i, page_text in enumerate(pages, start=1):
            m = pattern.search(page_text)
            if m:
                page_no = i if len(pages) > 1 else None
                found = (page_no, m.group(1))
                break
        if found is None:
            silent.append(p)
            continue
        page_no, value_str = found
        matched.append({
            "id": p["id"], "value": float(value_str), "unit": p.get("unit", "1"),
            "tol_plus": p.get("tol_plus"), "tol_minus": p.get("tol_minus"),
            "page": page_no,
        })
    return matched, silent


def _toml_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def append_params(project: Path, doc: str, matched: list[dict]) -> list[str]:
    """Appends new [<id>] tables to params/params.toml (never overwrites an existing key)."""
    params_path = project / "params" / "params.toml"
    params_path.parent.mkdir(parents=True, exist_ok=True)
    existing_keys: set[str] = set()
    if params_path.exists():
        try:
            existing = tomllib.loads(params_path.read_text())
            def _walk(d: dict, prefix: str = ""):
                for k, v in d.items():
                    path = f"{prefix}.{k}" if prefix else k
                    if isinstance(v, dict) and "value" in v:
                        existing_keys.add(path)
                    elif isinstance(v, dict):
                        _walk(v, path)
            _walk(existing)
        except tomllib.TOMLDecodeError:
            pass  # a malformed params.toml is a different skill's problem; still append safely below

    added = []
    blocks = []
    for m in matched:
        if m["id"] in existing_keys:
            continue
        page_str = str(m["page"]) if m["page"] is not None else "unknown"
        source = f"{doc}, p.{page_str}"
        lines = [f'\n[{m["id"]}]', f'value = {m["value"]}', f'unit = "{_toml_escape(m["unit"])}"']
        if m.get("tol_plus") is not None and m.get("tol_minus") is not None:
            lines.append(f'tol = {{ minus = {m["tol_minus"]}, plus = {m["tol_plus"]} }}')
        lines += ['status = "datasheet"', f'source = "{_toml_escape(source)}"', 'verified_by = ""', "evidence = []"]
        blocks.append("\n".join(lines) + "\n")
        added.append(m["id"])

    if blocks:
        with params_path.open("a") as f:
            f.write("\n".join(blocks))
    return added


MEASUREMENT_TEMPLATE = """# Caliper measurement procedure: {param_id}

The datasheet ({doc}) does not state this value. Measure it directly rather
than assuming or inventing a number (docs/brief/FORGE-BRIEF.md §0).

- **What to measure:** {param_id} (units: {unit})
- **Instrument:** digital calipers, resolution 0.01 mm (or the appropriate instrument
  for this quantity if not a length -- update this line; a caliper procedure is the
  default template).
- **Number of samples:** 5 independent measurements, on 5 different physical units if
  more than one is available (or 5 repeat measurements at different points on the same
  unit if only one exists) -- record all 5, not just the mean.
- **How to record:** enter each sample in a table (sample #, value, unit, note), compute
  mean and standard deviation, and write the result into `params/params.toml` under
  `[{param_id}]` with `status = "measured"`, `source = "caliper measurement, see
  docs/measurements/{slug}.md"`, and (once a qualified human signs off) `status =
  "verified"` with `verified_by` and `evidence` filled in.

| Sample | Value ({unit}) | Note |
|---|---|---|
| 1 |  |  |
| 2 |  |  |
| 3 |  |  |
| 4 |  |  |
| 5 |  |  |

Mean:
Std dev:
"""


def write_measurement_procedures(project: Path, doc: str, silent: list[dict]) -> list[Path]:
    out_dir = project / "docs" / "measurements"
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for p in silent:
        slug = re.sub(r"[^a-z0-9_]+", "_", p["id"].lower()).strip("_")
        path = out_dir / f"{slug}.md"
        path.write_text(MEASUREMENT_TEMPLATE.format(
            param_id=p["id"], doc=doc, unit=p.get("unit", "1"), slug=slug,
        ))
        written.append(path)
    return written


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", type=Path, default=Path.cwd())
    ap.add_argument("--spec", type=Path, required=True)
    ns = ap.parse_args()
    project = ns.project.resolve()
    spec_path = ns.spec if ns.spec.is_absolute() else project / ns.spec

    try:
        spec = tomllib.loads(spec_path.read_text())
        doc = spec["datasheet"]["doc"]
        text = _load_text(spec, spec_path, project)
        matched, silent = extract(spec, text)
        added = append_params(project, doc, matched)
        measurement_files = write_measurement_procedures(project, doc, silent)
    except (IntakeError, KeyError, tomllib.TOMLDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    report = {
        "doc": doc, "spec": str(spec_path),
        "matched": [{"id": m["id"], "page": m["page"]} for m in matched],
        "added_to_params": added,
        "silent": [p["id"] for p in silent],
        "measurement_procedures": [str(p.relative_to(project)) for p in measurement_files],
    }
    report_dir = project / "out" / "intake"
    report_dir.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9_]+", "_", doc.lower()).strip("_")
    report_path = report_dir / f"{slug}.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")

    print(f"OK matched {len(matched)}/{len(matched) + len(silent)} params from {doc}; "
          f"{len(added)} new params added; {len(measurement_files)} measurement procedures written.")
    print(f"OK report: {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
