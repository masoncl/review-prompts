- `rq_order_less()` in `kernel/sched/sched.h`: compares `rq->core->cpu`
  first and `rq->cpu` second. It never compares lock pointers.
- `rq_order_less()` core-first order: selected by `CONFIG_SCHED_CORE` at build
  time. It applies whether or not core scheduling is enabled at run time,
  because `sched_core_cpu_starting()` sets `rq->core` without testing whether
  core scheduling is enabled.
- `p->pi_lock` under a runqueue lock: no trylock escape exists. The only
  trylock in `_double_lock_balance()` is `raw_spin_rq_trylock(busiest)`, and
  only without `CONFIG_PREEMPTION`.
- `_double_lock_balance()` with `CONFIG_PREEMPTION`: always unlocks `this_rq`,
  calls `double_rq_lock()` and returns 1.
- `_double_lock_balance()` without `CONFIG_PREEMPTION`: returns 0 without
  dropping `this_rq` when both share a lock, when the trylock succeeds, or
  when `rq_order_less(this_rq, busiest)`. Otherwise it drops and returns 1.
- `kernel/sched/cpupri.c`: takes no lock. Nothing from cpupri nests inside a
  runqueue lock.
- Timer base lock of `struct hrtimer_cpu_base`: nests inside the runqueue lock
  and inside `cfs_b->lock`; `start_cfs_bandwidth()` asserts `cfs_b->lock` and
  starts the period timer.
- `CONFIG_SCHED_PROXY_EXEC`: `find_proxy_task()` takes `mutex->wait_lock` and
  then `p->blocked_lock` while it holds the runqueue lock.
  `proxy_needs_return()` takes `p->blocked_lock` under the runqueue lock.
- Other locks seen taken under a runqueue lock, for example: `dl_b->lock` in
  `dl_task_offline_migration()`, `rd->rto_lock` in `tell_cpu_to_push()`,
  `cp->lock` in `cpudl_set()`, `cfs_b->lock` in `throttle_cfs_rq()`. Search
  `kernel/sched/` for `raw_spin_lock` to list the rest.
