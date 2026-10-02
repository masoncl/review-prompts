- uffd carry: `pte_swp_uffd()` to `pte_mkuffd()`, `pmd_swp_uffd()` to
  `pmd_mkuffd()`; there is no pte_swp_uffd_wp() or pte_mkuffd_wp() here.
- `pte_mkuffd()`: also write-protects on x86, arm64 and riscv.
- RWP restore: when the old entry has the swap uffd bit and
  `userfaultfd_rwp(vma)`, the new entry gets `pte_modify(pte, PAGE_NONE)`
  (`pmd_modify()` for a PMD) after the uffd bit is set, so the first access
  still faults.
- `do_swap_page()` on an RWP restore: also skips `pte_mkwrite()` and skips the
  `do_wp_page()` call for a write fault.
- Sites that carry soft-dirty and uffd and do the RWP restore:
  `do_swap_page()` and `restore_exclusive_pte()` in `mm/memory.c`,
  `remove_migration_pte()` and `try_to_map_unused_to_zeropage()` in
  `mm/migrate.c`, `unuse_pte()` in `mm/swapfile.c`, `remove_migration_pmd()`
  in `mm/huge_memory.c`.
- `migrate_vma_insert_page()`: not such a site; it bails out on any
  non-present, non-empty PTE.
- `remove_migration_pte()`: sets uffd only when the entry is not a write
  entry (`else if`); `remove_migration_pmd()` tests write and uffd
  independently.
