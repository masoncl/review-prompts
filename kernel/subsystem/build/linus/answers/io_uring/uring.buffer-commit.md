- `io_should_commit()`: true for `IO_URING_F_UNLOCKED`, or for a file that
  cannot poll unless `io_is_uring_cmd()`; it does not test
  `REQ_F_APOLL_MULTISHOT`.
- `io_is_uring_cmd()`: matches `IORING_OP_URING_CMD` and
  `IORING_OP_URING_CMD128`.
- `io_should_commit()` has one caller, `io_ring_buffer_select()`; the
  multi-buffer paths decide differently:

| Selector (ring list) | Flags it leaves set | Commit at selection |
|---|---|---|
| `io_ring_buffer_select()` | `REQ_F_BUFFER_RING`; also `REQ_F_BUFFERS_COMMIT` unless it committed | when `io_should_commit()` is true |
| `io_buffers_select()` | `REQ_F_BUFFER_RING`, `REQ_F_BL_NO_RECYCLE` | always |
| `io_buffers_peek()` | `REQ_F_BUFFER_RING`, `REQ_F_BUFFERS_COMMIT` | never |

- uring_cmd, locked issue: `io_uring_cmd_buffer_select()` selects through
  `io_buffer_select()` without a commit; the commit is in
  `io_uring_mshot_cmd_post_cqe()`, through `io_put_kbuf()` with
  `sel->buf_list`.
- uring_cmd under `IO_URING_F_UNLOCKED`: committed at selection like any other
  opcode.
- `io_kbuf_commit()`: clears `REQ_F_BUFFERS_COMMIT` itself; with the flag
  clear it returns true and does not touch the list.
- `io_kbuf_commit()` with `len < 0`: clears the flag and returns true without
  moving `bl->head`, so the buffer stays in the ring.
- `io_kbuf_commit()` arguments: a plain ring moves `bl->head` by `nr` and
  ignores a non-negative `len`; an `IOBL_INC` ring uses only `len`.
- `REQ_F_BUF_MORE`: set when a select-time commit returns false; the later
  put commits nothing, `__io_put_kbufs()` reports `IORING_CQE_F_BUF_MORE` for
  the flag and `__io_put_kbuf_ring()` clears it.
- Byte count: pass the bytes placed in the buffer, not the raw return value;
  `io_recv()` and `io_recvmsg()` clamp `consumed` to the selected length
  because `MSG_TRUNC` returns the full packet size.
- Bundle count: `io_bundle_nbufs()` returns 0 for `ret <= 0`, so the put of a
  failed bundle moves the head by nothing.
- **Unsafe usage**: returning from the issue handler with
  `REQ_F_BUFFERS_COMMIT` still set.
  - Unsafe: the next issue skips selection (`io_do_buffer_select()` is false)
    and puts with a NULL list, so `bl->head` never moves and another request
    is handed the same buffer.
  - Safe: recycle before returning, as `io_recv()` does on `-EAGAIN` and
    `io_read()` does when `__io_read()` fails while the flag is set.
  - Safe: commit before returning, as `io_net_kbuf_recyle()` does.
- **Potentially unsafe usage**: `io_put_kbuf()` or `io_put_kbufs()` with a NULL
  list.
  - Unsafe: while `REQ_F_BUFFERS_COMMIT` is set; `__io_put_kbuf_ring()` skips
    `io_kbuf_commit()`, the CQE reports the bid and `bl->head` stays.
  - Safe: when `REQ_F_BUFFERS_COMMIT` is clear, as in `io_req_rw_complete()`:
    `io_should_commit()` committed at selection for `IO_URING_F_UNLOCKED` and
    for a file that cannot poll, and `io_read()` recycles on a negative return
    while the flag is set.
