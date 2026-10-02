- `this_cpu_*()` and `__this_cpu_*()` on data the lock covers: valid inside
  the section on RT; `check_preemption_disabled()` in
  `lib/smp_processor_id.c` accepts `current->migration_disabled`.
- Acquire form: `local_lock()`, `local_lock_irq()` and `local_lock_irqsave()`
  are the same operation on RT, so choose by what non-RT needs; a wrong
  choice shows only on non-RT.
- Initialisation: non-RT `local_lock_t` is an empty struct without
  `CONFIG_DEBUG_LOCK_ALLOC`, so a missing `local_lock_init()` shows only on
  RT or with lockdep.
- **Unsafe usage**: `local_lock_irq()` or `local_lock_irqsave()` followed by
  `raw_spin_lock()` as a stand-in for `raw_spin_lock_irq()`; the nesting is
  allowed by lock type, but on RT `__local_lock_irq()` is `__local_lock()`,
  which disables neither interrupts nor preemption
  (`Documentation/locking/locktypes.rst`, "local_lock on RT").
  - Safe: follow the local lock with a `spinlock_t`, as `kcov_remote_start()`
    in `kernel/kcov.c` does with `kcov_remote_lock`; on RT `spin_lock()` is
    `rt_spin_lock()` and needs no interrupt disabling.
  - Safe: use `raw_spin_lock_irq()` directly where interrupts must be off.
