- Scheduler debugfs: registered and removed after the unfreeze, not in
  `blk_mq_init_sched()`. `elv_register_queue()` calls
  `blk_mq_sched_reg_debugfs()`, `elv_unregister_queue()` calls
  `blk_mq_sched_unreg_debugfs()`; each takes `q->debugfs_mutex` itself.
- `elv_register_queue()`: skips debugfs registration when `kobject_add()`
  failed.
- wbt: `elevator_change_done()` has no wbt step, and there is no
  ELEVATOR_FLAG_ENABLE_WBT_ON_EXIT in this tree. The only call of
  `wbt_enable_default()` in a switch is in `bfq_exit_queue()`, inside a freeze
  under `q->elevator_lock`.
- Old scheduler's resources: freed with `blk_mq_free_sched_res()`, which frees
  the tags and calls `free_sched_data` when the type has that op.
- `ctx->old`: `elevator_change_done()` is the only code that unregisters it,
  frees its scheduler tags and puts its kobject; `elevator_exit()` does none
  of these.
- `q->elevator_lock`: released before the unfreeze; not held when
  `elevator_change_done()` is called.
- `q->sysfs_lock`: not taken by `elevator_change_done()` or its callees.
- Locks the caller holds across both stages:

  | Path | `set->update_nr_hwq_lock` | Also held |
  |---|---|---|
  | `elv_iosched_store()` | write | none |
  | `blk_register_queue()` to `elevator_set_default()` | read, in `add_disk_fwnode()` | `q->sysfs_lock` |
  | `blk_unregister_queue()` to `elevator_set_none()` | read, in `del_gendisk()` or `add_disk_fwnode()` | none |
  | `blk_mq_elv_switch_none()` to `elevator_set_none()` | write | `set->tag_list_lock` |
  | `elv_update_nr_hw_queues()`, which calls `elevator_switch()` itself | write | `set->tag_list_lock` |

- From `elv_iosched_store()`: the write lock keeps `queue_requests_store()`,
  `blk_mq_update_nr_hw_queues()`, `add_disk_fwnode()` and `del_gendisk()` on
  the same tag set out until `elevator_change_done()` has returned.
