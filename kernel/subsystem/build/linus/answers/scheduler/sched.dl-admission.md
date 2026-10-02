- `__checkparam_dl()` does not check flags beyond the `SCHED_FLAG_SUGOV`
  short-cut; `__sched_setscheduler()` tests the flag mask, and rejects
  `SCHED_FLAG_SUGOV` from user callers with `-EINVAL`.
- Period range: `__checkparam_dl()` rejects an effective period (the deadline
  when `sched_period` is 0) outside `sysctl_sched_dl_period_min` and
  `sysctl_sched_dl_period_max`; defaults 100 us and `1 << 22` us.
- Only `sched_runtime` is compared with `1 << DL_SCALE`; `sched_deadline` is
  tested for zero, for bit 63, and against the runtime and the effective
  period.
- Capacity in `sched_dl_overflow()`: `dl_bw_capacity()` only, scaled by
  `dl_b->bw` in `__dl_overflow()`. The `cpus` count that
  `sched_dl_overflow()` reads with `dl_bw_cpus()` is not passed to the test;
  it spreads the change over `extra_bw` in `__dl_add()` and `__dl_sub()`.
- Limit at the default sysctls: the full capacity of the active CPUs of the
  root domain, which is what `dl_bw_capacity()` returns.
- `cpuset_lock()`: `__sched_setscheduler()` takes it before `task_rq_lock()`
  when the old or the new policy is deadline, so with `CONFIG_CPUSETS` the
  root domain is stable for the test; without it `cpuset_lock()` is an empty
  inline.
- `dl_b->lock` in `sched_dl_overflow()` is taken with plain
  `raw_spin_lock()`; interrupts are already off under `task_rq_lock()`.
- `sched_dl_overflow()` returns -1 on overflow, not an errno;
  `__sched_setscheduler()` turns any non-zero result into `-EBUSY`.
