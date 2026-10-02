- There is no is_writable_migration_entry(),
  is_readable_exclusive_migration_entry() or
  is_writable_device_private_entry() here; use
  `softleaf_is_migration_write()`, `softleaf_is_migration_read_exclusive()`
  and `softleaf_is_device_private_write()`.
- There is no ptep_clear_flush_young_notify() here;
  `clear_flush_young_ptes_notify()` in `mm/internal.h` takes a count of PTEs.
- `softleaf_from_pte()`: strips soft-dirty, uffd and exclusive bits with
  `pte_swp_clear_flags()`, so read them from the `pte_t` with
  `pte_swp_soft_dirty()` and `pte_swp_uffd()`, not from the `softleaf_t`.
- `pte_swp_exclusive()`: used by no rmap callback; `try_to_migrate_one()`
  takes exclusivity from `PageAnonExclusive()` on the subpage, and
  `remove_migration_pte()` from the entry type
  (`!softleaf_is_migration_read(entry)` on an anon folio).
- **Potentially unsafe usage**: `pte_pfn()`, `pte_write()`, `pte_young()`,
  `pte_dirty()`, `pte_soft_dirty()` or `pte_uffd()` on the returned entry of a
  walk without `PVMW_MIGRATION`.
  - Unsafe: with no `pte_present()` test, when the folio can be mapped by a
    device-private or device-exclusive entry; `make_device_exclusive()`
    accepts any anonymous non-hugetlb folio.
  - Safe: after a `pte_present()` test, with the softleaf helpers on the
    other branch, as `try_to_migrate_one()` and `try_to_unmap_one()` do;
    `check_pte()` defines which non-present kinds are returned.
  - Safe: skipping the entry when `!pte_present()`, as
    `page_vma_mkclean_one()` and `write_protect_page()` in `mm/ksm.c` do.
- PMD level, present and non-present: `set_pmd_migration_entry()` in
  `mm/huge_memory.c`, called from `try_to_migrate_one()`, and
  `damon_pmdp_mkold()` in `mm/damon/ops-common.c`.
