- `filemap_map_folio_range()` in `mm/filemap.c`: raises the mapcount before
  the reference count. It calls `set_pte_range()` and only then
  `folio_ref_add(folio, count - ref_from_caller)`, with the folio locked and
  the PTL held.
- In that window: `folio_ref_count()` >= `folio_mapcount()` still holds
  through the page cache references, but the count is below
  `folio_expected_ref_count()` plus the held references when
  `count - ref_from_caller` > 0.
- `mm/memory.c` callers take the reference first, for example
  `finish_fault()`, `copy_present_ptes()`, `insert_page_into_pte_locked()`.
- Two unlocked reads bound nothing, in either order: an unmap between the
  reads lowers both counts, a map raises both, so the second value can be
  lower or higher than what matched the first.
- Stable comparison, large anon folio: `__wp_can_reuse_large_anon_folio()`
  compares under `folio_lock_large_mapcount()`; that is also the only place
  that asserts `folio_large_mapcount()` <= `folio_ref_count()`, with
  `VM_WARN_ON_ONCE_FOLIO()`.
- Stable comparison, one PTE: `write_protect_page()` in `mm/ksm.c` compares
  after `ptep_clear_flush()` under the PTL, so GUP-fast cannot find the page
  through that PTE.
