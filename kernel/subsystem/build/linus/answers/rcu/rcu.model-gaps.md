- Models take `call_rcu_tasks_rude()` and rcu_barrier_tasks_rude() to be
  callable, because `Documentation/RCU/whatisRCU.rst` lists both. The first is
  `static` in `kernel/rcu/tasks.h` and the second is defined nowhere.
- Models take `CONFIG_PREEMPT_RCU` to follow `CONFIG_PREEMPTION`, and Tiny RCU
  to mean a non-preemptible kernel. rcutorture builds both counter-examples
  with `CONFIG_PREEMPT_LAZY=y` and `CONFIG_PREEMPT_DYNAMIC=n`: `TREE04` checks
  `CONFIG_PREEMPT_RCU=n` and `TINY01` checks `CONFIG_TINY_RCU=y`, both in
  `tools/testing/selftests/rcutorture/configs/rcu/`.
- Models take Tasks Trace RCU to have its own `struct rcu_tasks` instance and
  kthread. `synchronize_rcu_tasks_trace()` is `synchronize_srcu()`, so under
  `CONFIG_TREE_SRCU` and `CONFIG_PROVE_RCU` it gets the `RCU_LOCKDEP_WARN()` of
  `__synchronize_srcu()`, which fires when `rcu_lock_map`, `rcu_bh_lock_map` or
  `rcu_sched_lock_map` is held.
- Models take Tasks Trace readers to be safe wherever RCU is not watching. The
  help text of `CONFIG_TASKS_TRACE_RCU_NO_MB` in `kernel/rcu/Kconfig` makes the
  builder promise that no tracing operation is attached to code that runs
  where `rcu_is_watching()` returns false.
- Models take `list_for_each_entry_rcu()` and `hlist_for_each_entry_rcu()` to
  warn under `CONFIG_PROVE_RCU` when used outside a reader. `__list_check_rcu()`
  in `include/linux/rculist.h` checks only under `CONFIG_PROVE_RCU_LIST`, which
  depends on `RCU_EXPERT`; otherwise the optional condition argument is not
  evaluated.
- Models take `rcu_segcblist_advance()` to take a grace-period number. It takes
  only the list and tests each segment's `struct rcu_gp_seq` with
  `poll_state_synchronize_rcu_full()`; `srcu_segcblist_advance()` is the form
  with a sequence argument.
- Models take `srcu_funnel_gp_start()` to queue the grace-period work itself.
  When it starts a grace period and `srcu_init_done` is set, it calls
  `irq_work_queue()` under the `struct srcu_usage` lock, and `srcu_irq_work()`
  calls `queue_delayed_work()`.
- Models take `WARN_ON_ONCE(!rcu_read_lock_held())`, or `lock_is_held()` on the
  map, as the way to assert a reader. `lockdep_assert_in_rcu_read_lock()`,
  `lockdep_assert_in_rcu_read_lock_bh()`,
  `lockdep_assert_in_rcu_read_lock_sched()` and
  `lockdep_assert_in_rcu_reader()` go through `lockdep_assert_rcu_helper()`, so
  under `CONFIG_PROVE_RCU` they also fire when `rcu_is_watching()` or
  `rcu_lockdep_current_cpu_online()` is false.
- Models take the reader primitives to carry sparse `__acquire()` annotations.
  They carry `__acquires_shared(RCU)` and related attributes from
  `include/linux/compiler-context-analysis.h`, which are empty under sparse and
  active only with `CONFIG_WARN_CONTEXT_ANALYSIS` (`lib/Kconfig.debug`), and
  only for objects whose Makefile sets `CONTEXT_ANALYSIS := y` or the
  per-object form, as `CONTEXT_ANALYSIS_kcov.o := y` in `kernel/Makefile`,
  unless `CONFIG_WARN_CONTEXT_ANALYSIS_ALL` is set.
