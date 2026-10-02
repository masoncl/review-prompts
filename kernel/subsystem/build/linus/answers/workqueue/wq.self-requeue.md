- `cancel_work_sync()`: stops a function whose only queuer is itself; the
  item is disabled while the call waits, so the function's own requeue is
  refused, and the function has finished before the item is enabled again.
- `drain_workqueue()` and `destroy_workqueue()` on a workqueue without
  `WQ_BH`: never return while the function keeps requeueing on the same
  workqueue; `is_chained_work()` lets the requeue through and
  `drain_workqueue()` loops with no bound, printing
  "isn't complete after %u tries".
