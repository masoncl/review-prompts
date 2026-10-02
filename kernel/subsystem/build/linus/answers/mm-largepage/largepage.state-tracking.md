- Anon exclusive, PMD-mapped or hugetlb: the head page's `PG_anon_exclusive`
  is the state itself, not a hint; no other copy exists while mapped.
- Anon exclusive, not mapped: kept in the entry, by `pte_swp_mkexclusive()`
  for swap (see `swp_pte_prepare()` in `mm/rmap.c`) and by the migration
  entry type for migration.
- Hardware poison, hugetlb: `hugetlb_update_hwpoison()` in
  `mm/memory-failure.c` sets `PG_hwpoison` on the head page and records the
  bad page in the list at `folio->_hugetlb_hwpoison`.
- `PG_has_hwpoisoned`: needs both `CONFIG_MEMORY_FAILURE` and
  `CONFIG_TRANSPARENT_HUGEPAGE`; otherwise the test is constant `false`.
- Mapcount under `CONFIG_NO_PAGE_MAPCOUNT`: `page->_mapcount` of pages in a
  large folio and `folio->_nr_pages_mapped` are not maintained; see
  `__folio_add_rmap()`.
- `folio_precise_page_mapcount()` in `fs/proc/internal.h`: `BUILD_BUG()`
  without `CONFIG_PAGE_MAPCOUNT`.
- `_mm_id_mapcount[]` and `_mm_ids`: maintained only under `CONFIG_MM_ID`,
  which `CONFIG_TRANSPARENT_HUGEPAGE` selects.
- `_entire_mapcount` and `_pincount` on 32-bit: in the third page of
  `struct folio`, so an order-1 folio has none and `folio_entire_mapcount()`
  returns 0 for it.
