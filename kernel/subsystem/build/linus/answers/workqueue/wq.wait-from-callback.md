- `touch_work_lockdep_map()` and `touch_wq_lockdep_map()`: acquire and at
  once release `work->lockdep_map` and `wq->lockdep_map`, so that lockdep
  records "the waiter depends on this item or workqueue"; they are not
  tied to `WQ_MEM_RECLAIM`.
- Acquire type: `process_one_work()` and both helpers use
  `lock_map_acquire()`, which is exclusive, not `lock_map_acquire_read()`.
- `touch_work_lockdep_map()`: called from `start_flush_work()` only after
  `insert_wq_barrier()`; `flush_work()` or `cancel_work_sync()` that finds
  the item idle records nothing.
- Lock held across `flush_work()` or `cancel_work_sync()`: lockdep reports
  the inversion only on a run where the item was pending or running at the
  `flush_work()` call, or running at the `cancel_work_sync()` call.
- `touch_wq_lockdep_map()` in `__flush_workqueue()`: unconditional after the
  `wq_online` test, so `drain_workqueue()` and `destroy_workqueue()` record
  the dependency even when the workqueue is empty.
- `touch_wq_lockdep_map()` in `start_flush_work()`: only when
  `!from_cancel && (wq->saved_max_active == 1 || wq->rescuer)`.
- `wq->rescuer`: set for every `WQ_MEM_RECLAIM` workqueue (`init_rescuer()`),
  so `flush_work()` on a busy item of such a workqueue, from a function
  running on the same workqueue, is reported whatever `max_active` is.
- `cancel_work_sync()` and `disable_work_sync()`: never touch
  `wq->lockdep_map`.
- The wait itself is not annotated: `init_completion_map()` in
  `include/linux/completion.h` discards the map.
- `check_flush_dependency()` worker test: exempts a caller whose workqueue
  has `__WQ_LEGACY`, which for example `create_workqueue()`,
  `create_freezable_workqueue()` and `create_singlethread_workqueue()` set.
