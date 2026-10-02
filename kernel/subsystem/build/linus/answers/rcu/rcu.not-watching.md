- `rcu_is_watching()` in `kernel/rcu/tree.c`: reads only the
  `CT_RCU_WATCHING` bit of the per-CPU `struct context_tracking`; it says
  nothing about whether the CPU is online to RCU.
- `rcutree_report_cpu_dead()`: does not change the context-tracking state,
  so `rcu_is_watching()` can return true on a CPU that RCU no longer waits
  for.
- `rcu_lockdep_current_cpu_online()`: is the offline test. It is real only
  under `CONFIG_PROVE_RCU` and `CONFIG_HOTPLUG_CPU`, otherwise constant true,
  and it returns true `in_nmi()` and before `rcu_scheduler_fully_active`.
- Tiny RCU: `rcu_is_watching()` is constant true in
  `include/linux/rcutiny.h`, and `irqentry_enter_from_kernel_mode()` skips
  `ct_irq_enter()`.
- `rcu_is_watching()`: is `notrace`, not `noinstr`.
  `rcu_is_watching_curr_cpu()` in `include/linux/context_tracking.h` is the
  `__always_inline` form that context-tracking code calls.
- There is no RCU_NONIDLE() and no _rcuidle tracepoint variant in this tree.
- `rcu_read_lock_sched_notrace()`: only skips lockdep; it does not make RCU
  watch, and a preempt-disabled region where RCU is not watching is not a
  reader.
- `irqentry_enter()` from kernel mode: calls `ct_irq_enter()` only if
  `is_idle_task(current)` or `arch_in_rcu_eqs()`; otherwise it expects RCU to
  be watching already.
- `irq_enter()`: calls `ct_irq_enter()`; `irq_enter_rcu()` does not.
- `ct_irq_enter_irqson()`: has one caller, `__trace_stack()` in
  `kernel/trace/trace.c`, which reaches it only when RCU is not watching, and
  before that warns and returns under `CONFIG_GENERIC_ENTRY` and returns
  `in_nmi()`.
- `srcu_read_lock()`: has no `RCU_LOCKDEP_WARN(!rcu_is_watching(), ...)`.
  `srcu_read_lock_fast()`, `srcu_read_lock_fast_updown()` and
  `srcu_down_read_fast()` have it.
- `lock_acquire()` under `CONFIG_LOCKDEP` and `CONFIG_TRACEPOINTS`: calls
  `trace_lock_acquire()`, which has `WARN_ONCE(!rcu_is_watching(), ...)`, so
  the lockdep annotation in `srcu_read_lock()` and in `rcu_read_lock_trace()`
  still warns where RCU is not watching.
- SRCU-fast grace periods: `srcu_readers_active_idx_check()` in
  `kernel/rcu/srcutree.c` calls `synchronize_rcu()` or
  `synchronize_rcu_expedited()` where the other flavours use `smp_mb()`,
  which is why those readers need RCU watching.
- `rcu_read_lock_trace()`: at the outermost nesting level calls
  `__srcu_read_lock_fast()` on `rcu_tasks_trace_srcu_struct` followed by
  `smp_mb()`. It has no `RCU_LOCKDEP_WARN()`; the `smp_mb()` is compiled out
  under `CONFIG_TASKS_TRACE_RCU_NO_MB`.
