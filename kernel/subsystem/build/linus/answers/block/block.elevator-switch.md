- `elv_iosched_store()`: takes `set->update_nr_hwq_lock` for write, with
  `down_write_trylock()`, and returns `-EBUSY` when the lock is contended.
- Comments in `block/blk-sysfs.c`, `block/blk-mq.c` and
  `block/blk-mq-sched.c` say the switch holds that lock for read;
  `elv_iosched_store()` does not.
- Pre-freeze allocation: there is no elv_alloc_et() here;
  `blk_mq_alloc_sched_res()` in `block/blk-mq-sched.c` fills the `res` member
  (`struct elevator_resources`) of `struct elv_change_ctx`.
- `res.et`: scheduler tags from `blk_mq_alloc_sched_tags()`;
  `struct elv_change_ctx` has no `et` member of its own.
- `res.data`: private data from the `alloc_sched_data` op, through
  `blk_mq_alloc_sched_data()`; `NULL` when the type has no such op.
- `alloc_sched_data`: only `block/kyber-iosched.c` sets it.
- Still allocated inside the freeze, with `GFP_KERNEL` under the
  `memalloc_noio_save()` of `blk_mq_freeze_queue()`: the
  `struct elevator_queue` in `elevator_alloc()`, private data in
  `dd_init_sched()` and `bfq_init_queue()`, per-hctx data in
  `kyber_init_hctx()`.
- Unused resources: `elevator_change()` frees them with
  `blk_mq_free_sched_res()` when `ctx->new` is `NULL`; that covers the
  same-name switch too.
- `elevator_exit()`: while frozen, also takes `sysfs_lock` of the old
  `struct elevator_queue` around `blk_mq_exit_sched()`, which sets
  `ELEVATOR_FLAG_DYING`.
- Failure inside `blk_mq_init_sched()` (`elevator_alloc()`, `init_sched` or
  `init_hctx`): `q->elevator` is `NULL`, the old scheduler is not restored.
- Failure before `elevator_exit()`: the old scheduler stays. For example,
  `blk_mq_alloc_sched_res()` fails before the freeze, or
  `elevator_find_get()` in `elevator_switch()` finds no such name and returns
  `-EINVAL`.
