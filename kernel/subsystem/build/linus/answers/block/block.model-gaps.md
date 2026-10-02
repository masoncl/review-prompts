- Models do not know `blk_crypto_submit_bio()`. `submit_bio_noacct()` ends a
  bio that has a crypt context with `BLK_STS_NOTSUPP` unless
  `blk_crypto_supported()`; the fallback runs only from
  `__blk_crypto_submit_bio()` in `block/blk-crypto.c`.
- Models take a split to fail only for `REQ_NOWAIT` or `REQ_ATOMIC`.
  `bio_split_io_at()` in `block/blk-merge.c` also returns `-EINVAL` for a
  bvec not aligned to `lim->dma_alignment` or when no block-aligned split
  exists, and `blk_mq_submit_bio()` fails a bio that `bio_unaligned()`
  rejects.
- Models take `blk_mq_find_and_get_req()` to run under `tags->lock`.
  `tags->lock` is taken only around the `active_queues` update, in
  `__blk_mq_tag_busy()` and `__blk_mq_tag_idle()`.
- Models take `elevator_change_done()` to re-enable wbt through
  ELEVATOR_FLAG_ENABLE_WBT_ON_EXIT. `wbt_enable_default()` only changes
  state, and `wbt_init_enable_default()`, called from
  `blk_register_queue()`, creates the policy. BFQ uses
  `QUEUE_FLAG_DISABLE_WBT_DEF`.
- Models name blk_mq_alloc_sched_tags_batch() or only
  `blk_mq_alloc_sched_tags()` as what is allocated before the freeze.
  `elevator_alloc()` takes the preallocated `struct elevator_resources` as
  its third argument.
- Models call the `blk_get_queue()` reference a kobject refcount. It is
  `refcount_t refs`, `blk_get_queue()` returns false on a dying queue, and
  the "queue" kobject is `queue_kobj` in `struct gendisk`.
- Models do not know `bio_await()`, declared in `include/linux/bio.h` and
  defined in `block/bio.c`.
- Models name QUEUE_FLAG_SKIP_TAGSET_QUIESCE. The test is
  `blk_queue_skip_tagset_quiesce()` in `include/linux/blkdev.h`.
