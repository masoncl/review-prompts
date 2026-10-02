- Wait for poll with nothing transferred: `io_kbuf_recycle()`, called by the
  handler; its only callers are in `io_uring/rw.c`, `io_uring/net.c` and
  `io_uring/uring_cmd.c`, no core path does it.
- Retry after a partial transfer: neither helper; `io_net_kbuf_recyle()` in
  `io_uring/net.c` (spelled so) sets `REQ_F_BL_NO_RECYCLE` and calls
  `io_kbuf_commit()` with the bytes done, building no cflags.
- After `io_net_kbuf_recyle()`: `REQ_F_BUFFER_RING` stays set, so the retry
  does no selection and continues in the same buffer with the iterator left
  in `kmsg->msg.msg_iter`.
- Final put after such a retry: gets a NULL list and builds cflags from
  `req->buf_index`.
- `io_kbuf_recycle()` on a ring buffer with a NULL list: returns false and
  leaves `REQ_F_BUFFER_RING` set; the buffer was already committed and stays
  with the request.
- `io_kbuf_recycle()` on a legacy buffer: ignores the list argument;
  `io_kbuf_recycle_legacy()` calls `io_ring_submit_lock()`, which takes
  `ctx->uring_lock` for `IO_URING_F_UNLOCKED`, and looks the list up again.
- `io_read()`: recycles only when `REQ_F_BUFFERS_COMMIT` is set, so a legacy
  buffer or an already committed ring buffer stays with the request on
  error.
- `io_put_kbufs()` on a legacy buffer: frees the `struct io_buffer` through
  `io_kbuf_drop_legacy()`; it does not return to the list.
- `io_put_kbuf()` and `io_put_kbufs()` with neither selected flag set: return
  0, so calling them after a recycle is harmless.
