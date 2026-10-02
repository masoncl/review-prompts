- `queue_requests_store()` in `block/blk-sysfs.c`: calls
  `blk_mq_alloc_sched_tags()` before freezing, only when the tags grow.
- `__blk_mq_update_nr_hw_queues()`: before freezing it calls
  `blk_mq_alloc_sched_res_batch()` and `blk_mq_prealloc_tag_set_tags()`.
  There is no blk_mq_alloc_sched_tags_batch() here.
- `__blk_mq_update_nr_hw_queues()`: its `memalloc_noio_save()` scope opens
  before those allocations, so they are NOIO too.
- hctxs in `__blk_mq_update_nr_hw_queues()`: allocated by
  `__blk_mq_realloc_hw_ctxs()` while the queues are frozen, not before;
  `blk_mq_alloc_hctx()` uses `GFP_NOIO`.
- `wbt_set_lat()` in `block/blk-wbt.c`: calls `wbt_alloc()` before
  `blk_mq_freeze_queue()`.
- `q->io_lockdep_map`: the only map primed against `fs_reclaim`, in
  `blk_alloc_queue()`, which records `fs_reclaim` before `io_lockdep_map`
  once, at queue allocation. `q->q_lockdep_map` is not primed. A freeze with
  `q->mq_freeze_disk_dead` set skips `io_lockdep_map` in
  `blk_freeze_acquire_lock()`, so lockdep does not see the reclaim dependency
  for such a freeze.
- NOIO scope: changes allocations only. I/O the caller starts itself must come
  before the freeze; `elv_iosched_store()` loads the scheduler module first.
- debugfs registration: done after unfreezing, under `blk_debugfs_lock()` in
  `block/blk.h`, which opens its own NOIO scope and then takes
  `q->debugfs_mutex`.
