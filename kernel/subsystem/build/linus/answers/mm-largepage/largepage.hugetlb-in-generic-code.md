- `try_to_unmap()` in `mm/rmap.c`: installs
  `try_to_unmap_poisoned_hugetlb_one()` as the callback for a hugetlb folio;
  `try_to_unmap_one()` is not reached with one.
- `try_to_unmap_one()`: its hwpoison and unmap paths use `set_pte_at()`,
  `dec_mm_counter()` and `folio_remove_rmap_ptes()`, so a new caller must go
  through `try_to_unmap()`.
- `try_to_unmap_poisoned_hugetlb_one()`: expects `TTU_HWPOISON` and a
  hwpoisoned folio, and calls `page_vma_mapped_walk()` once, not in a loop.
- `try_to_migrate_one()`: still handles hugetlb inline, branching on
  `folio_test_hugetlb()`.
- `page_vma_mapped_walk()`: both callbacks use it; for a hugetlb VMA it
  returns the one entry in `pvmw.pte` under `huge_pte_lock()`.
- Hugetlb VMA lock in the callbacks: `hugetlb_vma_trylock_write()`, only for
  a non-anon folio and only around `huge_pmd_unshare()`; it is dropped before
  the entry is cleared.
- `huge_pmd_unshare()`: takes a `struct mmu_gather *` first; the callbacks
  bracket it with `tlb_gather_mmu_vma()` and `tlb_finish_mmu()`.
- `huge_pmd_unshare()` returning 1: the callback calls
  `huge_pmd_unshare_flush()` and ends the walk; `huge_pmd_unshare_flush()`
  asserts `i_mmap_rwsem` is still write-held.
- Clearing the entry: `huge_ptep_clear_flush()`; the callbacks call neither
  `huge_ptep_get_and_clear()` nor `flush_hugetlb_tlb_range()`.
- `hugetlb_folio_mapping_lock_write()`: a trylock on `i_mmap_rwsem`; it
  returns NULL on contention and the caller must give up.
- `remove_migration_ptes()`: must get the same `TTU_RMAP_LOCKED`, so that it
  uses `rmap_walk_locked()` while the caller still holds `i_mmap_rwsem`.
- There is no unmap_and_move_huge_page() here;
  `unmap_and_move_hugetlb_folio()` in `mm/migrate.c` does that.
- **Unsafe usage**: `try_to_migrate()` or `try_to_unmap()` on a non-anon
  hugetlb folio without `i_mmap_rwsem` write-held and `TTU_RMAP_LOCKED`.
  - Safe: take `hugetlb_folio_mapping_lock_write()` on the locked folio and
    pass `TTU_RMAP_LOCKED`, as `unmap_and_move_hugetlb_folio()` and
    `unmap_poisoned_folio()` do; `__huge_pmd_unshare()` asserts the lock.
  - Safe: an anon hugetlb folio needs neither; both callbacks skip the
    unshare when `folio_test_anon()` is true.
