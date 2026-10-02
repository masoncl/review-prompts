- Order in `evict()`: `inode_io_list_del()`, `inode_sb_list_del()`, then under
  `i_lock` `inode_wait_for_lru_isolating()` and `inode_wait_for_writeback()`,
  the method, `cd_forget()` for a character device, `remove_inode_hash()`,
  `inode_wake_up_bit()` on `__I_NEW`, `destroy_inode()`.
- Waited for before the method: `I_LRU_ISOLATING` and `I_SYNC`; after it:
  nothing.
- Final `inode_wake_up_bit()`: called without `i_lock`; it changes no flag,
  and it wakes only `__wait_on_freeing_inode()` sleepers, which abort their
  sleep if they find the inode unhashed.
- `clear_inode()`: has `BUG_ON()` for `nrpages`, missing `I_FREEING`, `I_CLEAR`
  already set, and a non-empty `i_wb_list`.
- Metadata buffers: there is no i_private_list and no
  invalidate_inode_buffers() here; the buffer-list helpers, for example
  `mmb_invalidate()` and `mmb_sync()`, are in `fs/buffer.c`. A filesystem that
  keeps a `struct mapping_metadata_bhs` empties it with `mmb_invalidate()` in
  its own eviction method, as `ext2_evict_inode()` does; `clear_inode()` does
  not check it.
