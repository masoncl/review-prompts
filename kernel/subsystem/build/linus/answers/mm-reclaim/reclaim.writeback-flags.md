- `folio_clear_dirty_for_io()` accounting: on a successful test-and-clear it
  decrements `NR_FILE_DIRTY`, `NR_ZONE_WRITE_PENDING`, `WB_RECLAIMABLE`, and
  `WB_DONTCACHE_DIRTY` if `folio_test_dropbehind()`.
- `folio_clear_dirty_for_io()`: does not decrement `NR_DIRTIED` and does not
  call `folio_account_cleaned()`; that helper is for cleaning without
  writeback, for example `__folio_cancel_dirty()`.
- Mapping NULL or `mapping_can_writeback()` false:
  `folio_clear_dirty_for_io()` only test-and-clears the flag; no
  `folio_mkclean()`, no accounting.
- There is no folio_account_redirty() here; `folio_redirty_for_writepage()`
  does the accounting itself.
- `folio_redirty_for_writepage()`: adds the folio's pages to
  `wbc->pages_skipped`; it does not change `wbc->nr_to_write`.
- `folio_redirty_for_writepage()`: subtracts from `current->nr_dirtied`,
  `NR_DIRTIED` and `WB_DIRTIED` even when `filemap_dirty_folio()` returns
  false because the folio was already dirty; `ext4_bio_write_folio()` tests
  `folio_test_dirty()` first.
- `wbc->pages_skipped`: read by `requeue_inode()` and `writeback_sb_inodes()`
  in `fs/fs-writeback.c`; needed because `writeback_iter()` charges
  `nr_to_write` for redirtied folios too.
- `folio_mark_dirty()` on a skipped folio: also restores the flag and the
  tag; it does not add to `pages_skipped` and it counts the folio as newly
  dirtied.
- Redirty and writeback: `folio_redirty_for_writepage()` makes no test of the
  writeback flag; `ext4_bio_write_folio()` redirties and then starts
  writeback. Writeback that was started must still be ended.
- `folio_end_writeback()`: asserts that the writeback flag is set, not that
  the folio is unlocked; the folio may still be locked, as in the
  nothing-to-submit path of `ext4_bio_write_folio()`.
