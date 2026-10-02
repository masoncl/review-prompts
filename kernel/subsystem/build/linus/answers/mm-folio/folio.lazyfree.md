- `folio_test_lazyfree()` in `include/linux/page-flags.h`: the predicate for
  this state; `shrink_folio_list()` and `try_to_unmap_one()` use it.
- `VM_DROPPABLE` VMA: `folio_add_new_anon_rmap()` leaves `PG_swapbacked`
  clear, so its anon folios are lazyfree from their first mapping, with no
  `MADV_FREE`.
- `folio_mark_lazyfree()`: silently skips a folio with `PG_lru` clear, such as
  one isolated or still in another CPU's `lru_add` batch;
  `madvise_free_single_vma()` calls `lru_add_drain()` first, which covers
  this CPU only.
- `folio_mark_lazyfree()` on an active folio: accepted; `lru_lazyfree()`
  clears `PG_active`.
- `lru_lazyfree()`: repeats the tests at drain; a folio that fails them, or
  was isolated while queued, is left unchanged.
- `ttu_anon_lazyfree_folio()` in `mm/rmap.c`: holds the dirty and refcount
  tests; `try_to_unmap_one()` reaches it through `ttu_anon_folio()`.
- `ttu_anon_lazyfree_folio()` returning false: `try_to_unmap_one()` restores
  the PTEs with `set_ptes()` and aborts the walk.
- `VM_DROPPABLE` in `ttu_anon_lazyfree_folio()`: the dirty test is skipped, so
  a dirty folio is discarded; only the refcount test there can keep it.
- Refcount test failing in `ttu_anon_lazyfree_folio()` with a clean folio: the
  folio stays lazyfree, and `shrink_folio_list()` sets `PG_active` on it at
  `activate_locked`.
- PMD-mapped lazyfree folio: `try_to_unmap_one()` calls
  `unmap_huge_pmd_locked()` in `mm/huge_memory.c`, which applies the same
  dirty and refcount tests in `__discard_anon_folio_pmd_locked()`.
- PMD-mapped marking: `madvise_free_huge_pmd()` calls
  `folio_mark_lazyfree()`.
