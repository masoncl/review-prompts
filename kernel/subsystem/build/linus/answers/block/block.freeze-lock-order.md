- `queue_attr_store()` with `->store`: holds no lock and no freeze.
- `queue_attr_store()` with `->store_limit`: holds `limits_lock` only, queue
  not frozen; it never takes `sysfs_lock`.
- `tag_list_lock`: before the freeze, see `blk_mq_update_tag_set_shared()` and
  `__blk_mq_update_nr_hw_queues()`.
- `sysfs_lock`: before the freeze; `blk_register_queue()` holds it across
  `elevator_set_default()`.
- `elevator_lock`: show functions take it with no freeze, for example
  `queue_requests_show()` and `blk_mq_hw_sysfs_show()`.
- `rq_qos_mutex`: no single order. `rq_qos_add()` and `rq_qos_del()` assert it
  and freeze inside; `ioc_qos_write()` drops it, freezes, then retakes it.
- `debugfs_mutex`: `debugfs_create_files()` asserts that `elevator_lock` and
  `rq_qos_mutex` are not held; `wbt_set_lat()` and `elevator_change_done()`
  register debugfs entries after the unfreeze.
- `rqos_state_mutex` of `struct gendisk`: taken under the freeze in
  `wbt_set_lat()`.
- `queue_ra_store()`: takes `limits_lock`, does not freeze.
- `queue_wb_lat_store()`: calls `wbt_set_lat()`, takes no `elevator_lock`.
- Lockdep maps: fields `io_lockdep_map` and `q_lockdep_map`; a report prints
  them as "&q->q_usage_counter(io)" and "&q->q_usage_counter(queue)".
- `blk_freeze_acquire_lock()`: exclusive acquire with trylock set, so lockdep
  records no dependency from locks already held to the freeze, only from the
  freeze to locks taken under it.
- Opposite edge: comes from `bio_queue_enter()`, `__bio_queue_enter()` and
  `blk_queue_enter()`, which do a non-trylock read acquire and release.
- Lockdep therefore reports a lock that is taken under a freeze and also held
  while entering the queue; it does not check a lock held when the freeze
  starts.
- `mq_freeze_disk_dead`: set by `blk_freeze_set_owner()` when `q->disk` is
  NULL, `GD_DEAD` is set, or the queue is not registered; `io_lockdep_map` is
  then skipped, so a freeze before `add_disk()` is not modelled on it.
- Modelled freezes: only the first freeze (`mq_freeze_depth` 0) with an owner
  task; released when that task's `mq_freeze_owner_depth` reaches 0.
- Not modelled: nested freezes, `blk_freeze_queue_start_non_owner()` and
  `blk_mq_unfreeze_queue_non_owner()`.
