- `wbc_to_tag()`: static inline in `include/linux/writeback.h`.
- Folio handed out: dirty flag already cleared by `folio_clear_dirty_for_io()`
  in `folio_prepare_writeback()`; `PAGECACHE_TAG_DIRTY` is still set.
- Lock on the handed-out folio: owned by the caller; `writeback_iter()` never
  unlocks a folio it returned, on any path.
- First call: zeroes both `*error` and `wbc->saved_err`, so a value the
  caller put in `*error` beforehand is lost.
- `*error` passed back in: must be 0 or negative; a positive value hits
  `WARN_ON_ONCE()`.
- There is no err field in `struct writeback_control`; the first error goes
  in `wbc->saved_err`, and only under `WB_SYNC_ALL`.
- `WB_SYNC_ALL`: never stops early, neither on error nor on
  `wbc->nr_to_write`; at the end `*error` is overwritten with
  `wbc->saved_err`.
- Any other `sync_mode`, `tagged_writepages` included: stops on the first
  non-zero `*error` or `wbc->nr_to_write <= 0`; `*error` is left as the
  caller set it and `saved_err` stays 0.
- Breaking out of the loop: skips `folio_batch_release()` on `wbc->fbatch`
  (folio references leak), the `mapping->writeback_index` update, and the
  copy of `saved_err` into `*error`.
