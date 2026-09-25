"""``forge params get|set|lint`` (CONTRACTS.md §2, §11).

``params/params.toml`` is the single source of truth for every dimension
and value used in CAD, ECAD, firmware or analysis. Each leaf is a small
table (``value``, ``unit``, optional ``tol``, ``status``, ``source``,
optional ``verified_by``/``evidence``) validated against
``schemas/params.schema.json``.

``set`` on a leaf whose *current* ``status`` is ``verified`` requires
``--justification`` (a sentence naming the source) and appends the old
value, the justification and a timestamp to ``params/CHANGELOG.md`` --
this is the sourced, audited path the PreToolUse hook's verified-param
guard points agents at instead of a direct file edit.

**Round-trip note:** the standard library has no TOML *writer*, so ``set``
re-serializes the whole file from the parsed structure (via
:func:`render_params_toml`) rather than doing an in-place text edit. This
is correct -- every field the schema and CHANGELOG care about round-trips
exactly -- but it does not preserve comments or original formatting.
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


def _cmd_set(ns: argparse.Namespace, project: Path, params_path: Path, key_path: tuple[str, ...]) -> int:
    data = _load_params(params_path)
    current = _get_leaf(data, key_path)
    current_status = (current or {}).get("status")

    if current_status == "verified":
        if not ns.justification or len(ns.justification.strip()) < 10:
            print(f"forge params set: {ns.key} is status=verified; changing it needs "
                  "--justification \"<source>\" (CONTRACTS.md §2) of at least a sentence.", file=sys.stderr)
            return 1

    if current is None and not (ns.value and ns.unit and ns.status and ns.source):
        print(f"forge params set: {ns.key} does not exist yet; creating one needs "
              "--value --unit --status --source.", file=sys.stderr)
        return 1

    new_leaf = dict(current or {})
    if ns.value is not None:
        new_leaf["value"] = _coerce_value(ns.value)
    if ns.unit is not None:
        new_leaf["unit"] = ns.unit
    if ns.status is not None:
        new_leaf["status"] = ns.status
    if ns.source is not None:
        new_leaf["source"] = ns.source
    if ns.verified_by is not None:
        new_leaf["verified_by"] = ns.verified_by
    if ns.evidence_ids is not None:
        new_leaf["evidence"] = ns.evidence_ids
    if ns.tol_minus is not None or ns.tol_plus is not None:
        tol = dict(new_leaf.get("tol") or {})
        if ns.tol_minus is not None:
            tol["minus"] = ns.tol_minus
        if ns.tol_plus is not None:
            tol["plus"] = ns.tol_plus
        new_leaf["tol"] = tol

    errors = minischema.validate(new_leaf, _params_schema())
    if errors:
        print(f"forge params set: {ns.key} would violate schemas/params.schema.json:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    _set_leaf(data, key_path, new_leaf)
    params_path.parent.mkdir(parents=True, exist_ok=True)
    params_path.write_text(render_params_toml(data))

    if current_status == "verified" or ns.justification:
        _append_changelog(project, ns.key, current, new_leaf, ns.justification)

    print(f"forge params set: wrote {ns.key} to {params_path}")
    return 0


def _cmd_lint(ns: argparse.Namespace, params_path: Path) -> int:
    if not params_path.is_file():
        print(f"forge params lint: {params_path} not found", file=sys.stderr)
        return 1
    data = _load_params(params_path)
    schema = _params_schema()
    all_errors: list[str] = []
    count = 0
    for path, leaf in _iter_leaves(data):
        count += 1
        key = ".".join(path)
        for err in minischema.validate(leaf, schema):
            all_errors.append(f"{key}: {err}")
        if not leaf.get("unit"):
            all_errors.append(f"{key}: missing unit (every param needs one; use unit = \"1\" for unitless)")

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
