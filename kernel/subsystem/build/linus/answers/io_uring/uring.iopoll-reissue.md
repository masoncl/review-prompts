- Marking condition in `io_complete_rw_iopoll()`: `res == -EAGAIN` and
  `io_rw_should_reissue()` returns true; it is tested before any comparison
  with `req->cqe.res`.
- When `io_complete_rw_iopoll()` does not mark the request: `req->cqe.res`
  is set to the result of `io_fixup_rw_res()` when that differs from it.
- `-EOPNOTSUPP`: leads to reissue only in `__io_complete_rw_common()`, the
  non-IOPOLL path.
- `io_rw_should_reissue()` returns false when any of these holds, and makes
  no other test:
  - the file is neither a block device nor a regular file;
  - `REQ_F_NOWAIT` is set;
  - the caller is an io-wq worker and the request lacks `REQ_F_IOPOLL`;
  - `percpu_ref_is_dying(&ctx->refs)`;
  - `CONFIG_BLOCK` is off.
- Iterator restore: done inside `io_rw_should_reissue()` at marking time
  (`io_meta_restore()`, `iov_iter_restore()`), in the completion callback's
  context, not later in the retry.
- CQE skip: `__io_submit_flush_completions()` posts nothing for a request
  with `REQ_F_REISSUE`.
- `io_free_batch_list()`: clears `REQ_F_REISSUE` and calls `io_queue_iowq()`
  directly, with no task work in between; the request is not put or
  returned to the cache. There is no io_req_task_queue_reissue() here.
- Thread-group test: lives in `io_queue_iowq()`, not in
  `io_rw_should_reissue()`; when `current` is not in the thread group of
  `req->tctx->task` it warns and sets `IO_WQ_WORK_CANCEL`, so
  `io_wq_submit_work()` fails the request with `-ECANCELED`.
- `io_req_complete_post()`: sends a request with `REQ_F_REISSUE` through
  `io_req_task_complete()` task work instead of posting a CQE, so it reaches
  `io_free_batch_list()` too.
