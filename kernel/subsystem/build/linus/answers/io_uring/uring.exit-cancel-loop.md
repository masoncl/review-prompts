- `io_ring_exit_work()`: calls `io_cancel_local_task_work()` on every pass
  of its inner loop when `IORING_SETUP_DEFER_TASKRUN` is set; the handlers
  run in the exit kworker itself, not in a second work item.
- Loop shape: inner `do { io_cancel_local_task_work(); cond_resched(); }
  while (io_uring_try_cancel_requests(ctx, NULL, true, false))`; outer loop
  ends on `wait_for_completion_interruptible_timeout()` of `ctx->ref_comp`.
- `io_uring_try_cancel_requests()` with a NULL `tctx`: does not call
  `flush_delayed_work()` or `io_run_task_work()`, and skips
  `io_run_local_work()` in the kworker because `io_allowed_defer_tw_run()`
  is false.
- `io_cancel_local_task_work()`: returns `void`, so work it ran does not
  count as progress for the inner loop; the timed outer wait calls it again.
- **Unsafe usage**: a loop run by a task other than `submitter_task` that
  waits for the ring's requests to drain without calling
  `io_cancel_local_task_work()` on each pass.
  - Unsafe: `__io_run_local_work()` returns `-EEXIST` for that task, entries
    stay on `work_list`, and their requests keep `ctx->refs` from reaching
    zero.
  - Safe: `io_ring_exit_work()` calls it before every
    `io_uring_try_cancel_requests()`.
  - Safe: in `submitter_task`, `io_uring_try_cancel_requests()` runs the
    queue with `io_run_local_work()`, as under `io_uring_cancel_generic()`.
- **Unsafe usage**: taking `work_list` as empty after one call of
  `io_cancel_local_task_work()`.
  - Unsafe: when the cancelled requests have links; the final
    `io_submit_flush_completions()` reaches `io_queue_next()`, which queues
    the next request on `work_list` after the drain loop has ended.
  - Safe: call it again until `ctx->ref_comp` completes, as
    `io_ring_exit_work()` does.
- **Unsafe usage**: calling `io_cancel_local_task_work()` or
  `io_uring_try_cancel_requests()` with `ctx->uring_lock` held; both take it.
  - Safe: drop the lock first, as `io_iopoll_try_reap_events()` does before
    `io_cancel_local_task_work()`.
- **Potentially unsafe usage**: sleeping without a timeout after a pass that
  cancelled nothing.
  - Unsafe: when `cq_wait_nr` was not armed for this pass, or work queued
    before the sleep is not rechecked; `io_req_local_work_add()` wakes once
    per arming.
  - Safe: `io_uring_cancel_generic()` relies on
    `io_uring_try_cancel_requests()` storing 1 in `cq_wait_nr` each pass,
    and after `prepare_to_wait()` it tests `io_local_work_pending()` and
    `tctx_inflight()` before `schedule()`.
  - Safe: the cancel loop of `io_ring_exit_work()` waits for requests only
    in `wait_for_completion_interruptible_timeout()`.
