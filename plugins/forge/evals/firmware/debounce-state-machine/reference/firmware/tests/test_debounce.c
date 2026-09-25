#include "forge_test.h"
#include "debounce.h"

static btn_event_t run(debounce_t *d, int level, uint32_t *t, uint32_t ms, int *presses, int *releases, int *longs) {
    btn_event_t last = BTN_EVT_NONE;
    for (uint32_t i = 0; i < ms; i++) {
        btn_event_t e = debounce_update(d, level, (*t)++);
        if (e == BTN_EVT_PRESS) (*presses)++;
        if (e == BTN_EVT_RELEASE) (*releases)++;
        if (e == BTN_EVT_LONG_PRESS) (*longs)++;
        if (e != BTN_EVT_NONE) last = e;
    }
    return last;
}

static void test_init_released(void) {
    debounce_t d; debounce_init(&d, 0);
    FORGE_CHECK(debounce_state(&d) == BTN_RELEASED);
}

static void test_glitch_19ms_ignored(void) {
    debounce_t d; uint32_t t = 0; int p = 0, r = 0, l = 0;
    debounce_init(&d, t);
    run(&d, 1, &t, 19, &p, &r, &l);
    run(&d, 0, &t, 50, &p, &r, &l);
    FORGE_CHECK(p == 0);
    FORGE_CHECK(debounce_state(&d) == BTN_RELEASED);
}

static void test_no_press_before_20ms_elapsed(void) {
    debounce_t d; uint32_t t = 0; int p = 0, r = 0, l = 0;
    debounce_init(&d, t);
    run(&d, 1, &t, 20, &p, &r, &l);   /* last sample is 19 ms after the edge */
    FORGE_CHECK(p == 0);
}

static void test_press_after_20ms(void) {
    debounce_t d; uint32_t t = 0; int p = 0, r = 0, l = 0;
    debounce_init(&d, t);
    run(&d, 1, &t, 21, &p, &r, &l);
    FORGE_CHECK(p == 1);
    FORGE_CHECK(debounce_state(&d) == BTN_PRESSED);
}

static void test_release_event(void) {
    debounce_t d; uint32_t t = 0; int p = 0, r = 0, l = 0;
    debounce_init(&d, t);
    run(&d, 1, &t, 50, &p, &r, &l);
    run(&d, 0, &t, 50, &p, &r, &l);
    FORGE_CHECK(r == 1);
    FORGE_CHECK(debounce_state(&d) == BTN_RELEASED);
}

static void test_long_press_once(void) {
    debounce_t d; uint32_t t = 0; int p = 0, r = 0, l = 0;
    debounce_init(&d, t);
    run(&d, 1, &t, 3000, &p, &r, &l);
    FORGE_CHECK(p == 1);
    FORGE_CHECK(l == 1);
}

static void test_bounce_restarts_timer(void) {
    debounce_t d; uint32_t t = 0; int p = 0, r = 0, l = 0;
    debounce_init(&d, t);
    for (int k = 0; k < 10; k++) { run(&d, 1, &t, 5, &p, &r, &l); run(&d, 0, &t, 3, &p, &r, &l); }
    FORGE_CHECK(p == 0);
}

static void test_timestamp_wrap(void) {
    debounce_t d; uint32_t t = 0xFFFFFFF0u; int p = 0, r = 0, l = 0;
    debounce_init(&d, t);
    run(&d, 1, &t, 30, &p, &r, &l);
    FORGE_CHECK(p == 1);
}

int main(void) {
    test_init_released();
    test_glitch_19ms_ignored();
    test_no_press_before_20ms_elapsed();
    test_press_after_20ms();
    test_release_event();
    test_long_press_once();
    test_bounce_restarts_timer();
    test_timestamp_wrap();
    return FORGE_REPORT();
}
