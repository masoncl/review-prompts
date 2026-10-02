- Mapping:

  | Path | Entry | `cancel_all` | Count tested for zero |
  |---|---|---|---|
  | exit, `do_exit()` | `io_uring_files_cancel()` | false | `inflight_tracked` |
  | exec, `begin_new_exec()` | `io_uring_task_cancel()` | true | `inflight` sum |

- Second break in `io_uring_cancel_generic()`: the loop also ends when the
  `inflight` sum reads zero, whatever `cancel_all` is.
- Sleep test: the value saved before cancelling is always the `inflight` sum;
  `schedule()` runs only if it equals `tctx_inflight(tctx, !cancel_all)`,
  which on exit is `inflight_tracked`.
- `io_uring_clean_tctx()`: runs after the loop on exit and on exec.
- With `cancel_all`: `in_cancel` is decremented and the tctx is freed with
  `io_uring_free_tctx()` in `io_uring/tctx.c`, not `__io_uring_free()`.
  `__io_uring_free()` is the task-free path and also frees
  `io_uring_restrict`.
- `io_uring_try_cancel_requests()` under `uring_lock`, in order:
  `io_cancel_defer_files()`, `io_poll_remove_all()`,
  `io_waitid_remove_all()`, `io_futex_remove_all()`,
  `io_uring_try_cancel_uring_cmd()`, `io_kill_timeouts()`.
- `io_uring_try_cancel_requests()` last step: `io_run_task_work()` when
  `tctx` is set; nothing when it is NULL. There is no per-ring fallback work
  in this tree; `fallback_work` is in `struct io_uring_task` and is run by
  `io_tctx_fallback_work()` in `io_uring/tw.c`.
- `io_uring_try_cancel_uring_cmd()`: does not test `REQ_F_INFLIGHT`. With
  `cancel_all` false it cancels every cancelable command of the task; with
  `cancel_all` true it does not compare `req->tctx` at all.
- io-wq step with a `tctx`: `io_cancel_task_cb()` does not compare the ring,
  so one call cancels the task's matching io-wq work on all its rings.
- Local task work step: runs only when `io_allowed_defer_tw_run()` is true,
  that is when `ctx->submitter_task` is `current`.
- SQPOLL thread: `io_sq_thread()` drains pending task work with `io_sq_tw()`
  first, then calls `io_uring_cancel_generic(true, sqd)` with `sqd->lock`
  held; the call passes the thread's own tctx, not `sqd`, as the match.
- SQPOLL thread after the call: its tctx is already freed (`cancel_all` is
  true), so `io_uring_files_cancel()` in its `do_exit()` does nothing.
