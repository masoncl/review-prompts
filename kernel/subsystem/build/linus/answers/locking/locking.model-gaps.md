- Models take `lockdep_assert_held()`, `lockdep_assert_held_write()` and
  `lockdep_assert_held_read()` to compile to nothing without lockdep. With
  or without lockdep, in a file opted into context analysis a wrong
  assertion silences the compiler from that point on. `rwsem_assert_held()`
  does the same.
- Models take a spinning lock acquisition to always succeed. `rqspinlock_t`
  in `include/asm-generic/rqspinlock.h` does not: `raw_res_spin_lock()` and
  `raw_res_spin_lock_irqsave()` return `-EDEADLK` or `-ETIMEDOUT` with
  preemption and interrupts restored, and the caller must test the result.
- Models take `CONFIG_PREEMPT_COUNT` off to be an ordinary configuration.
  In `kernel/Kconfig.preempt`, `CONFIG_PREEMPT_NONE` depends on
  `ARCH_NO_PREEMPT` and `CONFIG_PREEMPT_VOLUNTARY` on
  `!ARCH_HAS_PREEMPT_LAZY`; with the remaining choices
  `CONFIG_PREEMPT_BUILD` is set, which selects `CONFIG_PREEMPT_COUNT`
  through `CONFIG_PREEMPTION`.
- Models take the mutex unlock slow path to hold `wait_lock` only.
  `__mutex_unlock_slowpath()` also takes `blocked_lock` of
  `struct task_struct` inside `wait_lock`.
- Models know `__cond_acquires()` only. `__cond_releases()` also exists and
  is used on `__mutex_unlock_fast()`.
- Models expect a guard class for each spinlock form. No guard class wraps
  `spin_lock_irq_disable()`.
- Models cite bcachefs as the user of `lockdep_set_notrack_class()`.
  bcachefs is not in the tree.
