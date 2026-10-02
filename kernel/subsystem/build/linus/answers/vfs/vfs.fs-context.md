- `struct file_system_type` (`include/linux/fs.h`): has no `mount` member;
  `init_fs_context` is the only entry point.
- There is no legacy_init_fs_context() wrapper in `fs/fs_context.c`.
- `init_fs_context` must be non-NULL: `alloc_fs_context()` and
  `finish_clean_context()` call it unconditionally, and
  `register_filesystem()` does not test it.
- `struct super_operations` has no remount_fs member; `fc->ops->reconfigure()`
  is the only remount hook.
- `init_fs_context()` also runs for a remount: `alloc_fs_context()` calls it
  with `fc->purpose == FS_CONTEXT_FOR_RECONFIGURE` and `fc->root` already set.
- `reconfigure_super()`: is entered with `s_umount` held exclusive; each
  caller takes it first, for example `do_remount()` and
  `vfs_cmd_reconfigure()`.
- `reconfigure_super()` on a remount read-only with `s_pins` not empty: drops
  and retakes `s_umount` around `group_pin_kill()`, and returns 0 if `s_root`
  is then NULL.
- `vfs_get_super()`: static in `fs/super.c`; a filesystem calls
  `get_tree_nodev()`, `get_tree_single()`, `get_tree_keyed()`,
  `get_tree_bdev()`, `get_tree_bdev_flags()`, `get_tree_mtd()`
  (`drivers/mtd/mtdsuper.c`), or `sget_fc()` and `sget_dev()` directly.
- `alloc_super()`: static in `fs/super.c`; `sget_fc()` is its only caller.
- `set` callback of `sget_fc()`: when it returns 0 it must have set `s_dev`
  and registered it in the device table; callbacks outside `fs/super.c` do
  this through `set_anon_super()` or `set_anon_super_fc()`.
- `sget_fc()` warns with `VFS_WARN_ON_ONCE()` if `s_super_dev->sd_dev` is
  still zero after `set()` succeeds.
- `set` callback of `sget_fc()`: runs under `sb_lock`, so it must not sleep.
- There is no kill_litter_super() here; in-memory filesystems use
  `kill_anon_super()`, for example debugfs in `fs/debugfs/inode.c`.
