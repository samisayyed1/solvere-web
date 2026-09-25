/* debounce.h -- debounced push-button state machine (fixed API; do not change).
 * Timing values come from params/params.toml [firmware.debounce]. */
#ifndef DEBOUNCE_H
#define DEBOUNCE_H

#include <stdint.h>

#define DEBOUNCE_MS 20u      /* params firmware.debounce.debounce_ms */
#define LONG_PRESS_MS 1000u  /* params firmware.debounce.long_press_ms */

typedef enum { BTN_RELEASED = 0, BTN_PRESSED = 1 } btn_state_t;
typedef enum { BTN_EVT_NONE = 0, BTN_EVT_PRESS, BTN_EVT_RELEASE, BTN_EVT_LONG_PRESS } btn_event_t;

typedef struct {
    btn_state_t state;       /* debounced state */
    int candidate;           /* raw level currently being timed */
    uint32_t candidate_since;/* ms timestamp the candidate level was first seen */
    uint32_t pressed_since;  /* ms timestamp of the debounced press */
    int long_sent;           /* LONG_PRESS already emitted for this press */
} debounce_t;

void debounce_init(debounce_t *d, uint32_t now_ms);
btn_event_t debounce_update(debounce_t *d, int raw_level, uint32_t now_ms);
btn_state_t debounce_state(const debounce_t *d);

#endif
