#include "ringbuf.h"

#define RB_SLOTS (RB_CAPACITY + 1u)

void rb_init(ringbuf_t *rb) { rb->head = 0; rb->tail = 0; }

size_t rb_count(const ringbuf_t *rb) {
    return (rb->head + RB_SLOTS - rb->tail) % RB_SLOTS;
}

int rb_push(ringbuf_t *rb, uint8_t byte) {
#ifdef FORGE_MUTANT
    if (rb_count(rb) > RB_CAPACITY) return -1;   /* mutant: never reports full */
#else
    if (rb_count(rb) >= RB_CAPACITY - 1u) return -1;
#endif
    rb->buf[rb->head] = byte;
    rb->head = (rb->head + 1u) % RB_SLOTS;
    return 0;
}

int rb_pop(ringbuf_t *rb, uint8_t *out) {
    if (rb->head == rb->tail) return -1;
    *out = rb->buf[rb->tail];
    rb->tail = (rb->tail + 1u) % RB_SLOTS;
    return 0;
}
