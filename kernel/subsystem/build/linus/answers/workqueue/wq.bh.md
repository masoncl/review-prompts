- `max_active`: must be 0; any other value gives `WARN_ON_ONCE()` and NULL.
- CPU an item runs on: the CPU of the BH pool it was queued to;
  `queue_work_on()` with another CPU makes `kick_bh_pool()` raise the softirq
  there through `irq_work_queue_on()`.
- Dead CPU: `workqueue_softirq_dead()` runs the dead pool's `bh_worker()`
  from a BH item on the current CPU, in `drain_dead_softirq_workfn()`.
- `cancel_work_sync()` and `disable_work_sync()`: not from hardirq;
  `__cancel_work_sync()` does `WARN_ON_ONCE(in_hardirq())` for a BH item.
- Which branch `__cancel_work_sync()` takes: decided by `WORK_OFFQ_BH` in the
  item's data, set when the item leaves a BH pool in `process_one_work()` or
  `try_to_grab_pending()`.
- **Potentially unsafe usage**: `cancel_work_sync()` or `disable_work_sync()`
  from atomic context on an item meant for a BH workqueue.
  - Unsafe: the item has never been queued, or was last queued on a non-BH
    workqueue; `WORK_OFFQ_BH` is clear and `__cancel_work_sync()` calls
    `might_sleep()`.
  - Safe: the item was last queued on a BH workqueue and the caller is not in
    hardirq; without `CONFIG_PREEMPT_RT`, `__flush_work()` busy-waits with
    `cpu_relax()` instead of sleeping.
- `CONFIG_PREEMPT_RT`: the wait in `__flush_work()` calls
  `workqueue_callback_cancel_wait_running()`, which takes and drops
  `pool->cb_lock`; `bh_worker()` holds that lock while it runs items.
