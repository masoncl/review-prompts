- `disable_elv_switch()`: runs first in `del_gendisk()` for a blk-mq queue,
  before the NOIO scope; sets `QUEUE_FLAG_NO_ELV_SWITCH`.
- Drain start: `blk_queue_start_drain()` in `__blk_mark_disk_dead()`, which
  `__del_gendisk()` calls under `disk->open_mutex`, before partitions are
  dropped and before any sysfs removal. `__del_gendisk()` has no
  `blk_mq_freeze_queue()` call in its body.
- `GD_ADDED`: not cleared by `__del_gendisk()`.
- Scheduler: torn down in `blk_unregister_queue()` by `elevator_set_none()`,
  before `blk_mq_freeze_queue_wait()` in `__del_gendisk()`.
- `elevator_set_none()`: `elevator_change()` takes a nested
  `blk_mq_freeze_queue()` that waits for the counter to reach zero. For a
  registered blk-mq queue the I/O has drained by the time
  `blk_unregister_queue()` returns.
- `__del_gendisk()` after the wait: `blk_throtl_cancel_bios()`,
  `blk_sync_queue()`, `blk_flush_integrity()`, `blk_mq_cancel_work_sync()`,
  `rq_qos_exit()`. There is no quiesce and no elevator call here.
- End state by `GD_OWNS_QUEUE`:

| | Disk owns the queue | Disk does not |
|---|---|---|
| Freeze | left frozen | `__blk_mq_unfreeze_queue(q, true)` |
| hctxs | `blk_mq_exit_queue()` has run | live |
| `QUEUE_FLAG_DYING` | set | not set by `__del_gendisk()`; `blk_mark_disk_dead()` sets it |

- `blk_mq_destroy_queue()`: does not quiesce, does not call
  `blk_mq_freeze_queue()` on the queue it destroys, and does not call
  `blk_put_queue()`; the caller drops the reference.
- `blk_mq_destroy_queue()`: touches neither the elevator nor rq_qos; it warns
  if the queue is still registered.
