- `s_passive`: the passive count, a `refcount_t` in `struct super_block`
  (`include/linux/fs/super_types.h`); `struct super_block` has no `s_count`
  member and there is no __put_super() in this tree.
- What each keeps alive: `s_active` the filesystem, `s_passive` the
  structure.
- `s_passive` needs no `sb_lock`: `put_super()` and `user_get_super()` change
  it without `sb_lock`.
- `put_super()` (`fs/super.c`, declared in `fs/internal.h`): takes `sb_lock`
  itself on the final drop, so call it with `sb_lock` not held.
- Final `put_super()`: unlinks `s_list` and `s_instances`, queues
  `destroy_super_rcu()`, then calls `put_filesystem()`.
- `s_passive` therefore also pins the filesystem module, taken by
  `get_filesystem()` in `sget_fc()`; `deactivate_locked_super()` has no
  `put_filesystem()` call of its own, only the one in its `put_super()`.
- A dead superblock stays on `super_blocks` and `fs_supers` until the last
  passive reference goes; `kill_super_notify()` does not unhash it.
- `kill_super_notify()`: drops the `struct super_dev` claim of `sget_fc()`,
  then sets `SB_DEAD` under `sb_lock`; `sget_fc()` skips entries with
  `SB_DEAD`.
- A listed superblock can have `s_passive` already at zero: walkers pin with
  `refcount_inc_not_zero()` under `sb_lock`, before they call `super_lock()`,
  and skip on failure, as `__iterate_supers()` and `iterate_supers_type()`
  do.
- Each `struct super_dev` in `super_dev_table` holds one passive reference:
  taken in `super_dev_insert()`, dropped in `super_dev_put()` when `sd_ref`
  reaches zero.
- `deactivate_super()`: `atomic_add_unless(&s->s_active, -1, 1)`; only when
  that fails does it take `s_umount` exclusive and call
  `deactivate_locked_super()`.
- `generic_shutdown_super()`: sets `SB_DYING` after the teardown, just before
  it releases `s_umount`; the teardown before it runs only if `s_root` is set.
