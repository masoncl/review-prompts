- `fc->conn_error` is tested in `fuse_req_prep()` in `fs/fuse/req.c`, for
  requests without `args->force`, before the request waits for
  `fch->initialized`; `fuse_get_req()` tests only `fch->connected` and
  returns `-ENOTCONN`.
- `fuse_send_init()` is the other reader of `fc->conn_error`.
- `fc->sync_fs` is cleared at run time, by `fuse_sync_fs()` on `-ENOSYS`.
- **Potentially unsafe usage**: storing to a one-bit field of
  `struct fuse_conn` once requests can run.
  - Unsafe: when losing the store changes behaviour; the stores take no lock
    and neighbouring bits share a word, so a concurrent store to another bit
    can undo it.
  - Safe: the bit only caches a `-ENOSYS` reply and the path that finds it
    clear sends the request again, as `fuse_file_open()` does with
    `fc->no_open`.
  - Safe: in `process_init_reply()`; `fuse_get_req()` holds every request
    without `args->force` until `fuse_chan_set_initialized()`.
  - Safe: before the device is installed, as `fuse_fill_super_common()` and
    `virtio_fs_get_tree()` do.
- `connected`, `initialized` and `no_interrupt` are not bit-fields but
  full-width members of `struct fuse_chan`: `connected` is written under
  `fch->lock`, `initialized` with release and acquire, `no_interrupt` is a
  `bool`.
