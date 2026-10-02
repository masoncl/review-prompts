- Elevator and `q->nr_requests`: changed under `q->elevator_lock`, not
  `q->sysfs_lock`. `elevator_change()` also asserts
  `set->update_nr_hwq_lock`.
- Lock order around a freeze, as the code takes them:

| Lock | Order | Example |
|---|---|---|
| `set->update_nr_hwq_lock` | before freezing | `elv_iosched_store()` |
| `q->limits_lock` | before freezing | `queue_limits_commit_update_frozen()` |
| `q->rq_qos_mutex` | both orders occur | before freezing: `rq_qos_add()`; after freezing: `ioc_qos_write()`, and `wbt_init()` called from `wbt_set_lat()` |
| `q->elevator_lock` | after freezing | `elevator_change()` |

- `WARN_ON_ONCE(q->mq_freeze_depth == 0)` in `elevator_switch()`: proves a
  freeze was started, not that the queue has drained.
- `__blk_mq_update_nr_hw_queues()`: switches each queue that has an elevator
  to none with `elevator_set_none()`, one freeze per queue, before it freezes
  the whole set. `elv_update_nr_hw_queues()` switches back and unfreezes, per
  queue.
- `elevator_set_default()`: called from `blk_register_queue()`; when it
  selects mq-deadline it goes through `elevator_change()` and freezes. There
  is no elevator_init_mq() here.
- There is no blk_mq_free_queue() here; `blk_mq_exit_queue()` and
  `blk_mq_release()` in `block/blk-mq.c` do the teardown and the free.
- Queue flags: some are flipped under a freeze although the bit operation is
  atomic. `queue_zoned_qd1_writes_store()` freezes and quiesces to flip
  `QUEUE_FLAG_ZONED_QD1_WRITES`; `rq_qos_add()` sets `QUEUE_FLAG_QOS_ENABLED`
  under freeze. Others are flipped with no freeze, for example
  `QUEUE_FLAG_NOMERGES` in `queue_nomerges_store()`.
- `q->queue_hw_ctx`: an RCU-managed array. `queue_hctx()` reads it with
  `rcu_dereference()`; `__blk_mq_realloc_hw_ctxs()` replaces it with
  `rcu_assign_pointer()` and `kfree_rcu_mightsleep()`.
- `set->tags_srcu`: the SRCU that tag iterators hold;
  `blk_mq_queue_tag_busy_iter()` takes it after `percpu_ref_tryget()`.
