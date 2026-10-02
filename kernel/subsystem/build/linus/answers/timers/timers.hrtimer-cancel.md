- Models have the return values, the wait loop and the absence of an
  operation that prevents re-arming right; see `hrtimer_cancel()` in
  `kernel/time/hrtimer.c`.
- `hrtimer_cancel_wait_running()` on `CONFIG_PREEMPT_RT`: sleeps on
  `softirq_expiry_lock` only when `timer->is_soft` is set; for a
  `HRTIMER_MODE_HARD` timer, or one on the migration base, it is
  `cpu_relax()`.
- `hrtimer_cancel()` without `CONFIG_PREEMPT_RT`: spins and checks nothing
  about the calling context.
- **Unsafe usage**: `hrtimer_cancel()` on a soft timer from a context that
  can interrupt its callback on the same CPU, such as a hard interrupt
  handler; the callback never finishes and the loop never ends.
  - Safe: `hrtimer_try_to_cancel()`, which returns -1 instead of waiting
    while `hrtimer_callback_running()` is true, and handling -1.
- **Unsafe usage**: `hrtimer_cancel()` while holding a lock the callback
  takes.
  - Safe: take the lock, call `hrtimer_try_to_cancel()`; on -1 drop the lock,
    call `hrtimer_cancel_wait_running()` and retry, as `do_timerfd_settime()`
    in `fs/timerfd.c` does.
