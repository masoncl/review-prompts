- `FUSE_NOWRITE`: `INT_MIN`; `fuse_set_nowrite()` adds it to
  `fi->writectr` as a bias and does not overwrite the counter.
- `fi->writectr`: `fuse_send_writepage()` increments it before it decides
  to send, and decrements it again at `out_free` for a request it finishes
  unsent.
- `fuse_flush()`: does not use the pair; users are `fuse_open()`,
  `fuse_do_setattr()` and `fuse_sync_writes()`.
- `__fuse_release_nowrite()`: static in `fs/fuse/dir.c`, needs `fi->lock`
  held, and may drop and retake it through `fuse_flush_writepages()`.
- **Unsafe usage**: calling `fuse_set_nowrite()` without the inode lock.
  - Unsafe: `BUG_ON(!inode_is_locked(inode))` fires.
  - Safe: under `inode_lock()`, as `fuse_fsync()` and `fuse_open()` do.
- **Unsafe usage**: a second `fuse_set_nowrite()` before the release.
  - Unsafe: `BUG_ON(fi->writectr < 0)` fires; `inode_is_locked()` is also
    true for a shared hold, so the first check does not exclude this.
  - Safe: one pair at a time under exclusive `inode_lock()`, as
    `fuse_fsync()` does.
- **Unsafe usage**: `fuse_release_nowrite()` with no completed
  `fuse_set_nowrite()` before it.
  - Unsafe: `BUG_ON(fi->writectr != FUSE_NOWRITE)` in
    `__fuse_release_nowrite()` fires.
  - Safe: release after `fuse_set_nowrite()` returned, as
    `fuse_sync_writes()` does.
- **Unsafe usage**: returning between set and release without the release.
  - Unsafe: `fuse_flush_writepages()` sends nothing while `fi->writectr` is
    negative, so later requests stay queued and their folios stay under
    writeback.
  - Safe: release on the error path too, as the `error` label of
    `fuse_do_setattr()` does.
- **Unsafe usage**: waiting for folio writeback between set and release,
  for example with `truncate_pagecache()` or `invalidate_inode_pages2()`.
  - Unsafe: a request queued during the block is never sent, so
    `folio_wait_writeback()` in `fuse_launder_folio()` never returns.
  - Safe: release first, then truncate or invalidate, as
    `fuse_do_setattr()` and `fuse_open()` do.
