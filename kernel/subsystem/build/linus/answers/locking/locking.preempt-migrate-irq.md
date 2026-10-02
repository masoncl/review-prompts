- `preempt_disable()` on PREEMPT_RT: also keeps softirq handlers off this
  CPU, because RT runs them only in task context (`invoke_softirq()` only
  wakes `ksoftirqd`).
- `local_bh_disable()` on PREEMPT_RT, sleeping: the region holds
  `rcu_read_lock()`, so `might_sleep()` complains; only blocking on a
  `spinlock_t`, `rwlock_t` or `local_lock_t` is accepted
  (`rtlock_might_resched()` in `kernel/locking/spinlock_rt.c`).
- `local_interrupt_disable()` in `include/linux/interrupt_rc.h`: a fifth
  primitive; guarantees as `local_irq_disable()` on both kernels, and it
  nests: interrupts return to the state saved by the first call only at the
  matching last `local_interrupt_enable()`.
- `local_interrupt_disable()`: warns when called in NMI; raises
  `preempt_count()`, so the region is also non-preemptible by count.
- `spinlock_t` inside `preempt_disable()` or `local_irq_disable()`: lockdep
  does not report it on a normal kernel; `check_wait_context()` sees held
  locks and hardirq or softirq context only.
- `CONFIG_PROVE_RAW_LOCK_NESTING`: reports a `spinlock_t` taken under a
  `raw_spinlock_t` or in a non-threaded hard interrupt handler; it never
  checks a trylock.
