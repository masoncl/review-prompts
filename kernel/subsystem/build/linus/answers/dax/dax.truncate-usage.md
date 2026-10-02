- `truncate_folio_batch_exceptionals()`: treats any value entry found in a DAX
  mapping as an error; it does `WARN_ON_ONCE(1)` and then calls
  `dax_delete_mapping_entry()`.
- Comment in `truncate_folio_batch_exceptionals()`: names
  dax_break_layout_entry(), which is defined nowhere; `dax_break_layout()` is
  the function meant.
- `invalidate_inode_pages2_range()`: calls
  `dax_invalidate_mapping_entry_sync()` directly; there is no
  invalidate_exceptional_entry2() in this tree.
- `invalidate_inode_pages2_range()` on a DAX mapping: removes entries first and
  calls `unmap_mapping_pages()` on the whole range only after the loop, also
  when it returns `-EBUSY`.
- **Unsafe usage**: `truncate_inode_pages_range()` on a DAX range that still
  holds entries; it warns and removes them without waiting for references.
  - Safe: after `dax_break_layout()` returned 0, with the fault-blocking lock
    still held, as `fuse_open()` does before `truncate_pagecache()`;
    `truncate_folio_batch_exceptionals()` defines the requirement.
  - Safe: at eviction after `dax_break_layout_final()`, as
    `xfs_fs_evict_inode()` does before `truncate_inode_pages_final()`.
- **Potentially unsafe usage**: `invalidate_inode_pages2_range()` on a DAX
  range.
  - Unsafe: when a clean entry that is neither zero nor empty has a folio
    that still has a reference, from a page table or a pin; the entry is
    disassociated while the folio is in use and `dax_folio_put()` warns on the
    non-zero refcount.
  - Safe: after `dax_break_layout()` returned 0 on the range under
    `mapping->invalidate_lock`, as `lookup_and_reclaim_dmap()` in
    `fs/fuse/dax.c` does before `dmap_writeback_invalidate()`; no entry is
    left to invalidate.
