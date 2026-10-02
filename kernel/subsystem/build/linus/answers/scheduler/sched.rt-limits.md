- `sysctl_sched_rt_runtime` default: 1000000 us, equal to
  `sysctl_sched_rt_period`; see `kernel/sched/rt.c`.
  `Documentation/scheduler/sched-rt-group.rst` still says 950000.
- `dl_b->bw` at the defaults: `to_ratio()` gives `BW_UNIT`, so `init_dl_bw()`
  sets the deadline admission limit to 100% of each CPU, not 95%.
- `sched_rt_runtime_exceeded()` at the defaults: returns 0 for the root
  `struct rt_rq`, because its runtime is not below its period; it is the only
  place that sets `rt_throttled` to 1, so with `CONFIG_RT_GROUP_SCHED` the root
  group is not throttled at boot values.
- Write to the runtime or period sysctl: the new value reaches no
  `rt_rq->rt_runtime`. The root group's `rt_bandwidth.rt_runtime` is copied
  from the sysctl in `sched_init()` and afterwards changes only through
  `tg_set_rt_bandwidth()`.
- Write that lowers the sysctl ratio while `rt_group_sched_enabled()`:
  `sched_rt_global_validate()` fails with `-EINVAL` if any group, the root
  group included, has a larger ratio; see `tg_rt_schedulable()`.
- `rt_group_sched_enabled()` false in a `CONFIG_RT_GROUP_SCHED` kernel:
  `update_curr_rt()` still accounts and tests the root `struct rt_rq`; it
  tests `rt_bandwidth_enabled()`, not `rt_group_sched_enabled()`.
- `balance_runtime()`: returns at once unless `RT_RUNTIME_SHARE` is set, and
  `kernel/sched/features.h` defines it `false`.
- Server parameters: not derived from the rt sysctls.
  `sched_init_dl_servers()` hard-codes 50 ms / 1000 ms; only
  `sched_server_write_common()` in `kernel/sched/debug.c` changes them.
- Runtime sysctl at -1: the deadline servers keep running.
  `dl_server_start()` tests no sysctl, and `__dl_overflow()` is never true
  when `dl_b->bw` is -1.
- A server gives no protection when its `dl_runtime` is 0 or its
  `dl_bw_attached` is 0; `dl_server_start()` returns early for both.
