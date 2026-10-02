- Overlap across pools: prevented. `__queue_work()` queues the item on the
  pwq of the worker that is running it in its last pool, not on the pool of
  the chosen CPU.
- Condition for that redirect: the running worker's `current_pwq->wq` is the
  workqueue being queued to, and `current_func` equals `work->func`
  (`find_worker_executing_work()`).
- Condition not met (item queued through another workqueue, or `work->func`
  changed): the item goes to the pool of the chosen CPU, and the second run
  can overlap the first unless both land in the same pool with `work->func`
  unchanged.
- `__WQ_ORDERED` workqueue: `__queue_work()` skips the redirect and queues on
  the pwq of the chosen CPU; it relies on ordering for non-reentrancy, and a
  `plugged` pwq activates nothing until `unplug_oldest_pwq()`.
- Same-pool collision: handled in `assign_work()`, not in
  `process_one_work()`; it moves the item to `collision->scheduled` with
  `move_linked_works()`. There is no move_linear_work here.
- `false` from `queue_work()`: guarantees a later start only when the bit was
  held by an instance that is being queued, queued or timer-armed and that is
  then left alone.
- `false` with no later run: the item is disabled; a canceller, disabler or
  `enable_work()` held the bit at that moment; the pending instance is
  cancelled afterwards; or `__queue_work()` drops the pending instance on a
  draining or destroying workqueue, for example when its timer fires there.
