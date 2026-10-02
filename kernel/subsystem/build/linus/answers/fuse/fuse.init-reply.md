- `process_init_reply()` ends in `fuse_chan_set_initialized()`: with a
  `struct fuse_chan_param` when accepted, with NULL when refused; there is
  no fuse_set_initialized().
- `fch->minor`, `fch->max_write`, `fch->max_pages`: copies that
  `fs/fuse/dev.c` and `fs/fuse/dev_uring.c` use; they are set only by an
  accepted reply and stay 0 after a refusal.
- `fc->minor`: stored as the server sent it, not clamped to
  `FUSE_KERNEL_MINOR_VERSION`.
- Major mismatch: refuses the reply; the kernel never sends a second INIT.
- Reply refused when: request error; `arg->major != FUSE_KERNEL_VERSION`;
  `FUSE_MAP_ALIGNMENT` fails `fuse_dax_check_alignment()` (`CONFIG_FUSE_DAX`);
  `FUSE_ALLOW_IDMAP` without `fc->default_permissions`.
- The last two refusals come after feature bits and `fm->sb` fields were
  set; those are not rolled back.
- `FUSE_DEV_IOC_SYNC_INIT`: sets `fud->sync_init`; returns `-EINVAL` once
  `fud->chan` is set; `fuse_fill_super_common()` copies it to
  `fc->sync_init`.
- Synchronous INIT: `process_init_reply()` runs in the mounting task,
  called by `fuse_send_init()` after `fuse_simple_request()` returns.
- `fuse_send_init()` returns `-ENOTCONN` when `fc->conn_error` is set after
  it ran `process_init_reply()` itself: sync INIT refused or failed, or the
  background send failed to queue.
- Background INIT that was queued: `fuse_send_init()` returns 0; a later
  refusal does not fail the mount.
- `virtio_fs_fill_super()`: ignores the return value of `fuse_send_init()`.
