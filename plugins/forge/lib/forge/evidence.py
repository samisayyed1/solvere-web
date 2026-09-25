"""Append-only evidence manifest (CONTRACTS.md §4, schema ``forge.evidence/1``).

``evidence/manifest.json`` in a product repo records every result-bearing claim
with its credibility level. Entries are never edited or removed; a newer entry
supersedes an older one for the same artifact. Standard library only.

Two kinds of entry share the manifest:

- **Claims** (``forge evidence add|from-checks``): free-standing records a
  human or agent makes. They are useful for traceability and gate records,
  but they can **never** satisfy the Stop-hook evidence gate on their own.
- **Verify runs** (:func:`add_verify_entry`, written only by ``forge verify``):
  one entry per ``(domain, entrypoint)`` run. Each is *bound* to the run it
  describes: it names the entrypoint, the ``forge.check/1`` files that run
  wrote together with their sha256, and ``inputs_sha256`` over every file the
  domain's ``forge.toml`` globs cover at the time of the run.
  :func:`binding_problems` re-checks all of that against the disk; the Stop
  hook accepts a domain only when the newest verify entry of every required
  entrypoint has no binding problems (review #1, C2/M6).
"""

from __future__ import annotations

import calendar
import hashlib
import json
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Iterable

from .checkresult import LEVELS, git_sha

SCHEMA = "forge.evidence/1"
DOMAINS = ("mech", "elec", "fw", "sw", "sys", "sim", "mfg", "compliance", "docs")
MANIFEST = Path("evidence/manifest.json")
RECORDED_BY_VERIFY = "forge verify"
CLOCK_SKEW_S = 120.0     # tolerated clock skew for "not in the future" checks
MTIME_SLACK_S = 1.0      # manifest timestamps have 1 s resolution
_ID = re.compile(r"^EV-(\d{4,})$")
_WALK_SKIP = {".git", "out", ".forge", "node_modules", "__pycache__", ".venv"}


class EvidenceError(ValueError):
    """An entry violates the evidence contract."""


def manifest_path(project: Path) -> Path:
    return Path(project) / MANIFEST


def load(project: Path) -> dict[str, Any]:
    path = manifest_path(project)
    if not path.exists():
        return {"schema": SCHEMA, "entries": []}
    data = json.loads(path.read_text())
    if not isinstance(data, dict) or data.get("schema") != SCHEMA or not isinstance(data.get("entries"), list):
        raise EvidenceError(f"{path} is not a {SCHEMA} manifest")
    return data


# ---------------------------------------------------------------------------
# hashing and project file enumeration
# ---------------------------------------------------------------------------

def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inputs_sha256(paths: Iterable[Path], root: Path | None = None) -> str:
    """Order-independent digest over the contents of the given files.

    With ``root`` the file names folded into the digest are the posix paths
    relative to ``root``, so the digest does not depend on where the project
    is checked out.
    """
    h = hashlib.sha256()
    items = []
    for x in paths:
        p = Path(x)
        full = (Path(root) / p) if (root is not None and not p.is_absolute()) else p
        name = p.as_posix() if root is not None and not p.is_absolute() else str(p)
        if root is not None and p.is_absolute():
            try:
                name = p.resolve().relative_to(Path(root).resolve()).as_posix()
            except ValueError:
                name = str(p)
        items.append((name, full))
    for name, full in sorted(items):
        h.update(name.encode())
        h.update(hashlib.sha256(full.read_bytes()).digest() if full.is_file() else b"<missing>")
    return h.hexdigest()


def _glob_to_regex(pattern: str) -> "re.Pattern[str]":
    out: list[str] = []
    i, n = 0, len(pattern)
    while i < n:
        c = pattern[i]
        if c == "*":
            if i + 1 < n and pattern[i + 1] == "*":
                out.append(".*")
                i += 2
                if i < n and pattern[i] == "/":
                    i += 1
            else:
                out.append("[^/]*")
                i += 1
        elif c == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(c))
            i += 1
    return re.compile("^" + "".join(out) + "$")


_GLOB_CACHE: dict[str, "re.Pattern[str]"] = {}


def glob_match(pattern: str, path: str) -> bool:
    """Match a relative forward-slash ``path`` against a ``forge.toml`` glob:
    ``**`` spans directories, ``*`` and ``?`` stay inside one segment. This is
    the single matcher used by ``forge verify`` and every hook, so they can
    never disagree about which domain a file belongs to."""
    rx = _GLOB_CACHE.get(pattern)
    if rx is None:
        rx = _GLOB_CACHE[pattern] = _glob_to_regex(pattern)
    return bool(rx.match(path))


def any_glob_match(patterns: Iterable[str], path: str) -> bool:
    return any(glob_match(p, path) for p in patterns)


def project_files(project: Path) -> list[str]:
    """Every non-ignored file of the project (tracked, plus untracked that are
    not gitignored), as posix paths relative to ``project``. Outside git, a
    directory walk that skips ``.git``, ``out``, ``.forge`` and caches."""
    project = Path(project)
    try:
        res = subprocess.run(["git", "-C", str(project), "ls-files", "-z", "--cached", "--others",
                              "--exclude-standard"], capture_output=True, timeout=10)
        if res.returncode == 0:
            names = sorted({n for n in res.stdout.decode("utf-8", "surrogateescape").split("\0") if n})
            return [n for n in names if (project / n).is_file()]
    except (OSError, subprocess.SubprocessError):
        pass
    out: list[str] = []
    for dirpath, dirnames, filenames in os.walk(project):
        dirnames[:] = [d for d in dirnames if d not in _WALK_SKIP]
        for f in filenames:
            out.append((Path(dirpath) / f).relative_to(project).as_posix())
    return sorted(out)


def domain_inputs(project: Path, patterns: Iterable[str], files: list[str] | None = None) -> list[str]:
    pats = list(patterns)
    files = project_files(project) if files is None else files
    return [f for f in files if any_glob_match(pats, f)]


def domain_inputs_sha256(project: Path, patterns: Iterable[str], files: list[str] | None = None) -> str:
    return inputs_sha256([Path(f) for f in domain_inputs(project, patterns, files)], root=Path(project))


# ---------------------------------------------------------------------------
# writing entries
# ---------------------------------------------------------------------------

def _next_id(entries: list[dict[str, Any]]) -> str:
    nums = [int(m.group(1)) for e in entries if (m := _ID.match(str(e.get("id", ""))))]
    return f"EV-{(max(nums) + 1 if nums else 1):04d}"


def _write_manifest(project: Path, data: dict[str, Any]) -> None:
    path = manifest_path(project)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    with os.fdopen(fd, "w") as fh:
        fh.write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    os.replace(tmp, path)


def add_entry(project: Path, *, artifact: str, domain: str, claim: str, check_ids: list[str],
              result: str, level: str, evidence_files: list[str], inputs: Iterable[Path] = (),
              model: str | None = None, tool_versions: dict[str, str] | None = None,
              status: str = "VERIFIED", signed_by: str | None = None, notes: str | None = None,
              _run: dict[str, Any] | None = None, _inputs_digest: str | None = None) -> str:
    """Append one entry atomically and return its id.

    ``_run`` / ``_inputs_digest`` are private: only :func:`add_verify_entry`
    passes them, which is what distinguishes a bound verify-run entry from a
    free-standing claim. The ``forge evidence`` CLI never exposes them.
    """
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
        "evidence_files": list(evidence_files),
        "inputs_sha256": _inputs_digest or inputs_sha256(inputs),
        "tool_versions": dict(tool_versions or {}), "git_sha": git_sha(project),
        "model": model or os.environ.get("FORGE_MODEL", "unknown"),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "status": status,
    }
    if signed_by:
        entry["signed_by"] = signed_by
    if notes:
        entry["notes"] = notes
    if _run:
        entry.update(_run)
    data["entries"].append(entry)
    _write_manifest(project, data)
    return entry["id"]


def _read_check(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(Path(path).read_text())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) and data.get("schema") == "forge.check/1" else None


def add_from_checks(project: Path, check_files: list[Path], *, artifact: str, domain: str,
                    claim: str, inputs: Iterable[Path] = (), model: str | None = None) -> str:
    """Summarise ``forge.check/1`` result files into one (claim) entry.

    The result is ``pass`` only if every check passed; the level is the lowest
    level among the checks; an ``error`` check makes the entry UNVERIFIED.
    Such an entry is a claim: it does not satisfy the Stop gate (only
    ``forge verify`` entries, :func:`add_verify_entry`, do).
    """
    project = Path(project)
    if not check_files:
        raise EvidenceError("no check result files given")
    results = []
    for f in check_files:
        r = _read_check(Path(f))
        if r is None:
            raise EvidenceError(f"not a forge.check/1 result: {f}")
        results.append(r)
    statuses = {r.get("status") for r in results}
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


def add_verify_entry(project: Path, *, domain: str, entrypoint: str, returncode: int,
                     check_files: list[Path], patterns: Iterable[str], scope: list[str] | None = None,
                     fast: bool = False, rung: str | None = None, model: str | None = None,
                     files: list[str] | None = None) -> str:
    """Record one ``forge verify`` run of one entrypoint, bound to its outputs.

    ``check_files`` are the result files the run wrote; files that are not
    ``forge.check/1`` results (e.g. graph dumps) are ignored. The entry is
    ``pass`` only if the entrypoint exited 0 **and** every check it wrote
    passed; an exit of 2 or an ``error`` check makes it UNVERIFIED. An exit-0
    run that wrote no check file is recorded as a ``[SKIP]`` (nothing to
    check): it carries no measurement, which the gate states explicitly.
    """
    project = Path(project).resolve()
    checks: list[tuple[Path, dict[str, Any]]] = []
    for f in check_files:
        r = _read_check(Path(f))
        if r is not None:
            checks.append((Path(f).resolve(), r))
    statuses = {r.get("status") for _, r in checks}
    passed = returncode == 0 and statuses <= {"pass"}
    errored = returncode not in (0, 1) or "error" in statuses
    rels = [os.path.relpath(p, project).replace(os.sep, "/") for p, _ in checks]
    tools: dict[str, str] = {}
    for _, r in checks:
        tools.update({str(k): str(v) for k, v in (r.get("tool_versions") or {}).items()})
    levels = [r.get("level") for _, r in checks if r.get("level") in LEVELS]
    run = {
        "entrypoint": entrypoint, "recorded_by": RECORDED_BY_VERIFY, "returncode": int(returncode),
        "mode": "fast" if fast else "full", "scope": list(scope) if scope else None,
        "evidence_sha256": {rel: sha256_file(p) for rel, (p, _) in zip(rels, checks)},
    }
    if rung:
        run["rung"] = rung
    skipped = not checks and returncode == 0
    claim = (f"forge verify {domain}/{entrypoint}: "
             + ("[SKIP] nothing to check" if skipped else
                f"{sum(1 for _, r in checks if r.get('status') == 'pass')}/{len(checks)} check(s) passed"))
    return add_entry(
        project, artifact=f"entrypoint:{entrypoint}", domain=domain, claim=claim,
        check_ids=[str(r.get("check_id")) for _, r in checks],
        result="pass" if passed else "fail",
        level=min(levels, key=LEVELS.index) if levels else "L0",
        evidence_files=rels, model=model, tool_versions=tools,
        status="UNVERIFIED" if errored else "VERIFIED",
        notes="[SKIP] entrypoint exited 0 without writing a check result" if skipped else None,
        _run=run, _inputs_digest=domain_inputs_sha256(project, patterns, files))


# ---------------------------------------------------------------------------
# reading entries back (the Stop gate)
# ---------------------------------------------------------------------------

def parse_ts(ts: Any) -> float | None:
    if not isinstance(ts, str) or not ts:
        return None
    try:
        return float(calendar.timegm(time.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")))
    except ValueError:
        return None


def newest_verify_entry(manifest: dict[str, Any], domain: str, entrypoint: str) -> dict[str, Any] | None:
    """The last-appended ``forge verify`` entry for ``(domain, entrypoint)``,
    pass **or** fail (review #1, M6: a newer failing run supersedes an older
    pass). Manifest order, not the timestamp, decides "newest": timestamps
    are data an attacker could set, the append order is not."""
    for entry in reversed(manifest.get("entries") or []):
        if (isinstance(entry, dict) and entry.get("domain") == domain
                and entry.get("entrypoint") == entrypoint
                and entry.get("recorded_by") == RECORDED_BY_VERIFY):
            return entry
    return None


def binding_problems(project: Path, entry: dict[str, Any] | None, *, patterns: Iterable[str],
                     changed: Iterable[str], files: list[str] | None = None,
                     now: float | None = None, digest: str | None = None) -> list[str]:
    """Why ``entry`` does not prove the current state of its domain (empty
    list = it does). ``changed`` are the domain's files changed since the
    last green run."""
    project = Path(project)
    now = time.time() if now is None else now
    if entry is None:
        return ["no `forge verify` run is recorded for it"]
    problems: list[str] = []
    ep = entry.get("entrypoint", "?")
    if entry.get("recorded_by") != RECORDED_BY_VERIFY or not entry.get("entrypoint"):
        problems.append(f"{entry.get('id')} is a hand-made claim, not a `forge verify` run")
        return problems
    if entry.get("result") != "pass" or entry.get("status") != "VERIFIED":
        problems.append(f"newest run {entry.get('id')} of {ep} did not pass "
                        f"(result={entry.get('result')}, status={entry.get('status')})")
        return problems
    if entry.get("mode") != "full":
        problems.append(f"{entry.get('id')} came from a --fast run; the gate needs a full `forge verify`")
    ts = parse_ts(entry.get("timestamp"))
    if ts is None:
        problems.append(f"{entry.get('id')} has no valid timestamp")
        return problems
    if ts > now + CLOCK_SKEW_S:
        problems.append(f"{entry.get('id')} is dated in the future ({entry.get('timestamp')})")
        return problems
    changed = list(changed)
    scope = entry.get("scope")
    if scope:
        missing = sorted(set(changed) - set(scope))
        if missing:
            problems.append(f"{entry.get('id')} only verified --changed {', '.join(scope[:3])}; "
                            f"not {', '.join(missing[:3])}")
    newest_change = 0.0
    for rel in changed:
        try:
            newest_change = max(newest_change, (project / rel).stat().st_mtime)
        except OSError:
            continue  # deleted: the inputs digest covers the deletion
    ev_files = entry.get("evidence_files") or []
    shas = entry.get("evidence_sha256") or {}
    if not ev_files:
        if entry.get("check_ids") or not str(entry.get("notes", "")).startswith("[SKIP]"):
            problems.append(f"{entry.get('id')} references no check result file")
        elif newest_change > ts + MTIME_SLACK_S:
            problems.append(f"{entry.get('id')} ([SKIP]) is older than the change")
    for rel in ev_files:
        path = project / rel
        try:
            path.resolve().relative_to(project.resolve())
        except (OSError, ValueError):
            problems.append(f"{entry.get('id')}: evidence file {rel} is outside the project")
            continue
        check = _read_check(path)
        if check is None:
            problems.append(f"{entry.get('id')}: {rel} is missing or not a forge.check/1 result")
            continue
        if check.get("status") != "pass":
            problems.append(f"{entry.get('id')}: {rel} has status {check.get('status')}")
        if check.get("check_id") not in (entry.get("check_ids") or []):
            problems.append(f"{entry.get('id')}: {rel} check_id {check.get('check_id')} not in the entry")
        if shas.get(rel) != sha256_file(path):
            problems.append(f"{entry.get('id')}: {rel} changed after the run was recorded")
        started = parse_ts(check.get("started"))
        if started is None or started > now + CLOCK_SKEW_S:
            problems.append(f"{entry.get('id')}: {rel} has a missing or future `started` time")
        try:
            file_mtime = path.stat().st_mtime
        except OSError:
            file_mtime = 0.0
        if file_mtime > now + CLOCK_SKEW_S:
            problems.append(f"{entry.get('id')}: {rel} has a future modification time")
        if newest_change > file_mtime + MTIME_SLACK_S:
            problems.append(f"{entry.get('id')}: {rel} is older than the change")
    current = digest if digest is not None else domain_inputs_sha256(project, patterns, files)
    if entry.get("inputs_sha256") != current:
        problems.append(f"{entry.get('id')}: inputs changed since that run (inputs_sha256 mismatch)")
    return problems
