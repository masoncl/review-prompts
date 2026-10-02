- `struct blk_plug`: holds requests only (`mq_list`), plus preallocated
  requests (`cached_rqs`) and unplug callbacks (`cb_list`); it never holds
  bios. A bio-based driver batches by registering a callback with
  `blk_check_plugged()`.
- `struct blk_mq_tags` (driver tags): belongs to the `struct blk_mq_tag_set`,
  not to the hctx. `hctx->tags` is a borrowed pointer to `set->tags[i]`, so
  hctx `i` of every queue on the set shares one tag space; with
  `BLK_MQ_F_TAG_HCTX_SHARED` every `set->tags[i]` is `set->shared_tags`.
- `struct elevator_tags` in `block/elevator.h`: owns the scheduler tags of one
  queue. It hangs off `elevator_queue->et`; `hctx->sched_tags` points into it
  (`blk_mq_init_sched()` in `block/blk-mq-sched.c`).
- `struct request` with an elevator attached: the structure comes from the
  queue's scheduler tags (`static_rqs`), not from the tag set.
  `hctx->tags->rqs[rq->tag]` is pointed at it only in
  `blk_mq_start_request()`.
- `struct blk_mq_ctx` and the elevator are alternatives, not stages: see
  `blk_mq_insert_request()` in `block/blk-mq.c`. With `q->elevator` set a
  request goes to the elevator and never onto `ctx->rq_lists`; flush and
  passthrough requests go straight to `hctx->dispatch` in both cases.
- `q->queue_hw_ctx`: an RCU-protected array of hctx pointers, read through
  `queue_hctx()`. There is no hctx_table xarray in this tree.
- `struct gendisk` and its queue: the disk always holds a queue reference
  (dropped in `disk_release()`), but owns the queue only when `GD_OWNS_QUEUE`
  is set. `blk_mq_alloc_disk_for_queue()` (used by `sd_probe()` and
  `sr_probe()`) does not set it; `__del_gendisk()` then unfreezes the queue so
  passthrough keeps working, instead of leaving it frozen and exiting it.
- `struct gendisk` has no refcount of its own: `disk_to_dev()` is
  `part0->bd_device`, and the gendisk memory is freed by `bdev_free_inode()`
  of the whole-disk bdev.
- `struct queue_limits`: embedded as `q->limits`, and `struct blk_integrity` is
  embedded inside it, so an integrity profile change is a limits update.
- `struct blkcg_gq` and `struct rq_qos`: both point at or hang off the queue
  but are set up and torn down with the disk (`blkcg_init_disk()`,
  `blkcg_exit_disk()`, `rq_qos_add()`, `rq_qos_exit()`); a queue with no
  `struct gendisk` has neither.
- Zoned disks never have partitions: `__add_disk()` in `block/genhd.c` sets
  `GENHD_FL_NO_PART`. Partition remap (`blk_partition_remap()`) runs in
  `submit_bio_noacct()`, before any zone write plugging.
- `struct blk_zone_wplug`: private to `block/blk-zoned.c`. Plugs are allocated
  on demand into `disk->zone_wplugs_hash` for zones being written; there is
  not one per zone. A plugged bio holds its own `q_usage_counter` reference.
- Zone write plugging on a bio-based disk: happens only if the driver calls
  `blk_zone_plug_bio()`, as `dm_zone_plug_bio()` does; blk-mq calls it from
  `blk_mq_submit_bio()` after the split and the merge attempt.
- `QUEUE_FLAG_ZONED_QD1_WRITES`: when set, plugged zone writes are issued by
  one kthread per disk, `disk->zone_wplugs_worker`, which waits for each bio
  to complete before issuing the next, instead of by per-plug work items.
