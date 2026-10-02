- `fuse_kill_sb_anon()`: `fuse_sb_destroy()`, then `kill_anon_super()`,
  then `fuse_mount_destroy()`.
- `fuse_conn_destroy()`: called from `fuse_sb_destroy()`, before the
  superblock is shut down; `fuse_mount_destroy()` only does
  `fuse_conn_put()` and frees `fm`.
- DESTROY is sent only when both `fc->destroy` and `fc->conn_init` are set.
- Unmount passes `false` as `abort_with_err`: a blocked device read then
  returns `-ENODEV`; only the abort file in `fs/fuse/control.c` passes
  `fc->abort_err`.
- Eviction: `generic_shutdown_super()` clears `SB_ACTIVE` only after
  `shrink_dcache_for_umount()`, so inodes dropped with their dentries still
  reach `fuse_chan_queue_forget()` in `fuse_evict_inode()`;
  `fuse_dev_queue_forget()` frees the link, because the abort already
  cleared `fiq->connected`.
- `fuse_umount_begin()`: skipped only by `fc->no_force_umount`; a mount
  with `fc->destroy` set, such as fuseblk, is aborted too.
- An open device keeps the connection and channel allocated after unmount,
  through the reference `fuse_dev_install()` took.
