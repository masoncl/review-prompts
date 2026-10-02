- `req->file` is NULL in `prep`: `io_init_req()` only stores `req->cqe.fd`
  when `needs_file` is set; `io_assign_file()` runs at issue.
- No file-table or fixed-file lookup precedes `prep`.
- Checks in `io_init_req()` before `prep`, besides opcode and SQE flags:
  `ioprio`, `iopoll` on an `IORING_SETUP_IOPOLL` ring, `buffer_select`,
  `io_check_restriction()`, personality.
- `is_128` opcodes: on a ring without `IORING_SETUP_SQE128`, `io_init_req()`
  requires `IORING_SETUP_SQE_MIXED` and a second contiguous entry, and consumes
  it before `prep`; otherwise `-EINVAL`.
- `req->cmd.data` is not cleared before a successful `prep`; `prep` must set
  every field that `issue`, `fail` or `cleanup` reads.
- `io_init_req()` sets `req->tctx` to `current->io_uring` and
  `req->async_data` to NULL.
- BPF filters run after `prep`, in `io_submit_sqe()`; a denial goes to
  `io_submit_fail_init()` with `-EACCES` on an already prepared request.
- Lock: every step in `io_submit_sqes()` is under `uring_lock`
  (`__must_hold`), but the first issue is not always one of those steps.

| Request | First issue | `uring_lock` | `IO_URING_F_INLINE` |
|---|---|---|---|
| plain, or link head once the link is complete | `io_queue_sqe()` in `io_submit_sqe()` | held | set |
| `REQ_F_FORCE_ASYNC`, no drain | `io_wq_submit_work()` | not held | not set |
| later link member | `io_req_task_submit()`, or io-wq via `io_wq_free_work()` | held / not held | not set |
| drained (carries `REQ_F_FORCE_ASYNC`) | `io_wq_submit_work()`, after `io_req_task_submit()` from `io_queue_deferred()` calls `io_queue_iowq()` | not held | not set |

- Init failure in a link: only the failing request and the head get
  `REQ_F_FAIL`; the other members get no flag and complete with `-ECANCELED`
  in `io_req_tw_fail_links()`.
- Init failure in a link: no member is issued, the head included.
- Members after the failed one are still prepared, so their `prep` may
  allocate; they are then cancelled.
- `io_submit_fail_init()` returns 0 when the failing request has
  `IO_REQ_LINK_FLAGS`; the batch continues whatever
  `IORING_SETUP_SUBMIT_ALL` says.
- `io_submit_fail_init()` returns the error when the failing request is
  unlinked or ends the link; `io_submit_sqes()` then stops, unless
  `IORING_SETUP_SUBMIT_ALL` is set.
