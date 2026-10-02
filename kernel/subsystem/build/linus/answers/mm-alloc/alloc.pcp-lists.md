- THP order: `pcp_allowed_order()` admits `HPAGE_PMD_ORDER` (through
  `is_pmd_order()`), not `pageblock_order`, and only under
  `CONFIG_TRANSPARENT_HUGEPAGE`.
- THP lists: `NR_PCP_THP` is 2 under `CONFIG_TRANSPARENT_HUGEPAGE`.
  `order_to_pindex()` gives movable its own list; unmovable and reclaimable
  share the other.
- `MIGRATE_HIGHATOMIC` and `MIGRATE_CMA` pages: freed onto the
  `MIGRATE_MOVABLE` per-CPU list by `__free_frozen_pages()` and
  `free_unref_folios()`. Of the migrate types, only `MIGRATE_ISOLATE`
  bypasses the lists, through `free_one_page()`.
- `rmqueue()`: tests only `pcp_allowed_order()` before `rmqueue_pcplist()`;
  it has no `ALLOC_CMA` test.
- Type on drain: `free_pcppages_bulk()` ignores which list a page sat on and
  re-reads `get_pfnblock_migratetype()` per page under `zone->lock`.
- `free_frozen_page_commit()` drain: frees `nr_pcp_free()` pages in chunks of
  `batch`, and drops and re-trylocks the list lock between chunks.
- `free_frozen_page_commit()` return value: false means the lock is no longer
  held (retry failed or task changed CPU).
- `ALLOC_HIGHATOMIC` on an empty list: `__rmqueue_pcplist()` returns NULL
  without refilling, so the request goes to `rmqueue_buddy()`.
- `zone_pcp_disable()`: sets `high_min` and `high_max` to 0 and `batch` to 1,
  then drains every online CPU. `nr_pcp_high()` then returns 0, so each
  `free_frozen_page_commit()` without `FPI_NOLOCK` drains.
