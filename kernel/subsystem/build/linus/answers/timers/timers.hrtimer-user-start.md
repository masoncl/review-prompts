- `hrtimer_start_range_ns_user()` in `kernel/time/hrtimer.c` is the separate
  start function; `hrtimer_start_expires_user()` in `include/linux/hrtimer.h`
  is its counterpart to `hrtimer_start_expires()`. Both return `bool`.
- Difference from `hrtimer_start_range_ns()`: after the same enqueue, when
  the timer would become the next event to program,
  `hrtimer_check_user_timer()` tests whether the soft expiry is already in
  the past; if so it dequeues the timer again and the clock event device is
  not armed for it.
- Callback on an expired timer: never invoked by the start function; the
  caller may hold a lock the callback takes.
- Return `true`: the timer is queued and the callback will run; this is also
  returned for a timer in the past that is not the first to expire.
- Return `false`: the timer is not queued and the callback will not run.
- Caller on `false`: does the expiry work itself in its own context, for
  example `timerfd_hrtimer_start()` in `fs/timerfd.c` calls
  `__timerfd_triggered()`, and `common_timer_set()` in
  `kernel/time/posix-timers.c` calls `posix_timer_queue_signal()`.
- `alarm_start_timer()` in `kernel/time/alarmtimer.c`: uses it and returns
  `bool` with the same meaning; a caller handles `false` itself, as
  `timerfd_alarm_start()` in `fs/timerfd.c` does.
- `hrtimer_sleeper_start_expires()`: uses `hrtimer_start_expires_user()`; on
  `false` it sets `sl->task` to NULL and the task state to `TASK_RUNNING`.
- **Unsafe usage**: ignoring the return value; the expiry is lost.
  - Safe: test it and handle the expiry, as `timerfd_hrtimer_start()` does.
- **Unsafe usage**: sleeping after `hrtimer_sleeper_start_expires()` without
  testing `sl->task`; for an expired sleeper no timer is queued to wake the
  task.
  - Safe: `if (t->task) schedule();`, as `do_nanosleep()` does.
