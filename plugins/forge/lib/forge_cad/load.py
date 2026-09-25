"""Load a part into a build123d ``Shape`` for measurement.

Two sources, matching CONTRACTS.md and the R3 implications doc:

- **A build123d part module** (`modeling-cad-parts`' convention: "part files
  export ``build()``"). The module is imported fresh (not via ``sys.path``
  package import) so sibling part files with the same stem never collide,
  and ``build()`` is called to get the current geometry -- never a cached
  import, so measurement always reflects the file on disk.
- **A STEP file**, for measuring a released or externally-supplied part.

Both return a plain build123d ``Shape`` (``Solid`` or ``Compound``), ready for
``forge_cad.measure``.
"""

from __future__ import annotations

import importlib.util
import inspect
import sys
import uuid
from pathlib import Path
from typing import Any, Mapping

import build123d as bd

__all__ = ["load_part", "load_step", "PartLoadError"]


class PartLoadError(RuntimeError):
    """The module/file did not yield a measurable build123d ``Shape``."""


def _as_shape(obj: Any, source: str) -> bd.Shape:
    """Coerce ``build()``'s / ``PART``'s return value into a ``Shape``.

    Accepts a bare ``Shape`` (``Solid``/``Compound``/``Part``), or a
    build123d ``Builder`` context object (``BuildPart``) left un-exited by a
    part module that forgot the ``with`` block's return -- both expose the
    finished geometry as ``.part``.
    """
    if isinstance(obj, bd.Shape):
        if obj.is_null:
            raise PartLoadError(f"{source} produced an empty/null shape")
        return obj
    part = getattr(obj, "part", None)
    if isinstance(part, bd.Shape):
        return part
    raise PartLoadError(
        f"{source} must expose a build123d Shape via build()/PART, got {type(obj)!r} "
        "(CONTRACTS: part files export build())"
    )


def load_part(module_path: str | Path, *, params: Mapping[str, Any] | None = None) -> bd.Shape:
    """Import ``module_path`` and return its built geometry.

    The module must define a zero-arg (or ``params=``-accepting) callable
    ``build()`` returning a build123d ``Shape``, or a module-level ``PART``
    already holding one. When ``build()`` accepts a ``params`` keyword,
    ``params`` (typically the parsed ``params/params.toml`` mapping) is
    passed through so the part is built from the single source of truth
    (CONTRACTS §2), never a value baked into the module.

    Raises ``FileNotFoundError`` if the module is missing and
    :class:`PartLoadError` if it does not expose ``build()``/``PART``, or if
    either yields something other than a ``Shape``.
    """
    module_path = Path(module_path).resolve()
    if not module_path.is_file():
        raise FileNotFoundError(f"part module not found: {module_path}")

    # A unique module name avoids clobbering sys.modules when two parts
    # share a filename stem (e.g. two enclosure.py under different cad/ dirs).
    mod_name = f"forge_cad_part_{module_path.stem}_{uuid.uuid4().hex[:8]}"
    spec = importlib.util.spec_from_file_location(mod_name, module_path)
    if spec is None or spec.loader is None:
        raise PartLoadError(f"could not build an import spec for {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(mod_name, None)

    build_fn = getattr(module, "build", None)
    if callable(build_fn):
        sig = inspect.signature(build_fn)
        if params is not None and "params" in sig.parameters:
            result = build_fn(params=params)
        else:
            result = build_fn()
        return _as_shape(result, f"{module_path.name}:build()")

    if hasattr(module, "PART"):
        return _as_shape(module.PART, f"{module_path.name}:PART")

    raise PartLoadError(
        f"{module_path} exposes neither build() nor PART (CONTRACTS: part files export build())"
    )


def load_step(step_path: str | Path) -> bd.Shape:
    """Import a STEP file and return its geometry as a build123d ``Shape``."""
    step_path = Path(step_path).resolve()
    if not step_path.is_file():
        raise FileNotFoundError(f"STEP file not found: {step_path}")
    shape = bd.import_step(str(step_path))
    if shape is None:
        raise PartLoadError(f"{step_path} imported no geometry")
    return _as_shape(shape, step_path.name)
