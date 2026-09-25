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

**Entry point.** ``hooks.json`` runs every hook as
``python3 hooks/_failclosed.py <hook_module>`` rather than the hook script
itself, so that *importing* the hook (its ``_common``/``forge.*`` imports,
the ``tomllib`` requirement) also happens inside the ``try``: an
``ImportError`` at module import time in a directly-run script would exit 1,
which the platform treats as fail-OPEN (review #1, C3). Running a hook
script directly still works (tests, debugging); ``_common`` then exits 2
itself when ``tomllib`` is missing.

Standard library only; keep this file importable on old Pythons (no syntax
newer than 3.7) so it can report "Python too old" instead of crashing.
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


HOOK_MODULES = (
    "session_start", "user_prompt_submit", "user_prompt_expansion", "pre_tool_use",
    "post_tool_use", "stop", "subagent_stop", "pre_compact",
)


def _reraise_exit(exc: SystemExit) -> None:
    """Only exit codes 0 and 2 mean something to the platform; any other
    ``SystemExit`` (1, a message string, None) raised under a hook would fail
    OPEN, so it becomes 2."""
    if exc.code in (0, 2):
        raise exc
    print(f"forge hook error: unexpected exit {exc.code!r}", file=sys.stderr)
    sys.exit(2)


def main(argv: "list[str] | None" = None) -> None:
    """``python3 _failclosed.py <hook_module>``: import the hook inside the
    fail-closed ``try`` and run its ``handle``."""
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        if len(argv) != 1 or argv[0] not in HOOK_MODULES:
            raise ValueError(f"usage: _failclosed.py <{'|'.join(HOOK_MODULES)}>, got {argv!r}")
        if sys.version_info < (3, 11):
            raise RuntimeError(
                f"Python {sys.version.split()[0]} at {sys.executable} is too old for Forge hooks "
                "(needs >= 3.11 for tomllib); guardrails cannot run, so this is blocked. Put a "
                "Python >= 3.11 first on PATH as `python3` and restart Claude Code.")
        os.environ["FORGE_HOOK_WRAPPED"] = "1"
        hooks_dir = os.path.dirname(os.path.abspath(__file__))
        if hooks_dir not in sys.path:
            sys.path.insert(0, hooks_dir)
        import importlib
        module = importlib.import_module(argv[0])
        handle = getattr(module, "handle")
    except SystemExit as exc:
        _reraise_exit(exc)
    except BaseException as exc:  # noqa: BLE001 -- fail closed by design
        print(f"forge hook error: {type(exc).__name__}: {exc}", file=sys.stderr)
        if os.environ.get(_DEBUG_ENV):
            traceback.print_exc(file=sys.stderr)
        sys.exit(2)
    run_hook(handle)


def run_hook(handle: Handler) -> None:
    """Read stdin, run ``handle``, emit JSON, exit. Never raises."""
    try:
        data = _read_stdin()
        code, output = handle(data)
        if not isinstance(code, int):
            raise TypeError(f"handle() must return an int exit code, got {type(code).__name__}")
    except SystemExit as exc:
        _reraise_exit(exc)
    except BaseException as exc:  # noqa: BLE001 -- fail closed by design, see module docstring
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


if __name__ == "__main__":
    main()
