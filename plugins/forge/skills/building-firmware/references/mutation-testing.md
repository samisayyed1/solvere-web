# The `FORGE_MUTANT` convention

A test suite that always passes proves nothing (brief §0: "prove every new check fails on
a deliberately wrong input"). `scripts/verify.py` proves each module's test suite *can*
fail by rebuilding it with a deliberately wrong implementation and requiring at least one
test to fail against it.

Every `firmware/src/<name>.c` that has a `firmware/tests/test_<name>.c` must guard at
least one meaningful comparison or branch with `#ifdef FORGE_MUTANT`, flipped to something
plausibly wrong:

```c
int debounce_is_stable(int reading, int previous, int count) {
#ifdef FORGE_MUTANT
    return count <= DEBOUNCE_THRESHOLD;   /* flipped: <= instead of >= */
#else
    return count >= DEBOUNCE_THRESHOLD;
#endif
}
```

`scripts/verify.py`:

1. Builds and runs the test binary normally — this must pass (`test_failures == 0`).
2. Greps the module's source files for the literal token `FORGE_MUTANT`. If none of them
   define a mutation point, the check **errors** (exit 2) rather than silently skipping —
   a module with no mutant is a module whose tests have never been proven to catch
   anything.
3. Rebuilds the *same* test binary with `-DFORGE_MUTANT` added and reruns it. At least one
   test must now fail. If every test still passes under the mutant, the whole check
   **fails** with a `mutation_kills` measurement of 0 — the test suite is a no-op and would
   not catch a real regression.

Put the mutation point wherever a bug would actually matter (a boundary comparison, a sign,
an off-by-one), not somewhere cosmetic — a mutant nobody's test would ever exercise passes
this check for the wrong reason.
