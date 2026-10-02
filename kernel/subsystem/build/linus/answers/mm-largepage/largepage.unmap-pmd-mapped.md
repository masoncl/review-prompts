- PMD mapping reached in `try_to_unmap_one()` without `TTU_SPLIT_HUGE_PMD`:
  the only check is `VM_BUG_ON_FOLIO(!pvmw.pte, folio)`; without
  `CONFIG_DEBUG_VM` it compiles out and `ptep_get()` reads through a NULL
  `pvmw.pte`.
- `VM_LOCKED` VMA without `TTU_IGNORE_MLOCK`: handled before the PMD branch;
  the PMD is not split, `mlock_vma_folio()` runs and the walk ends as failed.
- `folio_test_lazyfree()` folio: tested before `TTU_SPLIT_HUGE_PMD`, with or
  without the flag; `unmap_huge_pmd_locked()` discards the PMD mapping.
- `unmap_huge_pmd_locked()` failure: the walk aborts; the PMD is not split even
  with the flag.
- MMU notifier range: `address` to `vma_address_end()`; it does not depend on
  `TTU_SPLIT_HUGE_PMD`.
- `try_to_migrate_one()` with the flag: `split_huge_pmd_locked()` with `freeze`
  true, then a restart.
- `try_to_migrate_one()` without the flag: `set_pmd_migration_entry()` under
  `CONFIG_ARCH_HAS_PMD_SOFTLEAVES`; a failure aborts the walk, there is no
  fallback to a split.
- **Potentially unsafe usage**: `try_to_unmap()` without `TTU_SPLIT_HUGE_PMD`.
  - Unsafe: when the folio can be PMD-mapped and is not lazyfree;
    `try_to_unmap_one()` reaches `VM_BUG_ON_FOLIO(!pvmw.pte, folio)`.
  - Safe: when the folio cannot be PMD order; `collapse_file()` rejects
    `is_pmd_order()` folios before the call.
  - Safe: set the flag for `folio_test_pmd_mappable()` folios, as
    `shrink_folio_list()` and `unmap_folio()` do.
