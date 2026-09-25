"""Append-only evidence manifest (CONTRACTS.md §4, schema ``forge.evidence/1``).

``evidence/manifest.json`` in a product repo records every result-bearing claim
with its credibility level. Entries are never edited or removed; a newer entry
supersedes an older one for the same artifact. Standard library only.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import time
from pathlib import Path
from typing import Any, Iterable

from .checkresult import LEVELS, git_sha

SCHEMA = "forge.evidence/1"
DOMAINS = ("mech", "elec", "fw", "sw", "sys", "sim", "mfg", "compliance")
MANIFEST = Path("evidence/manifest.json")
_ID = re.compile(r"^EV-(\d{4,})$")


class EvidenceError(ValueError):
    """An entry violates the evidence contract."""


def manifest_path(project: Path) -> Path:
    return Path(project) / MANIFEST


def load(project: Path) -> dict[str, Any]:
    path = manifest_path(project)
    if not path.exists():
        return {"schema": SCHEMA, "entries": []}
    data = json.loads(path.read_text())
    if data.get("schema") != SCHEMA or not isinstance(data.get("entries"), list):
        raise EvidenceError(f"{path} is not a {SCHEMA} manifest")
    return data


def inputs_sha256(paths: Iterable[Path]) -> str:
    """Order-independent digest over the contents of the given files."""
    h = hashlib.sha256()
    for p in sorted(Path(x) for x in paths):
        h.update(str(p).encode())
        h.update(hashlib.sha256(p.read_bytes()).digest() if p.is_file() else b"<missing>")
    return h.hexdigest()


def _next_id(entries: list[dict[str, Any]]) -> str:
    nums = [int(m.group(1)) for e in entries if (m := _ID.match(e.get("id", "")))]
    return f"EV-{(max(nums) + 1 if nums else 1):04d}"


def add_entry(project: Path, *, artifact: str, domain: str, claim: str, check_ids: list[str],
              result: str, level: str, evidence_files: list[str], inputs: Iterable[Path] = (),
              model: str | None = None, tool_versions: dict[str, str] | None = None,
              status: str = "VERIFIED", signed_by: str | None = None, notes: str | None = None) -> str:
    """Append one entry atomically and return its id."""
    project = Path(project)
    if domain not in DOMAINS:
        raise EvidenceError(f"domain {domain!r} not in {DOMAINS}")
    if level not in LEVELS:
        raise EvidenceError(f"level {level!r} not in {LEVELS}")
    if result not in ("pass", "fail"):
        raise EvidenceError("result must be 'pass' or 'fail'")
    if status not in ("VERIFIED", "UNVERIFIED"):
        raise EvidenceError("status must be VERIFIED or UNVERIFIED")
    if level in ("L4", "L5") and not signed_by:
        raise EvidenceError(f"{level} evidence needs signed_by (physical test / qualified sign-off)")
    if len(claim.strip()) < 5:
        raise EvidenceError("claim must state what the evidence shows")
    data = load(project)
    entry: dict[str, Any] = {
        "id": _next_id(data["entries"]), "artifact": artifact, "domain": domain, "claim": claim,
        "check_ids": list(check_ids), "result": result, "level": level,
        "evidence_files": list(evidence_files), "inputs_sha256": inputs_sha256(inputs),
        "tool_versions": dict(tool_versions or {}), "git_sha": git_sha(project),
        "model": model or os.environ.get("FORGE_MODEL", "unknown"),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "status": status,
    }
    if signed_by:
        entry["signed_by"] = signed_by
    if notes:
        entry["notes"] = notes
    data["entries"].append(entry)
    path = manifest_path(project)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    with os.fdopen(fd, "w") as fh:
        fh.write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    os.replace(tmp, path)
    return entry["id"]


def add_from_checks(project: Path, check_files: list[Path], *, artifact: str, domain: str,
                    claim: str, inputs: Iterable[Path] = (), model: str | None = None) -> str:
    """Summarise ``forge.check/1`` result files into one entry.

    The result is ``pass`` only if every check passed; the level is the lowest
    level among the checks; an ``error`` check makes the entry UNVERIFIED.
    """
    project = Path(project)
    if not check_files:
        raise EvidenceError("no check result files given")
    results = [json.loads(Path(f).read_text()) for f in check_files]
    for r in results:
        if r.get("schema") != "forge.check/1":
            raise EvidenceError(f"not a forge.check/1 result: {r.get('check_id', '?')}")
    statuses = {r["status"] for r in results}
    tools: dict[str, str] = {}
    for r in results:
        tools.update(r.get("tool_versions", {}))
    return add_entry(
        project, artifact=artifact, domain=domain, claim=claim,
        check_ids=[r["check_id"] for r in results],
        result="pass" if statuses == {"pass"} else "fail",
        level=min((r["level"] for r in results), key=LEVELS.index),
        evidence_files=[os.path.relpath(Path(f).resolve(), project.resolve()) for f in check_files],
        inputs=inputs, model=model, tool_versions=tools,
        status="UNVERIFIED" if "error" in statuses else "VERIFIED")
