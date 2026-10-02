- `fm->sb` is never cleared; it is written only by
  `fuse_fill_super_common()` and `fuse_fill_super_submount()`.
- Teardown: `fuse_mount_remove()` unlinks `fm->fc_entry` under
  `down_write(&fc->killsb)`, called from `fuse_sb_destroy()` and
  `virtio_kill_sb()` before the superblock is killed; a mount found on
  `fc->mounts` under `down_read()` with `sb` set therefore has a live
  superblock.
- Mounts on `fc->mounts` with `sb == NULL`: the first mount between
  `fuse_conn_init()` and fill_super, and CUSE's `cc->fm` always, so
  `fuse_ilookup()` finds nothing on a CUSE connection.
- `fc->auto_submounts`: written only by `virtio_fs_get_tree()`.
- Mounting again with a device fd that is already installed: `fuse_get_tree()`
  reuses the existing superblock through `sget_fc()` with
  `fuse_test_super()`; no second superblock or `struct fuse_mount` joins the
  connection, and `fuse_set_no_super()` gives `-ENOTCONN` if none matches.
- Notify handlers that take `fc->killsb` are in `fs/fuse/notify.c`, not
  `fs/fuse/dev.c`; `fuse_epoch_work()` in `fs/fuse/dir.c` is the work-item
  user.
- **Potentially unsafe usage**: dereferencing `fm->sb` without `fc->killsb`.
  - Unsafe: when the mount was reached through the connection (`fc->mounts`,
    or the out pointer of `fuse_ilookup()`) from a device write or a work
    item; the superblock can be killed once `fuse_mount_remove()` returns.
  - Safe: with `down_read(&fc->killsb)` held from before `fuse_ilookup()`
    until the last use and the `iput()`, as `fuse_notify_retrieve()` does.
  - Safe: when the mount came from `get_fuse_mount()` on an inode the VFS
    caller holds, as `fuse_access()` does.
  - Safe: in `process_init_reply()`, on the mount the INIT request carries
    (`ia->fm`); INIT is counted in `fch->num_waiting`, and
    `fuse_conn_destroy()` waits for that in `fuse_chan_wait_aborted()`
    before the superblock is killed.
