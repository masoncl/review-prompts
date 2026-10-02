- Running but not pending item: nothing is corrupted in the worker;
  `process_one_work()` unlinked `work->entry` before the callback and reads
  nothing from the item afterwards.
- Running but not pending item, what is lost: the last pool id, so
  `flush_work()` and `cancel_work_sync()` return without waiting for the
  running instance, and the next queueing may run concurrently with it.
- Disable count: reset to zero by `WORK_DATA_INIT()`, which silently re-enables
  an item disabled with `disable_work_sync()`.
- Debug coverage: under `CONFIG_DEBUG_OBJECTS_WORK` an item is active only
  between `insert_work()` and `process_one_work()` or
  `try_to_grab_pending()`; a running item is not reported.
- Delayed item with an armed timer: the work object is not active, so only
  `CONFIG_DEBUG_OBJECTS_TIMERS` reports it, and `timer_fixup_init()` deletes
  the timer; `INIT_DELAYED_WORK()` has already wiped `work->data` by then.
- **Potentially unsafe usage**: `INIT_WORK()` before every queueing of the same
  item.
  - Unsafe: when nothing guarantees that the previous queueing has finished;
    `INIT_WORK()` then overwrites `work->data` and `work->entry` of an item
    that may still be on a worklist.
  - Safe: when one lock covers init, queue and `flush_work()`, as
    `__lru_add_drain_all()` in `mm/folio.c` does under its static mutex.
  - Safe: on a freshly allocated item that is flushed before the free, as
    `schedule_on_each_cpu()` does.
