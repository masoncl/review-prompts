- `iopoll_list`: a `struct list_head`; requests are linked through
  `iopoll_node`.
- `comp_list`: not the link while a request is on `iopoll_list`;
  `io_do_iopoll()` uses it only after `list_del()`, to queue the request on
  `submit_state.compl_reqs`.
- Membership test: `io_issue_sqe()` calls `io_iopoll_req_issued()` when the
  request has `REQ_F_IOPOLL` and the handler returned
  `IOU_ISSUE_SKIP_COMPLETE`; there is no iopoll_queue bit in
  `struct io_issue_def`.
- `__io_uring_cmd_done()`: chooses the release store to `iopoll_completed`
  by `REQ_F_IOPOLL`, not by `IORING_SETUP_IOPOLL`.
- Reap loop in `io_do_iopoll()`: skips a request that is not completed and
  goes on, so requests leave the list out of order; pairing is
  `smp_store_release()` in the callback with `smp_load_acquire()` here.
- Lockless `list_empty(&ctx->iopoll_list)`: used as a hint without
  `uring_lock` in `__io_sq_thread()`, `io_sq_thread()` and
  `io_uring_try_cancel_requests()`; every walk, add and delete is under
  `uring_lock`.
- Release store to `iopoll_completed`: must be the callback's last access
  to the request; a poller holding `uring_lock` can then recycle it through
  `io_free_batch_list()`.
- Task work on a `REQ_F_IOPOLL` uring_cmd: allowed when the task-work
  callback finishes through `__io_uring_cmd_done()`, which for
  `REQ_F_IOPOLL` stores `iopoll_completed` instead of completing the
  request; `io_do_iopoll()` still posts the CQE.
- `iopoll_start`: shares storage with `io_task_work`, so queueing task work
  overwrites it.
- `poll_ctx` of `struct io_comp_batch`: set to the ring by `io_do_iopoll()`;
  a driver compares it with `io_uring_cmd_ctx_handle()` to learn whether
  the completion runs under that ring's `uring_lock`.
- **Potentially unsafe usage**: completing a polled uring_cmd with
  `io_uring_cmd_done32()` and `issue_flags` 0.
  - Unsafe: when the completion does not run inside `io_do_iopoll()` of the
    request's own ring; `io_req_uring_cleanup()` then puts into
    `ctx->cmd_cache` without `uring_lock`.
  - Safe: when `iob->poll_ctx` equals the request's ring, as
    `nvme_uring_cmd_end_io()` tests; `io_req_uring_cleanup()` treats every
    call without `IO_URING_F_UNLOCKED` as locked.
  - Safe: otherwise punt with `io_uring_cmd_do_in_task_lazy()` and complete
    with `IO_URING_CMD_TASK_WORK_ISSUE_FLAGS`, as `nvme_uring_task_cb()`
    does; `tctx_task_work_run()` holds `uring_lock` around the callback.
