- `hrtimer_start_range_ns_common()`: `static` in `kernel/time/hrtimer.c`;
  holds the mismatch check and is called with the base locked by both
  `hrtimer_start_range_ns()` and `hrtimer_start_range_ns_user()`.
- `HRTIMER_MODE_LAZY_REARM`: takes effect at setup only, as `timer->is_lazy`;
  the start path never tests the bit in its `mode` argument and no check
  compares it.
- `is_lazy` timer that is first on the local CPU: removing it or moving it
  later does not reprogram the clock event device, so one pointless
  interrupt can follow; see `__remove_hrtimer()` and
  `__hrtimer_start_range_ns()`.
- Mismatch check: compares one bit, chosen at build time. Without
  `CONFIG_PREEMPT_RT` it compares `HRTIMER_MODE_SOFT` with `is_soft`; with it,
  `HRTIMER_MODE_HARD` with `is_hard`.
- `HRTIMER_MODE_HARD` at setup but not at start: silent without
  `CONFIG_PREEMPT_RT`, `WARN_ON_ONCE()` with it.
- Effect of a mismatch: the warning only; the timer is still started, with
  the soft or hard expiry chosen at setup.
- `is_rel`: written at start only under `CONFIG_TIME_LOW_RES`, in
  `hrtimer_update_lowres()`; otherwise it stays false.
- `__hrtimer_setup_sleeper()` on `CONFIG_PREEMPT_RT`: adds
  `HRTIMER_MODE_HARD` when `rt_or_dl_task_policy(current)` is true and
  `HRTIMER_MODE_SOFT` was not passed.
- `hrtimer_sleeper_start_expires()`: on `CONFIG_PREEMPT_RT` adds
  `HRTIMER_MODE_HARD` to the start mode when `sl->timer.is_hard` is set, so
  callers pass the plain mode and the check stays quiet.
- **Unsafe usage**: starting the timer of a `struct hrtimer_sleeper` with
  `hrtimer_start_expires()` or `hrtimer_start()`; on `CONFIG_PREEMPT_RT` the
  mismatch check warns when `__hrtimer_setup_sleeper()` added
  `HRTIMER_MODE_HARD`.
  - Safe: `hrtimer_sleeper_start_expires()`, as `do_nanosleep()` does; the
    check in `hrtimer_start_range_ns_common()` defines the requirement.
