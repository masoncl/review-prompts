- `igrab()`: first tries `atomic_add_unless(&inode->i_count, 1, 0)` with no
  lock; it takes `i_lock` and tests `I_FREEING | I_WILL_FREE` only when the
  count is 0.
- `i_count` transitions 0 to 1 and 1 to 0: made only under `i_lock`; every
  other change may be made without it.
- `__iget()` in `include/linux/fs.h`: `lockdep_assert_held()` on `i_lock` and
  an `atomic_inc()`; it does not touch the LRU, `inode_lru_isolate()` removes
  referenced inodes lazily.
- `icount_read()`: asserts `i_lock`; `icount_read_once()` is the lockless
  hint.
- `iput()`: asserts `i_lock` is not held, and under `CONFIG_DEBUG_VFS` that
  neither `I_FREEING` nor `I_CLEAR` is set and the count is at least 1.
- `iput_if_not_last()` in `include/linux/fs.h`: does not sleep; returns
  `false` without dropping when the reference is the last, and the caller
  must then call `iput()` from a context that may sleep.
- **Unsafe usage**: setting `I_FREEING` or `I_WILL_FREE` while `i_count` is
  nonzero or without `i_lock`; `igrab()` and `igrab_from_hash()` take the
  reference on a nonzero count alone, and their `VFS_BUG_ON_INODE()` catches
  it only under `CONFIG_DEBUG_VFS`.
  - Safe: test `icount_read()` under `i_lock`, then set the flag in the same
    hold, as `evict_inodes()` does.
