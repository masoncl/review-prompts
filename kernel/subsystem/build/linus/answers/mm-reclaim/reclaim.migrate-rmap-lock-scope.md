- In-tree callers that pass `TTU_RMAP_LOCKED` to `try_to_migrate()`:
  `unmap_and_move_hugetlb_folio()` in `mm/migrate.c` and
  `unmap_folio()` in `mm/huge_memory.c`. There is no
  unmap_and_move_huge_page().
- `unmap_folio()`: passes `TTU_RMAP_LOCKED` to `try_to_migrate()` for anon
  folios only. `__folio_split()` holds `anon_vma_lock_write()` and a reference
  from `folio_get_anon_vma()`.
- `unmap_and_move_hugetlb_folio()`: holds `i_mmap_rwsem` for write across
  `try_to_migrate()`, `move_to_new_folio()` and `remove_migration_ptes()`.
  It unlocks only after the remap.
- Anon folio: `folio_anon_vma()` must be non-NULL; `rmap_walk_anon()` does
  `VM_BUG_ON_FOLIO()` otherwise. `__folio_split()` returns `-EBUSY` first.
- Folio lock: required; `rmap_walk_file()` and `rmap_walk_anon()` assert it.
- **Unsafe usage**: `try_to_migrate()` on a file-backed hugetlb folio without
  `TTU_RMAP_LOCKED`. `try_to_migrate_one()` does `VM_BUG_ON()` on it.
  - Safe: take `hugetlb_folio_mapping_lock_write()` and pass the flag, as
    `unmap_and_move_hugetlb_folio()` does.
- **Unsafe usage**: calling `remove_migration_ptes()` without
  `TTU_RMAP_LOCKED` while the rmap lock is still held. `rmap_walk()` takes
  the same rwsem again.
  - Safe: pass the flag, as `remap_page()` and
    `unmap_and_move_hugetlb_folio()` do; `rmap_walk_locked()` skips the
    lock.
