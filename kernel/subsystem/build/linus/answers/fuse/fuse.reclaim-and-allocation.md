- `fuse_writepage_args_alloc()` and `fuse_pages_realloc()`: plain
  `GFP_NOFS`, no `__GFP_NOFAIL`; on failure
  `fuse_iomap_writeback_range()` returns `-ENOMEM` or sends what it has.
- `fuse_send_writepage()`: entered with `fi->lock` held; first try is
  `GFP_ATOMIC`; only on `-ENOMEM` it drops `fi->lock` and retries with
  `GFP_NOFS | __GFP_NOFAIL`.
- gfp argument of `fuse_simple_background()`: used only when `args->force`
  is set; otherwise `fuse_get_req()` allocates with `GFP_KERNEL` and may
  sleep on `fch->blocked_waitq`.
- `fuse_simple_request()`: `GFP_KERNEL | __GFP_NOFAIL` only for a forced
  request, in `fuse_chan_send()`; there is no preallocated
  `struct fuse_req`.
- `fuse_file_alloc()`: allocates `ff->args`, a `union fuse_file_args`, with
  `GFP_KERNEL_ACCOUNT`; it can fail, and `fuse_file_open()` then returns
  `-ENOMEM`.
- `fuse_file_open()` for a regular file: allocates `ff->args` even with
  `fc->no_open`, when no RELEASE is sent; `fuse_prepare_release()` keeps the
  inode reference there until the last `fuse_file_put()`, for example the
  one from `fuse_readpages_end()`.
- `AS_WRITEBACK_MAY_DEADLOCK_ON_RECLAIM`: `fuse_init_file_inode()` sets it
  only when `fc->writeback_cache`.
- **Potentially unsafe usage**: allocating with `__GFP_FS` after folio
  writeback has started and before the WRITE is queued.
  - Unsafe: outside a `memalloc_nofs_save()` scope; reclaim may reach
    `folio_wait_writeback()` in `shrink_folio_list()` for a mapping without
    `AS_WRITEBACK_MAY_DEADLOCK_ON_RECLAIM`, on a folio whose WRITE the
    allocating task has not yet queued.
  - Safe: `GFP_NOFS`, as `fuse_writepage_args_alloc()` and
    `fuse_pages_realloc()` use; `may_enter_fs()` in `mm/vmscan.c` is what
    keeps reclaim from waiting.
  - Safe: `GFP_KERNEL` between `memalloc_nofs_save()` and
    `memalloc_nofs_restore()`, as `virtio_fs_request_dispatch_work()` does
    around `virtio_fs_enqueue_req()`; `current_gfp_context()` clears
    `__GFP_FS` from the mask that reclaim sees.
