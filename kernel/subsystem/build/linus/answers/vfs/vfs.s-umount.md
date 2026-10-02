- `super_lock()`: waits first, with `wait_var_event()` on `s_flags`, for
  `SB_BORN` or `SB_DYING`; it does not sleep on the rwsem while the superblock
  is being set up.
- `super_lock()` with `SB_DYING` set after the wait: returns false and never
  takes `s_umount`; otherwise it locks, rechecks `SB_DYING`, and unlocks and
  returns false if set.
- `super_lock()`, `super_lock_shared()`, `super_lock_excl()`: static in
  `fs/super.c`. Code elsewhere uses `iterate_supers()`,
  `iterate_supers_type()`, `user_get_super()` or `super_trylock_shared()`.
- `__iterate_supers()`: makes no `s_root` test; the callback gets every
  superblock for which `super_lock()` returned true.
- `SUPER_ITER_UNLOCKED`: the callback runs with no `s_umount`; each in-tree
  callback calls `get_active_super()` before it acts, for example
  `filesystems_freeze_callback()`.
- `SUPER_ITER_EXCL`: the callback runs with `s_umount` exclusive; used by
  `do_emergency_remount()`.
- Lookup by device: there is no bdev_super_lock() here. `user_get_super()`
  and the four `fs_holder_ops` callbacks, for example `fs_bdev_mark_dead()`,
  walk `super_dev_table` with `super_dev_first()` and `super_dev_next()`,
  without `sb_lock`.
- The pinned `struct super_dev` supplies the passive reference for
  `super_lock()` in those walks.
- `->get_tree()`: entered with no superblock lock; returns with `s_umount`
  exclusive on `fc->root->d_sb`, for a reused superblock too (`grab_super()`).
- quotactl: `s_umount` exclusive when `quotactl_cmd_onoff()` is true, shared
  otherwise; see `quotactl_block()` in `fs/quota/quota.c`.
- `->evict_inode()`: no `s_umount` from `iput()`; exclusive when reached from
  `evict_inodes()` in `generic_shutdown_super()`; shared from
  `fs_bdev_mark_dead()`.
- `->remove_bdev()`: `s_umount` shared, from `fs_bdev_mark_dead()`.
- `->nr_cached_objects()`: called from `super_cache_count()` with no
  `s_umount`, after an `SB_BORN` test only; `super_cache_scan()` calls it
  under `super_trylock_shared()`.
- **Potentially unsafe usage**: taking `s_umount` with `down_read()` or
  `down_write()` instead of `super_lock()`.
  - Unsafe: on a superblock reached only through `super_blocks`, `fs_supers`
    or `super_dev_table`, with no active reference; it may lack `SB_BORN` or
    have `SB_DYING`, which `super_lock()` and `super_trylock_shared()` test.
  - Safe: while holding an active reference through a mount or an open file,
    as `do_remount()` and the `syncfs` syscall in `fs/sync.c` do;
    `deactivate_locked_super()` calls `->kill_sb()` only when `s_active`
    reaches zero.
- **Unsafe usage**: calling `put_super()` with `sb_lock` held; the final drop
  takes `sb_lock` again.
  - Safe: drop `sb_lock`, call `put_super()`, retake `sb_lock`, as
    `iterate_supers_type()` does.
