- There is no del_timer_sync() here; `timer_delete_sync()` in
  `kernel/time/timer.c` does that.
- `timer_delete_sync()` and a handler that re-arms itself with `mod_timer()`:
  handled. On return the timer is not pending and not running; only other
  code can arm it afterwards.
- **Unsafe usage**: a timer handler that calls `add_timer_on()` on its own
  timer, when the timer is stopped with `timer_delete_sync()`.
  `add_timer_on()` changes the base of the timer without testing
  `base->running_timer`, so the wait on `base->running_timer` can miss the
  running handler.
  - Safe: re-arm from the handler with `mod_timer()`; `__mod_timer()` keeps
    the base while `base->running_timer == timer`.
- Context of `timer_delete_sync()` and `timer_shutdown_sync()`:
  `__timer_delete_sync()` warns in `in_hardirq()` unless the timer is
  `TIMER_IRQSAFE`. On `CONFIG_PREEMPT_RT` a timer that is not `TIMER_IRQSAFE`
  also needs preemption enabled.
- After `timer_shutdown_sync()`: the timer has to be initialised again before
  it can be used.
- Context of `cancel_work_sync()`, `disable_work_sync()` and the delayed
  forms: sleepable if the item was last queued on a non-BH workqueue. If it
  was last queued on a `WQ_BH` workqueue, atomic context except hardirq, with
  interrupts enabled: `start_flush_work()` uses `raw_spin_lock_irq()` and
  `raw_spin_unlock_irq()`. On `CONFIG_PREEMPT_RT` the wait in
  `__flush_work()` also takes the `spinlock_t` `cb_lock` of the pool, so
  preemption must be enabled there too. See `__cancel_work_sync()` in
  `kernel/workqueue.c`.
- `cancel_work_sync()` while it runs: the item is disabled, so a concurrent
  `queue_work()` returns false and the request is dropped. `enable_work()`
  runs before return, so later queueing succeeds.
- **Unsafe usage**: `cancel_work_sync()` on the `work` member of a
  `struct delayed_work` whose timer is pending. The timer is not deleted, and
  `work_grab_pending()` spins on `-EAGAIN` from `try_to_grab_pending()` until
  the timer has fired.
  - Safe: `cancel_delayed_work_sync()`, which passes `WORK_CANCEL_DELAYED`.
  - Safe: when the timer cannot be pending, as in
    `ip_vs_control_net_cleanup_sysctl()` in `net/netfilter/ipvs/ip_vs_ctl.c`,
    which calls it right after `cancel_delayed_work_sync()` on the same item
    and nothing queues the item again; `try_to_grab_pending()` then claims
    `WORK_STRUCT_PENDING_BIT` at once.
