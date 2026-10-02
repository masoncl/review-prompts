- NULL callback: `dax_break_layout()` returns `-ERESTARTSYS` at the first busy
  page without waiting for it, and leaves the entries in place.
- NULL callback, in-tree use: `xfs_mmaplock_two_inodes_and_break_dax_layout()`
  in `fs/xfs/xfs_inode.c` for the second inode; on error it drops both
  `XFS_MMAPLOCK_EXCL` locks and starts again.
- Entries on return: deleted only when the return value is 0; on any error
  they all stay, although the range has already been unmapped from page
  tables.
- `dax_delete_mapping_range()`: removes entries without testing
  `PAGECACHE_TAG_DIRTY` or `PAGECACHE_TAG_TOWRITE` and flushes nothing.
- `dax_layout_busy_page_range()`: does not lock entries; it waits for a locked
  entry and releases it, so only the caller's lock keeps new faults out.
- Callback: drops only the lock that blocks faults, calls `schedule()`, and
  retakes it; `xfs_wait_dax_page()` drops `XFS_MMAPLOCK_EXCL` and keeps the
  IOLOCK.
- `dax_break_layout_final()` callers: search for the name; `ext4_evict_inode()`
  calls it without an `IS_DAX()` test, and `erofs_evict_inode()` calls it too.
- Order at eviction: each caller runs `dax_break_layout_final()` before
  `truncate_inode_pages_final()`.
