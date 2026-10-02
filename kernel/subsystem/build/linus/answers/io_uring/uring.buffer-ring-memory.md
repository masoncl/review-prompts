- `IOBL_INC` progress: kept only in the shared entry; `io_kbuf_inc_commit()`
  writes the advanced `addr` and reduced `len` back, and the next selection
  reads them again from shared memory.
- No kernel-private offset exists, so every selection must treat `addr` and
  `len` of the head entry as new untrusted input, including on a partly
  consumed buffer.
- `access_ok()`: both `io_ring_buffer_select()` and `io_ring_buffers_peek()`
  call it on the local copies of `addr` and `len`.
- Callers rely on that check: `io_recvmsg()` builds its iterator with
  `iov_iter_ubuf()` and `io_recv_buf_select()` for a bundle with
  `iov_iter_init()`, neither of which checks the range.
- Failed `access_ok()`: `io_ring_buffer_select()` returns a NULL `addr` with
  neither `REQ_F_BUFFER_RING` nor `REQ_F_BUFFERS_COMMIT` set;
  `io_ring_buffers_peek()` returns `-EFAULT`.
- `bl->min_left_sub_one`: `io_kbuf_inc_commit()` treats an incremental buffer
  as used up when the remainder is not above it, then writes `len` 0 and moves
  `bl->head`; it comes from `min_left` of `struct io_uring_buf_reg`.
- `io_kbuf_inc_commit()` with `len` 0, or on an entry whose `len` reads 0:
  returns false and does not move `bl->head`.
- `ctx->uring_lock`: must be held; `io_buffer_get_list()` and
  `io_buffers_peek()` assert it, `io_kbuf_commit()` has no assertion of its
  own and updates `bl->head` with plain stores.
- `bl->head`: kernel-private but not hidden; `io_register_pbuf_status()`
  copies it to userspace.
- **Potentially unsafe usage**: reading one field of a `struct io_uring_buf`
  more than once.
  - Unsafe: when the check (clamp, `access_ok()`, zero test) is applied to one
    read and a different read supplies the length or address of the transfer.
  - Safe: when each read is used on its own, as in `io_ring_buffers_peek()`:
    the first read of `len` only tests for zero and limits how many entries
    are walked, and each iovec takes one `READ_ONCE()` local that feeds both
    `access_ok()` and `iov_len`.
