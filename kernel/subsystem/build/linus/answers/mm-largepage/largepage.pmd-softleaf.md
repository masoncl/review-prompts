- Kinds: migration and device-private only; `softleaf_is_valid_pmd_entry()` in
  `include/linux/leafops.h` defines the set.
- Config: `CONFIG_ARCH_HAS_PMD_SOFTLEAVES`; there is no
  CONFIG_ARCH_ENABLE_THP_MIGRATION here. `thp_migration_supported()` tests it.
- Without `CONFIG_ARCH_HAS_PMD_SOFTLEAVES`: `softleaf_from_pmd()` returns the
  none entry, and `set_pmd_migration_entry()` is a `BUILD_BUG()` stub.
- `pmd_is_device_private_entry()`: also needs `CONFIG_ZONE_DEVICE`, constant
  false otherwise.
- There is no is_pmd_migration_entry() or pmd_to_swp_entry() here;
  `pmd_is_migration_entry()` and `softleaf_from_pmd()` do those jobs.
- There is no pmd_swp_uffd_wp() or pmd_swp_mkuffd_wp() here; the helpers are
  `pmd_swp_uffd()`, `pmd_swp_mkuffd()`, `pmd_swp_clear_uffd()`, and `pmd_uffd()`
  for a present PMD.
- The uffd bit serves both write-protect and RWP; `userfaultfd_huge_pmd_wp()`
  and `userfaultfd_huge_pmd_rwp()` tell them apart by the VMA.
- There is no pmd_none_or_trans_huge_or_clear_bad() here.
- `softleaf_from_pmd()`: returns the none entry for a present or none PMD.
- `softleaf_from_pmd()`: strips the soft-dirty and uffd bits; read them from the
  PMD with `pmd_swp_soft_dirty()` and `pmd_swp_uffd()`.
- `pmd_to_softleaf_folio()`: decodes a PMD to a folio; returns NULL, with a
  `VM_WARN_ON_ONCE()`, for an entry that is not a valid PMD softleaf.
- `softleaf_to_folio()` and `softleaf_to_page()` on a migration entry:
  `VM_WARN_ON_ONCE()` if the folio is not locked; see
  `softleaf_migration_sync()`.
- Migration PMD: holds no folio reference and no mapcount.
- Device-private PMD: holds a reference and a PMD mapcount; see
  `zap_huge_pmd_folio()`.
- `set_pmd_migration_entry()`: accepts a present PMD or a device-private PMD,
  and anonymous or file folios.
- `set_pmd_migration_entry()`: returns 0 and does nothing unless `pvmw` is at a
  PMD mapping; returns `-EBUSY`, with the PMD restored, only when
  `folio_try_share_anon_rmap_pmd()` fails.
