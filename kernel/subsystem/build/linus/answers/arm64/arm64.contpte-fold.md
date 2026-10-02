- `__flush_tlb_range()`: `contpte_convert()` passes `PAGE_SIZE`, level 3 and
  `TLBF_NOWALKCACHE`.
- `contpte_try_fold()`: has one caller, `set_ptes()` with `nr == 1`;
  write-protect paths never fold.
- Fold tests: the inline tests `pte_valid()`, not `PTE_USER`;
  `__contpte_try_fold()` then tests `mm_is_user(mm)` and that one folio covers
  the whole block, before it compares entries.
- `contpte_set_ptes()` (`set_ptes()` with `nr > 1`): writes `PTE_CONT`
  directly on every naturally aligned full block of a user mm, with no clear
  and no invalidation; it has no folio or special test of its own.
- Never unfold, act on the whole block instead:
  `contpte_test_and_clear_young_ptes()`, `contpte_clear_flush_young_ptes()`,
  `contpte_clear_young_dirty_ptes()`.
