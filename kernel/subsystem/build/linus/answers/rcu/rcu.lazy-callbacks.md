- Names: there is no jiffies_till_flush and no rcu_nocb_all here. The limit is
  `jiffies_lazy_flush` in `kernel/rcu/tree_nocb.h`, changed only by
  `rcu_set_jiffies_lazy_flush()` for tests.
- Offloaded CPUs come from `rcu_nocbs=`, `nohz_full=` or
  `CONFIG_RCU_NOCB_CPU_DEFAULT_ALL`; see `rcu_init_nohz()`.
- Which CPU decides: the CPU that executes `call_rcu()`;
  `__call_rcu_common()` tests `rcu_rdp_is_offloaded()` on
  `this_cpu_ptr(&rcu_data)`.
- Not lazy before `rcu_scheduler_active == RCU_SCHEDULER_RUNNING`:
  `rcu_nocb_try_bypass()` does not use the bypass list until then.
- `enable_rcu_lazy`: mode 0444, so boot command line only; default is
  `!IS_ENABLED(CONFIG_RCU_LAZY_DEFAULT_OFF)`.
- With `CONFIG_RCU_LAZY_DEFAULT_OFF`: laziness is turned on by
  rcutree.enable_rcu_lazy=1; the help text in `kernel/rcu/Kconfig` says =0.
- `kfree_rcu()` is affected by laziness on two of its three paths:
  - sheaf path (`__kfree_rcu_sheaf()` in `mm/slub.c`): a full sheaf is handed
    to plain `call_rcu()`;
  - without `CONFIG_KVFREE_RCU_BATCHED`: `kvfree_call_rcu()` calls plain
    `call_rcu()`;
  - batched path: `kvfree_rcu_queue_batch()` uses `queue_rcu_work()`, which
    calls `call_rcu_hurry()`.
- `synchronize_rcu()`: its default path queues no callback, so laziness does
  not apply; only the `wait_rcu_gp(call_rcu_hurry)` fallback queues one.
- `synchronize_rcu_mult()`: passes the given functions through unchanged, so
  with `call_rcu` the wait is subject to laziness; pass `call_rcu_hurry` to
  avoid the delay.
