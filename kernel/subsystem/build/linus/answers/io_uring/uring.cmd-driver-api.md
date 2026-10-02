- `io_uring_cmd_done(cmd, ret, issue_flags)`: no `res2` argument.
  `io_uring_cmd_done32(cmd, ret, res2, issue_flags)` stores `res2` in
  `req->big_cqe.extra1` and, on `IORING_SETUP_CQE_MIXED` rings, sets
  `IORING_CQE_F_32`.
- Task-work callback type: `io_req_tw_func_t`, arguments
  `struct io_tw_req` and `io_tw_token_t`. There is no io_uring_cmd_tw_t and
  the callback receives no issue_flags.
- Inside the callback: get the command with `io_uring_cmd_from_tw()`, pass
  `IO_URING_CMD_TASK_WORK_ISSUE_FLAGS` to `io_uring_cmd_done()`;
  `uring_lock` is held.
- `tw.cancel`: true when the task is exiting, runs as a kthread, or the ring
  is dying (`io_should_terminate_tw()` in `io_uring/tw.h`). There is no
  IO_URING_F_TASK_DEAD flag. The callback must still complete the command,
  as `ublk_ch_uring_cmd_cb()` and `fuse_uring_send_in_task()` do.
- `io_uring_cmd_do_in_task_lazy()`: the lazy form; there is no
  io_uring_cmd_complete_in_task_lazy. `IOU_F_TWQ_LAZY_WAKE` is for commands
  that post one CQE and is ignored without `IORING_SETUP_DEFER_TASKRUN`.
- `io_uring_cmd_issue_blocking()`: not exported, so built-in callers only.
- `IORING_SETUP_IOPOLL` ring, file without `->uring_cmd_iopoll`:
  `io_uring_cmd()` does not fail; it leaves `REQ_F_IOPOLL` and
  `IO_URING_F_IOPOLL` clear and issues the command as non-polled.
- `IORING_URING_CMD_MULTISHOT`: `io_uring_cmd()` has no special case. Any
  return other than `-EAGAIN` and `-EIOCBQUEUED` ends the request.
- `-EAGAIN` from an `io_queue_sqe()` issue (`IO_URING_F_NONBLOCK`):
  `io_queue_async()` sends the request to io-wq; `io_arm_poll_handler()`
  returns `IO_APOLL_ABORTED` because the two opcodes set neither `pollin`
  nor `pollout` in `io_issue_defs[]`.
- `-EAGAIN` from the io-wq issue (`IO_URING_F_UNLOCKED | IO_URING_F_IOWQ`):
  `io_wq_submit_work()` fails the request with `-EAGAIN`, unless
  `REQ_F_IOPOLL` is set, in which case it loops and reissues.
- Completing inside the issue call: after `io_uring_cmd_done()` the issue
  call must return `-EIOCBQUEUED`, as `fuse_uring_cmd()` does; any other
  value makes `io_uring_cmd()` complete the request a second time or, for
  `-EAGAIN`, reissue it.
- `issue_flags` given to `io_uring_cmd_done()` must match the caller's lock
  state; they need not come from the core:

| Caller | `issue_flags` |
|---|---|
| issue or cancel call | the argument received |
| task-work callback | `IO_URING_CMD_TASK_WORK_ISSUE_FLAGS` |
| sleepable context without `uring_lock` | `IO_URING_F_UNLOCKED`, as `fuse_uring_entry_teardown()` |

- `IO_URING_F_UNLOCKED` on a cancelable command: `io_uring_cmd_del_cancelable()`
  takes the `uring_lock` mutex, so the caller must be able to sleep and must
  not hold that lock.
