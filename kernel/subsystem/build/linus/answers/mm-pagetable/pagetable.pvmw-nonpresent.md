- There is no is_migration_entry(), is_device_private_entry(),
  is_pmd_migration_entry() or swp_offset_pfn() here; `check_pte()` uses
  `softleaf_from_pte()`, `softleaf_is_migration()`,
  `softleaf_is_device_private()`, `softleaf_is_device_exclusive()` and
  `softleaf_to_pfn()` from `include/linux/leafops.h`.
- Device-exclusive PTE: a non-present entry (`SOFTLEAF_DEVICE_EXCLUSIVE`);
  returned without `PVMW_MIGRATION`, never with it.
- Device-private PTE: returned without `PVMW_MIGRATION`, never with it.
- Device-private PMD: returned with `pvmw->pte` NULL without
  `PVMW_MIGRATION`, after `check_pmd()` on `softleaf_to_pfn()`; with the flag
  the walk returns false.
- Migration PMD: the walker does not call `thp_migration_supported()`; the
  gate is `IS_ENABLED(CONFIG_TRANSPARENT_HUGEPAGE)` plus
  `pmd_is_migration_entry()`, which is false without
  `CONFIG_ARCH_HAS_PMD_SOFTLEAVES`.
- PMD leaf of the wrong kind for the flag, or one that fails `check_pmd()`:
  `page_vma_mapped_walk()` returns false at once through `not_found()`; it
  does not `step_forward()` to the next PMD.
- Non-present PMD of any other kind with `PVMW_SYNC`:
  `sync_with_folio_pmd_zap()` runs only when `thp_vma_suitable_order()` holds
  and `pvmw->nr_pages >= HPAGE_PMD_NR`.
