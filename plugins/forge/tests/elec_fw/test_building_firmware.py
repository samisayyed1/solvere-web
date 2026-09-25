"""building-firmware verify.py: tests pass on good code, and the mutation check catches
a no-op test suite (CONTRACTS.md §9)."""
from __future__ import annotations

import json

import pytest

from .conftest import load_skill_module, require_tool

GOOD_SRC = """\
#include "add.h"
int add(int a, int b) {
#ifdef FORGE_MUTANT
    return a - b;
#else
    return a + b;
#endif
}
"""

HEADER = "int add(int a, int b);\n"

REAL_TEST = """\
#include "add.h"
#include "forge_test.h"
static void test_add_basic(void) { FORGE_CHECK(add(2, 3) == 5); }
static void test_add_negative(void) { FORGE_CHECK(add(-1, -1) == -2); }
int main(void) {
    test_add_basic();
    test_add_negative();
    return FORGE_REPORT();
}
"""

NOOP_TEST = """\
#include "add.h"
#include "forge_test.h"
static void test_tautology(void) { FORGE_CHECK(1 == 1); }
int main(void) {
    test_tautology();
    return FORGE_REPORT();
}
"""

NO_MUTANT_SRC = """\
#include "sub.h"
int sub(int a, int b) { return a - b; }
"""

NO_MUTANT_HEADER = "int sub(int a, int b);\n"
NO_MUTANT_TEST = """\
#include "sub.h"
#include "forge_test.h"
static void test_sub(void) { FORGE_CHECK(sub(5, 3) == 2); }
int main(void) { test_sub(); return FORGE_REPORT(); }
"""


@pytest.fixture(autouse=True)
def _tools():
    require_tool("cc")


@pytest.fixture
def verify_mod():
    return load_skill_module("building-firmware")


def _scaffold(project, *, name, src, header, test):
    (project / "firmware" / "src").mkdir(parents=True, exist_ok=True)
    (project / "firmware" / "include").mkdir(parents=True, exist_ok=True)
    (project / "firmware" / "tests").mkdir(parents=True, exist_ok=True)
    (project / "firmware" / "src" / f"{name}.c").write_text(src)
    (project / "firmware" / "include" / f"{name}.h").write_text(header)
    (project / "firmware" / "tests" / f"test_{name}.c").write_text(test)


def test_good_module_with_real_tests_and_mutant_passes(verify_mod, tmp_path):
    _scaffold(tmp_path, name="add", src=GOOD_SRC, header=HEADER, test=REAL_TEST)
    rc = verify_mod.main(["--project", str(tmp_path)])
    assert rc == 0
    result = json.loads((tmp_path / "out/verify/firmware.add.json").read_text())
    assert result["status"] == "pass"
    tests_run = next(m for m in result["measurements"] if m["name"] == "tests_run")
    failures = next(m for m in result["measurements"] if m["name"] == "test_failures")
    mutation = next(m for m in result["measurements"] if m["name"] == "mutation_kills")
    assert tests_run["value"] == 2
    assert failures["value"] == 0
    assert mutation["value"] == 1 and mutation["pass"] is True


def test_mutation_check_catches_a_noop_test_suite(verify_mod, tmp_path):
    _scaffold(tmp_path, name="add", src=GOOD_SRC, header=HEADER, test=NOOP_TEST)
    rc = verify_mod.main(["--project", str(tmp_path)])
    assert rc == 1  # host tests "pass" (vacuously) but the mutation check must fail the run
    result = json.loads((tmp_path / "out/verify/firmware.add.json").read_text())
    assert result["status"] == "fail"
    failures = next(m for m in result["measurements"] if m["name"] == "test_failures")
    mutation = next(m for m in result["measurements"] if m["name"] == "mutation_kills")
    assert failures["value"] == 0 and failures["pass"] is True  # the no-op suite itself "passes"
    assert mutation["value"] == 0 and mutation["pass"] is False  # but never catches the mutant
    assert "no-op" in mutation["remediation"] or "FORGE_MUTANT" in mutation["remediation"]


def test_module_without_a_mutation_point_errors(verify_mod, tmp_path):
    _scaffold(tmp_path, name="sub", src=NO_MUTANT_SRC, header=NO_MUTANT_HEADER, test=NO_MUTANT_TEST)
    rc = verify_mod.main(["--project", str(tmp_path)])
    assert rc == 2
    result = json.loads((tmp_path / "out/verify/firmware.sub.json").read_text())
    assert result["status"] == "error"
    assert "FORGE_MUTANT" in result["error"]


def test_seeded_broken_implementation_fails_the_real_test(verify_mod, tmp_path):
    broken_src = GOOD_SRC.replace("return a + b;", "return a - b;")  # seeded wrong-on-purpose
    _scaffold(tmp_path, name="add", src=broken_src, header=HEADER, test=REAL_TEST)
    rc = verify_mod.main(["--project", str(tmp_path)])
    assert rc == 1
    result = json.loads((tmp_path / "out/verify/firmware.add.json").read_text())
    failures = next(m for m in result["measurements"] if m["name"] == "test_failures")
    assert failures["value"] > 0 and failures["pass"] is False


def test_no_test_files_is_a_clean_skip(verify_mod, tmp_path):
    assert verify_mod.main(["--project", str(tmp_path)]) == 0


# --- S10 (review-2 addendum): the compile rung always runs; only the test rung may SKIP ---

BROKEN_SYNTAX_SRC = "int add(int a, int b) {\n    return a +\n"  # unterminated, no closing brace


def test_no_tests_but_broken_src_fails_not_skips(verify_mod, tmp_path):
    """S10 seeded-wrong case: firmware/src/main.c has a syntax error and there are no
    tests at all. Before the fix, `find_modules` was empty (no test_*.c) so main() printed
    a clean [SKIP] and exited 0 without ever invoking the compiler -- the brief says
    firmware/ -> compile, and a real compile error must never pass unseen."""
    (tmp_path / "firmware" / "src").mkdir(parents=True)
    (tmp_path / "firmware" / "src" / "main.c").write_text(BROKEN_SYNTAX_SRC)
    rc = verify_mod.main(["--project", str(tmp_path)])
    assert rc == 1
    result = json.loads((tmp_path / "out/verify/firmware.compile.json").read_text())
    assert result["status"] == "fail"
    errors = next(m for m in result["measurements"] if m["name"] == "compile_errors")
    assert errors["value"] == 1 and errors["pass"] is False
    assert "main.c" in errors["remediation"]


def test_no_tests_but_valid_src_compiles_clean(verify_mod, tmp_path):
    """Pass case for the same compile-only rung: valid source, still no tests."""
    (tmp_path / "firmware" / "src").mkdir(parents=True)
    (tmp_path / "firmware" / "src" / "add.c").write_text("int add(int a, int b) { return a + b; }\n")
    rc = verify_mod.main(["--project", str(tmp_path)])
    assert rc == 0
    result = json.loads((tmp_path / "out/verify/firmware.compile.json").read_text())
    assert result["status"] == "pass"
    errors = next(m for m in result["measurements"] if m["name"] == "compile_errors")
    assert errors["value"] == 0


def test_size_budget_enforced_when_declared(verify_mod, tmp_path):
    _scaffold(tmp_path, name="add", src=GOOD_SRC, header=HEADER, test=REAL_TEST)
    (tmp_path / "params").mkdir(parents=True, exist_ok=True)
    (tmp_path / "params" / "params.toml").write_text("""\
[firmware.add]
size_budget_bytes = 1
""")
    rc = verify_mod.main(["--project", str(tmp_path)])
    result = json.loads((tmp_path / "out/verify/firmware.add.json").read_text())
    names = {m["name"] for m in result["measurements"]}
    # no target cross-compiler on this machine -> a labelled host proxy measurement, not silence
    assert "host_size_proxy_bytes" in names or "target_size_bytes" in names
