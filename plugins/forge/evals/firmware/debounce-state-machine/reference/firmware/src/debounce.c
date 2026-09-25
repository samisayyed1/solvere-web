#include "debounce.h"

void debounce_init(debounce_t *d, uint32_t now_ms) {
    d->state = BTN_RELEASED;
    d->candidate = 0;
    d->candidate_since = now_ms;
    d->pressed_since = now_ms;
    d->long_sent = 0;
}

btn_event_t debounce_update(debounce_t *d, int raw_level, uint32_t now_ms) {
    int level = raw_level ? 1 : 0;
    if (level != d->candidate) {
        d->candidate = level;
        d->candidate_since = now_ms;
    }
    uint32_t stable = now_ms - d->candidate_since;
#ifdef FORGE_MUTANT
    int settled = stable + 1u >= DEBOUNCE_MS; /* off by one: accepts a 19 ms glitch */
#else
    int settled = stable >= DEBOUNCE_MS;
#endif
    if (settled && (btn_state_t)d->candidate != d->state) {
        d->state = (btn_state_t)d->candidate;
        if (d->state == BTN_PRESSED) {
            d->pressed_since = now_ms;
            d->long_sent = 0;
            return BTN_EVT_PRESS;
        }
        return BTN_EVT_RELEASE;
    }
    if (d->state == BTN_PRESSED && !d->long_sent && now_ms - d->pressed_since >= LONG_PRESS_MS) {
        d->long_sent = 1;
        return BTN_EVT_LONG_PRESS;
    }
    return BTN_EVT_NONE;
}

btn_state_t debounce_state(const debounce_t *d) { return d->state; }
