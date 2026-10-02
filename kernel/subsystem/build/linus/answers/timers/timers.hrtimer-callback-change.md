- `function` in `struct hrtimer`: marked `__private`; `__private` expands to
  nothing unless `__CHECKER__` is defined (`include/linux/compiler_types.h`),
  so a direct assignment compiles and only sparse reports it.
- `hrtimer_update_function()`: the function that changes the callback after
  setup; defined out of line in `kernel/time/hrtimer.c` with
  `EXPORT_SYMBOL_GPL()`, only declared in `include/linux/hrtimer.h`.
- Requirements of `hrtimer_update_function()`: the timer is not queued, the
  new callback is not NULL, and the caller excludes a concurrent start.
- Checks in `hrtimer_update_function()`: compiled in only under
  `CONFIG_PROVE_LOCKING`; there it warns once and leaves the old callback.
- Without `CONFIG_PROVE_LOCKING`: a plain store with no lock and no test; a
  NULL pointer is stored and `__run_hrtimer()` calls it unchecked.
- `hrtimer_setup()` on a timer that is already set up: not a callback change;
  `__hrtimer_setup()` clears the whole `struct hrtimer` with `memset()` and
  picks the base again.
- **Potentially unsafe usage**: calling `hrtimer_update_function()` on a
  timer that has been started.
  - Unsafe: while the timer is queued or another context can start it;
    `__run_hrtimer()` reads the pointer under `cpu_base->lock`, and without
    `CONFIG_PROVE_LOCKING` the store takes no lock, so either callback may
    run.
  - Safe: from the timer's own callback before it returns
    `HRTIMER_RESTART`, when nothing else starts the timer, as
    `io_cqring_min_timer_wakeup()` in `io_uring/wait.c` does;
    `__run_hrtimer()` dequeued the timer before the call.
  - Safe: between setup and the first start, as `rt2800mmio_probe_hw()` does
    on the timer that `rt2x00lib_probe_dev()` set up with
    `hrtimer_dummy_timeout()`.
- **Potentially unsafe usage**: calling `hrtimer_setup()` again on a used
  timer.
  - Unsafe: while the timer is queued or its callback runs; the `memset()`
    wipes the queue node and `is_queued`.
  - Safe: after a cancel that did not return -1, under the lock that
    serialises starts, as `common_hrtimer_arm()` does after
    `common_timer_set()` called `timer_try_to_cancel`.
