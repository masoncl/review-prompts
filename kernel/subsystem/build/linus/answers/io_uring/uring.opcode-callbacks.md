- `io_tw_lock()` in `io_uring/tw.h`: only `lockdep_assert_held()`; it takes
  nothing.
- Task work: the runner takes `uring_lock` before calling the handler; see
  `tctx_task_work_run()`, `io_run_local_work()` and
  `io_cancel_local_task_work()` in `io_uring/tw.c`.
- `issue` from poll: `io_poll_issue()` calls `__io_issue_sqe()` directly, so
  there is no `io_assign_file()` and no completion on `IOU_COMPLETE`;
  `io_poll_check_events()` acts on the return value.
- `filter_populate`: called from `io_submit_sqe()` after `prep` returned 0,
  under `uring_lock` and inside `guard(rcu)`, only when the ring has a filter
  for that opcode.
- `sqe_copy`: called through `io_req_sqe_copy()` under `uring_lock`, at most
  once per request (`REQ_F_SQE_COPIED`), from three places: `io_submit_sqe()`
  when the request is appended behind a link head, `io_queue_sqe_fallback()`,
  and `io_queue_async()`.
- `sqe_copy` from `io_queue_async()` without `IO_URING_F_INLINE`, for a
  request not yet copied whose opcode has `sqe_copy`: `io_req_sqe_copy()`
  warns and the request fails with `-EFAULT`.
- `cleanup`: `io_clean_op()` has one caller, `io_free_batch_list()`, reached
  only from `__io_submit_flush_completions()`; so `uring_lock` is held, the
  CQE is already filled, and the last reference is gone.
- `cleanup` relies on that lock: `io_uring_cmd_cleanup()` puts into
  `ctx->cmd_cache` with issue flags 0.
- `cleanup` also runs for a request whose `prep` failed after setting
  `REQ_F_NEED_CLEANUP`.
- `fail`: `io_req_defer_failed()` calls it after `req_set_fail()` and
  `io_req_set_res()`, before `io_req_complete_defer()`.
- `fail` on an unprepared request: `io_submit_fail_init()` leads to
  `io_req_defer_failed()` for an unlinked request or a link head whose `prep`
  failed or never ran; `io_init_fail_req()` zeroes `req->cmd.data` only for
  failures before `prep`.
- `fail` is not called for link members cancelled behind a failed head:
  `io_req_tw_fail_links()` in `io_uring/timeout.c` completes them with
  `io_req_task_complete()`.
