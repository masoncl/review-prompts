- `dax_fault_is_synchronous()`: tests `IOMAP_WRITE`, `VM_SYNC` and
  `IOMAP_F_DIRTY` only; it does not call `dax_synchronous()`.
- `dax_synchronous()`: not tested at fault time; `daxdev_mapping_supported()`
  tests it at mmap time.
- Entry when `dax_iomap_fault()` returns `VM_FAULT_NEEDDSYNC`:
  `dax_insert_entry()` computed `dirty` as false, so it set no
  `PAGECACHE_TAG_DIRTY` and skipped `__mark_inode_dirty()`.
- `dax_finish_sync_fault()`: calls `vfs_fsync_range()` itself, then
  `dax_insert_pfn_mkwrite()`; the filesystem does not fsync first.
- Locks around `dax_finish_sync_fault()`: in-tree callers hold the fault lock
  across it. `ext4_dax_huge_fault()` calls it after `ext4_journal_stop()` and
  before `filemap_invalidate_unlock_shared()`; `xfs_dax_fault_locked()` runs
  under the caller's `XFS_MMAPLOCK_SHARED` or `XFS_MMAPLOCK_EXCL`.
- `dax_insert_pfn_mkwrite()`: returns `VM_FAULT_NOPAGE` when the entry is
  gone, is of a smaller order than asked, or is a PMD entry at order 0.
- `dax_insert_pfn_mkwrite()`: does not test for a zero or empty entry, and
  does not compare the entry with the `pfn` it is given.
- `daxdev_mapping_supported()` in `include/linux/dax.h`: takes a
  `const struct vm_area_desc *`, the inode and the `struct dax_device`, and
  tests `VMA_SYNC_BIT` with `vma_desc_test()`.
- `daxdev_mapping_supported()` caller: the filesystem's `mmap_prepare`
  handler, not `mm/mmap.c`; see `ext4_file_mmap_prepare()`.
- Without `CONFIG_DAX`: `daxdev_mapping_supported()` is a stub that refuses
  every mapping with `VMA_SYNC_BIT`.
- Gate in `do_mmap()`: `MAP_SHARED_VALIDATE` with `MAP_SYNC` returns
  `-EOPNOTSUPP` unless `f_op->fop_flags` has `FOP_MMAP_SYNC`.
- There is no mmap_supported_flags member in this tree.
