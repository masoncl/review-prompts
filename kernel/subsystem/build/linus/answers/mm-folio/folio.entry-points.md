Rows for add, remove, lock, take a reference, mark dirty and truncate are
omitted: they are the functions models expect.

| Job | Start reading from | Easy to miss |
|---|---|---|
| Look up in the page cache | `__filemap_get_folio_mpol()` in `mm/filemap.c` | `__filemap_get_folio()` is a `static inline` in `include/linux/pagemap.h` that passes a NULL policy to it; `mm/filemap.c` does not define `__filemap_get_folio()`. |
| Drop a reference | `folio_put()` in `include/linux/mm.h` | Last reference goes to `__folio_put()` in `mm/folio.c`, not mm/swap.c. |
| Put on the LRU | `folio_add_lru()` in `mm/folio.c` | There is no lru_cache_add() here. |
| Start writeback | `__folio_start_writeback()` in `mm/page-writeback.c` | `folio_start_writeback()` is a macro in `include/linux/page-flags.h` that passes `keep_write` as `false`; there is no second wrapper for `true`. |
| End writeback | `folio_end_writeback()` in `mm/filemap.c` | It calls `folio_end_writeback_no_dropbehind()`, which is what calls `__folio_end_writeback()`; then it calls `folio_end_dropbehind()`. |
| Invalidate, best effort | `mapping_try_invalidate()` in `mm/truncate.c` | Per folio: `mapping_evict_folio()`. |
| Invalidate, hard | `invalidate_inode_pages2_range()` in `mm/truncate.c` | Per folio: `folio_unmap_invalidate()`, not `mapping_evict_folio()`. |
