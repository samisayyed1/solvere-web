#!/usr/bin/env python3
"""Verify entrypoint for stacking-tolerances (CONTRACTS.md §9).

Reads every ``analysis/stacks/<name>.toml`` chain (or just ``--changed``
ones), computes worst-case and RSS stacks (and Monte Carlo when the stack
file opts in), and checks the resultant gap against the requirement's
``gap_min``/``gap_max``. Writes one ``out/verify/mech.stack_<name>.json``
per stack via ``forge.checkresult``.

    forge-python skills/stacking-tolerances/scripts/verify.py --project <root> [--changed <path> ...] [--fast]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lib"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from forge.checkresult import Check, CheckContractError  # noqa: E402
from stack_math import StackFileError, evaluate, load_stack  # noqa: E402

_SAFE = re.compile(r"[^a-z0-9_]+")


def _safe_name(name: str) -> str:
    slug = _SAFE.sub("_", name.strip().lower()).strip("_")
    return slug or "stack"


def _find_stack_files(project: Path, changed: list[str]) -> list[Path]:
    stacks_dir = project / "analysis" / "stacks"
    if changed:
        out = []
        for c in changed:
            p = (project / c).resolve() if not Path(c).is_absolute() else Path(c)
            try:
                p.relative_to(stacks_dir.resolve())
            except ValueError:
                continue
            if p.suffix == ".toml" and p.exists():
                out.append(p)
        return sorted(out)
    if not stacks_dir.is_dir():
        return []
    return sorted(stacks_dir.glob("*.toml"))


def _run_one(stack_path: Path, project: Path) -> int:
    try:
        stack = load_stack(stack_path)
    except StackFileError as exc:
        chk = Check(f"mech.stack_{_safe_name(stack_path.stem)}", str(stack_path.relative_to(project)),
                    level="L1", project=project)
        return chk.error(str(exc))

    if stack.gap_min is None or stack.gap_max is None:
        chk = Check(f"mech.stack_{_safe_name(stack.name)}", str(stack_path.relative_to(project)),
                    level="L1", project=project)
        return chk.error(
            f"{stack_path}: [requirement] must set gap_min and gap_max in {stack.unit} "
            "-- a stack without a requirement cannot be checked."
        )

    mc_cfg = {}
    try:
        import tomllib
        mc_cfg = tomllib.loads(stack_path.read_text()).get("monte_carlo", {})
    except Exception:
        mc_cfg = {}
    mc_n = int(mc_cfg.get("n", 0))
    mc_seed = int(mc_cfg.get("seed", 12345))

    check_id = f"mech.stack_{_safe_name(stack.name)}"
    target = str(stack_path.relative_to(project)) if stack_path.is_relative_to(project) else str(stack_path)
    chk = Check(check_id, target, level="L1", project=project)
    try:
        result = evaluate(stack, monte_carlo_n=mc_n, monte_carlo_seed=mc_seed)
        unit = stack.unit
        req_str = f"{stack.name}: gap in [{stack.gap_min}, {stack.gap_max}] {unit}"

        chk.measure(
            "nominal_gap", round(result.nominal_gap, 6), unit,
            min=stack.gap_min, max=stack.gap_max,
            remediation=(
                f"Nominal stack gap {result.nominal_gap:.4f} {unit} is outside "
                f"[{stack.gap_min}, {stack.gap_max}] {unit} even before tolerances are applied. "
                "Re-nominal one or more contributors in the stack, or the requirement is unreachable."
            ),
        )
        chk.measure(
            "worst_case_min", round(result.wc_min, 6), unit, min=stack.gap_min,
            remediation=(
                f"Worst-case minimum gap {result.wc_min:.4f} {unit} < required minimum {stack.gap_min} {unit} "
                f"({req_str}). Tighten a contributor's minus tolerance or loosen the requirement."
            ),
        )
        chk.measure(
            "worst_case_max", round(result.wc_max, 6), unit, max=stack.gap_max,
            remediation=(
                f"Worst-case maximum gap {result.wc_max:.4f} {unit} > required maximum {stack.gap_max} {unit} "
                f"({req_str}). Tighten a contributor's plus tolerance or loosen the requirement."
            ),
        )
        chk.measure(
            "rss_min", round(result.rss_min, 6), unit, min=stack.gap_min,
            remediation=(
                f"RSS minimum gap {result.rss_min:.4f} {unit} < required minimum {stack.gap_min} {unit} "
                f"({req_str}). The statistical stack already fails at RSS confidence; the worst-case stack "
                "will fail too. Rework the tolerance chain."
            ),
        )
        chk.measure(
            "rss_max", round(result.rss_max, 6), unit, max=stack.gap_max,
            remediation=(
                f"RSS maximum gap {result.rss_max:.4f} {unit} > required maximum {stack.gap_max} {unit} "
                f"({req_str}). Rework the tolerance chain."
            ),
        )
        if mc_n > 0:
            chk.measure(
                "monte_carlo_min", round(result.mc_min, 6), unit, min=stack.gap_min,
                remediation=(
                    f"Monte Carlo (n={mc_n}, seed={mc_seed}) sampled a minimum gap of {result.mc_min:.4f} "
                    f"{unit} below the required minimum {stack.gap_min} {unit}. Rework the tolerance chain."
                ),
            )
            chk.measure(
                "monte_carlo_max", round(result.mc_max, 6), unit, max=stack.gap_max,
                remediation=(
                    f"Monte Carlo (n={mc_n}, seed={mc_seed}) sampled a maximum gap of {result.mc_max:.4f} "
                    f"{unit} above the required maximum {stack.gap_max} {unit}. Rework the tolerance chain."
                ),
            )
        chk.tool("python", sys.version.split()[0])
        return chk.finish(notes=(
            f"{len(stack.contributors)} contributors; GD&T intent per ASME Y14.5-2018 (R2024) -- "
            "see references/gdt-intent.md. Worst-case is the extreme-condition bound; RSS assumes "
            "independent, centred contributor distributions at the same confidence band as the input "
            "tolerances."
        ))
    except CheckContractError as exc:
        return chk.error(str(exc))
    except Exception as exc:  # noqa: BLE001 -- fail closed, never a silent pass
        return chk.error(f"{type(exc).__name__}: {exc}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", type=Path, default=Path.cwd())
    ap.add_argument("--changed", action="append", default=[])
    ap.add_argument("--fast", action="store_true", help="accepted for interface compatibility; this check is always fast")
    ns = ap.parse_args()
    project = ns.project.resolve()

    stack_files = _find_stack_files(project, ns.changed)
    if not stack_files:
        print("[SKIP] no analysis/stacks/*.toml files to check")
        return 0

    worst = 0
    for path in stack_files:
        rc = _run_one(path, project)
        worst = max(worst, rc)
    return worst


if __name__ == "__main__":
    sys.exit(main())
