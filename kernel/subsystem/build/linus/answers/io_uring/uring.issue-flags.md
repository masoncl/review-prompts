- `IO_URING_CMD_TASK_WORK_ISSUE_FLAGS` in `include/linux/io_uring/cmd.h` is
  `IO_URING_F_COMPLETE_DEFER`; uring_cmd task-work callbacks pass it on.

| Flag | Tells the handler | Set by |
|---|---|---|
| `IO_URING_F_NONBLOCK` | must not block | `io_queue_sqe()`; `io_poll_issue()`; `io_wq_submit_work()` only for `REQ_F_FORCE_ASYNC` with `pollin` or `pollout` and `io_file_can_poll()`, cleared after one poll attempt |
| `IO_URING_F_COMPLETE_DEFER` | `uring_lock` held, `io_req_complete_defer()` allowed | `io_queue_sqe()`; `io_poll_issue()`; `io_uring_try_cancel_uring_cmd()` |
| `IO_URING_F_UNLOCKED` | `uring_lock` not held; `io_ring_submit_lock()` takes it | `io_wq_submit_work()` |
| `IO_URING_F_IOWQ` | called from io-wq | `io_wq_submit_work()` |
| `IO_URING_F_INLINE` | called from `io_submit_sqes()`, SQE still readable | `io_submit_sqe()` only; `io_req_task_submit()` passes 0 |
| `IO_URING_F_MULTISHOT` | called from `io_poll_issue()`; may return `IOU_REQUEUE`; must not return `IOU_ISSUE_SKIP_COMPLETE` | `io_poll_issue()` only |
| `IO_URING_F_SQE128` | command has a 128-byte SQE | `io_uring_cmd()`: `IORING_SETUP_SQE128` or opcode `IORING_OP_URING_CMD128` |
| `IO_URING_F_CQE32` | 32-byte CQE may be posted | `io_uring_cmd()`: `IORING_SETUP_CQE32` or `IORING_SETUP_CQE_MIXED` |
| `IO_URING_F_IOPOLL` | command is polled to completion | `io_uring_cmd()`: `IORING_SETUP_IOPOLL` and the file has `uring_cmd_iopoll` |
| `IO_URING_F_CANCEL` | `->uring_cmd()` is asked to cancel an issued command | `io_uring_try_cancel_uring_cmd()` |
| `IO_URING_F_COMPAT` | compat layout | `io_uring_cmd()`: `io_is_compat()` |

- `IO_URING_F_SQE128`, `IO_URING_F_CQE32`, `IO_URING_F_IOPOLL`,
  `IO_URING_F_COMPAT`: only `f_op->uring_cmd` implementations see them; no
  other issue handler does.
- `IO_URING_F_INLINE` is tested in one place, `io_req_sqe_copy()`.
- `IO_URING_F_IOWQ`: `io_req_complete_post()` warns and drops the completion
  without it, so a caller of `io_issue_sqe()` passes either
  `IO_URING_F_COMPLETE_DEFER` or `IO_URING_F_IOWQ`.
