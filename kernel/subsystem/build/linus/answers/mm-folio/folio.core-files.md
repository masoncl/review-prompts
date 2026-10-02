Rows for the folio structure, flag accessors, reference counting, page cache,
truncation and invalidation, and GUP are omitted: they are where models expect.

| Job | File in this tree | Easy to miss |
|---|---|---|
| Release path and per-CPU LRU batches | `mm/folio.c` | There is no mm/swap.c here. `__folio_put()`, `folios_put_refs()`, `release_pages()`, `struct cpu_fbatches`, `folio_add_lru()` and `lru_add_drain()` are all in `mm/folio.c`. `mm/swap.h` is the swap subsystem's private header, not this code. |
| `__folio_put()` hand-offs | `mm/folio.c` | Hands off only zone-device folios (`free_zone_device_folio()`) and hugetlb folios (`free_huge_folio()`). Other large folios take the common path: `folio_unqueue_deferred_split()`, then `free_frozen_pages()`. |
| Batch type | `include/linux/folio_batch.h` | There is no include/linux/pagevec.h here. `struct folio_batch` and its inline helpers are in `include/linux/folio_batch.h`. |
| Batch type, out-of-line helpers | `mm/folio.c` | `__folio_batch_release()` and `folio_batch_remove_exceptionals()`. |
| Writeback | split: `mm/page-writeback.c` and `mm/filemap.c` | `__folio_start_writeback()` and `__folio_end_writeback()` are in `mm/page-writeback.c`; `folio_end_writeback()` is in `mm/filemap.c`. |
| Page-based wrappers | split: `mm/folio-compat.c` and headers | `mm/folio-compat.c` exists and holds the out-of-line wrappers, for example `unlock_page()` and `set_page_dirty()`. Inline wrappers are in headers: `put_page()` and `get_page()` in `include/linux/mm.h`, `lock_page()` in `include/linux/pagemap.h`. |
