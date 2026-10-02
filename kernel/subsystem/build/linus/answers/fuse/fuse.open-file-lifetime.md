- Synchronous RELEASE at close: `fuse_file_release()` passes
  `fc->auto_submounts` to `fuse_file_put()`; only `fs/fuse/virtio_fs.c` sets
  that field.
- `fc->destroy`: not read on the release path; a fuseblk close sends RELEASE
  in the background.
- `fuse_sync_release()`: always synchronous; used on the error paths of
  `fuse_open()` and `fuse_create_open()`, and for every close of a CUSE file
  in `cuse_release()`.
- Inode pin: `fuse_prepare_release()` does the `igrab()` into `ra->inode`,
  when its own `sync` argument is false.
- The `sync` of `fuse_prepare_release()` and the `sync` of `fuse_file_put()`
  are separate: a virtiofs close pins the inode and still sends
  synchronously.
- `fuse_release_end()`: only `iput(ra->inode)` and `kfree(ra)`; there is no
  fuse_mount_put() in this tree.
- `ff->args`: NULL only for a directory on a server with `fc->no_opendir`;
  `fuse_file_open()` allocates it for every regular file, also with
  `fc->no_open`.
- `fc->no_open`: `fuse_file_put()` sends no RELEASE but still calls
  `fuse_release_end()`, so the inode stays pinned until the last reference
  drops.
- `fuse_file_get()`: three callers, `fuse_send_readpages()` (async only),
  `__fuse_write_file_get()` and `fuse_iomap_writeback_range()`; direct I/O,
  sync or async, takes no `struct fuse_file` reference.
- Writeback: each `struct fuse_writepage_args` gets its own reference in
  `fuse_iomap_writeback_range()`; the one from `fuse_write_file_get()`
  belongs to the walk and is dropped in `fuse_iomap_writeback_submit()`.
- `fuse_file_io_release()`: called from `fuse_file_put()` on the last
  reference and only when `ra->inode` is set, not from
  `fuse_file_release()`; the I/O mode count outlives `->release` while
  requests are in flight.
- `fuse_sync_release()` path: `ra->inode` is NULL, so
  `fuse_file_io_release()` is not called.
- `fuse_prepare_release()` does not fill `release_flags`, `lock_owner` or
  `args->end`; `fuse_file_release()` fills the first two when `ff->flock` is
  set, `fuse_file_put()` sets `args->end` in the background branch.
- `FUSE_RELEASE_FLUSH`: never set under `fs/fuse/`.
- `struct fuse_file` is freed with `kfree()`, with no RCU delay.
