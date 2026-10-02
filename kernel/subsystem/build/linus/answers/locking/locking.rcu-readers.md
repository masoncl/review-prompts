- `rcu_dereference()`: accepts `rcu_read_lock()` only
  (`rcu_read_lock_held()` tests `rcu_lock_map`); preemption, BH or
  interrupts disabled, or a non-RT spinlock, give a lockdep complaint.
- `rcu_dereference_all()` in `include/linux/rcupdate.h`: accepts
  `rcu_read_lock()`, `rcu_read_lock_bh()`, `rcu_read_lock_sched()` or
  `!preemptible()`; use it where the protection differs by configuration.

| Protection | Accepted by |
|---|---|
| `preempt_disable()`, `raw_spinlock_t`, non-RT `spinlock_t` | `rcu_dereference_sched()`, `rcu_dereference_all()` |
| interrupts disabled, non-RT BH disabled | those two and `rcu_dereference_bh()` |
| PREEMPT_RT `spinlock_t`, `rwlock_t`, `local_lock_t` | `rcu_dereference()`, `rcu_dereference_all()` |
| PREEMPT_RT `local_bh_disable()` from preemptible code | `rcu_dereference()`, `rcu_dereference_bh()`, `rcu_dereference_all()` |

- PREEMPT_RT `spin_lock_irqsave()` on a `spinlock_t`: fails
  `rcu_dereference_sched()` and `rcu_dereference_bh()`, since neither
  preemption nor interrupts are off.
- Without `CONFIG_PREEMPT_COUNT`: `preemptible()` is the constant 0, so the
  `rcu_dereference_sched()` and `rcu_dereference_all()` checks do not catch
  preemptible code.
