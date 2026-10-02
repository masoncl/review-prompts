- There is no do_set_pte() here; `set_pte_range()` in `mm/memory.c` installs
  file and shmem entries.
- `set_pte_range()` calls `pte_sw_mkyoung()`, not `pte_mkyoung()`.
- `pte_sw_mkyoung()`: only `arch/mips` defines it as `pte_mkyoung()`; the
  generic one in `include/linux/pgtable.h` returns the entry unchanged.
- Anonymous fault: `pte_sw_mkyoung()` is called in `map_anon_folio_pte_nopf()`,
  not in `do_anonymous_page()`.
- `ptep_set_access_flags()` on x86 (`arch/x86/mm/pgtable.c`): writes the entry
  only when `dirty` is non-zero, so the `pte_mkyoung()` in `handle_pte_fault()`
  is not stored on a read fault.
- There is no is_migration_entry_young() here; `remove_migration_pte()` tests
  `softleaf_is_migration_young()` from `include/linux/leafops.h`.
