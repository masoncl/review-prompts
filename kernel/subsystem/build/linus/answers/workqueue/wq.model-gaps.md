- Models do not know the size of a `WQ_AFFN_CACHE_SHARD` pod. One LLC is split
  into shards of about `wq_cache_shard_size` cores, 8 by default; an LLC with
  fewer cores than that is one pod; see `llc_calc_shard_layout()`, reached
  from `workqueue_init_topology()`.
- Models take every entry on `pool->worklist` to have a `func` that may be
  called. The `func` of `pwq->mayday_cursor` is `mayday_cursor_func()`, which
  is `BUG()`.
- Models do not know `devm_alloc_workqueue()` and
  `devm_alloc_ordered_workqueue()`. They call `destroy_workqueue()` at driver
  detach through `devm_workqueue_release()`.
