- Condition in `dax_iomap_iter()`: `IOMAP_F_NEW` set in `iomap->flags`, or a
  write with `IOMAP_F_SHARED` set; `iomap->type` plays no part, so
  `IOMAP_UNWRITTEN` alone does not trigger it.
- `IOMAP_F_NEW` half of the condition: not combined with the direction of the
  iter; only the `IOMAP_F_SHARED` half requires a write.
- Function: `invalidate_inode_pages2_range()` on `inode->i_mapping`; for a DAX
  mapping it calls `dax_invalidate_mapping_entry_sync()` on each value entry
  (`mm/truncate.c`). Its return value is ignored.
- CoW write only: `__dax_clear_dirty_range()` runs first on the same range and
  clears both `PAGECACHE_TAG_DIRTY` and `PAGECACHE_TAG_TOWRITE`.
- `IOMAP_F_NEW` without `IOMAP_F_SHARED`: no mark is cleared, and
  `__dax_invalidate_entry()` with `trunc` false leaves an entry that has either
  mark in place.
