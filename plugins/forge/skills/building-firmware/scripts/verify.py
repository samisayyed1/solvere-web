#!/usr/bin/env python3
"""building-firmware verify entrypoint (CONTRACTS.md §9, fw domain: host build, unit
tests, static analysis, size/timing budgets, mutation check).

    forge-python skills/building-firmware/scripts/verify.py --project <root> [--changed <path> ...] [--fast]

Convention (references/mutation-testing.md, references/forge_test.h): each
``firmware/tests/test_<name>.c`` is compiled and linked with every ``firmware/src/*.c``
file, against ``firmware/include/`` and this skill's own ``forge_test.h`` (no download --
it ships with the skill). For each module:

1. **Host build + unit tests**: ``cc -std=c11 -Wall -Wextra`` the module; run the binary;
   parse its ``FORGE_SUMMARY <count> <failures>`` line and its exit code.
2. **Static analysis**: ``cc --analyze -Xanalyzer -analyzer-output=text`` on every source
   file; count analyzer warnings.
3. **Size budget**: if ``params/params.toml`` declares
   ``[firmware.<name>] size_budget_bytes``, compiles ``firmware/src/<name>.c`` alone with
   ``-Os -c`` and checks the object file's size against it.
4. **Mutation check** (the point of this script, brief §0 "prove every check can fail"):
   greps the module's sources for a ``FORGE_MUTANT`` guard (references/mutation-testing.md);
   errors if none exists; otherwise rebuilds with ``-DFORGE_MUTANT`` and requires at least
   one test to now fail. A test suite that still passes under the mutant FAILS this check.
5. **Target cross-compile**: if ``arm-none-eabi-gcc`` (or ``$FORGE_CROSS_CC``) exists,
   cross-compiles each source file and checks size against the budget instead of the host
   approximation. If absent, this rung SKIPs with the toolchain fix -- it never fakes a
   pass by silently falling back to the host number.

Missing `cc` -> exit 2 with the fix. No `firmware/tests/test_*.c` (or none match
`--changed`) -> exit 0, `[SKIP] ...`.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lib"))

from forge.checkresult import Check  # noqa: E402

try:
    import tomllib
except ImportError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]

REFERENCES_DIR = Path(__file__).resolve().parents[1] / "references"
_SUMMARY_RE = re.compile(r"^FORGE_SUMMARY (\d+) (\d+)\s*$", re.MULTILINE)
_ANALYZER_WARNING_RE = re.compile(r"^\S+\.c:\d+:\d+: warning:", re.MULTILINE)
_NON_SLUG = re.compile(r"[^a-z0-9_]+")


def _slug(name: str) -> str:
    return _NON_SLUG.sub("_", name.lower()).strip("_") or "module"


def find_modules(project: Path) -> dict[str, Path]:
    """``{module_name: test_file_path}`` for every ``firmware/tests/test_<name>.c``."""
    tests_dir = project / "firmware" / "tests"
    if not tests_dir.exists():
        return {}
    return {p.stem[len("test_"):]: p for p in sorted(tests_dir.glob("test_*.c"))}


def filter_by_changed(modules: dict[str, Path], changed: list[str] | None) -> dict[str, Path]:
    if changed is None:
        return modules
    changed_strs = {Path(c).as_posix() for c in changed}
    if any(s.startswith("firmware/") for s in changed_strs):
        return modules  # any firmware change re-runs every module (source is shared)
    return {}


def source_files(project: Path) -> list[Path]:
    src_dir = project / "firmware" / "src"
    return sorted(src_dir.glob("*.c")) if src_dir.exists() else []


def load_budget(project: Path, module: str) -> dict[str, Any]:
    path = project / "params" / "params.toml"
    if not path.exists():
        return {}
    data = tomllib.loads(path.read_text())
    return data.get("firmware", {}).get(module, {})


def _run(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess:
    return subprocess.run(argv, capture_output=True, text=True, timeout=kwargs.pop("timeout", 60), **kwargs)


def compile_and_link(cc: str, test_file: Path, sources: list[Path], include_dir: Path,
                     out_bin: Path, *, extra_defines: list[str] | None = None) -> subprocess.CompletedProcess:
    argv = [cc, "-std=c11", "-Wall", "-Wextra", "-I", str(include_dir), "-I", str(REFERENCES_DIR)]
    for d in extra_defines or []:
        argv += ["-D", d]
    argv += [str(test_file), *[str(s) for s in sources], "-o", str(out_bin)]
    return _run(argv)


def run_tests(binary: Path) -> tuple[bool, int, int, str]:
    """Returns (build_ok_and_ran, count, failures, raw_output)."""
    try:
        proc = _run([str(binary)], timeout=30)
    except (OSError, subprocess.SubprocessError) as exc:
        return False, 0, 0, f"could not run {binary}: {exc}"
    output = proc.stdout + proc.stderr
    m = _SUMMARY_RE.search(output)
    if not m:
        return False, 0, 0, output or f"(no output; exit code {proc.returncode})"
    count, failures = int(m.group(1)), int(m.group(2))
    # cross-check: exit code must agree with the summary line, or something's wrong
    exit_agrees = (proc.returncode == 0) == (failures == 0)
    return exit_agrees, count, failures, output


def static_analysis_warnings(cc: str, sources: list[Path], include_dir: Path) -> tuple[int, str]:
    total = 0
    details = []
    for src in sources:
        proc = _run([cc, "--analyze", "-Xanalyzer", "-analyzer-output=text",
                     "-I", str(include_dir), str(src), "-o", os.devnull])
        found = _ANALYZER_WARNING_RE.findall(proc.stdout + proc.stderr)
        total += len(found)
        if found:
            details.append(f"{src.name}: {len(found)} warning(s)")
    return total, "; ".join(details)


def has_mutation_point(sources: list[Path]) -> bool:
    return any("FORGE_MUTANT" in s.read_text(errors="ignore") for s in sources)


def cc_version(cc: str) -> str:
    try:
        proc = _run([cc, "--version"], timeout=10)
        first_line = (proc.stdout or proc.stderr).splitlines()
        return first_line[0] if first_line else cc
    except (OSError, subprocess.SubprocessError):
        return cc


def verify_module(module: str, test_file: Path, project: Path, out_dir: Path, cc: str,
                   cross_cc: str | None) -> int:
    check_id = f"firmware.{_slug(module)}"
    chk = Check(check_id, f"firmware/tests/{test_file.name}", project=project, level="L1")
    build_dir = out_dir / "fw_build"
    try:
        build_dir.mkdir(parents=True, exist_ok=True)
        include_dir = project / "firmware" / "include"
        sources = source_files(project)
        if not sources:
            raise RuntimeError("no firmware/src/*.c found to build against")

        # 1. host build + unit tests
        bin_path = build_dir / f"test_{_slug(module)}"
        build = compile_and_link(cc, test_file, sources, include_dir, bin_path)
        chk.tool("cc", cc_version(cc))
        if build.returncode != 0:
            raise RuntimeError(f"host build failed:\n{build.stderr}")
        ok, count, failures, output = run_tests(bin_path)
        if not ok:
            raise RuntimeError(f"test binary output didn't match the forge_test.h contract:\n{output}")
        chk.measure("tests_run", count, "1", min=1,
                   remediation=f"{test_file.name} defines no FORGE_CHECK assertions; a test file must test something.")
        chk.measure("test_failures", failures, "1", max=0,
                   remediation=f"{failures} of {count} test(s) failed; see output above.")

        # 2. static analysis
        warn_count, warn_detail = static_analysis_warnings(cc, sources, include_dir)
        chk.measure("static_analysis_warnings", warn_count, "1", max=0,
                   remediation=f"clang --analyze found {warn_count} issue(s): {warn_detail}")

        # 3 / 5. size budget: prefer the real target build; fall back to a host proxy
        budget = load_budget(project, module)
        size_budget = budget.get("size_budget_bytes")
        if size_budget is not None:
            module_src = project / "firmware" / "src" / f"{module}.c"
            if module_src.exists():
                if cross_cc:
                    obj = build_dir / f"{module}.target.o"
                    proc = _run([cross_cc, "-Os", "-I", str(include_dir), "-c", str(module_src), "-o", str(obj)])
                    if proc.returncode != 0:
                        raise RuntimeError(f"target cross-compile of {module_src.name} failed:\n{proc.stderr}")
                    size = obj.stat().st_size
                    chk.measure("target_size_bytes", size, "1", max=float(size_budget),
                               remediation=f"{module}.c's target object is {size} B, over the "
                                           f"{size_budget} B budget in params.toml [firmware.{module}].")
                else:
                    print(f"[SKIP] firmware.{module}: target size budget needs arm-none-eabi-gcc "
                          "(or $FORGE_CROSS_CC); install via plugins/forge/toolchain/install.sh embedded. "
                          "Falling back to a HOST -Os proxy measurement (not the real target number).")
                    obj = build_dir / f"{module}.host.o"
                    proc = _run([cc, "-Os", "-I", str(include_dir), "-c", str(module_src), "-o", str(obj)])
                    if proc.returncode == 0:
                        size = obj.stat().st_size
                        chk.measure("host_size_proxy_bytes", size, "1", max=float(size_budget) * 4,
                                   remediation=f"{module}.c's HOST object is {size} B -- unusually large even "
                                               "allowing for the missing target toolchain; investigate.")

        # 4. mutation check -- the check that must be provably able to fail
        if not has_mutation_point(sources):
            raise RuntimeError(
                f"no #ifdef FORGE_MUTANT guard found in firmware/src/*.c for module {module!r}; "
                "add one (references/mutation-testing.md) so this check can prove the test suite can fail"
            )
        mutant_bin = build_dir / f"test_{_slug(module)}_mutant"
        mutant_build = compile_and_link(cc, test_file, sources, include_dir, mutant_bin,
                                        extra_defines=["FORGE_MUTANT"])
        if mutant_build.returncode != 0:
            raise RuntimeError(f"mutant build failed to compile:\n{mutant_build.stderr}")
        _, mutant_count, mutant_failures, mutant_output = run_tests(mutant_bin)
        mutant_caught = 1 if mutant_failures > 0 else 0
        chk.measure("mutation_kills", mutant_caught, "1", equals=1,
                   remediation=f"tests for {module!r} still ALL PASSED when rebuilt with -DFORGE_MUTANT "
                               f"({mutant_count} run, {mutant_failures} failed) -- the test suite is a "
                               "no-op and would not catch a real regression. Assert on real behaviour, "
                               "not tautologies.")

        return chk.finish()
    except Exception as exc:  # noqa: BLE001 -- fail closed
        return chk.error(f"{type(exc).__name__}: {exc}")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True, type=Path)
    ap.add_argument("--changed", nargs="*", default=None)
    ap.add_argument("--fast", action="store_true")
    ns = ap.parse_args(argv)
    project = ns.project.resolve()

    modules = filter_by_changed(find_modules(project), ns.changed)
    if not modules:
        suffix = " matching --changed" if ns.changed is not None else ""
        print(f"[SKIP] no firmware/tests/test_*.c{suffix}")
        return 0

    cc = shutil.which("cc") or shutil.which("clang")
    if not cc:
        print("[ERROR] no C compiler (cc/clang) found; run plugins/forge/toolchain/install.sh core "
              "(Xcode Command Line Tools)", file=sys.stderr)
        return 2

    cross_cc = os.environ.get("FORGE_CROSS_CC") or shutil.which("arm-none-eabi-gcc")
    if not cross_cc:
        print("[SKIP] arm-none-eabi-gcc not found; target cross-compile and the real target size "
              "budget are skipped for every module. Install: "
              "plugins/forge/toolchain/install.sh embedded (Zephyr SDK / arm-none-eabi-gcc).")

    out_dir = project / "out" / "verify"
    out_dir.mkdir(parents=True, exist_ok=True)

    codes = [verify_module(module, test_file, project, out_dir, cc, cross_cc)
             for module, test_file in sorted(modules.items())]
    if any(c == 2 for c in codes):
        return 2
    if any(c == 1 for c in codes):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
