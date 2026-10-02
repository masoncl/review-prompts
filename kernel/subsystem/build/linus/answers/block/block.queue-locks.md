- `update_nr_hwq_lock` takers, complete for this tree:

| Taker | Mode |
|---|---|
| `blk_mq_update_nr_hw_queues()` | write, blocking, then `tag_list_lock` |
| `disable_elv_switch()`, from `del_gendisk()` | write, blocking |
| `elv_iosched_store()` | write, `down_write_trylock()` |
| `queue_requests_store()` | write, `down_write_trylock()` |
| `add_disk_fwnode()` around `__add_disk()` | read, blocking, blk-mq only |
| `del_gendisk()` around `__del_gendisk()` | read, blocking, blk-mq only |

- `update_nr_hwq_lock` held for write: lets `queue_requests_store()` and
  `blk_mq_elv_switch_none()` read `q->elevator` without `elevator_lock`.
- `elevator_change()`: only asserts `update_nr_hwq_lock` with
  `lockdep_assert_held()`, so either mode passes; `elevator_set_default()`
  and `elevator_set_none()` reach it under the read side from
  `blk_register_queue()` and `blk_unregister_queue()`.
- `sysfs_lock`: not taken by `queue_attr_show()` or `queue_attr_store()`.
  It covers `blk_register_queue()` from after `blk_mq_sysfs_register()` to
  the uevents, the clear of `QUEUE_FLAG_REGISTERED`, and independent access
  ranges (asserted in `block/blk-ia-ranges.c`).
- `tag_list_lock`: also held around hctx kobject add and delete in
  `blk_mq_sysfs_register()` and `blk_mq_sysfs_unregister()`.
- `elevator_lock`: `wbt_lat_usec` is not under it, whatever the comment in
  `struct request_queue` says; `queue_wb_lat_show()` and `wbt_set_lat()`
  take `rqos_state_mutex` of `struct gendisk`.
- `elevator_lock`: also covers `async_depth`.
- `queue_lock`: does not cover `queue_flags`; `blk_queue_flag_set()` is a bare
  `set_bit()`. It covers `quiesce_depth`, `rpm_status`, `icq_list` and blkg
  creation.
- `requeue_lock`: covers `requeue_list` and `flush_list`.
- `limits_lock`: also held by `queue_attr_show()` around `->show_limit`, and
  by `queue_ra_show()` and `queue_ra_store()` for `read_ahead_kb`.
- `tags_srcu` in `struct blk_mq_tag_set`: defers freeing of tags against tag
  iteration; `srcu` beside it is for `BLK_MQ_F_BLOCKING`.
- There is no sysfs_dir_lock field in `struct request_queue`.
