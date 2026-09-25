/* forge_test.h -- tiny stdlib-only C test harness for building-firmware.
 *
 * No downloads, no external test framework: this header is the whole harness.
 * A test file does:
 *
 *     #include "forge_test.h"
 *     static void test_something(void) { FORGE_CHECK(add(2, 3) == 5); }
 *     int main(void) { test_something(); return FORGE_REPORT(); }
 *
 * scripts/verify.py parses the "FORGE_SUMMARY <count> <failures>" line this
 * prints on the last line of stdout, and the process exit code (0 iff
 * failures == 0) as a second, independent signal.
 */
#ifndef FORGE_TEST_H
#define FORGE_TEST_H

#include <stdio.h>

static int forge_test_count = 0;
static int forge_test_failures = 0;

#define FORGE_CHECK(cond)                                                     \
    do {                                                                      \
        forge_test_count++;                                                   \
        if (!(cond)) {                                                        \
            forge_test_failures++;                                            \
            printf("FORGE_FAIL %s:%d: %s\n", __FILE__, __LINE__, #cond);      \
        }                                                                     \
    } while (0)

#define FORGE_REPORT()                                                        \
    (printf("FORGE_SUMMARY %d %d\n", forge_test_count, forge_test_failures),  \
     forge_test_failures == 0 ? 0 : 1)

#endif /* FORGE_TEST_H */
