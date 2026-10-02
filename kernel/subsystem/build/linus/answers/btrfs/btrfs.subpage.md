- `struct btrfs_folio_state` in `fs/btrfs/subpage.h`: the per-block state;
  there is no struct btrfs_subpage.
- Members: `lock`, a union of `eb_refs` (metadata) and `nr_locked` (data),
  and `bitmaps[]`.
- Bitmaps: uptodate, dirty, writeback, fixup, numbered up to
  `btrfs_bitmap_nr_max`.
- No ordered, checked or locked bitmap, no ordered helper and no ordered folio
  flag exist.
- `btrfs_invalidate_folio()`: uses `btrfs_folio_test_dirty()` to find the
  blocks of an ordered extent that were never submitted.
- `btrfs_is_subpage()`: `fs_info->sectorsize < folio_size(folio)`, so true for
  a large folio when block size equals page size; asserts a data inode.
- `btrfs_meta_is_subpage()`: `fs_info->nodesize < PAGE_SIZE`, for metadata.
- Fixup bit: a block dirtied with no space reservation; `writepage_fixup()`
  withholds it and `btrfs_writepage_fixup_worker()` reserves for it.
- `folio_test_fixup_pending()` in `fs/btrfs/fs.h`: the whole fixup state of a
  single-block folio; set on a multi-block folio while any fixup bit is set.
- `nr_locked`: a count only. `btrfs_folio_end_lock()` and
  `btrfs_folio_end_lock_bitmap()` subtract what the caller passes, so the
  blocks must be the ones `btrfs_folio_set_lock()` counted.
- **Potentially unsafe usage**: `folio_mark_dirty()` on a data folio.
  - Unsafe: from a path that reserved space. It reaches
    `btrfs_data_dirty_folio()`, which marks every clean block up to `i_size`
    dirty and fixup (on a multi-block folio only if the folio is uptodate);
    writeback withholds them and the worker sets delalloc again, or under
    `CONFIG_BTRFS_DEBUG` hits `DEBUG_WARN()` and clears the bit.
  - Safe: `btrfs_folio_set_dirty()` after the reservation, as
    `btrfs_page_mkwrite()` does; it clears the fixup bits and calls
    `filemap_dirty_folio()`.
  - Safe: a dirtier with no reservation, such as the GUP pin release in
    `unpin_user_pages_dirty_lock()`; `btrfs_data_dirty_folio()` exists for
    it, and `writepage_fixup()` needs the fixup bit to withhold the block.
- **Unsafe usage**: clearing a fixup bit and leaving the block dirty with no
  reservation.
  - Safe: `btrfs_folio_clear_fixup()` after delalloc is set, as
    `btrfs_writepage_fixup_worker()` does.
  - Safe: `btrfs_folio_clear_fixup_dirty()` when the data is discarded, as
    `btrfs_invalidate_folio()` does; it drops only blocks fully inside the
    range.
- **Potentially unsafe usage**: `folio_test_uptodate()` or
  `folio_test_dirty()` on a folio with several blocks.
  - Unsafe: to decide about one block; the flag is for the whole folio.
  - Safe: a whole-folio test, as `prepare_uptodate_folio()` in
    `fs/btrfs/file.c`; `btrfs_subpage_set_uptodate()` sets the flag only when
    every block is uptodate.
  - Safe: `btrfs_folio_test_dirty()` with the block's range, as
    `btrfs_invalidate_folio()` does.
