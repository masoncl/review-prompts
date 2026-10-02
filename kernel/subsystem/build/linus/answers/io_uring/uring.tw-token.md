- Guarantee: `ctx->uring_lock` of `req->ctx` is held, and the runner calls
  `io_submit_flush_completions()` after the handler returns.
- Not guaranteed: that `current` is the task that submitted the request; the
  runner can be a kworker (`io_tctx_fallback_work()`, `io_ring_exit_work()`),
  and then `tw.cancel` is true.
- Creators: a local `struct io_tw_state`, instantiated only in
  `io_uring/tw.c`, by `tctx_task_work_run()`, `io_run_local_work()`,
  `io_run_local_work_locked()` and `io_cancel_local_task_work()`; there is no
  macro for it.
- There is no io_fallback_req_func() here; `ctx_flush_and_put()` receives a
  token and does not create one.
- Code that is not task work: set the result, set `req->io_task_work.func`,
  call `io_req_task_work_add()`; `io_req_queue_tw_complete()` in
  `io_uring/io_uring.h` and `io_req_task_queue_fail()` do all three.
- **Potentially unsafe usage**: calling `io_req_complete_defer()`,
  `io_req_task_complete()` or `io_req_defer_failed()` outside a task work
  handler.
  - Unsafe: when `ctx->uring_lock` is not held or nothing flushes
    `submit_state.compl_reqs` afterwards; `io_req_complete_defer()` has
    `lockdep_assert_held()` and only appends to that list.
  - Safe: on the issue path with `IO_URING_F_COMPLETE_DEFER`, as
    `io_issue_sqe()` does; `io_submit_sqes()` runs under `uring_lock` and
    flushes in `io_submit_state_end()`.
  - Safe: under the lock with an explicit flush, as
    `io_uring_try_cancel_uring_cmd()` does.
- **Unsafe usage**: passing `IO_URING_CMD_TASK_WORK_ISSUE_FLAGS` to
  `io_uring_cmd_done()` outside a task work callback;
  `__io_uring_cmd_done()` then calls `io_req_complete_defer()`.
  - Safe: inside the callback given to `io_uring_cmd_complete_in_task()`, as
    `fuse_uring_send_in_task()` does.
  - Safe: inside `->uring_cmd()`, pass on the `issue_flags` it received, as
    `fuse_uring_cancel()` does; `io_uring_try_cancel_uring_cmd()` holds
    `uring_lock` and flushes after the call.
