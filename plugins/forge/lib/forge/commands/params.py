"""``forge params get|set|lint`` (CONTRACTS.md §2, §11).

``params/params.toml`` is the single source of truth for every dimension
and value used in CAD, ECAD, firmware or analysis. Each leaf is a small
table (``value``, ``unit``, optional ``tol``, ``status``, ``source``,
optional ``verified_by``/``evidence``) validated against
``schemas/params.schema.json``.

**Value changes** (``value``, ``unit`` or ``tol``) of an existing leaf
(review #1, M4):

- always need ``--source "<citation>"``: a new value needs its own citation,
  different from the old one (the old source described the old value);
- on a ``verified`` leaf also need ``--justification`` (a sentence), and
  the leaf drops to ``status = "measured"`` with ``verified_by`` and
  ``evidence`` cleared -- the old verification described the old value.
  Setting ``--status verified``/``--verified-by``/``--evidence`` in the same
  call is refused: re-verification is a separate step that must cite
  passing evidence entries that exist in ``evidence/manifest.json``;
- are appended (old leaf, new leaf, justification) to ``params/CHANGELOG.md``.

The Stop hook re-checks the same rule on the file itself, however it was
changed.

**Formatting:** ``set`` edits the leaf's table in place, so comments and
formatting elsewhere in the file are preserved. Only when the leaf is not a
plain ``[dotted.key]`` table (e.g. an inline table) does it fall back to
re-serialising the whole file (:func:`render_params_toml`), and it says so.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

from .. import minischema

try:
    import tomllib
except ImportError:  # pragma: no cover -- params commands require py3.11+ (tomllib)
    tomllib = None  # type: ignore[assignment]

NAME = "params"
HELP = "get, set (with justification for verified values), or lint params/params.toml"

PARAMS_REL = Path("params/params.toml")
CHANGELOG_REL = Path("params/CHANGELOG.md")
_PLUGIN_ROOT = Path(__file__).resolve().parents[3]  # lib/forge/commands -> lib/forge -> lib -> plugins/forge
_SCHEMA_PATH = _PLUGIN_ROOT / "schemas" / "params.schema.json"

_LEAF_FIELD_ORDER = ("value", "unit", "tol", "status", "source", "verified_by", "evidence")
_BARE_KEY_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def register(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--project", type=Path, default=Path("."), help="product repo root (default: cwd)")
    sub = parser.add_subparsers(dest="params_command", required=True)

    get_p = sub.add_parser("get", help="print one param leaf")
    get_p.add_argument("key", help="dotted path, e.g. enclosure.wall_thickness")
    get_p.add_argument("--json", action="store_true")

    set_p = sub.add_parser("set", help="change (or create) one param leaf")
    set_p.add_argument("key")
    set_p.add_argument("--value", default=None)
    set_p.add_argument("--unit", default=None)
    set_p.add_argument("--status", default=None, choices=("assumed", "datasheet", "measured", "verified"))
    set_p.add_argument("--source", default=None)
    set_p.add_argument("--verified-by", default=None)
    set_p.add_argument("--evidence", dest="evidence_ids", action="append", default=None, metavar="EV-0001")
    set_p.add_argument("--tol-minus", type=float, default=None)
    set_p.add_argument("--tol-plus", type=float, default=None)
    set_p.add_argument("--justification", default=None,
                        help='required (a sourced sentence) when the CURRENT value is status=verified')

    lint_p = sub.add_parser("lint", help="validate every leaf against schemas/params.schema.json")
    lint_p.add_argument("--json", action="store_true")


def _coerce_value(raw: str) -> Any:
    low = raw.lower()
    if low == "true":
        return True
    if low == "false":
        return False
    if re.fullmatch(r"[+-]?\d+", raw):
        return int(raw)
    try:
        return float(raw)
    except ValueError:
        return raw


def _load_params(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return tomllib.loads(path.read_text())


def _get_leaf(data: dict, path: tuple[str, ...]) -> dict | None:
    node: Any = data
    for key in path:
        if not isinstance(node, dict) or key not in node:
            return None
        node = node[key]
    return node if isinstance(node, dict) else None


def _set_leaf(data: dict, path: tuple[str, ...], leaf: dict) -> None:
    node = data
    for key in path[:-1]:
        node = node.setdefault(key, {})
    node[path[-1]] = leaf


def _iter_leaves(data: Any, prefix: tuple[str, ...] = ()):
    if not isinstance(data, dict):
        return
    if {"value", "unit", "status"} <= data.keys():
        yield prefix, data
        return
    for key, val in data.items():
        if isinstance(val, dict):
            yield from _iter_leaves(val, prefix + (key,))
        else:
            dotted = ".".join(prefix + (key,))
            raise ValueError(f"{dotted}: a bare value outside a param leaf table (missing value/unit/status)")


def _toml_key(key: str) -> str:
    return key if _BARE_KEY_RE.match(key) else json.dumps(key)


def _toml_string(value: str) -> str:
    escaped = (value.replace("\\", "\\\\").replace('"', '\\"')
               .replace("\n", "\\n").replace("\t", "\\t").replace("\r", "\\r"))
    return f'"{escaped}"'


def _toml_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, str):
        return _toml_string(value)
    if isinstance(value, dict):
        return "{ " + ", ".join(f"{_toml_key(k)} = {_toml_value(v)}" for k, v in value.items()) + " }"
    if isinstance(value, list):
        return "[" + ", ".join(_toml_value(v) for v in value) + "]"
    raise ValueError(f"unsupported TOML value for params.toml: {value!r}")


def render_params_toml(data: dict) -> str:
    """Serialize the whole params tree as ``[dotted.section]`` leaf tables."""
    lines: list[str] = []
    for path, leaf in _iter_leaves(data):
        lines.append(f"[{'.'.join(_toml_key(p) for p in path)}]")
        seen = set()
        for field in _LEAF_FIELD_ORDER:
            if field in leaf:
                lines.append(f"{field} = {_toml_value(leaf[field])}")
                seen.add(field)
        for field, value in leaf.items():
            if field not in seen:
                lines.append(f"{field} = {_toml_value(value)}")
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


def _params_schema() -> dict:
    return json.loads(_SCHEMA_PATH.read_text())


def _append_changelog(project: Path, key: str, old_leaf: dict | None, new_leaf: dict, justification: str | None) -> None:
    path = project / CHANGELOG_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    entry = (
        f"## {ts} -- {key}\n"
        f"- old: {json.dumps({k: v for k, v in (old_leaf or {}).items()}, sort_keys=True)}\n"
        f"- new: {json.dumps({k: v for k, v in new_leaf.items()}, sort_keys=True)}\n"
        f"- justification: {justification or '(none given)'}\n\n"
    )
    with path.open("a") as fh:
        fh.write(entry)


def _cmd_get(ns: argparse.Namespace, params_path: Path, key_path: tuple[str, ...]) -> int:
    data = _load_params(params_path)
    leaf = _get_leaf(data, key_path)
    if leaf is None:
        print(f"forge params get: no such param {ns.key!r}", file=sys.stderr)
        return 1
    if ns.json:
        print(json.dumps(leaf, indent=2, sort_keys=True, ensure_ascii=False))
    else:
        for k, v in leaf.items():
            print(f"{k}: {v}")
    return 0


_VALUE_FIELDS = ("value", "unit", "tol")
_HEADER_RE = re.compile(r"^\s*\[")


def _section_bounds(lines: list[str], key_path: tuple[str, ...]) -> tuple[int, int] | None:
    """Line range ``[start, end)`` of the ``[a.b.c]`` table for ``key_path``
    (header line included), or None."""
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith("[") or stripped.startswith("[["):
            continue
        header = stripped.split("#", 1)[0].strip()
        if not header.endswith("]"):
            continue
        try:
            parsed = tomllib.loads(header + "\n")
        except tomllib.TOMLDecodeError:
            continue
        node, path = parsed, []
        while isinstance(node, dict) and len(node) == 1:
            k = next(iter(node))
            path.append(k)
            node = node[k]
        if tuple(path) == key_path:
            end = i + 1
            while end < len(lines) and not _HEADER_RE.match(lines[end]):
                end += 1
            return i, end
    return None


def _field_span(lines: list[str], start: int, end: int, field: str) -> tuple[int, int] | None:
    rx = re.compile(r"^\s*" + re.escape(field) + r"\s*=")
    for i in range(start + 1, end):
        if rx.match(lines[i]):
            j = i + 1
            while j <= end:  # a multi-line value: extend until the assignment parses
                try:
                    tomllib.loads("".join(lines[i:j]))
                    return i, j
                except tomllib.TOMLDecodeError:
                    j += 1
            return i, i + 1
    return None


def _edit_in_place(text: str, key_path: tuple[str, ...], new_leaf: dict, old_leaf: dict | None) -> str | None:
    """Rewrite only the leaf's own lines; None if that is not possible."""
    lines = text.splitlines(keepends=True)
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"
    if old_leaf is None:
        block = [f"[{'.'.join(_toml_key(k) for k in key_path)}]\n"]
        for field in _LEAF_FIELD_ORDER:
            if field in new_leaf:
                block.append(f"{field} = {_toml_value(new_leaf[field])}\n")
        block += [f"{f} = {_toml_value(v)}\n" for f, v in new_leaf.items() if f not in _LEAF_FIELD_ORDER]
        sep = ["\n"] if lines and lines[-1].strip() else []
        return "".join(lines + sep + block)
    bounds = _section_bounds(lines, key_path)
    if bounds is None:
        return None
    start, end = bounds
    fields = [f for f in _LEAF_FIELD_ORDER if f in new_leaf or f in old_leaf]
    fields += [f for f in new_leaf if f not in fields]
    for field in fields:
        if new_leaf.get(field) == old_leaf.get(field) and (field in new_leaf) == (field in old_leaf):
            continue
        span = _field_span(lines, start, end, field)
        new_line = [f"{field} = {_toml_value(new_leaf[field])}\n"] if field in new_leaf else []
        if span:
            i, j = span
            comment = re.search(r"\s+#[^\"']*$", lines[j - 1].rstrip("\n")) if j == i + 1 else None
            if new_line and comment:
                new_line = [new_line[0].rstrip("\n") + comment.group(0) + "\n"]
            lines[i:j] = new_line
            end += len(new_line) - (j - i)
        elif new_line:
            insert_at = end
            while insert_at > start + 1 and not lines[insert_at - 1].strip():
                insert_at -= 1
            lines[insert_at:insert_at] = new_line
            end += 1
    return "".join(lines)


def _citation_ok(source: str | None, old_source: str | None) -> str | None:
    if not source or len(source.strip()) < 10:
        return "a value change needs --source \"<citation>\" (at least 10 characters: document, page, measurement)"
    if old_source and source.strip() == str(old_source).strip():
        return "--source must cite the new value; it repeats the old source, which described the old value"
    return None


def _evidence_ok(project: Path, ids: list[str], key: str) -> str | None:
    """N6: verifying evidence must be *tied* to this param -- its
    ``artifact`` must be ``param:<key>`` -- not just any passing entry
    (a sysml check, an unrelated claim, ...)."""
    from .. import evidence as evidence_lib
    try:
        entries = {e.get("id"): e for e in evidence_lib.load(project).get("entries", [])}
    except (evidence_lib.EvidenceError, ValueError, OSError) as exc:
        return f"cannot read evidence/manifest.json ({exc})"
    artifact = f"param:{key}"
    bad = [i for i in ids if i not in entries or entries[i].get("result") != "pass"
           or entries[i].get("status") != "VERIFIED"]
    if bad:
        return f"evidence {', '.join(bad)} is missing, failing or UNVERIFIED in evidence/manifest.json"
    untied = [i for i in ids if entries[i].get("artifact") != artifact]
    if untied:
        return (f"evidence {', '.join(untied)} is not tied to this param (its `artifact` must be {artifact!r}); "
                "verifying evidence must be recorded against the param itself")
    return None


def _cmd_set(ns: argparse.Namespace, project: Path, params_path: Path, key_path: tuple[str, ...]) -> int:
    text = params_path.read_text() if params_path.is_file() else ""
    data = tomllib.loads(text) if text else {}
    current = _get_leaf(data, key_path)
    current_status = (current or {}).get("status")

    def fail(msg: str) -> int:
        print(f"forge params set: {ns.key}: {msg}", file=sys.stderr)
        return 1

    if current is None and not (ns.value and ns.unit and ns.status and ns.source):
        return fail("does not exist yet; creating one needs --value --unit --status --source.")

    new_leaf = dict(current or {})
    if ns.value is not None:
        new_leaf["value"] = _coerce_value(ns.value)
    if ns.unit is not None:
        new_leaf["unit"] = ns.unit
    if ns.tol_minus is not None or ns.tol_plus is not None:
        tol = dict(new_leaf.get("tol") or {})
        if ns.tol_minus is not None:
            tol["minus"] = ns.tol_minus
        if ns.tol_plus is not None:
            tol["plus"] = ns.tol_plus
        new_leaf["tol"] = tol

    value_changed = current is not None and any(new_leaf.get(f) != current.get(f) for f in _VALUE_FIELDS)
    if value_changed:
        if current_status == "verified" and (not ns.justification or len(ns.justification.strip()) < 10):
            return fail("is status=verified; changing its value needs --justification \"<why>\" "
                        "(CONTRACTS.md §2) of at least a sentence, and --source \"<citation>\".")
        why = _citation_ok(ns.source, current.get("source"))
        if why:
            return fail(why)
        if current_status == "verified":
            if ns.status == "verified" or ns.verified_by or ns.evidence_ids:
                return fail("a changed value cannot keep or claim verification in the same step; the param "
                            "drops to measured. Re-verify afterwards with --status verified --verified-by "
                            "--evidence citing passing evidence for the new value.")
            new_leaf["status"] = "measured"
            new_leaf["verified_by"] = ""
            new_leaf["evidence"] = []
    elif current_status == "verified" and (ns.source is not None or ns.unit is not None
                                           or ns.status not in (None, "verified")):
        if not ns.justification or len(ns.justification.strip()) < 10:
            return fail("is status=verified; changing it needs --justification \"<why>\" (CONTRACTS.md §2).")

    if ns.status is not None:
        new_leaf["status"] = ns.status
    if ns.source is not None:
        new_leaf["source"] = ns.source
    if ns.verified_by is not None:
        new_leaf["verified_by"] = ns.verified_by
    if ns.evidence_ids is not None:
        new_leaf["evidence"] = ns.evidence_ids
    if new_leaf.get("status") != "verified" and (current_status == "verified" or value_changed):
        new_leaf["verified_by"] = ""
        new_leaf["evidence"] = []
    if new_leaf.get("status") == "verified" and current_status != "verified" or (
            new_leaf.get("status") == "verified" and ns.evidence_ids is not None):
        why = _evidence_ok(project, list(new_leaf.get("evidence") or []), ns.key)
        if why:
            return fail(why)

    errors = minischema.validate(new_leaf, _params_schema())
    if errors:
        print(f"forge params set: {ns.key} would violate schemas/params.schema.json:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    new_text = _edit_in_place(text, key_path, new_leaf, current)
    if new_text is not None:
        try:
            ok = _get_leaf(tomllib.loads(new_text), key_path) == new_leaf
        except tomllib.TOMLDecodeError:
            ok = False
        if not ok:
            new_text = None
    if new_text is None:
        _set_leaf(data, key_path, new_leaf)
        new_text = render_params_toml(data)
        print("forge params set: note: the leaf is not a plain [table]; the file was re-serialised and "
              "its comments were not preserved", file=sys.stderr)
    params_path.parent.mkdir(parents=True, exist_ok=True)
    params_path.write_text(new_text)

    if current_status == "verified" or value_changed or ns.justification:
        _append_changelog(project, ns.key, current, new_leaf, ns.justification or ns.source)

    print(f"forge params set: wrote {ns.key} to {params_path}"
          + (" (status dropped to measured: re-verify it)" if value_changed and current_status == "verified" else ""))
    return 0


# S18: the closed vocabulary of units a param leaf may use. A typo (e.g.
# "mmm") or an unrecognised unit is a lint error, not a silent pass. Add
# to this set rather than opening it up (CONTRACTS.md §2: "units must be
# explicit").
UNIT_VOCAB = {
    "mm", "cm", "m", "um", "µm", "in", "mil", "deg", "rad", "sr",
    "g", "kg", "mg", "N", "kN", "Nm", "N*m", "N·m",
    "Pa", "kPa", "MPa", "GPa", "psi", "bar",
    "V", "mV", "kV", "A", "mA", "uA", "µA", "W", "mW", "kW",
    "Hz", "kHz", "MHz", "GHz",
    "s", "ms", "us", "µs", "ns", "min", "h",
    "C", "°C", "K", "F", "°F",
    "ohm", "Ω", "kohm", "kΩ", "uF", "nF", "pF", "H", "mH",
    "%", "1", "ppm",
}

# S18: CONTRACTS.md §2 -- "a page ref for datasheets". A citation of a
# page, table or figure number, not just the word "datasheet".
_PAGE_REF_RE = re.compile(
    r"\b(p\.?\s*\d+|pg\.?\s*\d+|page\s+\d+|table\s+\d+|fig\.?\s*\d+|figure\s+\d+|§\s*\d+|section\s+\d+)\b",
    re.IGNORECASE)


def _lint_leaf(key: str, leaf: dict, schema: dict, evidence_ids: set[str] | None) -> list[str]:
    errors = [f"{key}: {err}" for err in minischema.validate(leaf, schema)]
    if not leaf.get("unit"):
        errors.append(f"{key}: missing unit (every param needs one; use unit = \"1\" for unitless)")
    elif leaf["unit"] not in UNIT_VOCAB:
        errors.append(f"{key}: unit {leaf['unit']!r} is not in the recognised unit vocabulary "
                      f"(forge.commands.params.UNIT_VOCAB) -- fix the unit or add it there")
    if leaf.get("status") == "datasheet" and not _PAGE_REF_RE.search(str(leaf.get("source") or "")):
        errors.append(f"{key}: status=\"datasheet\" needs a page/table/figure reference in `source` "
                      "(CONTRACTS.md §2), e.g. \"... datasheet p.4 Table 2\"")
    if evidence_ids is not None:
        for ev in leaf.get("evidence") or []:
            if ev not in evidence_ids:
                errors.append(f"{key}: evidence {ev!r} does not exist in evidence/manifest.json")
    return errors


def _cmd_lint(ns: argparse.Namespace, params_path: Path) -> int:
    if not params_path.is_file():
        print(f"forge params lint: {params_path} not found", file=sys.stderr)
        return 1
    data = _load_params(params_path)
    schema = _params_schema()
    project = params_path.resolve().parent.parent
    try:
        from .. import evidence as evidence_lib
        evidence_ids: set[str] | None = {
            e.get("id") for e in evidence_lib.load(project).get("entries", []) if isinstance(e, dict)}
    except (OSError, ValueError):
        evidence_ids = None  # can't read the manifest: skip that one check rather than fail closed here
    all_errors: list[str] = []
    count = 0
    for path, leaf in _iter_leaves(data):
        count += 1
        key = ".".join(path)
        all_errors.extend(_lint_leaf(key, leaf, schema, evidence_ids))

    if ns.json:
        print(json.dumps({"count": count, "errors": all_errors}, indent=2, ensure_ascii=False))
    else:
        for err in all_errors:
            print(f"[FAIL] {err}")
        print(f"forge params lint: {count} param(s), {len(all_errors)} error(s)")
    return 1 if all_errors else 0


def run(ns: argparse.Namespace, forge_root: Path) -> int:  # noqa: ARG001
    if tomllib is None:
        print("forge params: no TOML parser available (needs Python 3.11+ tomllib)", file=sys.stderr)
        return 2

    project = ns.project.resolve()
    params_path = project / PARAMS_REL
    key_path = tuple(ns.key.split(".")) if getattr(ns, "key", None) else ()

    try:
        if ns.params_command == "get":
            return _cmd_get(ns, params_path, key_path)
        if ns.params_command == "set":
            return _cmd_set(ns, project, params_path, key_path)
        if ns.params_command == "lint":
            return _cmd_lint(ns, params_path)
    except (ValueError, tomllib.TOMLDecodeError, OSError) as exc:
        print(f"forge params {ns.params_command}: {exc}", file=sys.stderr)
        return 1

    print(f"forge params: unknown subcommand {ns.params_command!r}", file=sys.stderr)
    return 2
