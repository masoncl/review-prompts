- `_nr_pages_mapped`, with `CONFIG_PAGE_MAPCOUNT`: 0 when unmapped, not -1;
  see `prep_compound_head()` in `mm/internal.h`. It carries
  `ENTIRELY_MAPPED` while a PMD/PUD mapping exists.
- Per-page read: there is no page_mapcount() in this tree.
  `folio_precise_page_mapcount()` in `fs/proc/internal.h` is `BUILD_BUG()`
  without `CONFIG_PAGE_MAPCOUNT`, so each caller tests
  `IS_ENABLED(CONFIG_PAGE_MAPCOUNT)` first and falls back to
  `folio_average_page_mapcount()` or `folio_maybe_mapped_shared()`.
- `CONFIG_PAGE_MAPCOUNT`: `def_bool !NO_PAGE_MAPCOUNT` in `mm/Kconfig`; code
  tests either symbol.
- `CONFIG_NO_PAGE_MAPCOUNT`: selectable only inside
  `if TRANSPARENT_HUGEPAGE`, so `CONFIG_MM_ID` is set with it.
- With `CONFIG_NO_PAGE_MAPCOUNT`: rmap does not change the per-page
  `_mapcount` of a large folio, and `folio_nr_pages_mapped()` returns -1.
- 32-bit order-1 folio: has no `_entire_mapcount`; `folio_entire_mapcount()`
  returns 0 for it.
- hugetlb: its rmap helpers in `include/linux/rmap.h` change only
  `_entire_mapcount` and `_large_mapcount`, both once per mapping;
  `_nr_pages_mapped` and the mm-id fields are not used.
