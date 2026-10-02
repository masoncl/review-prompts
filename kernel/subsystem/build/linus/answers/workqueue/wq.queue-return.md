- Drop on a draining or destroying workqueue: `__queue_work()` clears
  `WORK_STRUCT_PENDING_BIT` before it returns, keeping the pool id, disable
  count and off-queue flags.
- Caller after such a drop: sees `true`; the item is idle, not stuck pending.
- Later `queue_work()` on the dropped item: takes the bit again and returns
  `true`; it is dropped again while the flag is set and queued normally once
  `drain_workqueue()` has cleared `__WQ_DRAINING`.
- Warning for the drop: `WARN_ONCE()`, so only the first drop is reported;
  later drops are silent.
- `__WQ_DESTROYING`: tested together with `__WQ_DRAINING`; chained work is
  accepted under either flag.
- `is_chained_work()`: true only when `current_wq_worker()` (in
  `kernel/workqueue_internal.h`) returns a worker, which needs `in_task()` and
  `PF_WQ_WORKER`; queueing from a timer, softirq or hard IRQ is never chained.
- During `cancel_work_sync()` or `cancel_delayed_work_sync()`: `queue_work()`
  returns `false` and the request is dropped, because the disable count is
  raised for the whole wait.
- `work->entry` not empty on entry to `__queue_work()`: `WARN_ON()`, nothing
  is queued, the caller sees `true` and the pending bit stays set.
