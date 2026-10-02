- `pm_runtime_autosuspend_expiration()`: returns `u64` nanoseconds on the
  `ktime_get_mono_fast_ns()` clock, not jiffies, and does no rounding.
- `Documentation/power/runtime_pm.rst`: still describes it as returning
  `unsigned long` jiffies rounded up to a second for long delays; the code
  in `drivers/base/power/runtime.c` does neither.
- Delay of 0: not tested for; the delay test is `autosuspend_delay < 0`, and
  a zero delay returns 0 because the expiry is not in the future.
- `dev->power.last_busy`: written by `pm_runtime_mark_last_busy()`, which
  `rpm_resume()` also calls on every successful resume.
- Negative delay with `use_autosuspend` set: on the change to that state
  `update_autosuspend()` increments `usage_count` and calls `rpm_resume()`;
  the held reference is what blocks suspend, through
  `rpm_check_suspend_allowed()`.
- Negative delay with `use_autosuspend` clear: `update_autosuspend()` takes
  no reference.
- `pm_runtime_dont_use_autosuspend()` after `pm_runtime_disable()`: still
  clears the flag and drops the negative-delay reference; only the
  `rpm_idle()` at its end fails with `-EACCES`.
- `pm_runtime_reinit()`: resets neither `use_autosuspend` nor
  `autosuspend_delay` on unbind.
