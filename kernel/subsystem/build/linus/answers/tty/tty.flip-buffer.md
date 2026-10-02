- `next` is a second release/acquire pair, besides `commit`:
  `__tty_buffer_request_room()` stores `commit` and then `next`;
  `flush_to_ldisc()` and `lookahead_bufs()` load `next` before `commit`.
- `__tty_buffer_request_room()`: moves `buf->tail` to the new buffer first,
  then does the two release stores on the old tail.
- `tty_buffer_alloc()`: its limit test refuses only when `mem_used` is already
  above `mem_limit`; the requested size is added after the test, so one
  allocation can overshoot the limit.
- `tty_buffer_alloc()` with a size of at most `MIN_TTYB_SIZE`: takes a buffer
  from `buf->free` first, and that path skips the limit test.
- `tty_buffer_alloc()` with a size of at most `MIN_TTYB_SIZE` and `buf->free`
  empty: goes through the limit test and `kmalloc_flex()` like any other size.
- `mem_used`: counts `size` rounded up to a multiple of 256, while each buffer
  allocates `2 * size` data bytes plus the header; buffers parked on
  `buf->free` are not counted.
- There is no TTYB_MIN_SIZE here; the recycle threshold is `MIN_TTYB_SIZE` in
  `drivers/tty/tty_buffer.c`.
- `tty_buffer_lock_exclusive()` and `tty_buffer_flush()`: exclude only the
  consumer; the insert functions and `tty_flip_buffer_push()` neither take
  `buf->lock` nor test `buf->priority`, so the driver keeps appending.
