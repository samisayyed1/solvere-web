"""mech2-local pytest config: registers the 'slow' marker used across this directory's
suites (real CalculiX/FreeCAD/PyVista/Blender runs), scoped here so it doesn't touch the
shared plugins/forge/tests/conftest.py other builders own.
"""
from __future__ import annotations


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "slow: exercises a real external tool (CalculiX, freecadcmd, PyVista, Blender)"
    )
