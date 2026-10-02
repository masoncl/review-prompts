- Order, outermost first: `lock` of `struct io_sq_data`, `uring_lock`,
  `mmap_lock`, `completion_lock`, `timeout_lock`.
- `uring_lock`, `mmap_lock`, `completion_lock` in that order: see the swap in
  `io_register_resize_rings()`.
- `completion_lock` outside `timeout_lock`: see `io_kill_timeouts()` and
  `io_disarm_next()`.
- `tctx_lock`: a mutex of `struct io_ring_ctx` that protects `tctx_list`;
  `uring_lock` alone does not.
- `tctx_lock` inside `uring_lock`: for example `__io_async_cancel()` and
  `io_ring_exit_work()`.
- `tctx_lock` alone: `io_tctx_install_node()` and `io_uring_del_tctx_node()`.
- Interrupt context: only `timeout_lock`.
- `completion_lock`: every acquisition is a plain `spin_lock()`, process
  context only; `io_lockdep_assert_cq_locked()` asserts `in_task()`.
- **Potentially unsafe usage**: blocking on a second ring's `uring_lock` while
  holding the first ring's.
  - Unsafe: when the first lock is the one the submission path already holds,
    so the pair is not in address order; two rings messaging each other
    deadlock.
  - Safe: `mutex_trylock()` and return `-EAGAIN` when `issue_flags` lacks
    `IO_URING_F_UNLOCKED`, as `io_lock_external_ctx()` in
    `io_uring/msg_ring.c` does; `io_msg_ring()` passes `-EAGAIN` up unchanged.
  - Safe: with `IO_URING_F_UNLOCKED` no ring lock is held, so
    `io_lock_external_ctx()` uses `mutex_lock()`.
  - Safe: drop the first lock, then take both by address, the second with
    `mutex_lock_nested()` and `SINGLE_DEPTH_NESTING`, as `lock_two_rings()`
    in `io_uring/rsrc.c` does.
- `io_register_clone_buffers()`: does the drop and `lock_two_rings()`;
  `io_clone_buffers()` only asserts both locks.
- After the drop: state tested earlier is tested again; `io_clone_buffers()`
  re-tests `buf_table.nr`.
- Same ring as source and target: `io_register_clone_buffers()` skips the
  drop and relock; `lock_two_rings()` requires two different rings.
