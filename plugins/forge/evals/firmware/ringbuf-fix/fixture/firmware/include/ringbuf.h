/* ringbuf.h -- fixed-size byte ring buffer for the UART RX path. */
#ifndef RINGBUF_H
#define RINGBUF_H
#include <stdint.h>
#include <stddef.h>

#define RB_CAPACITY 8u   /* usable bytes */

typedef struct {
    uint8_t buf[RB_CAPACITY + 1u];
    size_t head;  /* next write */
    size_t tail;  /* next read */
} ringbuf_t;

void rb_init(ringbuf_t *rb);
int rb_push(ringbuf_t *rb, uint8_t byte);   /* 0 ok, -1 full */
int rb_pop(ringbuf_t *rb, uint8_t *out);    /* 0 ok, -1 empty */
size_t rb_count(const ringbuf_t *rb);
#endif
