- Copy storage: `sqes[2]` in `struct io_async_cmd` (`io_uring/uring_cmd.h`),
  allocated as `req->async_data` by `io_uring_cmd_prep()`; there is no
  io_uring_cmd_data structure in this tree.
- `io_uring_cmd_sqe_copy()`: core-only. It is declared in
  `io_uring/uring_cmd.h`, not exported, and reached only through the
  `sqe_copy` member of `io_cold_defs[]` from `io_req_sqe_copy()` in
  `io_uring/io_uring.c`. A driver cannot request the copy.
- `uring_sqe_size()`: takes the request; gives the copy length, 128 bytes for
  `IORING_SETUP_SQE128` rings or opcode `IORING_OP_URING_CMD128`, else 64.
  A plain `IORING_OP_URING_CMD` on an `IORING_SETUP_SQE_MIXED` ring gets 64.
- `io_req_sqe_copy()` callers: `io_queue_async()` after `-EAGAIN`,
  `io_queue_sqe_fallback()` (forced async, drain), and `io_submit_sqe()` for
  every request added behind a link head. In the last two the first
  `->uring_cmd()` call already sees the copy.
- `cmd->sqe` in a call whose `issue_flags` carry `IO_URING_F_INLINE`: the SQ
  ring slot. `io_submit_sqe()` passes that flag only for requests it has not
  copied.
- `io_req_uring_cleanup()`: on completion without `IO_URING_F_UNLOCKED` it
  puts the async data into `ctx->cmd_cache` and, when the cache takes it,
  sets `ioucmd->sqe` to NULL; `cmd->sqe` is dead after `io_uring_cmd_done()`
  or a final return value.
- Payload size: `io_uring_sqe_cmd()` bounds the type to a 64-byte SQE,
  `io_uring_sqe128_cmd()` to 128 bytes, both at build time only. A driver
  using the 128-byte form must reject calls without `IO_URING_F_SQE128`, as
  `fuse_uring_cmd()` and `ublk_ctrl_uring_cmd()` do; otherwise it reads past
  the slot or past the 64 copied bytes.
- **Potentially unsafe usage**: reading `cmd->sqe` after the issue call
  returned `-EIOCBQUEUED` (task-work callback, completion handler).
  - Unsafe: when that issue call had `IO_URING_F_INLINE`; nothing copies the
    SQE afterwards and userspace may rewrite the slot.
  - Safe: when that issue call had `IO_URING_F_UNLOCKED` and the driver never
    calls `io_uring_cmd_issue_blocking()`; `io_queue_async()` and
    `io_queue_sqe_fallback()` run `io_req_sqe_copy()` before
    `io_queue_iowq()`. `ublk_ch_uring_cmd()` defers such calls to
    `ublk_ch_uring_cmd_cb()`, which then reads the SQE.
- **Unsafe usage**: reading `cmd->sqe` in a reissue the driver requested with
  `io_uring_cmd_issue_blocking()` after an inline `-EIOCBQUEUED`;
  `io_queue_iowq()` copies nothing and `IORING_URING_CMD_REISSUE` is set only
  by `io_uring_cmd()` on a `-EAGAIN` return.
  - Safe: a reissue after `-EAGAIN` from the inline issue;
    `io_queue_async()` copied the SQE before it, so
    `btrfs_uring_encoded_read()` reads `cmd->sqe->addr` again from the copy.
