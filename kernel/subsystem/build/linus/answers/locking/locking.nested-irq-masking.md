- `spin_lock_irq_disable()` with `spin_unlock_irq_enable()`, on a normal
  kernel: the nesting is counted in `preempt_count()`, so two locks taken
  this way may be released in either order; interrupts return to the first
  saved state at the last release.
- Counted forms, precondition: both locks must use them; an outer
  `spin_unlock_irq_enable()` with a plain inner lock still held drops the
  count to zero and restores interrupts.
- PREEMPT_RT, `spinlock_t`: the outer `spin_lock_irqsave()` sets `flags` to 0
  and masks nothing, so the inner region has interrupts enabled; only
  `raw_spinlock_t` irq forms mask.
- **Unsafe usage**: inner `spin_lock_irq()` and `spin_unlock_irq()` inside a
  region that must stay irq-off.
  - Unsafe: `__raw_spin_unlock_irq()` calls `local_irq_enable()`
    unconditionally, so interrupts come on with the outer lock held.
  - Safe: plain `spin_lock()` and `spin_unlock()` inside, as
    `cgroup_leave_frozen()` takes `siglock` under `css_set_lock`.
- **Unsafe usage**: outer released first, last unlock restores `flags` saved
  by an inner `spin_lock_irqsave()`.
  - Unsafe: those `flags` record interrupts off, so interrupts stay off after
    both locks are dropped.
  - Safe: outer plain `raw_spin_unlock()`, last unlock carries the outer
    state, as `rt_mutex_adjust_prio_chain()` does with `pi_lock` then
    `wait_lock`.
