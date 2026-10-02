- `dax_insert_entry()`: has no `dirty` parameter; it computes
  `write && !dax_fault_is_synchronous()` from `iter->flags` and the vma.
- `dax_fault_is_synchronous()`: needs `IOMAP_WRITE`, `VM_SYNC` and
  `IOMAP_F_DIRTY` together, so a `MAP_SYNC` write fault on an iomap without
  `IOMAP_F_DIRTY` is marked `PAGECACHE_TAG_DIRTY` at fault time.
- Synchronous fault: the entry is marked dirty later, not by
  `dax_insert_entry()`; `dax_finish_sync_fault()` calls `vfs_fsync_range()` and
  then `dax_insert_pfn_mkwrite()`, which sets `PAGECACHE_TAG_DIRTY`.
- write(2) through `dax_iomap_rw()`: sets no mark, and `dax_copy_from_iter()`
  uses `_copy_from_iter_flushcache()` only when the device has `DAXDEV_NOCACHE`;
  otherwise it is a plain `_copy_from_iter()`.
- `dax_writeback_one()` does not call `dax_direct_access()`: the pfn is
  `dax_to_pfn(entry)` and the flushed address is
  `page_address(pfn_to_page(pfn))`.
- Write-protect step: between clearing `PAGECACHE_TAG_TOWRITE` and
  `dax_flush()`, it calls `pfn_mkclean_range()` on every vma found by
  `mapping_rmap_tree_foreach()`, under `i_mmap_lock_read()`; there is no
  vma_interval_tree_foreach in this tree.
- Entry found locked: `dax_writeback_one()` calls `get_next_unlocked_entry()`
  (there is no get_unlocked_entry here); the pfn comparison and the test that
  `PAGECACHE_TAG_TOWRITE` is still set are made only in this branch.
- Final unlock: open-coded as `xas_store()`, `xas_clear_mark()` of
  `PAGECACHE_TAG_DIRTY`, `dax_wake_entry()`; it does not call
  `dax_unlock_entry()`.
- `i_pages` lock: `dax_writeback_one()` is entered and returns with it held, on
  the skip path too; it drops it around the write-protect and flush, and
  `get_next_unlocked_entry()` drops it if it sleeps.
- `dax_writeback_mapping_range()` returns without writing in three cases:
  `inode->i_blkbits != PAGE_SHIFT` (`WARN_ON_ONCE()`, `-EIO`), `mapping_empty()`
  (0), `wbc->sync_mode != WB_SYNC_ALL` (0, no warning).
- `dax_writeback_mapping_range()` has no early return on
  `dax_write_cache_enabled()`, `mapping_tagged()` or `wbc->nr_to_write`; with
  `CONFIG_ARCH_HAS_PMEM_API`, `dax_flush()` tests `dax_write_cache_enabled()`
  for each entry.
