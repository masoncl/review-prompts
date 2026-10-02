- Check after the folio lock: `folio_matches_swap_entry()` in `mm/swap.h`.
  It compares `folio->swap` with the entry rounded down to the folio size,
  so a large folio that covers the entry matches; a plain compare of
  `folio->swap.val` with the entry does not.
- Names: there is no swap_free() or swap_free_nr() here; `do_swap_page()`
  drops the count with `folio_put_swap()`.
- Order, under folio lock and PTL: `arch_swap_restore()`, rmap add,
  `folio_put_swap()`, `set_ptes()`, `folio_free_swap()` if
  `should_try_to_free_swap()`, `folio_unlock()`.
- `folio_put_swap()` before `set_ptes()`: frees no slot even at count 0. It
  calls `swap_put_entries_cluster()` with `reclaim_cache` false, and that
  function leaves slots that hold a folio to `__swap_cache_del_folio()`.
- Large folio whose PTE range check fails under the PTL, folio already
  anon: one page is mapped.
- Large folio whose PTE range check fails under the PTL, folio not anon:
  `swap_cache_del_folio()` removes it and the fault returns without
  mapping.
