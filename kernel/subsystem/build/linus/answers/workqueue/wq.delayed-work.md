- Arming the timer: `__queue_delayed_work()` does not test `__WQ_DRAINING` or
  `__WQ_DESTROYING`; the test is made in `__queue_work()` when the timer
  fires.
- Timer firing during a drain or destroy: never counts as chained, even when
  a work function of that workqueue armed it, because `is_chained_work()`
  needs task context.
- Result of that firing: `WARN_ONCE()`, the item is dropped, and
  `WORK_STRUCT_PENDING_BIT` is cleared, so `delayed_work_pending()` turns
  false without the function having run.
- Timer firing after the workqueue has been freed: `delayed_work_timer_fn()`
  passes the stale `dwork->wq` to `__queue_work()`, which reads `wq->flags`
  with no other check.
- Zero delay: `__queue_delayed_work()` returns before it stores `dwork->wq`
  and `dwork->cpu`; they keep the values of the last nonzero-delay arming, if
  any.
- `flush_delayed_work()`: uses `timer_delete_sync()`; there is no
  del_timer_sync() here.
