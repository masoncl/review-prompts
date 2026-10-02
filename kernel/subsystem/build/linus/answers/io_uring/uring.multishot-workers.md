- The test: `req->flags & (REQ_F_MULTISHOT|REQ_F_APOLL_MULTISHOT)`; either
  flag is enough, and no prep function sets both.
- Order of the branches in `io_wq_submit_work()`:

  | Step | Condition | Result |
  |---|---|---|
  | 1 | `io_file_can_poll()` false | fail, `-EBADFD` |
  | 2 | `O_NONBLOCK` or `FMODE_NOWAIT` | `io_arm_poll_handler()`; anything but `IO_APOLL_OK` fails with `-ECANCELED`; the handler is not called |
  | 3 | otherwise | clear both flags, then the normal issue loop, as a single-shot request |

- Reason in the code: with `IORING_SETUP_DEFER_TASKRUN` only the submitter
  task may post CQEs, and auxiliary CQEs are not rerouted the way final
  completions are.
- Flag timing: the check sees only flags set before the worker runs;
  `io_cmd_poll_multishot()` sets `REQ_F_APOLL_MULTISHOT` at issue and is not
  caught on its first issue.
- After step 3 the cleared request flag is what a handler sees:
  `io_read_mshot()` takes its `!(req->flags & REQ_F_APOLL_MULTISHOT)` branch
  and completes once.
- **Potentially unsafe usage**: a request that posts more than one CQE and
  has neither flag set at prep.
  - Unsafe: when the issue handler itself calls `io_req_post_cqe()` and can
    run in a worker (`REQ_F_FORCE_ASYNC`, or a punt by `io_queue_async()`).
  - Safe: posting only from task_work, as `io_timeout_complete()` does, and
    `io_poll_check_events()` for `IORING_OP_POLL_ADD`.
  - Safe: posting only under `IO_URING_F_MULTISHOT`, which a worker never
    passes, as `io_uring_cmd_post_mshot_cqe32()` enforces.
  - Safe: a handler that tests a private flag, when prep also set
    `REQ_F_MULTISHOT`, as `io_sendmsg_prep()` does for
    `IORING_RECVSEND_BUNDLE` and `io_send_finish()`; a socket file always
    has `FMODE_NOWAIT` (`sock_alloc_file()`), so a worker takes step 2 and
    never calls `io_send()`.
