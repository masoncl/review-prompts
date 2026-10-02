- Holders of `fc->count`:
  - the first `struct fuse_mount`, which owns the initial count from
    `fuse_conn_init()`
  - each submount, taken in `fuse_get_tree_submount()`
  - each installed `struct fuse_dev`, taken in `fuse_dev_install_with_pq()`
  - `fuse_ctl_file_conn_get()` for one control-file operation
  - `fuse_uring_stop_queues()` while `async_teardown_work` is pending,
    dropped in `fuse_uring_async_stop_queues()`
  - each open CUSE file, from `cuse_open()` to `cuse_release()`
- CUSE: `cuse_channel_open()` drops the initial count right after
  `fuse_dev_alloc_install()`, so the device holds the long-lived reference.
- Device reference: dropped in `fuse_dev_release()`; dropped in the last
  `fuse_dev_put()` instead when the device was never released through a file,
  as in `virtio_fs_free_devs()`. There is no fuse_dev_free() here.
- `fuse_notify_retrieve()` and `fs/fuse/virtio_fs.c` do not call
  `fuse_conn_get()`.
- `struct fuse_chan` has no count of its own; once passed to
  `fuse_conn_init()` it is freed only with the connection.
- Last `fuse_conn_put()`, in order:
  1. `fuse_dax_conn_free()` under `CONFIG_FUSE_DAX`
  2. `cancel_work_sync(&fc->epoch_work)`
  3. `fuse_chan_release()`: `fiq->ops->release` if set, then
     `cancel_delayed_work_sync(&fch->timeout.work)` if a timeout is armed
  4. `put_pid_ns()`
  5. free `fc->curr_bucket`
  6. `fuse_backing_files_free()` under `CONFIG_FUSE_PASSTHROUGH`
  7. `call_rcu(&fc->rcu, delayed_release)`
- `delayed_release()`, after the grace period: `fuse_uring_destruct()`, then
  `fuse_chan_free()`, then `put_user_ns()`, then `fc->release()`; so ring,
  channel, connection.
- `fuse_free_conn()` is a plain `kfree()`; `cuse_fc_release()` frees the
  enclosing `struct cuse_conn`.
- Last `fuse_conn_put()` can sleep (steps 2 and 3; virtiofs's release takes
  `virtio_fs_mutex`).
- `fuse_chan_free()` warns if `fch->devices` is not empty;
  `fuse_uring_destruct()` warns if ring entries are still queued.
- `fuse_mount_destroy()` does not abort or wait; `fuse_conn_destroy()` does
  (DESTROY when `fc->destroy` and `fc->conn_init` are set,
  `fuse_chan_abort()`, `fuse_chan_wait_aborted()`), and `fuse_sb_destroy()`
  calls it only when `fuse_mount_remove()` reports the last mount.
- `fuse_get_tree()` and `virtio_fs_get_tree()` call `fuse_mount_destroy()` on
  the fresh mount when `fsc->s_fs_info` is still set, that is when no new
  superblock consumed it.
