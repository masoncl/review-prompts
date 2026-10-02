- `CONFIG_PREEMPT_RCU`: has no prompt and no `depends on`; it is
  `default y if (PREEMPT || PREEMPT_RT || PREEMPT_DYNAMIC)` and
  `select TREE_RCU`. It does not follow `CONFIG_PREEMPTION`.
- `CONFIG_PREEMPT_LAZY` without `CONFIG_PREEMPT_DYNAMIC` and
  `CONFIG_PREEMPT_RT`: gives `CONFIG_PREEMPTION=y`, `CONFIG_PREEMPT_COUNT=y`
  and `CONFIG_PREEMPT_RCU=n`. The kernel is preemptible, readers are not.
- The same configuration on `!SMP`: gives `CONFIG_TINY_RCU` and
  `CONFIG_TINY_SRCU` with `CONFIG_PREEMPTION=y`; `__srcu_read_lock()` in
  `include/linux/srcutiny.h` disables preemption around its counter update
  for that case.
- `kernel/Kconfig.preempt`: `PREEMPT_NONE` depends on `ARCH_NO_PREEMPT` and
  `PREEMPT_VOLUNTARY` on `!ARCH_HAS_PREEMPT_LAZY`. On an architecture that
  selects `ARCH_HAS_PREEMPT_LAZY`, the lazy build above is the only one with
  `CONFIG_PREEMPT_RCU=n`.
- `rcu_read_lock_dont_migrate()` and `rcu_read_unlock_migrate()` in
  `include/linux/rcupdate.h`: add `migrate_disable()` and `migrate_enable()`
  only under `CONFIG_PREEMPT_RCU`; use them where a reader must stay on one
  CPU in every build.
- Tiny `synchronize_rcu()` in `kernel/rcu/tiny.c`: does not call
  `might_sleep()`; its only check is the `RCU_LOCKDEP_WARN()` on the three
  RCU lockdep maps, so a call from any other atomic context is not reported.
- Tiny SRCU (`include/linux/srcutiny.h`): `srcu_check_read_flavor()` is
  empty, the fast readers are `__srcu_read_lock()`, and
  `synchronize_srcu_expedited()` and `srcu_barrier()` are
  `synchronize_srcu()`.
- `CONFIG_NEED_SRCU_NMI_SAFE`: is
  `HAVE_NMI && !ARCH_HAS_NMI_SAFE_THIS_CPU_OPS && !TINY_SRCU`. When unset,
  `__srcu_read_lock_nmisafe()` is `__srcu_read_lock()`; on Tree SRCU that is
  the default build for architectures that select
  `ARCH_HAS_NMI_SAFE_THIS_CPU_OPS`, where only
  `CONFIG_FORCE_NEED_SRCU_NMI_SAFE` sets it.
