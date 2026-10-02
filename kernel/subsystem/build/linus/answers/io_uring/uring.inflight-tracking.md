- Tracked kinds, two in this tree:

  | Kind | Where tracked | Condition |
  |---|---|---|
  | io_uring file used as a normal file | `io_file_get_normal()` | `io_is_uring_fops()` true |
  | futex wait | `io_futex_wait_prep()`, `io_futexv_prep()` | a futex without `FLAGS_SHARED` |

- Linked timeouts and io-wq work in general are not tracked; `REQ_F_INFLIGHT`
  is set nowhere but in `io_req_track_inflight()`.
- `io_req_track_inflight()`: sets the flag and increments
  `inflight_tracked`; nothing else.
- Futex tracking: done at prep, not in `io_futex_wait()` or
  `io_futexv_wait()`; for `io_futexv_prep()` one private futex in the vector
  is enough.
- Fixed files: never tracked because the file tables reject io_uring files;
  see the `io_is_uring_fops()` tests in `io_uring/rsrc.c` and
  `io_uring/filetable.c`.
- File tracking point: `io_assign_file()`, or an issue handler's own call of
  `io_file_get_normal()`, for example `io_splice_get_file()`.
  `io_assign_file()` runs at inline issue in `io_issue_sqe()`, or in
  `io_wq_submit_work()` for a request that `io_queue_sqe_fallback()` queued
  to io-wq unissued, so such a request waits on the io-wq list untracked.
- `io_put_task()` on the owning task: only does `cached_refs++`; `inflight`
  does not move and `tctx->wait` is not woken.
- `io_put_task()` from another task: subtracts from `inflight` and wakes
  `tctx->wait` when `in_cancel` is set.
- `inflight` during cancel: drops for the task's own completions only at
  `io_uring_drop_tctx_refs()`; `tctx_task_work_run()` calls it when
  `in_cancel` is set and `current->io_uring` is that tctx.
- `io_match_task()` in `io_uring/timeout.c`: a second copy of the
  `REQ_F_INFLIGHT` link walk, used by `io_kill_timeouts()` with
  `ctx->timeout_lock` already held; `io_match_task_safe()` must not be
  called with that lock held.
