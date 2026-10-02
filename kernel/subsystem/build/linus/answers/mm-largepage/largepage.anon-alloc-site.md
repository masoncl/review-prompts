- `add_mm_counter()` for `MM_ANONPAGES` and `MTHP_STAT_ANON_FAULT_ALLOC`: done
  by the static wrappers `map_anon_folio_pmd_pf()` and
  `map_anon_folio_pte_pf()`; `THP_FAULT_ALLOC` and `count_memcg_event_mm()` by
  `map_anon_folio_pmd_pf()` only.
- Caller of a `_nopf` helper: does its own `MM_ANONPAGES` update; the collapse
  does it in `__collapse_huge_page_copy_succeeded()` in `mm/khugepaged.c`.
- `update_mmu_cache_pmd()` and `update_mmu_cache_range()`: called inside the
  `_nopf` helpers, not left to the caller.
- `deferred_split_folio(folio, false)`: called inside
  `map_anon_folio_pmd_nopf()`; `map_anon_folio_pte_nopf()` does not call it.
- `mm_inc_nr_ptes()` and `pgtable_trans_huge_deposit()`: left to the caller of
  `map_anon_folio_pmd_nopf()`; see `__do_huge_pmd_anonymous_page()`.
- References: `map_anon_folio_pte_nopf()` adds `nr_pages - 1` with
  `folio_ref_add()`; `map_anon_folio_pmd_nopf()` adds none; both consume the
  caller's allocation reference, so an error path before the helper needs one
  `folio_put()`.
- `map_anon_folio_pte_nopf()` from a non-fault caller: takes no page table
  lock itself; `collapse_huge_page()` re-installs the table with
  `pmd_populate()` and holds the PTE lock, nested inside the PMD lock, around
  the call, because the helper calls `update_mmu_cache_range()`, which walks
  the page table on MIPS (`__update_tlb()`).
- Entry construction: `folio_mk_pmd()` and `folio_mk_pte()`; there is no
  mk_pmd() in this tree.
- Error paths after the charge in `__do_huge_pmd_anonymous_page()` (`release`,
  `unlock_release`, the `userfaultfd_missing()` branch): count no fallback
  stat; the failure branches inside `vma_alloc_anon_folio_pmd()` count
  `THP_FAULT_FALLBACK` and `MTHP_STAT_ANON_FAULT_FALLBACK`.
