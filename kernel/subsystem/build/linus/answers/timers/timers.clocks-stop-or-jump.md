- `CLOCK_MONOTONIC` and `CLOCK_MONOTONIC_RAW` stop only for the interval
  between `timekeeping_suspend()` and `timekeeping_resume()`; the rest of the
  suspend sequence is counted.
- Suspend-to-idle: `timekeeping_suspend()` runs only from `tick_freeze()` in
  `kernel/time/tick-common.c`, when the last online CPU enters a cpuidle
  state that has `enter_s2idle`.
- Suspend-to-idle without such a state: `cpuidle_enter_s2idle()` in
  `drivers/cpuidle/cpuidle.c` never reaches `tick_freeze()`, so timekeeping
  is not suspended and no clock is stopped by the timekeeping code.
- `CLOCK_REALTIME`, `CLOCK_BOOTTIME` and `CLOCK_TAI` do not run during
  suspend; `__timekeeping_inject_sleeptime()` steps them forward by the sleep
  time on resume, and only when a source for that time exists.
- Sources of sleep time, in order of preference:
  - a clocksource with `CLOCK_SOURCE_SUSPEND_NONSTOP`, through
    `clocksource_stop_suspend_timing()` in `timekeeping_resume()`
  - `read_persistent_clock64()`, in `timekeeping_resume()`; the `__weak`
    default returns zero, which injects nothing
  - the RTC, through `rtc_resume()` in `drivers/rtc/class.c`, which calls
    `timekeeping_inject_sleeptime64()`
- `timekeeping_inject_sleeptime64()` and `rtc_resume()` exist only under
  `CONFIG_PM_SLEEP` with `CONFIG_RTC_HCTOSYS_DEVICE`, and `rtc_resume()` acts
  only for the device named by `CONFIG_RTC_HCTOSYS_DEVICE`.
- With none of the three sources, all five clocks resume from the value they
  had at `timekeeping_suspend()`; `CLOCK_BOOTTIME` then equals
  `CLOCK_MONOTONIC` plus the old `offs_boot`.
- RTC source: the step happens in device resume, after
  `timekeeping_resume()`; a read of `CLOCK_BOOTTIME`, `CLOCK_REALTIME` or
  `CLOCK_TAI` before `rtc_resume()` does not yet include the sleep time.
- `__timekeeping_inject_sleeptime()` rejects a delta that fails
  `timespec64_valid_strict()` with a printed warning and injects nothing.
- `CLOCK_REALTIME` also steps on a leap second, in
  `accumulate_nsecs_to_secs()`; the same code changes `tai_offset` by the
  opposite amount, so `CLOCK_TAI` does not step.
- `CLOCK_AUX` clocks: `aux_clock_set()` steps only that clock, by changing
  its `offs_aux`; `do_settimeofday64()` and `timekeeping_inject_offset()`
  change `tk_core` only, so an aux clock does not jump when the wall clock is
  set.
- `CLOCK_AUX` across suspend: `timekeeping_suspend()` and
  `timekeeping_resume()` update `tk_core` only; they inject no sleep time
  into an aux timekeeper and do not rebase its `cycle_last`.
- `ktime_get_aux()` has `WARN_ON(timekeeping_suspended)`, and
  `__timekeeping_advance()` returns early for an aux timekeeper while
  `timekeeping_suspended` is set.
