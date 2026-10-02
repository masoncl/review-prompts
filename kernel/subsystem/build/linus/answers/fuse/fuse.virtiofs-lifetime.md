- Connection setup in `virtio_fs_get_tree()`: `fuse_chan_new()`, then
  `fuse_iqueue_init(&fch->iq, &virtio_fs_fiq_ops, fs)`, then
  `fuse_conn_init(fc, fm, fsc->user_ns, fch)`. `fuse_conn_init()` takes no ops
  or priv argument.
- The device instance is `fc->chan->iq.priv`; `struct fuse_conn` has no `iq`
  member of its own. `virtio_fs_test_super()` compares that pointer.
- `fc->release` is `fuse_free_conn`, the same as for a `/dev/fuse` mount.
- `struct virtio_fs` is a kobject, not a kref; `virtio_fs_ktype_release()` frees
  it together with `fs->vqs`.
- The connection's reference on `struct virtio_fs` is dropped by the last
  `fuse_conn_put()`, through `fuse_chan_release()` and
  `virtio_fs_fiq_release()`. `virtio_fs_put()` takes `virtio_fs_mutex`.
- **Potentially unsafe usage**: `fuse_dev_put()` or `fuse_conn_put()` with
  `virtio_fs_mutex` held.
  - Unsafe: when it can drop the last `struct fuse_conn` reference;
    `virtio_fs_put()` then locks the mutex again.
  - Safe: on a `struct fuse_dev` that was never installed, as in the error path
    of `virtio_fs_fill_super()`; `fuse_dev_put()` then skips `fuse_conn_put()`.
- `virtio_fs_fill_super()`: rechecks `list_empty(&fs->list)` under
  `virtio_fs_mutex` and fails with `-EINVAL`, because the device may have been
  removed after the lookup.
- Per-queue `struct fuse_dev`: `fuse_dev_alloc()` before
  `fuse_fill_super_common()`, `fuse_dev_install(fsvq->fud, fc->chan)` after it.
  `fuse_dev_alloc_install()` is not used.
- There is no fudptr in `fs/fuse`; `ctx->fud` stays NULL, so
  `fuse_fill_super_common()` installs nothing.
- The `kill_sb` hook is `virtio_kill_sb()`; there is no virtio_fs_kill_sb().
- `virtio_kill_sb()` order: `fuse_mount_remove()`, `virtio_fs_conn_destroy()` if
  that was the last mount, `kill_anon_super()`, `fuse_mount_destroy()`.
- `virtio_fs_conn_destroy()` steps, in order:
  - `fuse_dax_cancel_work()`;
  - `connected = false` on `VQ_HIPRIO` only, then `virtio_fs_drain_all_queues()`;
  - `fuse_conn_destroy()`: sends `FUSE_DESTROY` if `fc->conn_init` is set
    (`ctx->destroy` is forced true), then `fuse_chan_abort()` and
    `fuse_chan_wait_aborted()`;
  - `virtio_fs_stop_all_queues()`, drain again, `virtio_fs_free_devs()`.
- A `/dev/fuse` mount runs only `fuse_conn_destroy()` from `fuse_sb_destroy()`,
  and sets `ctx->destroy` only for fuseblk.
- `virtio_fs_remove()` does not end requests that are in the ring. It waits in
  `virtio_fs_drain_queue()` for the device to complete them, with
  `virtio_fs_mutex` held; a device that never answers blocks removal.
- Requests parked on `queued_reqs` at removal: failed with `-ENOTCONN` when the
  dispatch work resubmits them.
- After removal the connection is not aborted; `fs/fuse/virtio_fs.c` never calls
  `fuse_chan_abort()`. Each later request fails on its own with `-ENOTCONN`;
  forgets are freed.
- `no_control` and `no_force_umount` are forced on in
  `virtio_fs_ctx_set_defaults()`, so neither the control filesystem nor
  `umount -f` can abort the connection.
- `fsvq->vq` after removal: dangling, since `virtio_fs_cleanup_vqs()` deleted
  the virtqueues while `fs->vqs` stays allocated. `fsvq->connected`, tested
  under `fsvq->lock`, is the guard in `virtio_fs_enqueue_req()` and
  `send_forget_request()`.
