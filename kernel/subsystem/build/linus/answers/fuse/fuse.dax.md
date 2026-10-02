- `fuse_dax_break_layouts()`: a one-line wrapper around `dax_break_layout()`
  (`fs/dax.c`) with `fuse_wait_dax_page()` as the callback. There is no
  dax_wait_page_idle() in this tree.
- `dax_break_layout()` waits in `TASK_INTERRUPTIBLE`, so
  `fuse_dax_break_layouts()` can fail; all five callers check the result.
- `dax_break_layout()` on success also removes the DAX entries of the range from
  the page cache with `dax_delete_mapping_range()`. It does not touch
  `fi->dax->tree`.
- Truncate frees no `struct fuse_dax_mapping`. Ranges beyond the new size stay in
  the tree until reclaim or `fuse_dax_inode_cleanup()`; `fuse_fill_iomap()`
  reports a hole past `i_size`.
- Whole-file callers pass `0, -1`: `fuse_do_setattr()`, `fuse_open()` and
  `fuse_file_fallocate()`.
- `fuse_file_fallocate()`: breaks layouts for punch hole and zero range, and
  also for every call without `FALLOC_FL_KEEP_SIZE`; see `block_faults`.
- `fuse_setup_one_mapping()`: sends `inarg.fh = -1`, never a file handle.
- `fuse_setup_new_dax_mapping()`: is entered without `fi->dax->sem`. It
  allocates the range first, then takes the lock for write and rechecks the
  tree.
- With `IOMAP_FAULT`, `fuse_setup_new_dax_mapping()` never reclaims inline. It
  returns `-EAGAIN` when no range is free, and `__fuse_dax_fault()` drops the
  invalidate lock, waits on `fcd->range_waitq` and retries.
- `dmap->refcnt`: 1 when idle. Reclaim skips a range when
  `refcount_read(&dmap->refcnt) > 1`.
- `dax_iomap_rw()` is protected from reclaim by `dmap->refcnt`, raised under
  `fi->dax->sem`. No reclaim path takes the inode lock, and read/write takes
  the invalidate lock only inside `inode_inline_reclaim_one_dmap()`.
- The inode lock serialises read/write against truncate, not against reclaim.
- Reclaim functions for a live inode are `inode_inline_reclaim_one_dmap()`
  (inline) and `lookup_and_reclaim_dmap()` (worker); both end in
  `reclaim_one_dmap_locked()`. There is no
  inode_reclaim_one_dax_mapping_locked(), fuse_dax_free_one_mapping() or
  reclaim_one_dmap().
- `fuse_iomap_ops` in `fs/fuse/dax.c`: sets only `.iomap_next`.
  `fuse_iomap_begin()` and `fuse_iomap_end()` are called from
  `fuse_iomap_next()`, which `DEFINE_IOMAP_ITER_NEXT_END()` generates.
