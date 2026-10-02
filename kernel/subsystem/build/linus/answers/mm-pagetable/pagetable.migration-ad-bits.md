- `migration_entry_supports_ad()`: returns `swap_migration_ad_supported`,
  which `swapfile_init()` sets when
  `swapfile_maximum_size >= (1UL << SWP_MIG_TOTAL_BITS)`; it has nothing to do
  with THP migration support.
- `CONFIG_SWAP` off: `migration_entry_supports_ad()` returns false, so no
  migration entry carries A/D.
- Test helpers: `softleaf_is_migration_young()` and
  `softleaf_is_migration_dirty()` in `include/linux/leafops.h`; there is no
  is_migration_entry_young() or is_migration_entry_dirty() here.
- Unsupported case: the makers return the entry unchanged and the tests
  return false, so the PTE comes back old and clean; the dirtiness is kept on
  the folio, which `try_to_migrate_one()` marked with `folio_mark_dirty()`
  when it replaced a dirty PTE.
- Source entry not present: `try_to_migrate_one()`,
  `set_pmd_migration_entry()` and `migrate_vma_collect_pmd()` set the bits
  only when the replaced entry was present, so a device-private entry turned
  into a migration entry records neither.
- Dirty on removal: `remove_migration_pte()` and `remove_migration_pmd()`
  call the mkdirty helper only when `folio_test_dirty(folio)` and
  `softleaf_is_migration_dirty(entry)` both hold.
