- `blk_freeze_queue_start()`: ended with
  `blk_mq_unfreeze_queue_nomemrestore()`. Callers outside `block/blk-mq.c`
  are `nvme_mpath_start_freeze()` and `blk_pre_runtime_suspend()`.
- `nvme_start_freeze()`: calls `blk_freeze_queue_start_non_owner()`, not
  `blk_freeze_queue_start()`; `nvme_unfreeze()` ends it with
  `blk_mq_unfreeze_queue_non_owner()`.
- Owner and non-owner variants: differ only in lockdep. Without
  `CONFIG_LOCKDEP`, `blk_freeze_set_owner()` and `blk_unfreeze_check_owner()`
  return false and the variants behave the same.
- Owner variant unfrozen from another task, with `CONFIG_LOCKDEP`:
  `blk_unfreeze_check_owner()` compares `q->mq_freeze_owner` with `current`
  and returns false, so that unfreeze does not release the maps taken by
  `blk_freeze_acquire_lock()`.
- `blk_queue_start_drain()` in `block/blk-core.c`: the teardown form. It calls
  `__blk_freeze_queue_start(q, current)` and wakes `q->mq_freeze_wq` and tag
  waiters. `__del_gendisk()` calls `blk_freeze_acquire_lock()` by hand;
  `blk_mq_destroy_queue()` ignores the return value.
- Nested `blk_mq_freeze_queue()`: still runs `blk_mq_freeze_queue_wait()`, so
  it blocks until the counter is zero even when the depth was already raised.
- `q->mq_freeze_depth` above zero: means a freeze has started, not that the
  queue has drained.
- `__blk_mq_update_nr_hw_queues()`: its `blk_mq_freeze_queue_nomemsave()` is
  ended inside `elv_update_nr_hw_queues()` in `block/elevator.c`.
