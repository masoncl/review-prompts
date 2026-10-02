- `iput()` fast path: `atomic_add_unless(&inode->i_count, -1, 1)`; only a
  count of 1 goes on to `i_lock` and `atomic_dec_and_test()`; it does not call
  `atomic_dec_and_lock()`.
- Lazytime before the last drop: `iput()` calls `sync_lazytime()` when
  `i_nlink` is nonzero and retries if it returned true; `sync_lazytime()`
  returns false when `I_DIRTY_TIME` is clear, otherwise it calls
  `->sync_lazytime` of `struct inode_operations` if set, else
  `mark_inode_dirty_sync()`.
- `inode_generic_drop()`: what `iput_final()` calls when `->drop_inode` is
  NULL; static inline in `include/linux/fs.h`, true for `!i_nlink` or
  `inode_unhashed()` only; `I_DONTCACHE` is tested by `iput_final()`.
- Old helper names generic_drop_inode and generic_delete_inode: not in this
  tree.
- Inode kept: drop returned 0, `I_DONTCACHE` clear and `SB_ACTIVE` set;
  `iput_final()` then calls `__inode_lru_list_add(inode, true)`; there is no
  inode_add_lru() here, the non-static form is `inode_lru_list_add()`.
- `I_REFERENCED`: set by `__inode_lru_list_add()` only when called with
  `rotate` true, which only `iput_final()` does, and the inode was already on
  the LRU.
- Writeback before eviction: only when drop returned 0 (so `I_DONTCACHE` is
  set or `SB_ACTIVE` is clear); `write_inode_now(inode, 1)` runs under
  `I_WILL_FREE`, then `inode_state_replace()` swaps it for `I_FREEING`.
- `i_count` recheck after `->drop_inode`: `iput_final()` makes it only on the
  evict path and only with `CONFIG_DEBUG_VFS`; on the cache path
  `__inode_lru_list_add()` just declines a nonzero count.
