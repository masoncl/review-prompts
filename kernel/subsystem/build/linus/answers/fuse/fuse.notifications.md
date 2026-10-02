- State test: in `fuse_dev_do_write()`, not in `fuse_notify()`; `-EINVAL`
  unless `fch->initialized` and `fch->connected` (fields of
  `struct fuse_chan`).
- `fch->initialized`: set by `fuse_chan_set_initialized()`, which
  `process_init_reply()` calls for a failed INIT too, and `fuse_chan_abort()`
  calls after clearing `fch->connected`.
- The test is lockless and made once; a handler can run while
  `fuse_chan_abort()` runs.
- Only `fuse_dev_do_write()` calls `fuse_notify()`; virtio-fs and the io_uring
  commit path deliver no notifications.
- `fuse_copy_finish()`: `fuse_dev_do_write()` calls it after `fuse_notify()`
  returns, so a handler may return without it; for example
  `fuse_notify_store()` and `fuse_notify_prune()` have no call of their own.
- Handlers that call `fuse_copy_finish()` themselves do so after their last
  copy and before they take a lock, for example `fuse_notify_inval_inode()`
  before `fc->killsb`.
- `fuse_ilookup()`: warns unless `fc->killsb` is held; the inode is kept by
  the reference it returns, dropped with `iput()`.
- Kinds other than `FUSE_NOTIFY_INVAL_ENTRY` and `FUSE_NOTIFY_DELETE`:

| Code | Held while the inode is used |
|---|---|
| `FUSE_NOTIFY_POLL` | no inode; `fc->lock` in `fuse_notify_poll_wakeup()` |
| `FUSE_NOTIFY_INVAL_INODE` | `fc->killsb` read; `fi->lock` only around the `attr_version` bump; no `inode_lock()`, also for the range case |
| `FUSE_NOTIFY_STORE` | `fc->killsb` read, held across the copy from the server; folio lock per folio; `fi->lock` inside `fuse_write_update_attr()`; no `inode_lock()` |
| `FUSE_NOTIFY_RETRIEVE` | `fc->killsb` read; folio references only, no folio lock |
| `FUSE_NOTIFY_PRUNE` | `fc->killsb` read, taken per batch of 512 node ids; inode reference only |
| `FUSE_NOTIFY_RESEND` | no inode; `fch->lock` with `fpq->lock` nested, then `fiq->lock` alone |
| `FUSE_NOTIFY_INC_EPOCH` | no inode, no lock; `atomic_inc()` on `fc->epoch`, `schedule_work()` if `inval_wq` |
