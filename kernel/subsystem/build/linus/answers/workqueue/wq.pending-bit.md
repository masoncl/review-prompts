- `try_to_grab_pending()`: returns only 1, 0 or `-EAGAIN`; there is no
  -ENOENT return and no WORK_OFFQ_CANCELING flag in this tree.
- Timer steal: done with `timer_delete()`; there is no del_timer() timer
  function here.
- `set_work_pool_and_clear_pending()`: `smp_wmb()` before the store, the full
  `smp_mb()` after it.
- PENDING set, `WORK_STRUCT_PWQ` clear, no timer to steal: tells
  `try_to_grab_pending()` that an owner is in transit; it returns `-EAGAIN`
  and `work_grab_pending()` spins.
- Owner in transit, other than `queue_rcu_work()`: keeps IRQs off from taking
  the bit until it queues, arms the timer or clears; `__queue_work()` has
  `lockdep_assert_irqs_disabled()`.
- Grab without `WORK_CANCEL_DELAYED` on a timer-armed item: sees the same
  transit state, so it gets `-EAGAIN` until the timer fires.
- Pool id and `WORK_OFFQ_BH` survive cancel, disable and enable:
  `__cancel_work()` and `enable_work()` write back what `work_offqd_unpack()`
  read and change only the disable count.
