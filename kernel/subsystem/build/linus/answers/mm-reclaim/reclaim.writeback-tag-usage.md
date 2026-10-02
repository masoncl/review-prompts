- There is no folio_start_writeback_keepwrite here; callers pass `true` to
  `__folio_start_writeback()` directly. `folio_start_writeback()` is a macro
  in `include/linux/page-flags.h` that passes `false`.
- `__folio_start_writeback()`: asserts that the folio is locked and not
  under writeback (`VM_BUG_ON_FOLIO()`), not that it is clean; when the
  dirty flag is set, `PAGECACHE_TAG_DIRTY` is kept too.
- `keep_write` true is not tied to the dirty flag: on a clean folio the DIRTY
  tag is cleared and `PAGECACHE_TAG_TOWRITE` stays, stale, until a later
  start with `false`, removal from the cache, or a clear by hand.
- A `writeback_iter()` walk that finds a clean folio by a stale TOWRITE
  skips it: see the `folio_test_dirty()` test in
  `folio_prepare_writeback()`.
- **Unsafe usage**: starting writeback with `keep_write` false (which
  `folio_start_writeback()` always does) on a folio that keeps data
  unwritten that was dirty when the writer took it; a `WB_SYNC_ALL` walk
  that tagged the folio earlier follows TOWRITE only and never visits it.
  - Safe: redirty, then pass `true` only when something stays dirty, as
    `ext4_bio_write_folio()` does with its `keep_towrite`; the requirement
    comes from `wbc_to_tag()`.
  - Safe: always pass `true` and clear DIRTY and TOWRITE by hand once the
    folio is no longer dirty, as `btrfs_subpage_set_writeback()` does with
    `folio_clear_tags()`.
