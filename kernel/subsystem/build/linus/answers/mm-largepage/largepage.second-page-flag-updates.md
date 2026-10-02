- `PG_has_hwpoisoned`, `PG_large_rmappable`, `PG_partially_mapped`: declared
  with `FOLIO_FLAG()` only. No `__FOLIO_SET_FLAG` or `__FOLIO_CLEAR_FLAG` line
  uses `FOLIO_SECOND_PAGE`, so no non-atomic setter or clearer exists for
  them.
- Bits 0-7 of the same word: the folio order, read by `folio_large_order()`.
  The mapcounts are separate fields, not part of the word.
- `folio_set_order()` in `mm/internal.h` and `folio_reset_order()` in
  `include/linux/mm.h`: plain read-modify-write of all of `folio->_flags_1`.
- `__free_pages_prepare()` in `mm/page_alloc.c`: clears `PAGE_FLAGS_SECOND`
  from page 1 with a plain `&=`.
- Per-page flags of page 1, written with atomic bit operations: for example
  `PG_anon_exclusive` under the page table lock, `PG_hwpoison`, and arm64
  `PG_mte_tagged`.
- `memory_failure()`: calls `TestSetPageHWPoison()` before
  `get_hwpoison_page()`, so it can write the word while holding no reference.
- A new second-page flag: must avoid bits 0-7 and any `PF_ANY` flag; one that
  aliases a flag in `PAGE_FLAGS_CHECK_AT_FREE`, as `PG_has_hwpoisoned` aliases
  `PG_active`, must be in `PAGE_FLAGS_SECOND`, which `__free_pages_prepare()`
  clears from page 1 before `free_page_is_bad()` tests that page.
- **Unsafe usage**: a non-atomic setter or clearer for a `FOLIO_SECOND_PAGE`
  flag, used on a folio that can be mapped.
  - Unsafe: `SetPageAnonExclusive()` on page 1 is a concurrent `set_bit()` on
    the same word that holds only the page table lock.
  - Safe: the atomic `folio_set_partially_mapped()`, as
    `deferred_split_folio()` uses it; `FOLIO_SET_FLAG` declares it with
    `set_bit()`.
