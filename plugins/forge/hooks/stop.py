#!/usr/bin/env python3
"""Stop: the evidence gate (CONTRACTS.md §8-9, ADR-001 D5, brief §3.4).

**What counts as changed.** For every ``forge.toml`` ``[[verify]]`` domain,
the files that differ between the domain's *base* and the working tree:
committed, staged, unstaged, deleted and untracked. The base is the domain's
last-green SHA (``.forge/state.json``, written by an all-pass
``forge verify``, and trusted only when passing verify entries vouch for it),
else the scaffold commit (the one that added ``forge.toml``). Committing a
change therefore never hides it from the gate (review #1, C2).

**What counts as evidence.** For each changed domain, every entrypoint
``forge.toml`` lists for the matching block(s) is required. For each one the
*newest* ``forge verify`` entry for ``(domain, entrypoint)`` -- pass or fail,
so a failing sibling run is never masked by an older pass (M6) -- must be
bound to reality (:func:`forge.evidence.binding_problems`): it references
``forge.check/1`` files that exist, parse, pass, still hash to what the run
recorded and are newer than the change; it is not dated in the future; it
came from a full (not ``--fast``) run whose ``--changed`` scope covers the
change; and its ``inputs_sha256`` equals the digest of the domain's files
now. Hand-made claims (``forge evidence add``) never satisfy the gate.

**Verified params.** Independently of how a change was made (Edit, ``sed
-i``, a Python one-liner), a verified param in ``params/params.toml`` whose
value, unit or tolerance differs from the base must have been demoted from
``verified`` with its stale ``verified_by``/``evidence`` cleared and a
``params/CHANGELOG.md`` entry added (what ``forge params set`` does, M3/M4).

**Block-cap handling** (R1a §18: the platform overrides any Stop hook after
8 consecutive blocks). Forge counts consecutive blocks in
``.forge/state.json``. On the 7th it stops blocking, appends an
``UNVERIFIED`` entry per unsatisfied domain (a write failure is reported,
never raised) and resets the counter in a ``finally`` so it always resets.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (  # noqa: E402
    find_project_root, load_forge_toml, any_glob_match, truncate, tomllib,
)
from forge import evidence, state  # noqa: E402

BLOCK_CAP_HANDOFF = 7  # one before the platform's 8-consecutive-block cap (R1a §18)
REASON_MAX_CHARS = 1800
SYSTEM_MESSAGE_MAX_CHARS = 1800
PARAMS_REL = "params/params.toml"
CHANGELOG_REL = "params/CHANGELOG.md"
_VALUE_FIELDS = ("value", "unit", "tol")


def _blocks(toml: dict) -> list[dict]:
    return [b for b in (toml.get("verify") or []) if isinstance(b, dict) and b.get("domain")]


def _patterns_for(toml: dict, domain: str, entrypoint: str) -> list[str]:
    pats: list[str] = []
    for b in _blocks(toml):
        if b["domain"] == domain and entrypoint in (b.get("entrypoints") or []):
            pats.extend(p for p in (b.get("paths") or []) if p not in pats)
    return pats


def _all_files(project: Path) -> list[str]:
    return evidence.project_files(project)


def _changed_for(project: Path, domain: str, manifest: dict, cache: dict) -> tuple[str | None, list[str]]:
    bases = cache.setdefault("__bases__", {})
    if domain not in bases:
        bases[domain] = state.resolve_base(project, domain, manifest)
    base = bases[domain]
    if base not in cache:
        changed = state.changed_since(project, base)
        cache[base] = changed if changed is not None else _all_files(project)
    return base, cache[base]


def _required(project: Path, toml: dict, manifest: dict) -> tuple[dict, dict]:
    """``{(domain, entrypoint): set(changed paths)}`` and ``{domain: base}``."""
    required: dict[tuple[str, str], set[str]] = {}
    bases: dict[str, str | None] = {}
    cache: dict = {}
    for b in _blocks(toml):
        domain = b["domain"]
        base, changed = _changed_for(project, domain, manifest, cache)
        bases[domain] = base
        patterns = b.get("paths") or []
        matched = {p for p in changed if any_glob_match(patterns, p)}
        # N3: gitignored files under this domain's globs are still inputs,
        # and .gitignore itself is an input of every domain.
        matched.update(evidence.ignored_inputs(project, patterns))
        if ".gitignore" in changed:
            matched.add(".gitignore")
        if not matched:
            continue
        eps = b.get("entrypoints") or []
        if not eps:
            required.setdefault((domain, "(no entrypoint registered)"), set()).update(matched)
        for ep in eps:
            required.setdefault((domain, ep), set()).update(matched)
    return required, bases


# ---------------------------------------------------------------------------
# verified params: a Stop-time diff, independent of how the file changed
# ---------------------------------------------------------------------------

def _leaves(data, prefix=()):
    if not isinstance(data, dict):
        return
    if "value" in data and "status" in data:
        yield prefix, data
        return
    for k, v in data.items():
        if isinstance(v, dict):
            yield from _leaves(v, prefix + (k,))


def _params_domain(toml: dict) -> str | None:
    for b in _blocks(toml):
        if any_glob_match(b.get("paths") or [], PARAMS_REL):
            return b["domain"]
    return None


def _params_base(project: Path, toml: dict, manifest: dict) -> str | None:
    domain = _params_domain(toml)
    return state.resolve_base(project, domain, manifest) if domain else state.scaffold_base(project)


def _git_show(project: Path, base: str, rel: str) -> str | None:
    code, out = state._git(project, "show", f"{base}:./{rel}")
    return out if code == 0 else None


def verified_param_violations(project: Path, toml: dict, manifest: dict) -> list[str]:
    base = _params_base(project, toml, manifest)
    if not base:
        return []
    old_text = _git_show(project, base, PARAMS_REL)
    if old_text is None:
        return []
    try:
        old = dict(_leaves(tomllib.loads(old_text)))
    except tomllib.TOMLDecodeError:
        return []
    try:
        new_text = (project / PARAMS_REL).read_text()
    except FileNotFoundError:
        new_text = ""
    try:
        new = dict(_leaves(tomllib.loads(new_text)))
    except tomllib.TOMLDecodeError as exc:
        return [f"{PARAMS_REL} no longer parses ({exc})"]
    old_log = _git_show(project, base, CHANGELOG_REL) or ""
    try:
        new_log = (project / CHANGELOG_REL).read_text()
    except OSError:
        new_log = ""
    added_log = new_log[len(old_log):] if new_log.startswith(old_log) else new_log
    ids = {e.get("id"): e for e in manifest.get("entries") or [] if isinstance(e, dict)}
    problems: list[str] = []
    for path, leaf in old.items():
        if leaf.get("status") != "verified":
            continue
        key = ".".join(path)
        logged = f"-- {key}\n" in added_log
        cur = new.get(path)
        if cur is None:
            if not logged:
                problems.append(f"verified param {key} was removed without a params/CHANGELOG.md entry")
            continue
        if all(cur.get(f) == leaf.get(f) for f in _VALUE_FIELDS):
            continue
        if not logged:
            problems.append(f"verified param {key} changed ({leaf.get('value')!r} -> {cur.get('value')!r}) "
                            "without a params/CHANGELOG.md entry; use `forge params set`")
        if cur.get("status") == "verified":
            new_ev = cur.get("evidence") or []
            stale = not new_ev or any(i in (leaf.get("evidence") or []) for i in new_ev)
            unknown = [i for i in new_ev
                       if i not in ids or ids[i].get("result") != "pass" or ids[i].get("status") != "VERIFIED"]
            if stale or unknown or not cur.get("verified_by"):
                problems.append(f"verified param {key} changed value but still claims status=verified with "
                                "the old verification; it must drop to measured until re-verified")

    # N6: a leaf promoted straight to status="verified" (old status was NOT
    # verified), bypassing `forge params set --status verified` entirely --
    # e.g. a Write/Edit made behind the hooks' back. Its evidence must be
    # tied to this exact param (artifact == "param:<key>"), pass, and
    # VERIFIED, the same rule `forge params set` enforces.
    for path, leaf in new.items():
        if leaf.get("status") != "verified":
            continue
        old_leaf = old.get(path)
        if old_leaf is not None and old_leaf.get("status") == "verified":
            continue  # a value change on an already-verified leaf: covered above
        key = ".".join(path)
        artifact = f"param:{key}"
        ev = leaf.get("evidence") or []
        bad = [i for i in ev if i not in ids or ids[i].get("result") != "pass" or ids[i].get("status") != "VERIFIED"]
        untied = [i for i in ev if i not in bad and ids.get(i, {}).get("artifact") != artifact]
        if not ev or bad or untied or not leaf.get("verified_by"):
            if not ev:
                detail = "no evidence"
            elif bad:
                detail = f"evidence {', '.join(bad)} missing/failing/UNVERIFIED"
            elif untied:
                detail = f"evidence {', '.join(untied)} not tied to {artifact!r}"
            else:
                detail = "no verified_by"
            problems.append(f"verified param {key} was promoted to status=verified outside `forge params set` "
                            f"({detail}); only `forge params set --status verified` may verify a param, with "
                            "evidence tied to it")
    return problems


# ---------------------------------------------------------------------------

def _build_reason(failures: dict[tuple[str, str], list[str]], required: dict, param_problems: list[str]) -> str:
    lines = ["Forge evidence gate: these changes have no bound, passing `forge verify` evidence "
             "(CONTRACTS.md §9; hand-written evidence does not count):"]
    for (domain, ep), problems in sorted(failures.items()):
        paths = sorted(required[(domain, ep)])
        shown = ", ".join(paths[:4]) + (f" (+{len(paths) - 4} more)" if len(paths) > 4 else "")
        why = "; ".join(problems[:2])
        if domain not in evidence.DOMAINS:
            why += f"; domain {domain!r} is not one of {', '.join(evidence.DOMAINS)} -- fix forge.toml"
        lines.append(f"- {domain}/{ep}: changed {shown}. {why}.")
    for p in param_problems:
        lines.append(f"- params: {p}.")
    domains = sorted({d for d, _ in failures})
    if domains:
        lines.append(f"Run `forge verify --all` (or `forge verify --changed <paths>`) and fix what fails.")
    return truncate("\n".join(lines), REASON_MAX_CHARS)


def _handoff(project: Path, domains: list[str], count: int) -> dict:
    notes: list[str] = []
    try:
        for domain in domains:
            try:
                evidence.add_entry(
                    project, artifact=f"domain:{domain}",
                    domain=domain if domain in evidence.DOMAINS else "sys",
                    claim=(f"{domain} changed but was not verified after {count} consecutive Stop attempts; "
                           "recorded UNVERIFIED so downstream gates cannot mistake this for passing evidence."),
                    check_ids=[], result="fail", level="L0", evidence_files=[], status="UNVERIFIED",
                    notes=None if domain in evidence.DOMAINS else f"forge.toml domain {domain!r}",
                )
            except Exception as exc:  # noqa: BLE001 -- the handoff must never raise
                notes.append(f"could not record UNVERIFIED for {domain}: {type(exc).__name__}: {exc}")
    finally:
        try:
            state.reset_stop_block(project)
        except Exception as exc:  # noqa: BLE001
            notes.append(f"could not reset the Stop counter: {exc}")
    msg = (f"Forge: evidence gate reached its {BLOCK_CAP_HANDOFF}-block handoff (before the platform's "
           f"8-block cap) for {', '.join(domains)}; recorded UNVERIFIED evidence and let the turn stop. "
           "These still need real verification before anything downstream (release, fab) can proceed.")
    if notes:
        msg += " WARNING: " + " | ".join(notes)
    return {"systemMessage": truncate(msg, SYSTEM_MESSAGE_MAX_CHARS)}


def handle(data: dict) -> tuple[int, dict | None]:
    project = find_project_root(data.get("cwd"))
    if project is None:
        return 0, None  # not a Forge product repo: no-op fast (brief §3.4)

    toml = load_forge_toml(project)

    base_sha = state.ensure_base_pinned(project)
    if base_sha is None:
        reason = (".forge/base_sha is missing (N11): it pins the scaffold commit the evidence gate diffs "
                  "against and must not be deleted. Restore it (the commit that added forge.toml, see "
                  "`git log --diff-filter=A -- forge.toml`) or ask a human to re-pin it.")
        count = state.record_stop_block(project, reason=reason)
        if count >= BLOCK_CAP_HANDOFF:
            return 0, _handoff(project, ["sys"], count)
        return 2, {"decision": "block", "reason": reason}

    manifest_error = None
    try:
        manifest = evidence.load(project)
    except (evidence.EvidenceError, ValueError, OSError) as exc:
        manifest, manifest_error = {"entries": []}, str(exc)

    required, _ = _required(project, toml, manifest)
    now = time.time()
    files = _all_files(project) if required else []
    digests: dict[tuple[str, ...], str] = {}
    failures: dict[tuple[str, str], list[str]] = {}
    for (domain, ep), paths in required.items():
        pats = _patterns_for(toml, domain, ep)
        key = tuple(pats)
        if key not in digests:
            digests[key] = evidence.domain_inputs_sha256(project, pats, files)
        entry = evidence.newest_verify_entry(manifest, domain, ep)
        problems = evidence.binding_problems(project, entry, patterns=pats, changed=paths, files=files,
                                             now=now, digest=digests[key])
        if manifest_error:
            problems.insert(0, f"evidence/manifest.json is unreadable ({manifest_error})")
        if problems:
            failures[(domain, ep)] = problems

    param_problems = verified_param_violations(project, toml, manifest)

    if not failures and not param_problems:
        state.reset_stop_block(project)
        return 0, None

    reason = _build_reason(failures, required, param_problems)
    count = state.record_stop_block(project, reason=reason)
    if count >= BLOCK_CAP_HANDOFF:
        domains = sorted({d for d, _ in failures} | ({_params_domain(toml) or "sys"} if param_problems else set()))
        return 0, _handoff(project, domains, count)
    return 2, {"decision": "block", "reason": reason}


if __name__ == "__main__":
    from _failclosed import run_hook
    run_hook(handle)
