"""forge_cad-specific fixtures. The top-level tests/conftest.py already puts
plugins/forge/lib on sys.path, which is enough for `from forge_cad import ...`
since forge_cad is a sibling package under lib/.

Deliberately not a ``conftest.py``: ``tests/mech/`` has no ``__init__.py``,
so pytest's default "prepend" import mode would name it bare ``conftest``,
colliding with ``plugins/forge/tests/conftest.py`` and breaking that file's
``from conftest import BIN_GUARD, ...`` users (see tests/hooks/hookutil.py
for the full explanation). To use the fixture, a test module does
``from mechutil import fixture_project``."""

from __future__ import annotations

from pathlib import Path

import pytest

MECH_TESTS_DIR = Path(__file__).resolve().parent
FIXTURE_PROJECT = MECH_TESTS_DIR.parent / "fixtures" / "mech_project"


@pytest.fixture
def fixture_project() -> Path:
    return FIXTURE_PROJECT
