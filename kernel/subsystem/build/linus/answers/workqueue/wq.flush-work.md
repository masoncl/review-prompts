- Never-initialised item: `__flush_work()` does `WARN_ON(!work->func)` and
  returns false; this catches only a NULL `func`, as in zero-filled memory.
- `cancel_work_sync()` and `disable_work_sync()` on a zero-filled item: hit
  the same `WARN_ON(!work->func)`, through `__cancel_work_sync()`, once
  `wq_online` is set.
