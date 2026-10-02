- `PG_large_rmappable`: there is no folio_prep_large_rmappable() or
  folio_undo_large_rmappable() here; `page_rmappable_folio()` in
  `mm/internal.h` sets the flag.
- `page_rmappable_folio()`: runs in `__folio_alloc_noprof()`,
  `folio_alloc_noprof()`, `folio_alloc_mpol_noprof()` and
  `compaction_alloc_noprof()`, so any large folio from those has the flag,
  whoever allocated it.
- `alloc_pages()` with `__GFP_COMP`: does not set the flag.
- Other setters of the flag: `__split_folio_to_order()` for each new large
  folio, `zone_device_folio_init()`, and
  `migrate_vma_insert_huge_pmd_page()` in `mm/migrate_device.c`.
- Huge zero folio: large and PMD-order, but `alloc_huge_zero_folio()` clears
  the flag; `is_transparent_hugepage()` in `mm/huge_memory.c` tests for it
  separately.
- `__folio_rmap_sanity_checks()`: does not test `folio_test_large_rmappable()`,
  so the rmap functions accept large folios without the flag.
- Without `CONFIG_TRANSPARENT_HUGEPAGE`: `folio_test_pmd_mappable()` and
  `folio_test_large_rmappable()` are constant `false`, hugetlb included, and
  `folio_set_large_rmappable()` is empty.
- `folio_test_large_rmappable()` on a folio not known to be large: only
  `VM_BUG_ON_PGFLAGS()` in `const_folio_flags()` catches it; without
  `CONFIG_DEBUG_VM_PGFLAGS` it reads the flags of the next `struct page`.
