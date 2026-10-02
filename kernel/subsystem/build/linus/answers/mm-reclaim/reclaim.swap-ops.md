- `struct swap_ops` is in `include/linux/swap_ops.h`; each device points at one
  through `si->ops`.
- `flags`: only `SWAP_OPS_F_REQUIRE_NOFS` exists; `may_enter_fs()` reads it.
- `can_merge()`: whether a folio may join the batch after the previous folio.
- `submit_write()` and `submit_read()`: send the whole batch `ctx->sio` to
  `ctx->sis`.
- All three hooks are called with no NULL test, by `swap_can_merge()`,
  `swap_write_submit()` and `swap_read_submit()`.
- Not decided by `struct swap_ops`: `SWP_SYNCHRONOUS_IO`, `SWP_BLKDEV` and
  `SWP_STABLE_WRITES` stay in `si->flags`; `swap_activate` and
  `swap_deactivate` stay in `struct address_space_operations`.
- There is no SWP_FS_OPS flag and no swap_rw method in this tree.
- `setup_swap_extents()`: installs `swap_bdev_ops` on every device before it
  calls `->swap_activate()`.
- `swap_fs_activate()`: called from a filesystem's `->swap_activate()`, it
  replaces `si->ops` and adds one extent for the whole file; for example
  `nfs_swap_activate()`.
- A swap file whose `->swap_activate()` only adds extents, or that goes through
  `generic_swapfile_activate()`, keeps `swap_bdev_ops` and gets bios to
  `si->bdev`.
- A filesystem submit hook calls `swap_fs_prepare_rw()`, then must call
  `sio->iocb.ki_complete()` itself when the I/O call returns anything but
  `-EIOCBQUEUED`, as `nfs_swap_submit_write()` does.
- `ctx->sio` and `ctx->sis` are cleared as soon as the hook returns; the
  completion handler frees the `struct swap_iocb` to `sio_pool`.
