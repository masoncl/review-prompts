- `rcu_read_lock_bh()` on `CONFIG_PREEMPT_RT`: `__local_bh_disable_ip()`
  takes `softirq_ctrl.lock` only under `CONFIG_PREEMPT_RT_NEEDS_BH_LOCK`.
  Without that option it does `migrate_disable()` and `rcu_read_lock()`, the
  task stays preemptible, and the section is not serialized against other
  BH-disabled sections on that CPU.
- `rcu_read_lock_sched()`: is `preempt_disable()` in every build, also on
  `CONFIG_PREEMPT_RT`; `rcu_sched_lock_map` has
  `wait_type_inner = LD_WAIT_SPIN`, so under
  `CONFIG_PROVE_RAW_LOCK_NESTING` lockdep reports a `spinlock_t` taken
  inside it.
- `rcu_sleep_check()`: skips the `rcu_bh_lock_map` test when
  `CONFIG_PREEMPT_RT` is set, and keeps the `rcu_sched_lock_map` test.
