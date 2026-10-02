- `REQ_F_MULTISHOT`: set only by `io_sendmsg_prep()` for
  `IORING_RECVSEND_BUNDLE`; tested only by `io_wq_submit_work()`. No handler
  reads it.
- `REQ_F_APOLL_MULTISHOT`: set by opcode prep, for example
  `io_recvmsg_prep()`, `io_accept_prep()`, `io_read_mshot_prep()` and
  `io_recvzc_prep()`; `io_arm_poll_handler()` does not set it.
- `io_cmd_poll_multishot()` in `io_uring/uring_cmd.c`: the one place that
  sets `REQ_F_APOLL_MULTISHOT` at issue time, just before `io_arm_apoll()`.
- `REQ_F_APOLL_MULTISHOT` readers in `io_uring/poll.c`: `io_arm_apoll()`
  leaves out `EPOLLONESHOT`; `io_poll_check_events()` calls `io_poll_issue()`
  instead of posting the poll mask itself.
- `IORING_POLL_ADD_MULTI` and `IORING_TIMEOUT_MULTISHOT` requests: carry
  neither request flag; the state is the missing `EPOLLONESHOT` in
  `poll->events` and the flag in `struct io_timeout_data`.
- Staying armed: a handler tests `req->flags & REQ_F_APOLL_MULTISHOT`, as
  `io_accept()`, `io_recv_finish()` and `io_read_mshot()` do.
- First inline issue: has no `IO_URING_F_MULTISHOT`, yet these handlers post
  with `IORING_CQE_F_MORE` and return `IOU_RETRY`; `io_queue_async()` then
  arms poll.
- `IO_URING_F_MULTISHOT` in a handler: gates what the poll loop alone
  understands, for example `IOU_REQUEUE` and `io_poll_multishot_retry()`; see
  "Multishot handler results".
- `io_uring_cmd_post_mshot_cqe32()`: the exception, it refuses to post
  without `IO_URING_F_MULTISHOT`.
- Clearing: only `io_wq_submit_work()` clears `REQ_F_APOLL_MULTISHOT`; a
  handler that ends multishot leaves it set and returns `IOU_COMPLETE`.
