# Button debounce -- behaviour spec

- Input: raw active-high level (1 = pressed), sampled every 1 ms by the caller, which passes a monotonic ms timestamp.
- A change of the raw level only changes the debounced state after the new level has been stable for at least DEBOUNCE_MS (20 ms). Any shorter glitch is ignored and restarts the timing.
- `debounce_update` returns BTN_EVT_PRESS once when the debounced state becomes PRESSED and BTN_EVT_RELEASE once when it becomes RELEASED.
- While the debounced state stays PRESSED, it returns BTN_EVT_LONG_PRESS exactly once, when the press has lasted LONG_PRESS_MS (1000 ms) since the debounced press.
- After `debounce_init`, the state is RELEASED and no event is pending.
- Timestamps may wrap around at 2^32 ms; use unsigned subtraction.
