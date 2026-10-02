- `IOU_RETRY` is `-EAGAIN`; the core cannot tell them apart.
- `IOU_ISSUE_SKIP_COMPLETE`: `io_issue_sqe()` returns 0 for it, and calls
  `io_iopoll_req_issued()` when the request has `REQ_F_IOPOLL`.
- Other non-zero return, inline: `io_queue_async()` calls
  `io_req_defer_failed()` with that value.
- Other non-zero return, io-wq: `io_wq_submit_work()` calls
  `io_req_task_queue_fail()`.
- `-EAGAIN` in io-wq: retried in a loop only when the request has
  `REQ_F_IOPOLL` and `io_wq_worker_stopped()` is false; retried once blocking
  after a poll attempt for `REQ_F_FORCE_ASYNC` that did not arm; otherwise the
  request fails with `-EAGAIN`.
- **Unsafe usage**: returning `IOU_REQUEUE` without `IO_URING_F_MULTISHOT`.
  - Unsafe: inline or in io-wq the value is treated as an error and the CQE
    carries `-3072`.
  - Safe: test `IO_URING_F_MULTISHOT` first and fall back to `IOU_RETRY`, as
    `io_recv_finish()` in `io_uring/net.c` and `io_zcrx_tcp_recvmsg()` in
    `io_uring/zcrx.c` do.
- **Unsafe usage**: returning `IOU_ISSUE_SKIP_COMPLETE` under
  `IO_URING_F_MULTISHOT`.
  - Unsafe: `io_poll_issue()` warns, and `io_poll_check_events()` returns it
    as an error, so the request fails with `-EIOCBQUEUED`.
  - Safe: return `IOU_RETRY` to stay armed, as `io_read_mshot()` does.
- Handler return under `io_poll_issue()`, as mapped by
  `io_poll_check_events()`:

| Handler returns | `io_poll_check_events()` |
|---|---|
| `IOU_COMPLETE` | returns `IOU_POLL_REMOVE_POLL_USE_RES` |
| `IOU_REQUEUE` | returns `IOU_POLL_REQUEUE` |
| `IOU_RETRY` | drops its references and returns `IOU_POLL_NO_ACTION`, or loops if a wakeup came in meanwhile; poll stays armed |
| other negative | returns it |

- `io_poll_check_events()` results, as handled by `io_poll_task_func()`:

| Result | `IORING_OP_POLL_ADD` | Any other opcode |
|---|---|---|
| `IOU_POLL_NO_ACTION` | nothing | nothing |
| `IOU_POLL_REQUEUE` | `__io_poll_execute()` again, entries stay armed | same |
| `IOU_POLL_DONE` | complete with the mask | `io_req_task_submit()` |
| `IOU_POLL_REISSUE` | `io_req_task_submit()` | `io_req_task_submit()` |
| `IOU_POLL_REMOVE_POLL_USE_RES` | complete with `req->cqe.res` | `io_req_task_complete()` |
| negative | `req_set_fail()`, complete with it | `io_req_defer_failed()` |

- `tw.cancel` set: `io_poll_check_events()` returns `-ECANCELED` before
  looking at events, and `io_req_task_submit()` fails the request with
  `-EFAULT` instead of reissuing.
