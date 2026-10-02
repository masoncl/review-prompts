- `io_req_complete_defer()`: the only requirement checked is
  `lockdep_assert_held(&req->ctx->uring_lock)`; the caller need not be a
  submission path, and must be the submitter task only where "CQ locking"
  asks that of the flush.
  - For example `io_uring_try_cancel_uring_cmd()` in `io_uring/uring_cmd.c`
    passes `IO_URING_F_CANCEL | IO_URING_F_COMPLETE_DEFER` and flushes itself.
  - Task work reaches it from a kworker through `io_tctx_fallback_work()`, and
    from `io_cancel_local_task_work()` in `io_ring_exit_work()`.
- `io_req_task_complete()`: calls `io_req_complete_defer()` and nothing else.
- Flush after `io_req_complete_defer()`: must run before `uring_lock` is
  dropped; search callers of `io_submit_flush_completions()` for the places
  that do it.
- Request after `io_req_complete_defer()`: may be recycled before the caller's
  own flush, because `io_req_post_cqe()` calls
  `__io_submit_flush_completions()` when `compl_reqs` is not empty.
- `__io_uring_cmd_done()` on a request without `REQ_F_IOPOLL`:
  `WARN_ON_ONCE()` and return when `IO_URING_F_COMPLETE_DEFER` comes with
  `IO_URING_F_UNLOCKED`.
- `io_req_complete_post()`: static in `io_uring/io_uring.c`, called only by
  `io_issue_sqe()` when `IO_URING_F_COMPLETE_DEFER` is not set.
  - Without `IO_URING_F_IOWQ` it does `WARN_ON_ONCE()` and returns; the
    request is not completed.
  - It never posts on a ring with `IO_RING_F_LOCKLESS_CQ` in `ctx->int_flags`
    (there is no lockless_cq field); it queues `io_req_task_complete()`.
  - It never frees; `req_ref_put()` relies on the extra reference that
    `io_wq_submit_work()` takes.
  - An opcode handler reaches it by `io_req_set_res()` and returning
    `IOU_COMPLETE`; other code cannot call it.
- `io_req_queue_tw_complete()`: overwrites `req->cqe.flags` with 0. A
  completion that carries cflags calls `io_req_set_res()`, sets
  `io_task_work.func` to `io_req_task_complete()` and calls
  `io_req_task_work_add()`, as `io_nop()` does.
- `io_req_queue_tw_complete()` queue: `ctx->work_list` on
  `IORING_SETUP_DEFER_TASKRUN` rings, else `req->tctx->task_list`; see
  `__io_req_task_work_add()` in `io_uring/tw.h`.
