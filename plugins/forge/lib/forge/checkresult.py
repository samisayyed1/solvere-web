"""Writer for domain check results (CONTRACTS.md §3, schema ``forge.check/1``).

Every Forge verification script records measurements through :class:`Check`, so
all checks share one format, one exit-code convention and one rule: a failing
measurement must say how to fix it.

    with run_check("geometry.min_wall", "cad/enclosure.py", project=root) as chk:
        chk.tool("build123d", build123d.__version__)
        chk.measure("min_wall", 1.62, "mm", min=2.0, requirement="REQ-MECH-004",
                    remediation="Thicken the lid lip to >= 2.0 mm (params enclosure.wall_thickness).")
    # exits 0 pass / 1 fail / 2 internal error; writes out/verify/geometry.min_wall.json

Standard library only.
"""

from __future__ import annotations

import contextlib
import json
import math
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Iterator

SCHEMA = "forge.check/1"
LEVELS = ("L0", "L1", "L2", "L3", "L4", "L5")
_CHECK_ID = re.compile(r"^[a-z0-9_]+(\.[a-z0-9_]+)+$")
_REQ_ID = re.compile(r"^REQ-[A-Z]+-[0-9]{3,}$")


class CheckContractError(ValueError):
    """The check itself is malformed (a bug in the check, not a design failure)."""


def git_sha(project: Path) -> str:
    """HEAD sha of ``project``, suffixed ``-dirty`` for uncommitted changes; ``nogit`` outside git."""
    try:
        sha = subprocess.run(["git", "-C", str(project), "rev-parse", "HEAD"],
                             capture_output=True, text=True, timeout=10, check=True).stdout.strip()
        dirty = subprocess.run(["git", "-C", str(project), "status", "--porcelain"],
                               capture_output=True, text=True, timeout=10).stdout.strip()
        return sha + ("-dirty" if dirty else "")
    except (OSError, subprocess.SubprocessError):
        return "nogit"


def _within(value: Any, *, min: float | None, max: float | None, equals: Any, tol: float | None) -> bool:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if isinstance(value, float) and math.isnan(value):
            return False
        if min is not None and value < min:
            return False
        if max is not None and value > max:
            return False
        if equals is not None:
            return abs(value - equals) <= (tol or 0.0)
        return True
    if min is not None or max is not None:
        raise CheckContractError(f"min/max limits need a numeric value, got {value!r}")
    return value == equals


class Check:
    """Accumulates measurements for one check and writes the result file."""

    def __init__(self, check_id: str, target: str, *, level: str = "L1",
                 project: Path | str = ".", out_dir: str = "out/verify") -> None:
        if not _CHECK_ID.match(check_id):
            raise CheckContractError(f"check_id {check_id!r} must look like 'domain.name'")
        if level not in LEVELS:
            raise CheckContractError(f"level {level!r} not in {LEVELS}")
        self.check_id, self.target, self.level = check_id, target, level
        self.project = Path(project).resolve()
        self.out_path = self.project / out_dir / f"{check_id}.json"
        self.measurements: list[dict[str, Any]] = []
        self.tool_versions: dict[str, str] = {}
        self._t0 = time.time()
        self.started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(self._t0))

    def tool(self, name: str, version: str) -> None:
        self.tool_versions[name] = str(version)

    def measure(self, name: str, value: Any, unit: str, *, min: float | None = None,
                max: float | None = None, equals: Any = None, tol: float | None = None,
                requirement: str | None = None, location: str | None = None,
                remediation: str | None = None) -> bool:
        """Record one measurement against its limit; returns whether it passed.

        A failing measurement without a remediation string is a bug in the check
        and raises :class:`CheckContractError` (reported as exit 2).
        """
        if not unit:
            raise CheckContractError(f"measurement {name!r} has no unit (use '1' for unitless)")
        if min is None and max is None and equals is None:
            raise CheckContractError(f"measurement {name!r} has no limit, so it cannot fail")
        if requirement is not None and not _REQ_ID.match(requirement):
            raise CheckContractError(f"requirement id {requirement!r} is not REQ-<AREA>-<NNN>")
        ok = _within(value, min=min, max=max, equals=equals, tol=tol)
        if not ok and not (remediation and len(remediation) >= 10):
            raise CheckContractError(f"measurement {name!r} failed without a remediation string")
        limit = {k: v for k, v in (("min", min), ("max", max), ("equals", equals), ("tol", tol)) if v is not None}
        row: dict[str, Any] = {"name": name, "value": value, "unit": unit, "limit": limit, "pass": ok}
        for key, val in (("requirement", requirement), ("location", location), ("remediation", remediation)):
            if val is not None:
                row[key] = val
        self.measurements.append(row)
        return ok

    @property
    def passed(self) -> bool:
        return bool(self.measurements) and all(m["pass"] for m in self.measurements)

    def _write(self, status: str, error: str | None = None, notes: str | None = None) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema": SCHEMA, "check_id": self.check_id, "target": self.target, "status": status,
            "level": self.level, "measurements": self.measurements, "tool_versions": self.tool_versions,
            "git_sha": git_sha(self.project), "started": self.started,
            "duration_s": round(time.time() - self._t0, 3),
        }
        if error:
            result["error"] = error
        if notes:
            result["notes"] = notes
        self.out_path.parent.mkdir(parents=True, exist_ok=True)
        self.out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
        return result

    def finish(self, notes: str | None = None) -> int:
        """Write the result and print a summary. Returns 0 pass, 1 fail, 2 if nothing was measured."""
        if not self.measurements:
            return self.error("check recorded no measurements, so it cannot have passed")
        status = "pass" if self.passed else "fail"
        self._write(status, notes=notes)
        print(f"[{status.upper()}] {self.check_id} ({self.target})")
        for m in self.measurements:
            if not m["pass"]:
                print(f"  - {m['name']} = {m['value']} {m['unit']} vs {m['limit']}: {m['remediation']}")
        return 0 if status == "pass" else 1

    def error(self, message: str) -> int:
        self._write("error", error=message)
        print(f"[ERROR] {self.check_id} ({self.target}): {message}", file=sys.stderr)
        return 2


@contextlib.contextmanager
def run_check(check_id: str, target: str, **kwargs: Any) -> Iterator[Check]:
    """Context manager that finishes the check and exits the process fail-closed.

    Any exception inside the block (including a malformed check) becomes an
    ``error`` result with exit code 2, never a pass.
    """
    chk = Check(check_id, target, **kwargs)
    try:
        yield chk
    except Exception as exc:  # noqa: BLE001 -- fail closed by design
        sys.exit(chk.error(f"{type(exc).__name__}: {exc}"))
    sys.exit(chk.finish())
