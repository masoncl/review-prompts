- `thread` writers: `io_sq_offload_create()` stores the task and
  `io_sq_thread()` stores NULL at its two exits, all under `sqd->lock`;
  nothing else writes it.
- `io_sq_thread_stop()`, `io_put_sq_data()`, `io_sq_thread_finish()`: do not
  clear `thread`; `io_sq_thread_stop()` sets `IO_SQ_THREAD_SHOULD_STOP`,
  wakes the thread and waits on `exited`, and the other two reach it only
  when the last `refs` of the `struct io_sq_data` is dropped.
- Task reference: taken by `get_task_struct(tsk)` in
  `io_sq_offload_create()`, after `thread` is published and before
  `wake_up_new_task()`.
- `create_io_thread()` in `kernel/fork.c`: only returns what
  `copy_process()` returns.
- Reference drop: `put_task_struct(current)` in `io_sq_thread()`, under
  `sqd->lock`, directly after the NULL store, so a non-NULL result of
  `sqpoll_task_locked()` stays valid until `sqd->lock` is released.
- Lock order: `sqd->lock` is taken outside `ctx->uring_lock`;
  `io_sq_thread()` holds `sqd->lock` while `__io_sq_thread()` takes
  `uring_lock`.
- Code holding `uring_lock`: drops it before `io_sq_thread_park()` or
  `mutex_lock(&sqd->lock)`, as `io_register_iowq_max_workers()` and
  `__io_register_iowq_aff()` in `io_uring/register.c` do.
- `tsk->io_uring` of the returned task: can be NULL while `thread` is not.
  `io_sq_offload_create()` assigns it after publishing `thread`, outside
  `sqd->lock`, and leaves it NULL when `io_uring_alloc_task_context()`
  fails.
- `io_uring_alloc_task_context()`: returns the `struct io_uring_task *`; the
  caller stores it in `tsk->io_uring`.
- Readers of `tsk->io_uring`: test it for NULL, for example
  `io_ring_exit_work()` and `io_wq_cpu_affinity()`.
- **Potentially unsafe usage**: a plain load of `thread`, without
  `sqpoll_task_locked()` or `rcu_dereference()`.
  - Unsafe: when the loaded pointer is dereferenced or handed to another
    function; `io_sq_thread()` can clear it and drop the reference at any
    time.
  - Safe: when the value is only compared with NULL, as `io_uring_enter()`
    does to return `-EOWNERDEAD` and `io_sq_offload_create()` does to return
    `-ENXIO` on attach.
- Task signalled for task work on an `IORING_SETUP_SQPOLL` ring:
  `req->tctx->task`, by `__set_notify_signal()` in
  `io_req_normal_work_add()` in `io_uring/tw.c`; the function returns
  without `task_work_add()` and reads neither `sq_data` nor `thread`.
- `req->tctx`: set to `current->io_uring` in `io_init_req()`. On an SQPOLL
  ring `io_submit_sqes()` is reached only from `__io_sq_thread()`, so the
  task is the SQPOLL thread.
- `IORING_SETUP_DEFER_TASKRUN` with `IORING_SETUP_SQPOLL`: rejected by
  `io_uring_sanitise_params()`, so `io_req_local_work_add()` is never the
  path on an SQPOLL ring.
- `-EPERM` from `io_attach_sq_data()` (other `task_tgid`): not returned to
  user space; `io_get_sq_data()` falls through and allocates a new
  `struct io_sq_data` with its own thread.
