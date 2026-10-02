- `check_flush_dependency()` has two `WARN_ONCE()` calls, both only for a
  target without `WQ_MEM_RECLAIM`: the flusher has `PF_MEMALLOC`, or the
  flusher is a worker running an item of a `WQ_MEM_RECLAIM` workqueue.
- `from_cancel` true: exempt from both warnings; `__cancel_work_sync()`
  passes it, so the four cancel-sync and disable-sync calls never warn.
- `__WQ_LEGACY` on the flusher's workqueue: exempts the second warning only;
  the `PF_MEMALLOC` warning still applies.
- `check_flush_dependency()` has no test for a flush within the same
  workqueue, no test of `WQ_BH`, and no test for the rescuer.
- A BH workqueue as target: it cannot have `WQ_MEM_RECLAIM`, so `flush_work()`
  on its queued or running item from a `WQ_MEM_RECLAIM` worker warns.
- The second warning needs task context: `current_wq_worker()` in
  `kernel/workqueue_internal.h` returns NULL outside `in_task()`.
- `current_is_workqueue_mem_reclaim()`: exported; makes the same test of the
  caller as the second warning, for code that must decide before it
  flushes. It does not cover the `PF_MEMALLOC` case.
