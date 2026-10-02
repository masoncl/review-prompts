- `PAGECACHE_TAG_DIRTY`: within `mm/`, cleared only by
  `__folio_start_writeback()`, and only when `folio_test_dirty()` is false at
  that moment; otherwise it goes when the entry leaves the cache (for
  example `xas_init_marks()` in `page_cache_delete()`).
- `folio_clear_dirty_for_io()`, `__folio_cancel_dirty()` and
  `__folio_end_writeback()`: none clears `PAGECACHE_TAG_DIRTY`.
- After `folio_clear_dirty_for_io()`: flag clear, tag still set, until
  writeback is started or `__folio_mark_dirty()` runs again.
- Dropping a stale tag on a clean folio: done by cycling
  `__folio_start_writeback(folio, false)` then `folio_end_writeback()` with
  no I/O, for example `mpage_prepare_extent_to_map()` in `fs/ext4/inode.c`
  and `netfs_kill_dirty_pages()`.
- `tag_pages_for_writeback()`: run by the first `writeback_iter()` call when
  `wbc->sync_mode == WB_SYNC_ALL` or `wbc->tagged_writepages`, so also for
  `WB_SYNC_NONE` with `tagged_writepages`.
- Mapping with `AS_NO_WRITEBACK_TAGS`: `__folio_start_writeback()` and
  `__folio_end_writeback()` set and clear the writeback flag but no tag, and
  `keep_write` is ignored. Only `swap_space` in `mm/swap_state.c` sets it.
