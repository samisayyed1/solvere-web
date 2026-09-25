#include "forge_test.h"
#include "ringbuf.h"

static void test_empty_pop_fails(void) {
    ringbuf_t rb; uint8_t b;
    rb_init(&rb);
    FORGE_CHECK(rb_pop(&rb, &b) == -1);
}

static void test_fill_to_capacity(void) {
    ringbuf_t rb;
    rb_init(&rb);
    for (unsigned i = 0; i < RB_CAPACITY; i++) FORGE_CHECK(rb_push(&rb, (uint8_t)i) == 0);
    FORGE_CHECK(rb_count(&rb) == RB_CAPACITY);
    FORGE_CHECK(rb_push(&rb, 0xAA) == -1);
}

static void test_fifo_order_across_wrap(void) {
    ringbuf_t rb; uint8_t b = 0;
    rb_init(&rb);
    for (unsigned round = 0; round < 3; round++) {
        for (unsigned i = 0; i < 5; i++) FORGE_CHECK(rb_push(&rb, (uint8_t)(round * 10 + i)) == 0);
        for (unsigned i = 0; i < 5; i++) { FORGE_CHECK(rb_pop(&rb, &b) == 0); FORGE_CHECK(b == round * 10 + i); }
    }
    FORGE_CHECK(rb_count(&rb) == 0);
}

int main(void) {
    test_empty_pop_fails();
    test_fill_to_capacity();
    test_fifo_order_across_wrap();
    return FORGE_REPORT();
}
