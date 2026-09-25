"""forge_cad -- CAD-env measurement library (CONTRACTS.md §9-10, §12).

Importable by any Forge skill script that runs on ``~/.forge/bin/forge-python``
(the CAD env: build123d 0.11.1, OCP, trimesh, pyvista, numpy -- CONTRACTS §10).
It has two modules:

  - ``forge_cad.load``    -- get a build123d ``Shape`` from a part module or STEP file.
  - ``forge_cad.measure`` -- robust, documented geometry measurements: validity,
    watertight export, bounding box, volume/area/mass, min wall thickness,
    clearance/interference, draft angle, min concave radius, hole-to-edge
    distance and boss/rib thickness.

``forge_cad`` never writes ``out/verify/*.json`` itself -- that is
``forge.checkresult`` (CONTRACTS §3). Skills call ``forge_cad.measure.*`` to get
numbers, then hand them to ``forge.checkresult.Check.measure(...)`` for the
pass/fail-with-remediation record.

This package is CAD-env only (build123d/OCP/trimesh are not stdlib); it is
never imported by ``plugins/forge/lib/forge`` (stdlib-only, CONTRACTS §10).
"""

from __future__ import annotations

__all__ = ["load", "measure"]
