- `IORING_OP_REMOVE_BUFFERS`: does not free the list;
  `io_remove_buffers_legacy()` frees only `struct io_buffer` entries and an
  emptied legacy list stays in `ctx->io_bl_xa`.
- A list that was stored in `ctx->io_bl_xa` is freed only in `io_put_bl()`,
  reached from:
  - `io_unregister_pbuf_ring()`, ring lists only (`-EINVAL` for legacy);
  - `io_register_pbuf_ring()`, which replaces an empty legacy list of the
    same group through `io_destroy_bl()`;
  - `io_destroy_buffers()` at ring teardown.
- A group can change kind while a request owns a legacy buffer;
  `io_kbuf_recycle_legacy()` frees the buffer when the list is gone or is now
  a ring.
- `buf_list` after `io_ring_buffer_select()`: NULL whenever the buffer was
  committed at selection, locked or not; non-NULL means the commit is
  pending.
- `buf_list` after `io_buffers_select()`: when the group exists, NULL only for
  `IO_URING_F_UNLOCKED`; in the locked case it stays set, also for a legacy
  list and although the commit is done.
- `buf_list` after `io_buffers_peek()`: the ring list, or NULL for a legacy
  list.
- `addr` and `val` of `struct io_br_sel`: one union; storing the result in
  `val` destroys `addr`, so handlers consume `addr` first, as
  `__ublk_batch_dispatch()` does.
- Reset per pass: `io_recv()`, `io_recvmsg()` and `io_send()` set
  `sel.buf_list = NULL` at the top of each retry pass, since a pass where
  `io_do_buffer_select()` is false does no selection.
- The put and recycle helpers dereference the list only in
  `io_kbuf_commit()`, and only while `REQ_F_BUFFERS_COMMIT` is set;
  `io_kbuf_recycle_ring()` tests it for NULL only.
- uring_cmd: `io_uring_mshot_cmd_post_cqe()` must get the `struct io_br_sel`
  from `io_uring_cmd_buffer_select()` within the same issue call.
- **Unsafe usage**: calling `io_kbuf_commit()` directly with a NULL list while
  `REQ_F_BUFFERS_COMMIT` is set.
  - Unsafe: it reads `bl->flags` with no NULL test.
  - Safe: go through `io_put_kbuf()` or `io_put_kbufs()`, which test the list
    in `__io_put_kbuf_ring()`.
  - Safe: call it with the list just returned by a locked selection, as
    `io_net_kbuf_recyle()` does behind its test of `REQ_F_BUFFERS_COMMIT`.
