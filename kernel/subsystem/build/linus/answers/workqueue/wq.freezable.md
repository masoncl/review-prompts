- Items already active when `freeze_workqueues_begin()` runs, running or
  still on the pool's worklist, all run; `freeze_workqueues_busy()` reports
  busy while any `pwq->nr_active` is nonzero.
- Frozen window in system suspend (with `CONFIG_SUSPEND_FREEZER`): from
  `suspend_freeze_processes()`, which `suspend_prepare()` in
  `kernel/power/suspend.c` calls after the `PM_SUSPEND_PREPARE` notifiers, to
  `suspend_thaw_processes()` in `suspend_finish()`, so it covers
  `dpm_suspend_start()` and `dpm_resume_end()`.
- `pm_wq`: created with `WQ_UNBOUND` only in `kernel/power/main.c`; it is not
  freezable.
- **Unsafe usage**: `flush_work()`, `flush_delayed_work()` or
  `flush_workqueue()` on a freezable workqueue inside the frozen window while
  an item is pending.
  - Unsafe: the item is on `pwq->inactive_works` and `max_active` is 0, so
    the `wait_for_completion()` in `__flush_work()` or `__flush_workqueue()`
    cannot return before `thaw_workqueues()`.
  - Unsafe: `flush_delayed_work()` when only the timer is pending; it queues
    the item first, then waits for it.
  - Safe: `flush_work()` on an idle item; `start_flush_work()` returns
    `false` without waiting.
  - Safe: `cancel_work_sync()` or `cancel_delayed_work_sync()` on a pending
    item, as `r852_suspend()` does; `try_to_grab_pending()` takes it off
    `inactive_works`, and `start_flush_work()` then finds no worker running
    it.
  - Safe: flushing before `freeze_kernel_threads()` or after
    `thaw_processes()`.
