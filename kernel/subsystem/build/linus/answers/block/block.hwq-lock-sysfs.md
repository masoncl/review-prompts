- In-tree stores that take `update_nr_hwq_lock`: `elv_iosched_store()` in
  `block/elevator.c` and `queue_requests_store()` in `block/blk-sysfs.c`.
- Both use `down_write_trylock()` and return `-EBUSY` when it fails;
  `queue_attr_store()` passes that to user space unchanged.
- Write mode in `elv_iosched_store()`: serialises both stages of
  `elevator_change()`, the switch and `elevator_change_done()`.
- Holder that waits for the store: `del_gendisk()` keeps the read side across
  `__del_gendisk()`, which reaches `kobject_del(&disk->queue_kobj)` through
  `blk_unregister_queue()`.
- `q->tag_set`: dereferenced with no check and no reference; safe because both
  attributes are in `blk_mq_queue_attrs`, which `blk_mq_queue_attr_visible()`
  hides for bio-based queues.
- Allocation goes between the trylock and the freeze:
  `queue_requests_store()` calls `blk_mq_alloc_sched_tags()` there.
- **Unsafe usage**: a blocking `down_read()` or `down_write()` on
  `update_nr_hwq_lock` in the store function of a queue attribute.
  - Unsafe: the store holds a kernfs active reference on its attribute while
    `del_gendisk()` holds the lock and waits in `kobject_del()` for that
    reference.
  - Safe: `down_write_trylock()` and `-EBUSY`, as `elv_iosched_store()` and
    `queue_requests_store()` do.
  - Safe: a blocking acquisition outside any sysfs callback of the disk and
    its queue, as `add_disk_fwnode()` and `blk_mq_update_nr_hw_queues()` do;
    `__del_gendisk()` removes those attributes under the read side.
