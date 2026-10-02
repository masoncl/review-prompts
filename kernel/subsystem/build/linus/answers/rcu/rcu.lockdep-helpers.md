- `rcu_read_lock_sched_held()` and `rcu_read_lock_any_held()` without
  `CONFIG_DEBUG_LOCK_ALLOC`: return `!preemptible()`, not 1. `preemptible()`
  is constant 0 without `CONFIG_PREEMPT_COUNT`, so there they return 1.
- `rcu_read_lock_bh_held()` with lockdep working: returns
  `in_softirq() || irqs_disabled()` and never looks at `rcu_bh_lock_map`; it
  is true in any BH-disabled or irq-disabled region.
- `srcu_read_lock_held()`: tests `debug_lockdep_rcu_enabled()`, then
  `lock_is_held(&ssp->dep_map)`. It has no watching test and no online test.
- `rcu_read_lock_trace_held()`: is
  `srcu_read_lock_held(&rcu_tasks_trace_srcu_struct)` under
  `CONFIG_DEBUG_LOCK_ALLOC` and `CONFIG_TASKS_TRACE_RCU`, otherwise 1.
- `rcu_read_lock_held_common()` in `kernel/rcu/update.c`: tests
  `debug_lockdep_rcu_enabled()` first, so with lockdep switched off the four
  RCU predicates return 1 even where RCU is not watching.
- `debug_lockdep_rcu_enabled()`: also requires
  `current->lockdep_recursion == 0`, so the predicates return 1 when called
  from inside lockdep.
- Offline CPU: the four RCU predicates return 0 only where
  `rcu_lockdep_current_cpu_online()` is real, that is under
  `CONFIG_PROVE_RCU` and `CONFIG_HOTPLUG_CPU`, and not `in_nmi()`.
- `lockdep_assert_in_rcu_read_lock()`,
  `lockdep_assert_in_rcu_read_lock_bh()` and
  `lockdep_assert_in_rcu_read_lock_sched()` in `include/linux/rcupdate.h`:
  test the lockdep map itself, so `local_bh_disable()` or
  `preempt_disable()` alone does not satisfy the bh and sched forms. They
  generate no check without `CONFIG_PROVE_RCU`.
- `lock_is_held()`: without `CONFIG_LOCKDEP` it is declared and not defined,
  so it only builds where the compiler drops the call, as inside
  `RCU_LOCKDEP_WARN()`. With lockdep built and disabled it returns
  `LOCK_STATE_UNKNOWN`, which is nonzero.
- **Potentially unsafe usage**: letting the result of a predicate choose a
  code path, a GFP mask or whether to take a lock.
  - Unsafe: when the path taken on a nonzero result is correct only inside a
    reader. It runs outside any reader when `CONFIG_DEBUG_LOCK_ALLOC` is off
    or `debug_lockdep_rcu_enabled()` is false, because the stubs in
    `include/linux/rcupdate.h` and `rcu_read_lock_held_common()` return 1
    there.
  - Safe: when the path taken on a nonzero result is correct in any context.
    `rxrpc_alloc_ack()` in `net/rxrpc/output.c` picks `GFP_ATOMIC` on a
    nonzero result, so a wrong 1 only gives up the sleeping allocation.
  - Safe: warn only on a zero result, as `percpu_ref_tryget_live_rcu()` does
    with `WARN_ON_ONCE(!rcu_read_lock_held())`; a wrong 1 only loses the
    warning.
  - Safe: pass the predicate as the condition of `rcu_dereference_check()`,
    which puts it inside `RCU_LOCKDEP_WARN()`, as `task_storage_lookup()` in
    `kernel/bpf/bpf_task_storage.c` does.
  - Safe: `rcu_preempt_depth()` for a real nesting count, under
    `CONFIG_PREEMPT_RCU` only, as `rcu_preempt_need_deferred_qs()` in
    `kernel/rcu/tree_plugin.h` does; it is constant 0 in the other builds.
- **Unsafe usage**: asserting that no reader is active by warning on a
  nonzero result, as in `WARN_ON(rcu_read_lock_held())`.
  - Unsafe: the warning fires on every call without
    `CONFIG_DEBUG_LOCK_ALLOC`, where `rcu_read_lock_held()` is constant 1.
  - Safe: `RCU_LOCKDEP_WARN(lock_is_held(&rcu_lock_map), ...)`, as
    `synchronize_rcu()` does; `RCU_LOCKDEP_WARN()` tests
    `debug_lockdep_rcu_enabled()` before and after the condition.
