"""A stdlib-only JSON-Schema (draft 2020-12) subset validator.

Forge's own schemas (``plugins/forge/schemas/*.json``) only ever use the
following keywords, so this module implements exactly that subset -- no
external ``jsonschema`` dependency, because hooks and the ``forge`` CLI run
on bare ``python3`` (CONTRACTS.md §8, §10):

    type (incl. union lists), required, properties, additionalProperties
    (false only), enum, const, pattern, minLength, minItems, minimum,
    items, $ref (to "#/$defs/<name>" only), allOf, if/then, format
    (accepted but not enforced -- draft 2020-12 leaves format-assertion
    off by default).

Anything outside that subset (e.g. ``oneOf``, remote ``$ref``, ``anyOf``,
regex ``patternProperties``) is out of scope; Forge's schemas don't use them.

Usage::

    errors = validate(instance, schema)   # [] means valid
    if errors:
        ...report errors...

``errors`` entries are ``"<json-pointer-ish path>: <message>"`` strings,
e.g. ``"criteria[0].severity: value 'huge' not in ['critical', 'major',
'minor']"``.
"""

from __future__ import annotations

import re
from typing import Any

__all__ = ["validate", "SchemaError"]


class SchemaError(ValueError):
    """The *schema* itself uses something this subset validator doesn't support."""


_JSON_TYPES = {
    "object": dict,
    "array": list,
    "string": str,
    "number": (int, float),
    "integer": int,
    "boolean": bool,
    "null": type(None),
}


def _type_ok(value: Any, type_name: str) -> bool:
    if type_name == "number":
        # JSON Schema: bool is not a number, even though Python bool is an int subclass.
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if type_name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if type_name == "boolean":
        return isinstance(value, bool)
    py_type = _JSON_TYPES.get(type_name)
    if py_type is None:
        raise SchemaError(f"unsupported type {type_name!r}")
    return isinstance(value, py_type)


def _resolve_ref(ref: str, root: dict[str, Any]) -> dict[str, Any]:
    if not ref.startswith("#/"):
        raise SchemaError(f"only local '#/...' $ref is supported, got {ref!r}")
    node: Any = root
    for part in ref[2:].split("/"):
        if not isinstance(node, dict) or part not in node:
            raise SchemaError(f"$ref {ref!r} does not resolve in schema")
        node = node[part]
    return node


def _fmt(value: Any) -> str:
    if isinstance(value, str):
        return repr(value)
    return str(value)


def _validate(instance: Any, schema: dict[str, Any], root: dict[str, Any], path: str, errors: list[str]) -> None:
    if "$ref" in schema:
        schema = {**_resolve_ref(schema["$ref"], root), **{k: v for k, v in schema.items() if k != "$ref"}}

    if "const" in schema:
        if instance != schema["const"]:
            errors.append(f"{path}: value {_fmt(instance)} != const {_fmt(schema['const'])}")

    if "enum" in schema:
        if instance not in schema["enum"]:
            errors.append(f"{path}: value {_fmt(instance)} not in {schema['enum']}")

    if "type" in schema:
        types = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(_type_ok(instance, t) for t in types):
            errors.append(f"{path}: expected type {schema['type']!r}, got {type(instance).__name__}")
            return  # further structural checks would be meaningless

    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            errors.append(f"{path}: length {len(instance)} < minLength {schema['minLength']}")
        if "pattern" in schema and re.search(schema["pattern"], instance) is None:
            errors.append(f"{path}: value {instance!r} does not match pattern {schema['pattern']!r}")

    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append(f"{path}: value {instance} < minimum {schema['minimum']}")

    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            errors.append(f"{path}: {len(instance)} item(s) < minItems {schema['minItems']}")
        items_schema = schema.get("items")
        if items_schema is not None:
            for i, item in enumerate(instance):
                _validate(item, items_schema, root, f"{path}[{i}]", errors)

    if isinstance(instance, dict):
        properties = schema.get("properties", {})
        for req in schema.get("required", []):
            if req not in instance:
                errors.append(f"{path}: missing required property {req!r}")
        if schema.get("additionalProperties") is False:
            allowed = set(properties)
            extra = set(instance) - allowed
            if extra:
                errors.append(f"{path}: unexpected propert{'y' if len(extra) == 1 else 'ies'} {sorted(extra)}")
        for key, subschema in properties.items():
            if key in instance:
                _validate(instance[key], subschema, root, f"{path}.{key}" if path else key, errors)

    for subschema in schema.get("allOf", []):
        _validate(instance, subschema, root, path, errors)

    if "if" in schema:
        cond_errors: list[str] = []
        _validate(instance, schema["if"], root, path, cond_errors)
        if not cond_errors and "then" in schema:
            _validate(instance, schema["then"], root, path, errors)
        elif cond_errors and "else" in schema:
            _validate(instance, schema["else"], root, path, errors)


def validate(instance: Any, schema: dict[str, Any]) -> list[str]:
    """Validate ``instance`` against ``schema``. Returns a list of error
    strings; an empty list means the instance is valid."""
    errors: list[str] = []
    _validate(instance, schema, schema, "$", errors)
    return errors
