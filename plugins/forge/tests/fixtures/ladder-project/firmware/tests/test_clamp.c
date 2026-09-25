#include "clamp.h"
#include "forge_test.h"

static void test_inside_range_is_unchanged(void) { FORGE_CHECK(clamp_setpoint(50, 0, 100) == 50); }
static void test_below_range_clamps_to_lo(void) { FORGE_CHECK(clamp_setpoint(-5, 0, 100) == 0); }
static void test_above_range_clamps_to_hi(void) { FORGE_CHECK(clamp_setpoint(250, 0, 100) == 100); }

int main(void) {
    test_inside_range_is_unchanged();
    test_below_range_clamps_to_lo();
    test_above_range_clamps_to_hi();
    return FORGE_REPORT();
}
