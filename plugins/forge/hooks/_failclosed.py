"""Fail-closed wrapper for every Forge hook script (CONTRACTS.md §8, brief §3.4).

Every hook module defines ``handle(data: dict) -> tuple[int, dict | None]``
and ends with::

    if __name__ == "__main__":
        from _failclosed import run_hook
        run_hook(handle)

:func:`run_hook`:

- reads and parses stdin as JSON (empty/whitespace-only stdin -> ``{}``);
- calls ``handle(data)``;
- prints the returned dict as JSON (via ``json.dumps``, never string
  concatenation) to stdout when it is not ``None``;
- exits the process with the returned code.

Any exception anywhere in that sequence -- malformed stdin, a bug in the
handler, an unreadable file, an unexpected schema -- is caught right here
and turned into **exit code 2** with a single-line reason on stderr. That
is the platform's own fail-closed contract (R1a §17: exit 2 is the only
code that reliably blocks; 1, a missing script, or bad JSON all fail
*open*). Centralising the ``try/except`` in this one module, rather than
repeating it in every hook, is what makes "any exception -> exit 2" true
for every hook without relying on each author to remember it.

Standard library only.
"""

from __future__ import annotations

import json
import os
import sys
import traceback
from typing import Callable

Handler = Callable[[dict], "tuple[int, dict | None]"]

_DEBUG_ENV = "FORGE_HOOK_DEBUG"


def _read_stdin() -> dict:
    raw = sys.stdin.read()
    if not raw or not raw.strip():
        return {}
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError(f"hook stdin JSON must be an object, got {type(data).__name__}")
    return data


def run_hook(handle: Handler) -> None:
    """Read stdin, run ``handle``, emit JSON, exit. Never raises."""
    try:
        data = _read_stdin()
        code, output = handle(data)
        if not isinstance(code, int):
            raise TypeError(f"handle() must return an int exit code, got {type(code).__name__}")
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001 -- fail closed by design, see module docstring
        print(f"forge hook error: {type(exc).__name__}: {exc}", file=sys.stderr)
        if os.environ.get(_DEBUG_ENV):
            traceback.print_exc(file=sys.stderr)
        sys.exit(2)

    if output is not None:
        try:
            payload = json.dumps(output)
        except Exception as exc:  # noqa: BLE001 -- still fail closed on an encode bug
            print(f"forge hook error: could not encode output JSON: {exc}", file=sys.stderr)
            sys.exit(2)
        print(payload)
    sys.exit(code)
