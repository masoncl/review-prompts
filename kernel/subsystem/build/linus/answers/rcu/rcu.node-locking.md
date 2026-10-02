- Release wrappers: `raw_spin_unlock_rcu_node()`,
  `raw_spin_unlock_irq_rcu_node()` and
  `raw_spin_unlock_irqrestore_rcu_node()` in `kernel/rcu/rcu.h` each call
  `lockdep_assert_irqs_disabled()` before unlocking; the acquire wrappers
  contain no assertion.
- `smp_mb__after_unlock_lock()`: `smp_mb()` only under
  `CONFIG_ARCH_WEAK_RELEASE_ACQUIRE`, empty otherwise
  (`include/linux/rcupdate.h`).
- `CONFIG_ARCH_WEAK_RELEASE_ACQUIRE`: selected only in `arch/powerpc/Kconfig`
  and, if `ARCH_USE_QUEUED_SPINLOCKS`, in `arch/riscv/Kconfig`, so on other
  architectures a plain `raw_spin_lock()` on the field behaves the same as
  the wrapper and testing there cannot show a missing barrier.
- The wrappers are macros over any structure with a `__private` field named
  `lock`: `struct rcu_tasks_percpu` in `kernel/rcu/tasks.h` and
  `struct srcu_data`, `struct srcu_node`, `struct srcu_usage` in
  `include/linux/srcutree.h` use them too.
- SRCU: those locks are `raw_spinlock_t`; there is no non-raw
  spin_lock_irqsave_rcu_node() family in this tree.
- Lock order, outermost first: `rcu_state.ofl_lock`,
  `rcu_state.barrier_lock`, `rdp->nocb_lock`, then either
  `rdp->nocb_bypass_lock` or the leaf `->lock`, then one ancestor's `->lock`.
  See `rcutree_report_cpu_starting()` and `rcutree_migrate_callbacks()` in
  `kernel/rcu/tree.c`.
- `rdp->nocb_lock` before `->lock`: blocking in `nocb_gp_wait()`, trylock in
  `nocb_cb_wait()` and `rcu_advance_cbs_nowake()`.
- With `->lock` held and an offloaded `rdp`: `__note_gp_changes()` skips
  `rcu_advance_cbs()` and `rcu_accelerate_cbs()`, and `rcu_report_qs_rdp()`
  skips `rcu_accelerate_cbs()`; both callees assert `nocb_lock` through
  `rcu_lockdep_assert_cblist_protected()`.
- `rdp->nocb_gp_lock`: taken after `nocb_lock` is dropped
  (`__call_rcu_nocb_wake()`), and `__wake_nocb_gp()` drops it before
  `swake_up_one()`.
- **Unsafe usage**: a wakeup, `resched_cpu()` or `task_call_func()` while a
  `struct rcu_node` `->lock` is held.
  - Unsafe: these take `pi_lock` or the rq lock, while
    `__call_rcu_common()` takes the leaf `->lock` in `check_cb_ovld()`
    whatever locks its caller holds.
  - Safe: record the need under the lock and act after the release, as
    `force_qs_rnp()` does with `rsmask`, `rcu_print_task_stall()` with its
    `ts[]` array, `rcu_gp_cleanup()` with `sq`, and the callers of
    `rcu_start_this_gp()` with its return value.
- `rcu_read_unlock_special()` in `kernel/rcu/tree_plugin.h`, entered with
  irqs, preemption or bh disabled: returns without taking any `->lock`; the
  report is made later through `rcu_preempt_deferred_qs_irqrestore()`.
- `rcutorture_one_extend()` in `kernel/rcu/rcutorture.c`: sometimes holds
  `current->pi_lock` across the reader unlock, unless `cur_ops->no_pi_lock`
  is set, so rcutorture can catch a patch that makes the unlock path wake a
  task.
- `call_rcu()` from an irqs-disabled caller on an offloaded CPU:
  `__call_rcu_nocb_wake()` uses `wake_nocb_gp_defer()` (timer) instead of
  `wake_nocb_gp()`.
