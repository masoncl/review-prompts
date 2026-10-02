- `fuse_uring_send_in_task()`: signature is `(struct io_tw_req, io_tw_token_t)`;
  it gets no issue flags and uses the constant
  `IO_URING_CMD_TASK_WORK_ISSUE_FLAGS`, which is `IO_URING_F_COMPLETE_DEFER`.
- There is no IO_URING_F_TASK_DEAD here; the callback tests `tw.cancel`, set
  from `io_should_terminate_tw()` in `io_uring/tw.h`.
- `tw.cancel` is true for an exiting task, a kernel thread and a dying ring, so
  the fallback worker never copies.
- `tw.cancel` branch: unlinks the entry, recycles its buffer, completes the
  command with `-ECANCELED`, ends the request with `-ECANCELED`, frees the
  entry and drops `ring->queue_refs`.
- There is no fuse_uring_send_next_to_ring() here; the commit path calls
  `fuse_uring_get_next_fuse_req()` then `fuse_uring_send()`.

| Path | Task | Issue flags used |
|---|---|---|
| request meets an available entry | server, task work | `IO_URING_CMD_TASK_WORK_ISSUE_FLAGS` |
| fetch after commit | server, in `fuse_uring_cmd()` | flags of that call, unchanged |
| `fuse_uring_entry_teardown()` | aborting task or worker | `IO_URING_F_UNLOCKED` |
| `fuse_uring_cancel()` | io_uring cancel | flags of that call |

- Issue flags also reach `io_buffer_register_bvec()`,
  `io_buffer_unregister()` and `io_uring_cmd_import_fixed()` through
  `fuse_uring_prepare_send()` and `fuse_uring_req_end()`.
- `io_ring_submit_lock()` in `io_uring/io_uring.h`: takes `ctx->uring_lock`
  only with `IO_URING_F_UNLOCKED`, so the flags must match the real lock state.
