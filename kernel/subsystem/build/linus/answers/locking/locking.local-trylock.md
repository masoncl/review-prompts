- Non-RT marker: the field is `acquired` (`u8`) in `local_trylock_t`,
  `include/linux/local_lock_internal.h`.
- `local_lock_irq()` and `local_unlock_irq()`: accept both types; the
  `_Generic` in `__local_lock_acquire()` and `__local_lock_release()` covers
  all three lock and unlock forms.
- `local_lock_nested_bh()`: `local_lock_t` only; non-RT
  `__local_lock_nested_bh()` calls `local_lock_acquire()` directly and never
  writes `acquired`.
- Guard classes in `include/linux/local_lock.h` that take the lock: defined
  for `local_lock_t __percpu` only; `local_trylock_t` has only the
  `local_trylock_init` class.
- `local_lock_is_locked()`: non-RT reads `acquired`, so `local_trylock_t`
  only; RT tests whether `current` owns the rtmutex.
- Type checking: non-RT only; on RT both types are `typedef spinlock_t`, so
  `local_trylock()` on a `local_lock_t` compiles there.
- RT, task or softirq context: `local_trylock()` is `migrate_disable()` plus
  `spin_trylock()`, whose slow path takes the rtmutex `wait_lock`.
- RT with `pi_lock` of `struct task_struct` held: `local_trylock()` is not
  usable; `mm/slab_common.c` skips `kfree_rcu_sheaf()` on RT for this reason.
- `mm/page_alloc.c`: has no `local_trylock_t`; its nolock paths gate
  `spin_trylock_irqsave()` with `can_spin_trylock()`.
- **Potentially unsafe usage**: `local_lock()`, `local_lock_irq()` or
  `local_lock_irqsave()` on a `local_trylock_t` on non-RT.
  - Unsafe: from a context that can interrupt a holder on this CPU;
    `__local_lock_acquire()` sets `acquired` whatever its value, and only its
    `lockdep_assert()`, under `CONFIG_LOCKDEP`, tests it.
  - Safe: from task context only, as `drain_local_memcg_stock()` in
    `mm/memcontrol.c`, which returns unless `in_task()`; `__local_lock()`
    disables preemption, so no other task-context holder exists on the CPU.
  - Safe: `local_trylock()` with a fallback on failure, as `consume_stock()`
    in `mm/memcontrol.c` does.
