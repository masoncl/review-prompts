- `int_flags`: one `unsigned int` in the first, read-mostly group of
  `struct io_ring_ctx`, next to `flags`.
- Bit names: the `IO_RING_F_` enum just above the struct in
  `include/linux/io_uring_types.h`. Tests read
  `ctx->int_flags & IO_RING_F_TASK_COMPLETE`.
- No 1-bit bitfields remain; a patch that uses ctx->task_complete or
  ctx->lockless_cq does not build here.
- The former single restricted bit is two: `IO_RING_F_OP_RESTRICTED` (SQE
  checks, `io_check_restriction()`) and `IO_RING_F_REG_RESTRICTED` (register
  opcodes, `__io_uring_register()`).
- Written only in `io_uring_create()`: `IO_RING_F_TASK_COMPLETE`,
  `IO_RING_F_LOCKLESS_CQ`, `IO_RING_F_SYSCALL_IOPOLL`, `IO_RING_F_COMPAT`.
- `IO_RING_F_TASK_COMPLETE`: needs `IORING_SETUP_DEFER_TASKRUN` set and
  `IORING_SETUP_IOPOLL` clear.
- `IO_RING_F_LOCKLESS_CQ`: `IO_RING_F_TASK_COMPLETE` or `IORING_SETUP_IOPOLL`.
- A ring with both `IORING_SETUP_DEFER_TASKRUN` and `IORING_SETUP_IOPOLL` has
  `IO_RING_F_LOCKLESS_CQ` without `IO_RING_F_TASK_COMPLETE`.
- Restricted bits: set at creation from `op_registered` and `reg_registered`
  of `current->io_uring_restrict` (`io_ctx_restriction_clone()`), or later by
  `io_register_restrictions()`; nothing clears them.
- `IO_RING_F_POLL_ACTIVATED`: set at creation only when
  `IO_RING_F_TASK_COMPLETE` is clear; otherwise by `io_activate_pollwq_cb()`.
- Bits that are cleared at run time: `IO_RING_F_HAS_EVFD`,
  `IO_RING_F_DRAIN_ACTIVE`, `IO_RING_F_DRAIN_NEXT`.
- Writes after creation: plain `|=` and `&=` on the shared word, under
  `uring_lock`; `io_activate_pollwq_cb()` takes the mutex only for that.
- Reads without `uring_lock`: for example `io_commit_cqring_flush()` and
  `io_uring_poll()` wrap them in `data_race()`.
