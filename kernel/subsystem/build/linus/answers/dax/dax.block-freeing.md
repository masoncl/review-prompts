- `dax_break_layout()`: asserts no lock itself; `xfs_break_dax_layouts()` and
  `ext4_break_layouts()` check only the fault-blocking lock, and
  `fuse_dax_break_layouts()` checks none.
- `xfs_break_dax_layouts()`: defined in `fs/xfs/xfs_inode.c`; asserts
  `XFS_MMAPLOCK_EXCL`.
- `ext4_break_layouts()`: returns `-EINVAL` with a warning when
  `mapping->invalidate_lock` is not locked; the test is `rwsem_is_locked()`,
  which does not tell shared from exclusive.
- `i_rwsem`: held by the truncate and fallocate callers, but not everywhere;
  `xfs_break_layouts()` asserts the IOLOCK in either mode, and
  `lookup_and_reclaim_dmap()` in `fs/fuse/dax.c` holds only
  `mapping->invalidate_lock` across the call and takes `fi->dax->sem` for
  write afterwards, around the reclaim.
- ext4 call sites: `ext4_break_layouts()` is called in `ext4_fallocate()` once,
  under `filemap_invalidate_lock()`, before the mode switch, and in
  `ext4_setattr()`; `ext4_punch_hole()`, `ext4_collapse_range()`,
  `ext4_insert_range()` and `ext4_zero_range()` rely on that caller.
- ext4 scope: every fallocate mode except `FALLOC_FL_ALLOCATE_RANGE`, and every
  `ATTR_SIZE` change, growing included.
- XFS scope: `__xfs_file_fallocate()` breaks layouts for every mode, and
  `xfs_vn_setattr()` for every `ATTR_SIZE`; `xfs_zone_gc_finish_chunk()` does
  it before remapping garbage-collected blocks.
- XFS two-inode operations: `xfs_ilock2_io_mmap()` breaks DAX layouts only when
  both inodes are DAX; otherwise it takes the two invalidate locks with
  `filemap_invalidate_lock_two()` and breaks no DAX layout. Its callers are
  found by searching for the name.
- fuse scope: `fuse_do_setattr()` on `ATTR_SIZE`, `fuse_open()` on an atomic
  `O_TRUNC`, `fuse_file_fallocate()` when its `block_faults` is set, and dmap
  reclaim, which passes one dmap's byte range instead of the whole file.
