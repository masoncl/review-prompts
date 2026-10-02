- Softirq context: allowed; `__timer_delete_sync()` warns only for
  `in_hardirq()` on a timer without `TIMER_IRQSAFE`, with `WARN_ON()`.
- Lockdep map: `__timer_delete_sync()` acquires and releases
  `timer->lockdep_map` under `CONFIG_LOCKDEP` for every timer, `TIMER_IRQSAFE`
  included.
- Sleepable-context check: `lockdep_assert_preemption_enabled()`, made only
  with `CONFIG_PREEMPT_RT` and without `TIMER_IRQSAFE`; it is empty without
  `CONFIG_PROVE_LOCKING`. `__timer_delete_sync()` has no unconditional
  `might_sleep()`; the only other sleep check is in `rt_spin_lock()`, reached
  through `del_timer_wait_running()` on `CONFIG_PREEMPT_RT` while the callback
  runs.
- `TIMER_IRQSAFE` timer on `CONFIG_PREEMPT_RT`: `del_timer_wait_running()` does
  not block on `base->expiry_lock`; the caller spins.
- **Unsafe usage**: calling `timer_delete_sync()` or `timer_shutdown_sync()` on
  a timer without `TIMER_IRQSAFE` while holding a lock that a hardirq handler
  takes, even one the callback never touches.
  - Unsafe: the callback runs with interrupts enabled; a hardirq on its CPU
    that spins on the held lock keeps `base->running_timer` set, and the loop in
    `__timer_delete_sync()` never ends.
  - Safe: `timer_delete()` or `timer_shutdown()` under the lock; neither waits
    for `base->running_timer`.
  - Safe: drop the lock before the sync call, as `ioc_rqos_exit()` in
    `block/blk-iocost.c` does.
- **Potentially unsafe usage**: a callback that re-arms its own timer with
  `add_timer_on()`.
  - Unsafe: when the timer is ever deleted with `timer_delete_sync()` or
    `timer_shutdown_sync()`; `add_timer_on()` does not test
    `base->running_timer` before it moves the timer to a different
    `struct timer_base`, so the sync call can return while the callback still
    runs. Nothing detects this.
  - Safe: when the timer is never deleted, as with `tsc_sync_check_timer_fn()`
    in `arch/x86/kernel/tsc_sync.c`.
  - Safe: re-arm with `mod_timer()`; `__mod_timer()` leaves a timer on its base
    while `base->running_timer` points at it.
