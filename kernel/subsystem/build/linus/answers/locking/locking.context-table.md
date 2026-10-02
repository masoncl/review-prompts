- `spin_lock_bh()` on PREEMPT_RT: excludes softirq handlers on this CPU only
  with `CONFIG_PREEMPT_RT_NEEDS_BH_LOCK` (off unless selected by hand).
- `spin_lock_bh()` on PREEMPT_RT without that option: a softirq handler can
  run in another task on this CPU while the lock is held; it is kept out of
  the data only by taking the same lock.
- `local_lock_nested_bh()`: the `local_lock_t` form for per-CPU data touched
  in BH-disabled code; lockdep-only on a normal kernel, a per-CPU
  `spin_lock()` on PREEMPT_RT.
- A fifth form exists beside plain, bh, irq and irqsave:

| Acquire | Release | Normal kernel | PREEMPT_RT |
|---|---|---|---|
| `raw_spin_lock_irq_disable()` | `raw_spin_unlock_irq_enable()` | as irqsave, no `flags` argument | same |
| `spin_lock_irq_disable()` | `spin_unlock_irq_enable()` | as irqsave, no `flags` argument | same as `spin_lock()`; interrupts stay on, can sleep |
| `spin_trylock_irq_disable()` | `spin_unlock_irq_enable()` | the interrupt disable is kept only on success | same as `spin_trylock()` |

- The irq_disable forms nest: see "Nesting under irq-disabling locks".
- `rwlock_t` and `local_lock_t` have no irq_disable form.
- In-tree callers of the irq_disable forms: only `rust/helpers/spinlock.c`;
  `kernel/irq/refcount_interrupt_test.c` exercises
  `local_interrupt_disable()`.
