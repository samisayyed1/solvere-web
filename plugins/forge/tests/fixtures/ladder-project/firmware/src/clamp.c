#include "clamp.h"

int clamp_setpoint(int value, int lo, int hi) {
#ifdef FORGE_MUTANT
    /* Mutation point (building-firmware references/mutation-testing.md):
       drops the upper bound, which the unit tests must catch. */
    (void)hi;
    return value < lo ? lo : value;
#else
    if (value < lo) {
        return lo;
    }
    if (value > hi) {
        return hi;
    }
    return value;
#endif
}
