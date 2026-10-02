- `io_lockdep_assert_cq_locked()`: body compiled only under
  `CONFIG_PROVE_LOCKING`; first asserts `in_task()` for every ring.

| `IORING_SETUP_DEFER_TASKRUN` | `IORING_SETUP_IOPOLL` | Required |
|---|---|---|
| no | no | `completion_lock` held |
| no | yes | `uring_lock` held |
| yes | no | `uring_lock` held and `current == ctx->submitter_task` |
| yes | yes | `uring_lock` held only |

- Submitter test: skipped when `ctx->submitter_task` is NULL or `ctx->refs` is
  dying.
- Flags read by the assert: `ctx->flags` for the two setup flags, and
  `IO_RING_F_TASK_COMPLETE` in `ctx->int_flags`.
- `IO_RING_F_LOCKLESS_CQ`: not read by the assert. Posting code reads it to
  skip `completion_lock`, for example `__io_cq_lock()` and
  `io_req_post_cqe()`.
- `IO_RING_F_SYSCALL_IOPOLL`: not read by the assert; it suppresses the
  wakeup in `__io_cq_unlock_post()` and makes `io_uring_enter()` call
  `io_iopoll_check()`.
- `io_cq_lock()`: always takes `completion_lock`; `__io_cq_lock()` is the
  conditional one.
