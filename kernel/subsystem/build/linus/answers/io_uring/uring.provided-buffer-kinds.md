- `req->buf_index` after selection: the buffer id for both kinds
  (`io_provided_buffer_select()` and `io_ring_buffer_select()` both store the
  bid).
- `req->buf_index` before selection: the group id, set by `io_init_req()`;
  prep copies it to `io->buf_group` (`io_uring/rw.c`) or `sr->buf_group`
  (`io_uring/net.c`).
- Legacy recycle: takes the group from `req->kbuf->bgid`, not from
  `req->buf_index`.
- Ring flag states:

| Flags on the request | Meaning |
|---|---|
| `REQ_F_BUFFER_RING` and `REQ_F_BUFFERS_COMMIT` | ring buffer picked, `bl->head` not yet moved |
| `REQ_F_BUFFER_RING` alone | ring buffer picked and already committed; the request keeps it across retries |

- `io_do_buffer_select()`: false while `REQ_F_BUFFER_RING` or
  `REQ_F_BUFFER_SELECTED` is set, so a retry reuses the buffer it holds.
- `io_ring_buffers_peek()`: sets `REQ_F_BUFFER_RING` and not
  `REQ_F_BUFFERS_COMMIT`; its callers `io_buffers_select()` and
  `io_buffers_peek()` add `REQ_F_BUFFERS_COMMIT`.
- `IO_REQ_CLEAN_FLAGS` in `io_uring/io_uring.c`: contains
  `REQ_F_BUFFER_SELECTED` but not `REQ_F_BUFFER_RING`; `io_clean_op()` frees a
  legacy buffer the handler never put, a ring buffer has no such fallback.
