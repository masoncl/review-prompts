- `io_should_terminate_tw()`: true for `PF_EXITING` or `PF_KTHREAD` in
  `current->flags`, or `percpu_ref_is_dying(&ctx->refs)`; it does not test
  for a pending signal.
- Handlers do not call `io_should_terminate_tw()`; only the runners in
  `io_uring/tw.c` do, and they store the result in `cancel` of
  `struct io_tw_state`. Handlers test `tw.cancel`.
- `tctx_task_work_run()`: recomputes `ts.cancel` each time it locks a ctx,
  that is when `req->ctx` is not the ctx it holds; not for every entry.
- `__io_run_local_work()`: recomputes `tw.cancel` on every pass of its
  `again` loop.
- `io_cancel_local_task_work()`: sets `cancel` to true without calling
  `io_should_terminate_tw()`.
- Result code on cancel is per handler: for example `io_req_task_submit()`
  fails the request with `-EFAULT`, `io_poll_check_events()` returns
  `-ECANCELED`.
- Per-task queue: there is no fallback_llist, no `fallback_work` in
  `struct io_ring_ctx` and no io_fallback_req_func(); entries are never moved
  off `task_list`.
- `io_fallback_tw()`: takes one argument; it takes a task reference and
  queues `fallback_work` of `struct io_uring_task`, a `struct work_struct`,
  on `system_dfl_wq`.
- `io_tctx_fallback_work()`: calls `tctx_task_work_run()` on the same
  `task_list` from a kworker, so `PF_KTHREAD` makes every handler see
  `tw.cancel`.
- `tctx_task_work_run()` in a task with `PF_EXITING`: does not punt; it runs
  the handlers in that task with `tw.cancel` true.
- Per-ring queue: there is no io_move_task_work_from_local();
  `io_cancel_local_task_work()` pops `work_list` under `ctx->uring_lock` and
  calls each handler in the calling task.
- `io_cancel_local_task_work()` callers: `io_ring_exit_work()` and
  `io_iopoll_try_reap_events()`.
