#ifndef CLAMP_H
#define CLAMP_H
/* REQ-FW-001: clamp a commanded setpoint into [lo, hi] before use. */
int clamp_setpoint(int value, int lo, int hi);
#endif
